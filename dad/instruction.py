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


class IRForm(object):
    def __init__(self):
        self.var_map = {}

    def is_call(self):
        return False

    def is_cond(self):
        return False

    def is_propagable(self):
        return True

    def get_type(self):
        return None

    def has_side_effect(self):
        return False

    def get_used_vars(self):
        return []

    def modify_rhs(self, old, new):
        self.var_map[old] = new

    def remove_defined_var(self):
        pass

    def get_rhs(self):
        return []

    def get_lhs(self):
        return None

    def write(self, writer):
        pass


class Constant(IRForm):
    def __init__(self, value, atype, int_value=None):
        self.v = 'c%s' % value
        self.cst = value
        if int_value is None:
            self.cst2 = value
        else:
            self.cst2 = int_value
        self.type = atype

    def get_used_vars(self):
        return []

    def is_call(self):
        return False

    def has_side_effect(self):
        return False

    def write(self, writer, to_int=False):
        if self.type == 'Z':
            if self.cst == 0:
                writer.write_constant('false')
            else:
                writer.write_constant('true')
        if to_int:
            writer.write_constant(self.cst2)
        else:
            writer.write_constant(self.cst)


class BaseClass(IRForm):
    def __init__(self, name):
        self.v = 'c%s' % name
        self.cls = name

    def write(self, writer):
        writer.write_base_class(self.cls)


class Variable(IRForm):
    def __init__(self, value):
        self.v = value

    def get_type(self):
        return None

    def get_used_vars(self):
        return [self.v]

    def is_call(self):
        return False

    def has_side_effect(self):
        return False

    def write(self, writer):
        writer.write_variable(self.v)

    def write_decl(self, writer):
        writer.write_decl(self.v)


class Param(IRForm):
    def __init__(self, value, atype):
        self.v = value
        self.type = atype

    def get_type(self):
        return self.type

    def get_used_vars(self):
        return [self.v]

    def is_call(self):
        return False

    def has_side_effect(self):
        return False

    def write(self, writer):
        writer.write_param(self.v)

    def write_decl(self, writer):
        pass


class ThisParam(Param):
    def __init__(self, value, atype):
        super(ThisParam, self).__init__(value, atype)

    def get_used_vars(self):
        return []

    def write(self, writer):
        writer.write_this()

    def write_decl(self, writer):
        pass


class AssignExpression(IRForm):
    def __init__(self, lhs, rhs):
        super(AssignExpression, self).__init__()
        self.lhs = lhs.v
        self.rhs = rhs
        self.var_map[lhs.v] = lhs

    def remove_wide_var(self, var):
        self.rhs.remove_wide_var(var)

    def is_propagable(self):
        return self.rhs.is_propagable()

    def is_call(self):
        return self.rhs.is_call()

    def has_side_effect(self):
        return self.rhs.has_side_effect()

    def get_rhs(self):
        return self.rhs

    def get_lhs(self):
        return self.lhs

    def get_used_vars(self):
        return self.rhs.get_used_vars()

    def remove_defined_var(self):
        self.lhs = None

    def modify_rhs(self, old, new):
        self.rhs.modify_rhs(old, new)

    def write(self, writer):
        writer.write_assign(self.var_map.get(self.lhs), self.rhs)


class MoveResultExpression(IRForm):
    def __init__(self, lhs, rhs):
        super(MoveResultExpression, self).__init__()
        self.lhs = lhs.v
        self.rhs = rhs.v
        self.var_map.update([(lhs.v, lhs), (rhs.v, rhs)])

    def is_propagable(self):
        return self.var_map[self.rhs].is_propagable()

    def is_call(self):
        return self.var_map[self.rhs].is_call()

    def get_used_vars(self):
        return self.var_map[self.rhs].get_used_vars()

    def get_rhs(self):
        return self.var_map[self.rhs]

    def get_lhs(self):
        return self.lhs

    def write(self, writer):
        m = self.var_map
        writer.write_move_result(m[self.lhs], m[self.rhs])


class MoveExpression(IRForm):
    def __init__(self, lhs, rhs):
        super(MoveExpression, self).__init__()
        self.lhs = lhs.v
        self.rhs = rhs.v
        self.var_map.update([(lhs.v, lhs), (rhs.v, rhs)])

    def has_side_effect(self):
        return False

    def is_call(self):
        return self.var_map[self.rhs].is_call()

    def get_used_vars(self):
        return self.var_map[self.rhs].get_used_vars()

    def get_rhs(self):
        return self.var_map[self.rhs]

    def get_lhs(self):
        return self.lhs

    def write(self, writer):
        m = self.var_map
        writer.write_move(m[self.lhs], m[self.rhs])


