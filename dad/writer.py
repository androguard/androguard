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

from dad.util import get_type, log, ACCESS_FLAGS_METHODS
from dad.opcode_ins import Op
from dad.instruction import Constant, ThisParam, BinaryCompExpression

SPACE = ' '


class Writer(object):
    def __init__(self, graph, method):
        self.graph = graph
        self.method = method
        self.visited_nodes = set()
        self.ind = 4
        self.buffer = []
        self.loop_follow = [None]
        self.latch_node = [None]
        self.if_follow = [None]
        self.switch_follow = [None]
        self.skip = False

    def __str__(self):
        return ''.join(self.buffer)

    def inc_ind(self, i=1):
        self.ind += (4 * i)

    def dec_ind(self, i=1):
        self.ind -= (4 * i)

    def write_ind(self):
        if self.skip:
            self.skip = False
        else:
            self._write(SPACE * self.ind)

    def _write(self, s):
        self.buffer.append(s)

    def end_ins(self):
        self._write(';\n')

    def write_method(self):
        acc = []
        access = self.method.access
        self.constructor = 0x10000 in access
        for i in self.method.access:
            if i == 0x10000:
                continue
            acc.append(ACCESS_FLAGS_METHODS.get(i))
        if self.constructor:
            name = get_type(self.method.method.class_name).split('.')[-1]
            proto = '%s %s(' % (' '.join(acc), name)
        else:
            name = self.method.name
            proto = '%s %s %s(' % (' '.join(acc), self.method.type, name)
        self._write('%s%s' % (SPACE * self.ind, proto))
        if 0x8 in self.method.access:
            params = self.method.lparams
        else:
            params = self.method.lparams[1:]
        if self.method.params_type:
            proto = ', '.join(['%s p%s' % (get_type(p_type), param) for
                        p_type, param in zip(self.method.params_type, params)])
        self._write('%s)' % proto)
        if self.method.graph is None:
            return self._write(';')
        self._write('\n%s{\n' % (SPACE * self.ind))
        self.inc_ind()
