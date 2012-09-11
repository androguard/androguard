# This file is part of Androguard.
#
# Copyright (c) 2012 Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
# All Rights Reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

from util import log
from instruction import Constant, BinaryCompExpression


class Visitor(object):
    def __init__(self, graph):
        self.graph = graph
        self.visited_nodes = set()
        self.loop_follow = [None]
        self.latch_node = [None]
        self.if_follow = [None]
        self.switch_follow = [None]
        self.next_case = None

    def visit_ins(self, ins):
        ins.visit(self)

    def visit_node(self, node):
        if node in (self.if_follow[-1], self.switch_follow[-1],
                    self.loop_follow[-1], self.latch_node[-1]):
            return
        if node in self.visited_nodes:
            return
        self.visited_nodes.add(node)
        node.visit(self)

    def visit_loop_node(self, loop):
        follow = loop.get_loop_follow()
        if follow is None and not loop.looptype.endless():
            log('Loop has no follow !', 'error')
        if loop.looptype.pretest():
            if loop.true is follow:
                loop.neg()
                loop.true, loop.false = loop.false, loop.true
            loop.visit_cond(self)
        elif loop.looptype.posttest():
            self.latch_node.append(loop.latch)
        elif loop.looptype.endless():
            pass
        self.loop_follow.append(follow)
        if loop.looptype.pretest():
            self.visit_node(loop.true)
        else:
            self.visit_node(loop.cond)
        self.loop_follow.pop()
        if loop.looptype.pretest():
            pass
        elif loop.looptype.posttest():
            self.latch_node.pop()
            loop.latch.visit_cond(self)
        else:
            self.visit_node(loop.latch)
        if follow is not None:
            self.visit_node(follow)

    def visit_cond_node(self, cond):
        follow = cond.get_if_follow()
        if cond.false is self.loop_follow[-1]:
            cond.neg()
            cond.true, cond.false = cond.false, cond.true
            cond.visit_cond(self)
            self.visit_node(cond.false)
        elif follow is not None:
            is_else = not (follow in (cond.true, cond.false))
            if (cond.true in (follow, self.next_case)
                                                or cond.num > cond.true.num):
                cond.neg()
                cond.true, cond.false = cond.false, cond.true
            self.if_follow.append(follow)
            if not cond.true in self.visited_nodes:
                cond.visit_cond(self)
                self.visit_node(cond.true)
            if is_else and not cond.false in self.visited_nodes:
                self.visit_node(cond.false)
            self.if_follow.pop()
            self.visit_node(follow)
        else:
            cond.visit_cond(self)
            self.visit_node(cond.true)
            self.visit_node(cond.false)

    def visit_short_circuit_condition(self, nnot, aand, cond1, cond2):
        if nnot:
            cond1.neg()
        cond1.visit_cond(self)
        cond2.visit_cond(self)

    def visit_switch_node(self, switch):
        lins = switch.get_ins()
        for ins in lins[:-1]:
            self.visit_ins(ins)
        switch_ins = switch.get_ins()[-1]
        self.visit_ins(switch_ins)
        follow = switch.switch_follow
        cases = switch.cases
        self.switch_follow.append(follow)
        default = switch.default
        for i, node in enumerate(cases):
            if node in self.visited_nodes:
                continue
            for case in switch.node_to_case[node]:
                pass
            if i + 1 < len(cases):
                self.next_case = cases[i + 1]
            else:
                self.next_case = None
            if node is default:
                default = None
            self.visit_node(node)
        if default not in (None, follow):
            self.visit_node(default)
        self.switch_follow.pop()
        self.visit_node(follow)

    def visit_statement_node(self, stmt):
        sucs = self.graph.sucs(stmt)
        for ins in stmt.get_ins():
            self.visit_ins(ins)
        if len(sucs) == 0:
            return
        follow = sucs[0]
        self.visit_node(follow)

    def visit_return_node(self, ret):
        for ins in ret.get_ins():
            self.visit_ins(ins)

    def visit_throw_node(self, throw):
        for ins in throw.get_ins():
            self.visit_ins(ins)

    def visit_constant(self, cst):
        pass

    def visit_base_class(self, cls):
        pass

    def visit_variable(self, var):
        pass

    def visit_param(self, param):
        pass

    def visit_this(self):
        pass

    def visit_assign(self, lhs, rhs):
        if lhs is None:
            rhs.visit(self)
            return
        lhs.visit(self)
        rhs.visit(self)

    def visit_move_result(self, lhs, rhs):
        lhs.visit(self)
        rhs.visit(self)

    def visit_move(self, lhs, rhs):
        if lhs is rhs:
            return
        lhs.visit(self)
        rhs.visit(self)

    def visit_astore(self, array, index, rhs):
        array.visit(self)
        if isinstance(index, Constant):
            index.visit(self, 'I')
        else:
            index.visit(self)
        rhs.visit(self)

    def visit_put_static(self, cls, name, rhs):
        rhs.visit(self)

    def visit_put_instance(self, lhs, name, rhs):
        lhs.visit(self)
        rhs.visit(self)

    def visit_new(self, atype):
        pass

    def visit_invoke(self, name, base, args):
        base.visit(self)
        for arg in args:
            arg.visit(self)

    def visit_return_void(self):
        pass

    def visit_return(self, arg):
        arg.visit(self)

    def visit_nop(self):
        pass

    def visit_switch(self, arg):
        arg.visit(self)

    def visit_check_cast(self, arg, atype):
        arg.visit(self)

    def visit_aload(self, array, index):
        array.visit(self)
        index.visit(self)

    def visit_alength(self, array):
        array.visit(self)

    def visit_new_array(self, atype, size):
        size.visit(self)

    def visit_filled_new_array(self, atype, size, args):
        atype.visit(self)
        size.visit(self)
        for arg in args:
            arg.visit(self)

    def visit_fill_array(self, array, value):
        array.visit(self)

    def visit_monitor_enter(self, ref):
        ref.visit(self)

    def visit_monitor_exit(self, ref):
        pass

    def visit_throw(self, ref):
        ref.visit(self)

    def visit_binary_expression(self, op, arg1, arg2):
        arg1.visit(self)
        arg2.visit(self)

    def visit_unary_expression(self, op, arg):
        arg.visit(self)

    def visit_cast(self, op, arg):
        arg.visit(self)

    def visit_cond_expression(self, op, arg1, arg2):
        arg1.visit(self)
        arg2.visit(self)

    def visit_condz_expression(self, op, arg):
        if isinstance(arg, BinaryCompExpression):
            arg.op = op
            arg.visit(self)
        else:
            arg.visit(self)

    def visit_get_instance(self, arg, name):
        arg.visit(self)

    def visit_get_static(self, cls, name):
        pass