class ArrayStoreInstruction(IRForm):
    def __init__(self, rhs, array, index):
        super(ArrayStoreInstruction, self).__init__()
        self.rhs = rhs.v
        self.array = array.v
        self.index = index.v
        self.var_map.update([(rhs.v, rhs), (array.v, array), (index.v, index)])

    def has_side_effect(self):
        return True

    def get_used_vars(self):
        m = self.var_map
        lused_vars = set()
        lused_vars.update(m[self.array].get_used_vars())
        lused_vars.update(m[self.index].get_used_vars())
        lused_vars.update(m[self.rhs].get_used_vars())
        return list(lused_vars)

    def write(self, writer):
        m = self.var_map
        writer.write_astore(m[self.array], m[self.index], m[self.rhs])


class StaticInstruction(IRForm):
    def __init__(self, rhs, klass, ftype, name):
        super(StaticInstruction, self).__init__()
        self.rhs = rhs.v
        self.cls = klass
        self.ftype = ftype
        self.name = name
        self.var_map[rhs.v] = rhs

    def has_side_effect(self):
        return True

    def get_used_vars(self):
        return self.var_map[self.rhs].get_used_vars()

    def get_lhs(self):
        return None

    def write(self, writer):
        m = self.var_map
        writer.write_put_static(self.cls, self.name, m[self.rhs])


class InstanceInstruction(IRForm):
    def __init__(self, rhs, lhs, klass, atype, name):
        super(InstanceInstruction, self).__init__()
        self.lhs = lhs.v
        self.rhs = rhs.v
        self.atype = atype
        self.cls = klass
        self.name = name
        self.var_map.update([(lhs.v, lhs), (rhs.v, rhs)])

    def has_side_effect(self):
        return True

    def get_used_vars(self):
        m = self.var_map
        lused_vars = set()
        lused_vars.update(m[self.lhs].get_used_vars())
        lused_vars.update(m[self.rhs].get_used_vars())
        return list(lused_vars)

    def get_lhs(self):
        return None

    def write(self, writer):
        m = self.var_map
        writer.write_put_instance(m[self.lhs], self.name, m[self.rhs])


class NewInstance(IRForm):
    def __init__(self, ins_type):
        super(NewInstance, self).__init__()
        self.type = ins_type

    def get_type(self):
        return self.type

#    def has_side_effect(self):
#        return True

    def get_used_vars(self):
        return []

    def write(self, writer):
        writer.write_new(self.type)


class InvokeInstruction(IRForm):
    def __init__(self, clsname, name, base, rtype, ptype, nbargs, args):
        super(InvokeInstruction, self).__init__()
        self.cls = clsname
        self.name = name
        self.base = base.v
        self.rtype = rtype
        self.ptype = ptype
        self.nbargs = nbargs
        self.args = [arg.v for arg in args]
        self.var_map[base.v] = base
        for arg in args:
            self.var_map[arg.v] = arg

    def get_type(self):
        return self.rtype

    def remove_wide_var(self, var):
        self.args = filter(lambda x: x != var, self.args)
        self.var_map.pop(var)

    def is_call(self):
        return True

    def has_side_effect(self):
        return True

    def get_used_vars(self):
        m = self.var_map
        lused_vars = set()
        for a in self.args:
            lused_vars.update(m[a].get_used_vars())
        lused_vars.update(m[self.base].get_used_vars())
        return list(lused_vars)

    def write(self, writer):
        m = self.var_map
        largs = [m[arg] for arg in self.args]
        writer.write_invoke(self.name, m[self.base], largs)


class InvokeRangeInstruction(InvokeInstruction):
    def __init__(self, clsname, name, rtype, ptype, nbargs, args):
        base = args.pop(0)
        super(InvokeRangeInstruction, self).__init__(clsname, name, base,
                                                    rtype, ptype, nbargs, args)


class InvokeDirectInstruction(InvokeInstruction):
    def __init__(self, clsname, name, base, rtype, ptype, nbargs, args):
        super(InvokeDirectInstruction, self).__init__(clsname, name, base,
                                                    rtype, ptype, nbargs, args)


class InvokeStaticInstruction(InvokeInstruction):
    def __init__(self, clsname, name, base, rtype, ptype, nbargs, args):
        # TODO: check base class name and current class name
        super(InvokeStaticInstruction, self).__init__(clsname, name, base,
                                                    rtype, ptype, nbargs, args)

    def get_used_vars(self):
        res = set(a for a in self.args)
        return list(res)


class ReturnInstruction(IRForm):
    def __init__(self, arg):
        super(ReturnInstruction, self).__init__()
        self.arg = arg
        if arg is not None:
            self.var_map[arg.v] = arg
            self.arg = arg.v

    def get_used_vars(self):
        if self.arg is None:
            return []
        return self.var_map[self.arg].get_used_vars()

    def get_lhs(self):
        return None

    def write(self, writer):
        if self.arg is None:
            writer.write_return_void()
        else:
            writer.write_return(self.var_map[self.arg])