#        for v, var in self.method.var_to_name.iteritems():
#            var.write_decl(self)
        self.write_node(self.method.graph.get_entry())
        self.dec_ind()
        self._write('%s}' % (SPACE * self.ind))

    def write_node(self, node):
        if node in (self.if_follow[-1], self.switch_follow[-1],
                    self.loop_follow[-1], self.latch_node[-1]):
            return
        if node in self.visited_nodes:
            return
        self.visited_nodes.add(node)
        node.write(self)

    def write_ins(self, ins):
        ins.write(self)

    def write_loop_node(self, loop):
        follow = loop.get_loop_follow()
        if follow is None and not loop.looptype.endless():
            log('Loop has no follow !', 'error')
        if loop.looptype.pretest():
            if loop.true is follow:
                loop.neg()
                loop.true, loop.false = loop.false, loop.true
            self._write('%swhile (' % (SPACE * self.ind))
            loop.write_cond(self)
            self._write(') {\n')
        elif loop.looptype.posttest():
            self._write('%sdo {\n' % (SPACE * self.ind))
            self.latch_node.append(loop.latch)
        elif loop.looptype.endless():
            self._write('%swhile(true) {\n' % (SPACE * self.ind))
        self.inc_ind()
        self.loop_follow.append(follow)
        if loop.looptype.pretest():
            if loop.true not in self.visited_nodes:
                self.write_node(loop.true)
        else:
            self.write_node(loop.cond)
        self.loop_follow.pop()
        self.dec_ind()
        if loop.looptype.pretest():
            self._write('%s}\n' % (SPACE * self.ind))
        elif loop.looptype.posttest():
            self.latch_node.pop()
            self._write('%s} while(' % (SPACE * self.ind))
            loop.latch.write_cond(self)
            self._write(');\n')
        else:
            self.inc_ind()
            self.write_node(loop.latch)
            self.dec_ind()
            self._write('%s}\n' % (SPACE * self.ind))
        if follow is not None:
            if follow not in self.visited_nodes:
                self.write_node(follow)

    def write_cond_node(self, cond):
        follow = cond.get_if_follow()
        if cond.false is self.loop_follow[-1]:
            cond.neg()
            cond.true, cond.false = cond.false, cond.true
            self._write('%sif(' % (SPACE * self.ind))
            cond.write_cond(self)
            self._write(') {\n')
            self.inc_ind()
            self._write('%sbreak;\n' % (SPACE * self.ind))
            self.dec_ind()
            self._write('%s}\n' % (SPACE * self.ind))
            self.write_node(cond.false)
            return
        is_else = True
        if follow is not None:
            if cond.true is follow:
                cond.neg()
                cond.true, cond.false = cond.false, cond.true
                is_else = False
            self.if_follow.append(follow)
            if not cond.true in self.visited_nodes:
                self._write('%sif(' % (SPACE * self.ind))
                cond.write_cond(self)
                self._write(') {\n')
                self.inc_ind()
                self.write_node(cond.true)
                self.dec_ind()
            if is_else and not cond.false in self.visited_nodes:
                self._write('%s} else {\n' % (SPACE * self.ind))
                self.inc_ind()
                self.write_node(cond.false)
                self.dec_ind()
            self.if_follow.pop()
            self._write('%s}\n' % (SPACE * self.ind))
            if follow not in self.visited_nodes:
                self.write_node(follow)
        else:
            # No follow node. If one of the branch loop to a header node
            # this is not an if-then-else
            if cond.true.num < cond.num or cond.false.num < cond.num:
                cond.neg()
                cond.true, cond.false = cond.false, cond.true
                self._write('%sif (' % (SPACE * self.ind))
                cond.write_cond(self)
                self._write(') {\n')
                self.inc_ind()
                self.write_node(cond.true)
                self.dec_ind()
                self._write('%s}\n' % (SPACE * self.ind))
            else:
                self._write('%sif (' % (SPACE * self.ind))
                cond.write_cond(self)
                self._write(') {\n')
                self.inc_ind()
                self.write_node(cond.true)
                self.dec_ind()
                self._write('%s} else {\n' % (SPACE * self.ind))
                self.inc_ind()
                self.write_node(cond.false)
                self.dec_ind()
                self._write('%s}\n' % (SPACE * self.ind))

    def write_short_circuit_condition(self, nnot, aand, cond1, cond2):
        if nnot:
            cond1.neg()
        self._write('(')
        cond1.write_cond(self)
        self._write(')')
        self._write(' %s ' % ['||', '&&'][aand])
        self._write('(')
        cond2.write_cond(self)
        self._write(')')

    def write_switch_node(self, switch):
        lins = switch.get_ins()
        if len(lins) > 1:
            for ins in lins[:-1]:
                self.write_ins(ins)
        switch_ins = switch.get_ins()[-1]
        self._write('%sswitch(' % (SPACE * self.ind))
        self.write_ins(switch_ins)
        self._write(') {\n')
        follow = switch.switch_follow
        values = switch.switch.get_values()
        cases = filter(lambda x: x in self.graph, switch.cases)
        print 'CASES:', cases
        print 'Value:', values
        if follow in cases:
            cases.remove(follow)
        self.switch_follow.append(follow)
        default = len(values) < len(cases)
        for i, n in enumerate(values):
            self.inc_ind()
            self._write('%scase %d:\n' % (SPACE * self.ind, values[i]))
            self.inc_ind()
            if default:
                self.write_node(cases[i + 1])
            else:
                self.write_node(cases[i])
            self._write('%sbreak;\n' % (SPACE * self.ind))
            self.dec_ind(2)
        if len(values) < len(cases):
            self.inc_ind()
            self._write('%sdefault:\n' % (SPACE * self.ind))
            self.inc_ind()
            self.write_node(cases[0])
            self._write('%sbreak;\n' % (SPACE * self.ind))
            self.dec_ind(2)
        self._write('%s}\n' % (SPACE * self.ind))
        self.switch_follow.pop()
        if follow not in self.visited_nodes:
            self.write_node(follow)

    def write_statement_node(self, stmt):
        sucs = self.graph.sucs(stmt)
        for ins in stmt.get_ins():
            self.write_ins(ins)
        if len(sucs) == 0:
            return
        follow = sucs[0]
        if follow not in self.visited_nodes:
            self.write_node(follow)

    def write_return_node(self, ret):
        for ins in ret.get_ins():
            self.write_ins(ins)

    def write_throw_node(self, throw):
        for ins in throw.get_ins():
            self.write_ins(ins)

