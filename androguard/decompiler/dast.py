# This file is part of Androguard.
#
# Copyright (C) 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file is a simplified version of writer.py that outputs an AST instead of source code."""
import struct

from loguru import logger

from androguard.core.dex.dex_types import TYPE_DESCRIPTOR
from androguard.decompiler import basic_blocks, instruction, opcode_ins


class JSONWriter:
    def __init__(self, graph, method):
        self.graph = graph
        self.method = method

        self.visited_nodes = set()
        self.loop_follow = [None]
        self.if_follow = [None]
        self.switch_follow = [None]
        self.latch_node = [None]
        self.try_follow = [None]
        self.next_case = None
        self.need_break = True
        self.constructor = False

        self.context = []

    # This class is created as a context manager so that it can be used like
    # with self as foo:
    #   ...
    # which pushes a statement block on to the context stack and assigns it to foo
    # within the with block, all added instructions will be added to foo
    def __enter__(self):
        self.context.append(self.statement_block())
        return self.context[-1]

    def __exit__(self, *args):
        self.context.pop()
        return False

    # Add a statement to the current context
    def add(self, val):
        self._append(self.context[-1], val)

    def visit_ins(self, op):
        self.add(self._visit_ins(op, isCtor=self.constructor))

    # Note: this is a mutating operation
    def get_ast(self):
        m = self.method
        flags = m.access
        if 'constructor' in flags:
            flags.remove('constructor')
            self.constructor = True

        params = m.lparams[:]
        if 'static' not in m.access:
            params = params[1:]

        # DAD doesn't create any params for abstract methods
        if len(params) != len(m.params_type):
            assert 'abstract' in flags or 'native' in flags
            assert not params
            params = list(range(len(m.params_type)))

        paramdecls = []
        for ptype, name in zip(m.params_type, params):
            t = self.parse_descriptor(ptype)
            v = self.local('p{}'.format(name))
            paramdecls.append(self.var_decl(t, v))

        if self.graph is None:
            body = None
        else:
            with self as body:
                self.visit_node(self.graph.entry)

        return {
            'triple': m.triple,
            'flags': flags,
            'ret': self.parse_descriptor(m.type),
            'params': paramdecls,
            'comments': [],
            'body': body,
        }

    def _visit_condition(self, cond):
        if cond.isnot:
            cond.cond1.neg()
        left = self.parenthesis(self.get_cond(cond.cond1))
        right = self.parenthesis(self.get_cond(cond.cond2))
        op = '&&' if cond.isand else '||'
        res = self.binary_infix(op, left, right)
        return res

    def get_cond(self, node):
        if isinstance(node, basic_blocks.ShortCircuitBlock):
            return self._visit_condition(node.cond)
        elif isinstance(node, basic_blocks.LoopBlock):
            return self.get_cond(node.cond)
        else:
            assert type(node) == basic_blocks.CondBlock
            assert len(node.ins) == 1
            return self.visit_expr(node.ins[-1])

    def visit_node(self, node):
        if node in (
            self.if_follow[-1],
            self.switch_follow[-1],
            self.loop_follow[-1],
            self.latch_node[-1],
            self.try_follow[-1],
        ):
            return
        if not node.type.is_return and node in self.visited_nodes:
            return
        self.visited_nodes.add(node)
        for var in node.var_to_declare:
            if not var.declared:
                self.add(self.visit_decl(var))
            var.declared = True
        node.visit(self)

    def visit_loop_node(self, loop):
        isDo = cond_expr = body = None

        follow = loop.follow['loop']
        if loop.looptype.is_pretest:
            if loop.true is follow:
                loop.neg()
                loop.true, loop.false = loop.false, loop.true
            isDo = False
            cond_expr = self.get_cond(loop)

        elif loop.looptype.is_posttest:
            isDo = True
            self.latch_node.append(loop.latch)

        elif loop.looptype.is_endless:
            isDo = False
            cond_expr = self.literal_bool(True)

        with self as body:
            self.loop_follow.append(follow)
            if loop.looptype.is_pretest:
                self.visit_node(loop.true)
            else:
                self.visit_node(loop.cond)
            self.loop_follow.pop()

            if loop.looptype.is_pretest:
                pass
            elif loop.looptype.is_posttest:
                self.latch_node.pop()
                cond_expr = self.get_cond(loop.latch)
            else:
                self.visit_node(loop.latch)

        assert cond_expr is not None and isDo is not None
        self.add(self.loop_stmt(isDo, cond_expr, body))
        if follow is not None:
            self.visit_node(follow)

    def visit_cond_node(self, cond):
        cond_expr = None
        scopes = []

        follow = cond.follow['if']
        if cond.false is cond.true:
            self.add(self.expression_stmt(self.get_cond(cond)))
            self.visit_node(cond.true)
            return

        if cond.false is self.loop_follow[-1]:
            cond.neg()
            cond.true, cond.false = cond.false, cond.true

        if self.loop_follow[-1] in (cond.true, cond.false):
            cond_expr = self.get_cond(cond)
            with self as scope:
                self.add(self.jump_stmt('break'))
            scopes.append(scope)

            with self as scope:
                self.visit_node(cond.false)
            scopes.append(scope)

            self.add(self.if_stmt(cond_expr, scopes))
        elif follow is not None:
            if (
                cond.true in (follow, self.next_case)
                or cond.num > cond.true.num
            ):
                # or cond.true.num > cond.false.num:
                cond.neg()
                cond.true, cond.false = cond.false, cond.true
            self.if_follow.append(follow)
            if cond.true:  # in self.visited_nodes:
                cond_expr = self.get_cond(cond)
                with self as scope:
                    self.visit_node(cond.true)
                scopes.append(scope)

            is_else = not (follow in (cond.true, cond.false))
            if is_else and cond.false not in self.visited_nodes:
                with self as scope:
                    self.visit_node(cond.false)
                scopes.append(scope)
            self.if_follow.pop()

            self.add(self.if_stmt(cond_expr, scopes))
            self.visit_node(follow)
        else:
            cond_expr = self.get_cond(cond)
            with self as scope:
                self.visit_node(cond.true)
            scopes.append(scope)

            with self as scope:
                self.visit_node(cond.false)
            scopes.append(scope)
            self.add(self.if_stmt(cond_expr, scopes))

    def visit_switch_node(self, switch):
        lins = switch.get_ins()
        for ins in lins[:-1]:
            self.visit_ins(ins)
        switch_ins = switch.get_ins()[-1]

        cond_expr = self.visit_expr(switch_ins)
        ksv_pairs = []

        follow = switch.follow['switch']
        cases = switch.cases
        self.switch_follow.append(follow)
        default = switch.default
        for i, node in enumerate(cases):
            if node in self.visited_nodes:
                continue

            cur_ks = switch.node_to_case[node][:]
            if i + 1 < len(cases):
                self.next_case = cases[i + 1]
            else:
                self.next_case = None

            if node is default:
                cur_ks.append(None)
                default = None

            with self as body:
                self.visit_node(node)
                if self.need_break:
                    self.add(self.jump_stmt('break'))
                else:
                    self.need_break = True
            ksv_pairs.append((cur_ks, body))

        if default not in (None, follow):
            with self as body:
                self.visit_node(default)
            ksv_pairs.append(([None], body))

        self.add(self.switch_stmt(cond_expr, ksv_pairs))
        self.switch_follow.pop()
        self.visit_node(follow)

    def visit_statement_node(self, stmt):
        sucs = self.graph.sucs(stmt)
        for ins in stmt.get_ins():
            self.visit_ins(ins)
        if len(sucs) == 1:
            if sucs[0] is self.loop_follow[-1]:
                self.add(self.jump_stmt('break'))
            elif sucs[0] is self.next_case:
                self.need_break = False
            else:
                self.visit_node(sucs[0])

    def visit_try_node(self, try_node):
        with self as tryb:
            self.try_follow.append(try_node.follow)
            self.visit_node(try_node.try_start)

        pairs = []
        for catch_node in try_node.catch:
            if catch_node.exception_ins:
                ins = catch_node.exception_ins
                assert isinstance(ins, instruction.MoveExceptionExpression)
                var = ins.var_map[ins.ref]
                var.declared = True

                ctype = var.get_type()
                name = 'v{}'.format(var.name)
            else:
                ctype = catch_node.catch_type
                name = '_'
            catch_decl = self.var_decl(
                self.parse_descriptor(ctype), self.local(name)
            )

            with self as body:
                self.visit_node(catch_node.catch_start)
            pairs.append((catch_decl, body))

        self.add(self.try_stmt(tryb, pairs))
        self.visit_node(self.try_follow.pop())

    def visit_return_node(self, ret):
        self.need_break = False
        for ins in ret.get_ins():
            self.visit_ins(ins)

    def visit_throw_node(self, throw):
        for ins in throw.get_ins():
            self.visit_ins(ins)

    def _visit_ins(self, op, isCtor=False):
        if isinstance(op, instruction.ReturnInstruction):
            expr = (
                None if op.arg is None else self.visit_expr(op.var_map[op.arg])
            )
            return self.return_stmt(expr)
        elif isinstance(op, instruction.ThrowExpression):
            return self.throw_stmt(self.visit_expr(op.var_map[op.ref]))
        elif isinstance(op, instruction.NopExpression):
            return None

        # Local var decl statements
        if isinstance(
            op,
            (
                instruction.AssignExpression,
                instruction.MoveExpression,
                instruction.MoveResultExpression,
            ),
        ):
            lhs = op.var_map.get(op.lhs)
            rhs = (
                op.rhs
                if isinstance(op, instruction.AssignExpression)
                else op.var_map.get(op.rhs)
            )
            if isinstance(lhs, instruction.Variable) and not lhs.declared:
                lhs.declared = True
                expr = self.visit_expr(rhs)
                return self.visit_decl(lhs, expr)

        # skip this() at top of constructors
        if isCtor and isinstance(op, instruction.AssignExpression):
            op2 = op.rhs
            if op.lhs is None and isinstance(
                op2, instruction.InvokeInstruction
            ):
                if op2.name == '<init>' and len(op2.args) == 0:
                    if isinstance(
                        op2.var_map[op2.base], instruction.ThisParam
                    ):
                        return None

        # MoveExpression is skipped when lhs = rhs
        if isinstance(op, instruction.MoveExpression):
            if op.var_map.get(op.lhs) is op.var_map.get(op.rhs):
                return None

        return self.expression_stmt(self.visit_expr(op))

    def write_inplace_if_possible(self, lhs, rhs):
        if (
            isinstance(rhs, instruction.BinaryExpression)
            and lhs == rhs.var_map[rhs.arg1]
        ):
            exp_rhs = rhs.var_map[rhs.arg2]
            # post increment/decrement
            if (
                rhs.op in '+-'
                and isinstance(exp_rhs, instruction.Constant)
                and exp_rhs.get_int_value() == 1
            ):
                return self.unary_postfix(self.visit_expr(lhs), rhs.op * 2)
            # compound assignment
            return self.assignment(
                self.visit_expr(lhs), self.visit_expr(exp_rhs), op=rhs.op
            )
        return self.assignment(self.visit_expr(lhs), self.visit_expr(rhs))

    def visit_expr(self, op):
        if isinstance(op, instruction.ArrayLengthExpression):
            expr = self.visit_expr(op.var_map[op.array])
            return self.field_access([None, 'length', None], expr)
        if isinstance(op, instruction.ArrayLoadExpression):
            array_expr = self.visit_expr(op.var_map[op.array])
            index_expr = self.visit_expr(op.var_map[op.idx])
            return self.array_access(array_expr, index_expr)
        if isinstance(op, instruction.ArrayStoreInstruction):
            array_expr = self.visit_expr(op.var_map[op.array])
            index_expr = self.visit_expr(op.var_map[op.index])
            rhs = self.visit_expr(op.var_map[op.rhs])
            return self.assignment(
                self.array_access(array_expr, index_expr), rhs
            )

        if isinstance(op, instruction.AssignExpression):
            lhs = op.var_map.get(op.lhs)
            rhs = op.rhs
            if lhs is None:
                return self.visit_expr(rhs)
            return self.write_inplace_if_possible(lhs, rhs)

        if isinstance(op, instruction.BaseClass):
            if op.clsdesc is None:
                assert op.cls == "super"
                return self.local(op.cls)
            return self.parse_descriptor(op.clsdesc)
        if isinstance(op, instruction.BinaryExpression):
            lhs = op.var_map.get(op.arg1)
            rhs = op.var_map.get(op.arg2)
            expr = self.binary_infix(
                op.op, self.visit_expr(lhs), self.visit_expr(rhs)
            )
            if not isinstance(op, instruction.BinaryCompExpression):
                expr = self.parenthesis(expr)
            return expr

        if isinstance(op, instruction.CheckCastExpression):
            lhs = op.var_map.get(op.arg)
            return self.parenthesis(
                self.cast(
                    self.parse_descriptor(op.clsdesc), self.visit_expr(lhs)
                )
            )
        if isinstance(op, instruction.ConditionalExpression):
            lhs = op.var_map.get(op.arg1)
            rhs = op.var_map.get(op.arg2)
            return self.binary_infix(
                op.op, self.visit_expr(lhs), self.visit_expr(rhs)
            )
        if isinstance(op, instruction.ConditionalZExpression):
            arg = op.var_map[op.arg]
            if isinstance(arg, instruction.BinaryCompExpression):
                arg.op = op.op
                return self.visit_expr(arg)

            expr = self.visit_expr(arg)
            atype = str(arg.get_type())
            if atype == 'Z':
                if op.op == opcode_ins.Op.EQUAL:
                    expr = self.unary_prefix('!', expr)
            elif atype in 'VBSCIJFD':
                expr = self.binary_infix(op.op, expr, self.literal_int(0))
            else:
                expr = self.binary_infix(op.op, expr, self.literal_null())
            return expr

        if isinstance(op, instruction.Constant):
            if op.type == 'Ljava/lang/String;':
                return self.literal_string(op.cst)
            elif op.type == 'Z':
                return self.literal_bool(op.cst == 0)
            elif op.type in 'ISCB':
                return self.literal_int(op.cst2)
            elif op.type in 'J':
                return self.literal_long(op.cst2)
            elif op.type in 'F':
                return self.literal_float(op.cst)
            elif op.type in 'D':
                return self.literal_double(op.cst)
            elif op.type == 'Ljava/lang/Class;':
                return self.literal_class(op.clsdesc)
            return self.dummy('??? Unexpected constant: ' + str(op.type))

        if isinstance(op, instruction.FillArrayExpression):
            array_expr = self.visit_expr(op.var_map[op.reg])
            rhs = self.visit_arr_data(op.value)
            return self.assignment(array_expr, rhs)
        if isinstance(op, instruction.FilledArrayExpression):
            tn = self.parse_descriptor(op.type)
            params = [self.visit_expr(op.var_map[x]) for x in op.args]
            return self.array_initializer(params, tn)
        if isinstance(op, instruction.InstanceExpression):
            triple = op.clsdesc[1:-1], op.name, op.ftype
            expr = self.visit_expr(op.var_map[op.arg])
            return self.field_access(triple, expr)
        if isinstance(op, instruction.InstanceInstruction):
            triple = op.clsdesc[1:-1], op.name, op.atype
            lhs = self.field_access(
                triple, self.visit_expr(op.var_map[op.lhs])
            )
            rhs = self.visit_expr(op.var_map[op.rhs])
            return self.assignment(lhs, rhs)

        if isinstance(op, instruction.InvokeInstruction):
            base = op.var_map[op.base]
            params = [op.var_map[arg] for arg in op.args]
            params = list(map(self.visit_expr, params))
            if op.name == '<init>':
                if isinstance(base, instruction.ThisParam):
                    keyword = (
                        'this' if base.type[1:-1] == op.triple[0] else 'super'
                    )
                    return self.method_invocation(
                        op.triple, keyword, None, params
                    )
                elif isinstance(base, instruction.NewInstance):
                    return [
                        'ClassInstanceCreation',
                        op.triple,
                        params,
                        self.parse_descriptor(base.type),
                    ]
                else:
                    assert isinstance(base, instruction.Variable)
                    # fallthrough to create dummy <init> call
            return self.method_invocation(
                op.triple, op.name, self.visit_expr(base), params
            )
        # for unmatched monitor instructions, just create dummy expressions
        if isinstance(op, instruction.MonitorEnterExpression):
            return self.dummy(
                "monitor enter(", self.visit_expr(op.var_map[op.ref]), ")"
            )
        if isinstance(op, instruction.MonitorExitExpression):
            return self.dummy(
                "monitor exit(", self.visit_expr(op.var_map[op.ref]), ")"
            )
        if isinstance(op, instruction.MoveExpression):
            lhs = op.var_map.get(op.lhs)
            rhs = op.var_map.get(op.rhs)
            return self.write_inplace_if_possible(lhs, rhs)
        if isinstance(op, instruction.MoveResultExpression):
            lhs = op.var_map.get(op.lhs)
            rhs = op.var_map.get(op.rhs)
            return self.assignment(self.visit_expr(lhs), self.visit_expr(rhs))
        if isinstance(op, instruction.NewArrayExpression):
            tn = self.parse_descriptor(op.type[1:])
            expr = self.visit_expr(op.var_map[op.size])
            return self.array_creation(tn, [expr], 1)
        # create dummy expression for unmatched newinstance
        if isinstance(op, instruction.NewInstance):
            return self.dummy("new ", self.parse_descriptor(op.type))
        if isinstance(op, instruction.Param):
            if isinstance(op, instruction.ThisParam):
                return self.local('this')
            return self.local('p{}'.format(op.v))
        if isinstance(op, instruction.StaticExpression):
            triple = op.clsdesc[1:-1], op.name, op.ftype
            return self.field_access(triple, self.parse_descriptor(op.clsdesc))
        if isinstance(op, instruction.StaticInstruction):
            triple = op.clsdesc[1:-1], op.name, op.ftype
            lhs = self.field_access(triple, self.parse_descriptor(op.clsdesc))
            rhs = self.visit_expr(op.var_map[op.rhs])
            return self.assignment(lhs, rhs)
        if isinstance(op, instruction.SwitchExpression):
            return self.visit_expr(op.var_map[op.src])
        if isinstance(op, instruction.UnaryExpression):
            lhs = op.var_map.get(op.arg)
            if isinstance(op, instruction.CastExpression):
                expr = self.cast(
                    self.parse_descriptor(op.clsdesc), self.visit_expr(lhs)
                )
            else:
                expr = self.unary_prefix(op.op, self.visit_expr(lhs))
            return self.parenthesis(expr)
        if isinstance(op, instruction.Variable):
            # assert(op.declared)
            return self.local('v{}'.format(op.name))
        return self.dummy('??? Unexpected op: ' + type(op).__name__)

    def visit_arr_data(self, value):
        data = value.get_data()
        tab = []
        elem_size = value.element_width
        if elem_size == 4:
            for i in range(0, value.size * 4, 4):
                tab.append(struct.unpack('<i', data[i : i + 4])[0])
        else:  # FIXME: other cases
            for i in range(value.size):
                tab.append(data[i])
        return self.array_initializer(list(map(self.literal_int, tab)))

    def visit_decl(self, var, init_expr=None):
        t = self.parse_descriptor(var.get_type())
        v = self.local('v{}'.format(var.name))
        return self.local_decl_stmt(init_expr, self.var_decl(t, v))

    @staticmethod
    def literal_null():
        return JSONWriter.literal('null', ('.null', 0))

    @staticmethod
    def literal_double(f):
        return JSONWriter.literal(str(f), ('.double', 0))

    @staticmethod
    def literal_float(f):
        return JSONWriter.literal(str(f) + 'f', ('.float', 0))

    @staticmethod
    def literal_long(b):
        return JSONWriter.literal(str(b) + 'L', ('.long', 0))

    @staticmethod
    def literal_hex_int(b):
        return JSONWriter.literal(hex(b), ('.int', 0))

    @staticmethod
    def literal_int(b):
        return JSONWriter.literal(str(b), ('.int', 0))

    @staticmethod
    def literal_bool(b):
        return JSONWriter.literal(str(b).lower(), ('.boolean', 0))

    @staticmethod
    def literal_class(desc):
        return JSONWriter.literal(
            JSONWriter.parse_descriptor(desc), ('java/lang/Class', 0)
        )

    @staticmethod
    def literal_string(s):
        return JSONWriter.literal(str(s), ('java/lang/String', 0))

    @staticmethod
    def parse_descriptor(desc: str) -> list:
        dim = 0
        while desc and desc[0] == '[':
            desc = desc[1:]
            dim += 1

        if desc in TYPE_DESCRIPTOR:
            return JSONWriter.typen('.' + TYPE_DESCRIPTOR[desc], dim)
        if desc and desc[0] == 'L' and desc[-1] == ';':
            return JSONWriter.typen(desc[1:-1], dim)
        # invalid descriptor (probably None)
        return JSONWriter.dummy(str(desc))

    @staticmethod
    def _append(sb, stmt):
        # Add a statement to the end of a statement block
        assert sb[0] == 'BlockStatement'
        if stmt is not None:
            sb[2].append(stmt)

    @staticmethod
    def statement_block():
        # Create empty statement block (statements to be appended later)
        # Note, the code below assumes this can be modified in place
        return ['BlockStatement', None, []]

    @staticmethod
    def switch_stmt(cond_expr, ksv_pairs):
        return ['SwitchStatement', None, cond_expr, ksv_pairs]

    @staticmethod
    def if_stmt(cond_expr, scopes):
        return ['IfStatement', None, cond_expr, scopes]

    @staticmethod
    def try_stmt(tryb, pairs):
        return ['TryStatement', None, tryb, pairs]

    @staticmethod
    def loop_stmt(isdo, cond_expr, body):
        type_ = 'DoStatement' if isdo else 'WhileStatement'
        return [type_, None, cond_expr, body]

    @staticmethod
    def jump_stmt(keyword):
        return ['JumpStatement', keyword, None]

    @staticmethod
    def throw_stmt(expr):
        return ['ThrowStatement', expr]

    @staticmethod
    def return_stmt(expr):
        return ['ReturnStatement', expr]

    @staticmethod
    def local_decl_stmt(expr, decl):
        return ['LocalDeclarationStatement', expr, decl]

    @staticmethod
    def expression_stmt(expr):
        return ['ExpressionStatement', expr]

    @staticmethod
    def dummy(*args):
        return ['Dummy', args]

    @staticmethod
    def var_decl(typen, var):
        return [typen, var]

    @staticmethod
    def unary_postfix(left, op):
        return ['Unary', [left], op, True]

    @staticmethod
    def unary_prefix(op, left):
        return ['Unary', [left], op, False]

    @staticmethod
    def typen(baset: str, dim: int) -> list:
        return ['TypeName', (baset, dim)]

    @staticmethod
    def parenthesis(expr):
        return ['Parenthesis', [expr]]

    @staticmethod
    def method_invocation(triple, name, base, params):
        if base is None:
            return ['MethodInvocation', params, triple, name, False]
        return ['MethodInvocation', [base] + params, triple, name, True]

    @staticmethod
    def local(name):
        return ['Local', name]

    @staticmethod
    def literal(result, tt):
        return ['Literal', result, tt]

    @staticmethod
    def field_access(triple, left):
        return ['FieldAccess', [left], triple]

    @staticmethod
    def cast(tn, arg):
        return ['Cast', [tn, arg]]

    @staticmethod
    def binary_infix(op, left, right):
        return ['BinaryInfix', [left, right], op]

    @staticmethod
    def assignment(lhs, rhs, op=''):
        return ['Assignment', [lhs, rhs], op]

    @staticmethod
    def array_initializer(params, tn=None):
        return ['ArrayInitializer', params, tn]

    @staticmethod
    def array_creation(tn, params, dim):
        return ['ArrayCreation', [tn] + params, dim]

    @staticmethod
    def array_access(arr, ind) -> list:
        return ['ArrayAccess', [arr, ind]]