class NopExpression(IRForm):
    def __init__(self):
        pass

    def get_used_vars(self):
        return []

    def get_lhs(self):
        return None

    def write(self, writer):
        writer.write_nop()


class SwitchExpression(IRForm):
    def __init__(self, src, branch):
        super(SwitchExpression, self).__init__()
        self.src = src.v
        self.var_map[src.v] = src

    def get_used_vars(self):
        m = self.var_map
        return m[self.src].get_used_vars()

    def write(self, writer):
        writer.write_switch(self.var_map[self.src])


class CheckCastExpression(IRForm):
    def __init__(self, arg, _type):
        super(CheckCastExpression, self).__init__()
        self.arg = arg.v
        self.var_map[arg.v] = arg
        self.type = _type

    def get_used_vars(self):
        return self.var_map[self.arg].get_used_vars()

    def write(self, writer):
        writer.write_check_cast(self.var_map[self.arg], self.type)


class ArrayExpression(IRForm):
    def __init__(self):
        super(ArrayExpression, self).__init__()


class ArrayLoadExpression(ArrayExpression):
    def __init__(self, arg, index):
        super(ArrayLoadExpression, self).__init__()
        self.array = arg.v
        self.idx = index.v
        self.var_map.update([(arg.v, arg), (index.v, index)])

    def get_used_vars(self):
        m = self.var_map
        lused_vars = set()
        lused_vars.update(m[self.array].get_used_vars())
        lused_vars.update(m[self.idx].get_used_vars())
        return list(lused_vars)

    def write(self, writer):
        m = self.var_map
        writer.write_aload(m[self.array], m[self.idx])


class ArrayLengthExpression(ArrayExpression):
    def __init__(self, array):
        super(ArrayLengthExpression, self).__init__()
        self.array = array.v
        self.var_map[array.v] = array

    def get_type(self):
        return 'I'

    def get_used_vars(self):
        m = self.var_map
        return m[self.array].get_used_vars()

    def write(self, writer):
        writer.write_alength(self.var_map[self.array])


class NewArrayExpression(ArrayExpression):
    def __init__(self, asize, atype):
        super(NewArrayExpression, self).__init__()
        self.size = asize.v
        self.type = atype
        self.var_map[asize.v] = asize

    def is_propagable(self):
        return False

    def get_used_vars(self):
        m = self.var_map
        return m[self.size].get_used_vars()

    def write(self, writer):
        writer.write_new_array(self.type, self.var_map[self.size])


class FilledArrayExpression(ArrayExpression):
    def __init__(self, asize, atype, args):
        super(FilledArrayExpression, self).__init__()
        self.size = asize.v
        self.var_map[asize.v] = asize
        self.type = atype
        self.args = []
        for arg in args:
            self.var_map[arg.v] = arg
            self.args.append(arg.v)

    def is_propagable(self):
        return False

    def has_side_effect(self):
        return True

    def get_used_vars(self):
        lused_vars = set()
        for arg in self.args:
            lused_vars.update(self.var_map[arg].get_used_vars())
        lused_vars.add(self.size)
        return list(lused_vars)

    def write(self, writer):
        m = self.var_map
        largs = [m[arg] for arg in self.args]
        writer.write_filled_new_array(self.type, m[self.size], largs)


class FillArrayExpression(ArrayExpression):
    def __init__(self, reg, value):
        super(FillArrayExpression, self).__init__()
        self.reg = reg.v
        self.var_map[reg.v] = reg
        self.value = value

#    def has_side_effect(self):
#        return True

    def get_rhs(self):
        return self.reg

    def get_used_vars(self):
        m = self.var_map
        return m[self.reg].get_used_vars()

    def write(self, writer):
        writer.write_fill_array(self.var_map[self.reg], self.value)


class RefExpression(IRForm):
    def __init__(self, ref):
        super(RefExpression, self).__init__()
        self.ref = ref.v
        self.var_map[ref.v] = ref

    def get_used_vars(self):
        m = self.var_map
        return m[self.ref].get_used_vars()


class MonitorEnterExpression(RefExpression):
    def __init__(self, ref):
        super(MonitorEnterExpression, self).__init__(ref)

    def write(self, writer):
        writer.write_monitor_enter(self.var_map[self.ref])


class MonitorExitExpression(RefExpression):
    def __init__(self, ref):
        super(MonitorExitExpression, self).__init__(ref)

    def write(self, writer):
        writer.write_monitor_exit(self.var_map[self.ref])


class ThrowExpression(RefExpression):
    def __init__(self, ref):
        super(ThrowExpression, self).__init__(ref)

    def write(self, writer):
        writer.write_throw(self.var_map[self.ref])