#    def write_decl(self, var):
#        self._write('%sdecl v%s' % (SPACE * self.ind, var))
#        self.end_ins()

    def write_constant(self, cst):
        if isinstance(cst, str):
            return self._write(string('%s' % cst))
        self._write('%s' % cst)

    def write_base_class(self, cls):
        self._write(cls)

    def write_variable(self, var):
        if isinstance(var, str):
            return self._write(var)
        self._write('v%d' % var)

    def write_param(self, param):
        self._write('p%s' % param)

    def write_this(self):
        self._write('this')

    def write_assign(self, lhs, rhs):
        self.write_ind()
        if lhs is None:
            rhs.write(self)
            if not self.skip:
                self.end_ins()
            return
        lhs.write(self)
        self._write(' = ')
        rhs.write(self)
        self.end_ins()

    def write_move_result(self, lhs, rhs):
        self.write_ind()
        lhs.write(self)
        self._write(' = ')
        rhs.write(self)
        self.end_ins()

    def write_move(self, lhs, rhs):
        if lhs is rhs:
            return
        self.write_ind()
        lhs.write(self)
        self._write(' = ')
        rhs.write(self)
        self.end_ins()

    def write_astore(self, array, index, rhs):
        self.write_ind()
        array.write(self)
        self._write('[')
        if isinstance(index, Constant):
            index.write(self, 'I')
        else:
            index.write(self)
        self._write('] = ')
        rhs.write(self)
        self.end_ins()

    def write_put_static(self, cls, name, rhs):
        self.write_ind()
        self._write('%s.%s = ' % (cls, name))
        rhs.write(self)
        self.end_ins()

    def write_put_instance(self, lhs, name, rhs):
        self.write_ind()
        lhs.write(self)
        self._write('.%s = ' % name)
        rhs.write(self)
        self.end_ins()

    def write_new(self, atype):
        self._write('new %s' % get_type(atype))

    def write_invoke(self, name, base, args):
        if isinstance(base, ThisParam) and self.constructor and len(args) == 0:
            self.skip = True
            return
        base.write(self)
        if name != '<init>':
            self._write('.%s' % name)
        self._write('(')
        comma = False
        for arg in args:
            if comma:
                self._write(', ')
            comma = True
            arg.write(self)
        self._write(')')

    def write_return_void(self):
        self.write_ind()
        self._write('return')
        self.end_ins()

    def write_return(self, arg):
        self.write_ind()
        self._write('return ')
        arg.write(self)
        self.end_ins()

    def write_nop(self):
        pass

    def write_switch(self, arg):
        arg.write(self)

    def write_check_cast(self, arg, atype):
        self._write('(checkcast)(')
        arg.write(self)
        self._write(', %s)' % atype)

    def write_aload(self, array, index):
        array.write(self)
        self._write('[')
        index.write(self)
        self._write(']')

    def write_alength(self, array):
        array.write(self)
        self._write('.length')

    def write_new_array(self, atype, size):
        self._write('new %s[' % get_type(atype[1:]))
        size.write(self)
        self._write(']')

    def write_filled_new_array(self, atype, size, args):
        self._write('filled-new-array(type=')
        atype.write(self)
        self._write(', size=')
        size.write(self)
        for arg in args:
            self._write(', arg=')
            arg.write(self)
        self._write(')')

    def write_fill_array(self, array, value):
        self.write_ind()
        array.write(self)
        self._write(' = {')
        self._write('%r' % value.get_data())
        self._write('}')
        self.end_ins()

    def write_monitor_enter(self, ref):
        self.write_ind()
        self._write('synchronized(')
        ref.write(self)
        self._write(') {\n')
        self.inc_ind()

    def write_monitor_exit(self, ref):
        self.dec_ind()
        self.write_ind()
        self._write('}\n')

    def write_throw(self, ref):
        self.write_ind()
        self._write('throw ')
        ref.write(self)
        self.end_ins()

    def write_binary_expression(self, op, arg1, arg2):
        self._write('(')
        arg1.write(self)
        self._write(' %s ' % op)
        arg2.write(self)
        self._write(')')

    def write_unary_expression(self, op, arg):
        self._write('(%s ' % op)
        arg.write(self)
        self._write(')')

    def write_cast(self, op, arg):
        self._write('(%s ' % op)
        arg.write(self)
        self._write(')')

    def write_cond_expression(self, op, arg1, arg2):
        arg1.write(self)
        self._write(' %s ' % op)
        arg2.write(self)

    def write_condz_expression(self, op, arg):
        if isinstance(arg, BinaryCompExpression):
            arg.op = op
            return arg.write(self)
        atype = arg.get_type()
        if atype == 'Z':
            if op is Op.EQUAL:
                self._write('!')
                arg.write(self)
            else:
                arg.write(self)
        else:
            arg.write(self)
            self._write(' %s 0' % op)

    def write_get_instance(self, arg, name):
        arg.write(self)
        self._write('.%s' % name)

    def write_get_static(self, cls, name):
        self._write('%s.%s' % (cls, name))


def string(s):
    # Based on http://stackoverflow.com/a/1676407
    ret = ['"']
    for c in s[1:-1]:
        if c == '\n':
            to_add = '\\\n'
        elif ord(c) < 32 or 0x80 <= ord(c) <= 0xff:
            to_add = '\\x%02x' % ord(c)
        elif c in '\\"':
            to_add = '\\%c' % c
        else:
            to_add = c
        ret.append(to_add)
    ret.append('"')
    return ''.join(ret)