class BinaryExpression(IRForm):
    def __init__(self, op, arg1, arg2):
        super(BinaryExpression, self).__init__()
        self.op = op
        self.arg1 = arg1.v
        self.arg2 = arg2.v
        self.var_map.update([(arg1.v, arg1), (arg2.v, arg2)])

    # TODO: return the max type of arg1 & arg2
    def get_type(self):
        return None

    def has_side_effect(self):
        m = self.var_map
        res = m[self.arg1].has_side_effect() or m[self.arg2].has_side_effect()
        return res

    def get_used_vars(self):
        m = self.var_map
        lused_vars = set()
        lused_vars.update(m[self.arg1].get_used_vars())
        lused_vars.update(m[self.arg2].get_used_vars())
        return list(lused_vars)

    def write(self, writer):
        m = self.var_map
        writer.write_binary_expression(self.op, m[self.arg1], m[self.arg2])


class BinaryCompExpression(BinaryExpression):
    def __init__(self, op, arg1, arg2):
        super(BinaryCompExpression, self).__init__(op, arg1, arg2)

    def write(self, writer):
        m = self.var_map
        writer.write_cond_expression(self.op, m[self.arg1], m[self.arg2])


class BinaryExpression2Addr(BinaryExpression):
    def __init__(self, op, dest, arg):
        super(BinaryExpression2Addr, self).__init__(op, dest, arg)


class BinaryExpressionLit(BinaryExpression):
    def __init__(self, op, arg1, arg2):
        super(BinaryExpressionLit, self).__init__(op, arg1, arg2)


class UnaryExpression(IRForm):
    def __init__(self, op, arg):
        super(UnaryExpression, self).__init__()
        self.op = op
        self.arg = arg.v
        self.var_map[arg.v] = arg

    def get_type(self):
        return self.var_map[self.arg].get_type()

    def get_used_vars(self):
        m = self.var_map
        return m[self.arg].get_used_vars()

    def write(self, writer):
        writer.write_unary_expression(self.op, self.var_map[self.arg])


class CastExpression(UnaryExpression):
    def __init__(self, op, atype, arg):
        super(CastExpression, self).__init__(op, arg)
        self.type = atype

    def get_type(self):
        return self.type

    def get_used_vars(self):
        return self.var_map[self.arg].get_used_vars()

    def write(self, writer):
        writer.write_cast(self.op, self.var_map[self.arg])


CONDS = {
    '==': '!=',
    '!=': '==',
    '<': '>=',
    '<=': '>',
    '>=': '<',
    '>': '<=',
}


class ConditionalExpression(IRForm):
    def __init__(self, op, arg1, arg2):
        super(ConditionalExpression, self).__init__()
        self.op = op
        self.arg1 = arg1.v
        self.arg2 = arg2.v
        self.var_map.update([(arg1.v, arg1), (arg2.v, arg2)])

    def get_lhs(self):
        return None

    def is_cond(self):
        return True

    def get_used_vars(self):
        m = self.var_map
        lused_vars = set()
        lused_vars.update(m[self.arg1].get_used_vars())
        lused_vars.update(m[self.arg2].get_used_vars())
        return list(lused_vars)

    def neg(self):
        self.op = CONDS[self.op]

    def write(self, writer):
        m = self.var_map
        writer.write_cond_expression(self.op, m[self.arg1], m[self.arg2])


class ConditionalZExpression(IRForm):
    def __init__(self, op, arg):
        super(ConditionalZExpression, self).__init__()
        self.op = op
        self.arg = arg.v
        self.var_map[arg.v] = arg

    def get_lhs(self):
        return None

    def is_cond(self):
        return True

    def get_used_vars(self):
        m = self.var_map
        return m[self.arg].get_used_vars()

    def neg(self):
        self.op = CONDS[self.op]

    def write(self, writer):
        writer.write_condz_expression(self.op, self.var_map[self.arg])


class InstanceExpression(IRForm):
    def __init__(self, arg, klass, ftype, name):
        super(InstanceExpression, self).__init__()
        self.arg = arg.v
        self.cls = klass
        self.ftype = ftype
        self.name = name
        self.var_map[arg.v] = arg

    def get_type(self):
        return self.ftype

    def get_used_vars(self):
        m = self.var_map
        return m[self.arg].get_used_vars()

    def write(self, writer):
        writer.write_get_instance(self.var_map[self.arg], self.name)


class StaticExpression(IRForm):
    def __init__(self, cls_name, field_type, field_name):
        super(StaticExpression, self).__init__()
        self.cls = cls_name
        self.ftype = field_type
        self.name = field_name

    def get_type(self):
        return self.ftype

    def write(self, writer):
        writer.write_get_static(self.cls, self.name)
