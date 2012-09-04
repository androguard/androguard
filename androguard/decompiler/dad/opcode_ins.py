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

import util
from struct import pack, unpack
from instruction import (ArrayLengthExpression, ArrayLoadExpression,
                             ArrayStoreInstruction, AssignExpression,
                             BaseClass, BinaryCompExpression, BinaryExpression,
                             BinaryExpression2Addr, BinaryExpressionLit,
                             CastExpression, CheckCastExpression,
                             ConditionalExpression, ConditionalZExpression,
                             Constant, FillArrayExpression,
                             FilledArrayExpression, InstanceExpression,
                             InstanceInstruction, InvokeInstruction,
                             InvokeDirectInstruction, InvokeRangeInstruction,
                             InvokeStaticInstruction, MonitorEnterExpression,
                             MonitorExitExpression, MoveExpression,
                             MoveResultExpression, NewArrayExpression,
                             NewInstance, NopExpression, RefExpression,
                             ThrowExpression, Variable, ReturnInstruction,
                             StaticExpression, StaticInstruction,
                             SwitchExpression, UnaryExpression)

EXPR = 0
INST = 1
COND = 2


class Op(object):
    CMP = 'cmp'
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    AND = '&'
    OR = '|'
    XOR = '^'
    EQUAL = '=='
    NEQUAL = '!='
    GREATER = '>'
    LOWER = '<'
    GEQUAL = '>='
    LEQUAL = '<='
    NEG = '-'
    NOT = '~'
    INTSHL = '<<'  # '(%s << ( %s & 0x1f ))'
    INTSHR = '>>'  # '(%s >> ( %s & 0x1f ))'
    LONGSHL = '<<'  # '(%s << ( %s & 0x3f ))'
    LONGSHR = '>>'  # '(%s >> ( %s & 0x3f ))'


def get_variables(vmap, *variables):
    res = []
    for variable in variables:
        res.append(vmap.setdefault(variable, Variable(variable)))
    if len(res) == 1:
        return res[0]
    return res


# nop
def nop(ins, vmap):
    return NopExpression()


# move vA, vB ( 4b, 4b )
def move(ins, vmap):
    util.log('Move %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return MoveExpression(a, b)


# move/from16 vAA, vBBBB ( 8b, 16b )
def movefrom16(ins, vmap):
    util.log('MoveFrom16 %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AA, ins.BBBB)
    return MoveExpression(a, b)


# move/16 vAAAA, vBBBB ( 16b, 16b )
def move16(ins, vmap):
    util.log('Move16 %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AAAA, ins.BBBB)
    return MoveExpression(a, b)


# move-wide vA, vB ( 4b, 4b )
def movewide(ins, vmap):
    util.log('MoveWide %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return MoveExpression(a, b)


# move-wide/from16 vAA, vBBBB ( 8b, 16b )
def movewidefrom16(ins, vmap):
    util.log('MoveWideFrom16 : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AA, ins.BBBB)
    return MoveExpression(a, b)


# move-wide/16 vAAAA, vBBBB ( 16b, 16b )
def movewide16(ins, vmap):
    util.log('MoveWide16 %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AAAA, ins.BBBB)
    return MoveExpression(a, b)


# move-object vA, vB ( 4b, 4b )
def moveobject(ins, vmap):
    util.log('MoveObject %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return MoveExpression(a, b)


# move-object/from16 vAA, vBBBB ( 8b, 16b )
def moveobjectfrom16(ins, vmap):
    util.log('MoveObjectFrom16 : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AA, ins.BBBB)
    return MoveExpression(a, b)


# move-object/16 vAAAA, vBBBB ( 16b, 16b )
def moveobject16(ins, vmap):
    util.log('MoveObject16 : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AAAA, ins.BBBB)
    return MoveExpression(a, b)


# move-result vAA ( 8b )
def moveresult(ins, vmap, ret):
    util.log('MoveResult : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return MoveResultExpression(a, ret)


# move-result-wide vAA ( 8b )
def moveresultwide(ins, vmap, ret):
    util.log('MoveResultWide : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return MoveResultExpression(a, ret)


# move-result-object vAA ( 8b )
def moveresultobject(ins, vmap, ret):
    util.log('MoveResultObject : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return MoveResultExpression(a, ret)


# move-exception vAA ( 8b )
def moveexception(ins, vmap):
    util.log('MoveException : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return RefExpression(a)


# return-void
def returnvoid(ins, vmap):
    util.log('ReturnVoid', 'debug')
    return ReturnInstruction(None)


# return vAA ( 8b )
def return_reg(ins, vmap):
    util.log('Return : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ReturnInstruction(a)


# return-wide vAA ( 8b )
def returnwide(ins, vmap):
    util.log('ReturnWide : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ReturnInstruction(a)


# return-object vAA ( 8b )
def returnobject(ins, vmap):
    util.log('ReturnObject : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ReturnInstruction(a)


# const/4 vA, #+B ( 4b, 4b )
def const4(ins, vmap):
    util.log('Const4 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.B, 'I')
    a = get_variables(vmap, ins.A)
    exp = AssignExpression(a, cst)
    return exp


# const/16 vAA, #+BBBB ( 8b, 16b )
def const16(ins, vmap):
    util.log('Const16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.BBBB, 'I')
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const vAA, #+BBBBBBBB ( 8b, 32b )
def const(ins, vmap):
    util.log('Const : %s' % ins.get_output(), 'debug')
    value = unpack("=f", pack("=i", ins.BBBBBBBB))[0]
    cst = Constant(value, 'F', ins.BBBBBBBB)
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const/high16 vAA, #+BBBB0000 ( 8b, 16b )
def consthigh16(ins, vmap):
    util.log('ConstHigh16 : %s' % ins.get_output(), 'debug')
    value = unpack('=f', '\x00\x00' + pack('=h', ins.BBBB))[0]
    cst = Constant(value, 'F', ins.BBBB)
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-wide/16 vAA, #+BBBB ( 8b, 16b )
def constwide16(ins, vmap):
    util.log('ConstWide16 : %s' % ins.get_output(), 'debug')
    value = unpack('=d', pack('=d', ins.BBBB))[0]
    cst = Constant(value, 'J', ins.BBBB)
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-wide/32 vAA, #+BBBBBBBB ( 8b, 32b )
def constwide32(ins, vmap):
    util.log('ConstWide32 : %s' % ins.get_output(), 'debug')
    value = unpack('=d', pack('=d', ins.BBBBBBBB))[0]
    cst = Constant(value, 'J', ins.BBBBBBBB)
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-wide vAA, #+BBBBBBBBBBBBBBBB ( 8b, 64b )
def constwide(ins, vmap):
    util.log('ConstWide : %s' % ins.get_output(), 'debug')
    value = unpack('=d', pack('=q', ins.BBBBBBBBBBBBBBBB))[0]
    cst = Constant(value, 'D', ins.BBBBBBBBBBBBBBBB)
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-wide/high16 vAA, #+BBBB000000000000 ( 8b, 16b )
def constwidehigh16(ins, vmap):
    util.log('ConstWideHigh16 : %s' % ins.get_output(), 'debug')
    value = unpack('=d',
                    '\x00\x00\x00\x00\x00\x00' + pack('=h', ins.BBBB))[0]
    cst = Constant(value, 'D', ins.BBBB)
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-string vAA ( 8b )
def conststring(ins, vmap):
    util.log('ConstString : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.get_string(), 'STR')
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-string/jumbo vAA ( 8b )
def conststringjumbo(ins, vmap):
    util.log('ConstStringJumbo %s' % ins.get_output(), 'debug')
    cst = Constant(ins.get_string(), 'STR')
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# const-class vAA, type@BBBB ( 8b )
def constclass(ins, vmap):
    util.log('ConstClass : %s' % ins.get_output(), 'debug')
    cst = Constant(util.get_type(ins.get_string()), 'class')
    a = get_variables(vmap, ins.AA)
    exp = AssignExpression(a, cst)
    return exp


# monitor-enter vAA ( 8b )
def monitorenter(ins, vmap):
    util.log('MonitorEnter : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return MonitorEnterExpression(a)


# monitor-exit vAA ( 8b )
def monitorexit(ins, vmap):
    util.log('MonitorExit : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return MonitorExitExpression(a)


# check-cast vAA ( 8b )
def checkcast(ins, vmap):
    util.log('CheckCast: %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    cast_type = util.get_type(ins.get_translated_kind())
    exp = CheckCastExpression(a, cast_type)
    return exp


# instance-of vA, vB ( 4b, 4b )
def instanceof(ins, vmap):
    util.log('InstanceOf : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    c = BaseClass(util.get_type(ins.get_translated_kind()))
    exp = BinaryExpression('instanceof', b, c)
    return AssignExpression(a, exp)


# array-length vA, vB ( 4b, 4b )
def arraylength(ins, vmap):
    util.log('ArrayLength: %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = ArrayLengthExpression(b)
    return AssignExpression(a, exp)


# new-instance vAA ( 8b )
def newinstance(ins, vmap):
    util.log('NewInstance : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    ins_type = ins.cm.get_type(ins.BBBB)
    exp = NewInstance(ins_type)
    return AssignExpression(a, exp)


# new-array vA, vB ( 8b, size )
def newarray(ins, vmap):
    util.log('NewArray : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = NewArrayExpression(b, ins.cm.get_type(ins.CCCC))
    return AssignExpression(a, exp)


# filled-new-array {vD, vE, vF, vG, vA} ( 4b each )
def fillednewarray(ins, vmap, ret):
    util.log('FilledNewArray : %s' % ins.get_output(), 'debug')
    a, b, c, d, e, f, g = get_variables(vmap, ins.A, ins.BBBB, ins.C, ins.D,
                                                    ins.E, ins.F, ins.G)
    exp = FilledArrayExpression(a, c, [d, e, f, g, a])
    return AssignExpression(ret, exp)


# filled-new-array/range {vCCCC..vNNNN} ( 16b )
def fillednewarrayrange(ins, vmap, ret):
    util.log('FilledNewArrayRange : %s' % ins.get_output(), 'debug')
    a, b, c, n = get_variables(vmap, ins.AA, ins.BBBB, ins.CCCC, ins.NNNN)
    exp = FilledArrayExpression(a, b, [c, n])
    return AssignExpression(ret, exp)


# fill-array-data vAA, +BBBBBBBB ( 8b, 32b )
def fillarraydata(ins, vmap, value):
    util.log('FillArrayData : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return FillArrayExpression(a, value)


# fill-array-data-payload vAA, +BBBBBBBB ( 8b, 32b )
def fillarraydatapayload(ins, vmap):
    util.log('FillArrayDataPayload : %s' % ins.get_output(), 'debug')
    return FillArrayExpression(None)


# throw vAA ( 8b )
def throw(ins, vmap):
    util.log('Throw : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ThrowExpression(a)


# goto +AA ( 8b )
def goto(ins, vmap):
    return NopExpression()


# goto/16 +AAAA ( 16b )
def goto16(ins, vmap):
    return NopExpression()


# goto/32 +AAAAAAAA ( 32b )
def goto32(ins, vmap):
    return NopExpression()


# packed-switch vAA, +BBBBBBBB ( reg to test, 32b )
def packedswitch(ins, vmap):
    util.log('PackedSwitch : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AA, ins.BBBBBBBB)
    return SwitchExpression(a, b)


# sparse-switch vAA, +BBBBBBBB ( reg to test, 32b )
def sparseswitch(ins, vmap):
    util.log('SparseSwitch : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.AA, ins.BBBBBBBB)
    return SwitchExpression(a, b)


# cmpl-float vAA, vBB, vCC ( 8b, 8b, 8b )
def cmplfloat(ins, vmap):
    util.log('CmpglFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryCompExpression(Op.CMP, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# cmpg-float vAA, vBB, vCC ( 8b, 8b, 8b )
def cmpgfloat(ins, vmap):
    util.log('CmpgFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryCompExpression(Op.CMP, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# cmpl-double vAA, vBB, vCC ( 8b, 8b, 8b )
def cmpldouble(ins, vmap):
    util.log('CmplDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryCompExpression(Op.CMP, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# cmpg-double vAA, vBB, vCC ( 8b, 8b, 8b )
def cmpgdouble(ins, vmap):
    util.log('CmpgDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryCompExpression(Op.CMP, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# cmp-long vAA, vBB, vCC ( 8b, 8b, 8b )
def cmplong(ins, vmap):
    util.log('CmpLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryCompExpression(Op.CMP, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# if-eq vA, vB, +CCCC ( 4b, 4b, 16b )
def ifeq(ins, vmap):
    util.log('IfEq : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return ConditionalExpression(Op.EQUAL, a, b)


# if-ne vA, vB, +CCCC ( 4b, 4b, 16b )
def ifne(ins, vmap):
    util.log('IfNe : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return ConditionalExpression(Op.NEQUAL, a, b)


# if-lt vA, vB, +CCCC ( 4b, 4b, 16b )
def iflt(ins, vmap):
    util.log('IfLt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return ConditionalExpression(Op.LOWER, a, b)


# if-ge vA, vB, +CCCC ( 4b, 4b, 16b )
def ifge(ins, vmap):
    util.log('IfGe : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return ConditionalExpression(Op.GEQUAL, a, b)


# if-gt vA, vB, +CCCC ( 4b, 4b, 16b )
def ifgt(ins, vmap):
    util.log('IfGt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return ConditionalExpression(Op.GREATER, a, b)


# if-le vA, vB, +CCCC ( 4b, 4b, 16b )
def ifle(ins, vmap):
    util.log('IfLe : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    return ConditionalExpression(Op.LEQUAL, a, b)


# if-eqz vAA, +BBBB ( 8b, 16b )
def ifeqz(ins, vmap):
    util.log('IfEqz : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ConditionalZExpression(Op.EQUAL, a)


# if-nez vAA, +BBBB ( 8b, 16b )
def ifnez(ins, vmap):
    util.log('IfNez : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ConditionalZExpression(Op.NEQUAL, a)


# if-ltz vAA, +BBBB ( 8b, 16b )
def ifltz(ins, vmap):
    util.log('IfLtz : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ConditionalZExpression(Op.LOWER, a)


# if-gez vAA, +BBBB ( 8b, 16b )
def ifgez(ins, vmap):
    util.log('IfGez : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ConditionalZExpression(Op.GEQUAL, a)


# if-gtz vAA, +BBBB ( 8b, 16b )
def ifgtz(ins, vmap):
    util.log('IfGtz : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ConditionalZExpression(Op.GREATER, a)


# if-lez vAA, +BBBB (8b, 16b )
def iflez(ins, vmap):
    util.log('IfLez : %s' % ins.get_output(), 'debug')
    a = get_variables(vmap, ins.AA)
    return ConditionalZExpression(Op.LEQUAL, a)


#TODO: check type for all aget
# aget vAA, vBB, vCC ( 8b, 8b, 8b )
def aget(ins, vmap):
    util.log('AGet : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aget-wide vAA, vBB, vCC ( 8b, 8b, 8b )
def agetwide(ins, vmap):
    util.log('AGetWide : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aget-object vAA, vBB, vCC ( 8b, 8b, 8b )
def agetobject(ins, vmap):
    util.log('AGetObject : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aget-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
def agetboolean(ins, vmap):
    util.log('AGetBoolean : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aget-byte vAA, vBB, vCC ( 8b, 8b, 8b )
def agetbyte(ins, vmap):
    util.log('AGetByte : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aget-char vAA, vBB, vCC ( 8b, 8b, 8b )
def agetchar(ins, vmap):
    util.log('AGetChar : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aget-short vAA, vBB, vCC ( 8b, 8b, 8b )
def agetshort(ins, vmap):
    util.log('AGetShort : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = ArrayLoadExpression(b, c)
    return AssignExpression(a, exp)


# aput vAA, vBB, vCC
def aput(ins, vmap):
    util.log('APut : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# aput-wide vAA, vBB, vCC ( 8b, 8b, 8b )
def aputwide(ins, vmap):
    util.log('APutWide : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# aput-object vAA, vBB, vCC ( 8b, 8b, 8b )
def aputobject(ins, vmap):
    util.log('APutObject : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# aput-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
def aputboolean(ins, vmap):
    util.log('APutBoolean : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# aput-byte vAA, vBB, vCC ( 8b, 8b, 8b )
def aputbyte(ins, vmap):
    util.log('APutByte : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# aput-char vAA, vBB, vCC ( 8b, 8b, 8b )
def aputchar(ins, vmap):
    util.log('APutChar : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# aput-short vAA, vBB, vCC ( 8b, 8b, 8b )
def aputshort(ins, vmap):
    util.log('APutShort : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    return ArrayStoreInstruction(a, b, c)


# iget vA, vB ( 4b, 4b )
def iget(ins, vmap):
    util.log('IGet : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iget-wide vA, vB ( 4b, 4b )
def igetwide(ins, vmap):
    util.log('IGetWide : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iget-object vA, vB ( 4b, 4b )
def igetobject(ins, vmap):
    util.log('IGetObject : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iget-boolean vA, vB ( 4b, 4b )
def igetboolean(ins, vmap):
    util.log('IGetBoolean : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iget-byte vA, vB ( 4b, 4b )
def igetbyte(ins, vmap):
    util.log('IGetByte : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iget-char vA, vB ( 4b, 4b )
def igetchar(ins, vmap):
    util.log('IGetChar : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iget-short vA, vB ( 4b, 4b )
def igetshort(ins, vmap):
    util.log('IGetShort : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = InstanceExpression(b, klass, ftype, name)
    return AssignExpression(a, exp)


# iput vA, vB ( 4b, 4b )
def iput(ins, vmap):
    util.log('IPut %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# iput-wide vA, vB ( 4b, 4b )
def iputwide(ins, vmap):
    util.log('IPutWide %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# iput-object vA, vB ( 4b, 4b )
def iputobject(ins, vmap):
    util.log('IPutObject %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# iput-boolean vA, vB ( 4b, 4b )
def iputboolean(ins, vmap):
    util.log('IPutBoolean %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# iput-byte vA, vB ( 4b, 4b )
def iputbyte(ins, vmap):
    util.log('IPutByte %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# iput-char vA, vB ( 4b, 4b )
def iputchar(ins, vmap):
    util.log('IPutChar %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# iput-short vA, vB ( 4b, 4b )
def iputshort(ins, vmap):
    util.log('IPutShort %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.CCCC)
    klass = util.get_type(klass)
    a, b = get_variables(vmap, ins.A, ins.B)
    return InstanceInstruction(a, b, klass, atype, name)


# sget vAA ( 8b )
def sget(ins, vmap):
    util.log('SGet : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sget-wide vAA ( 8b )
def sgetwide(ins, vmap):
    util.log('SGetWide : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sget-object vAA ( 8b )
def sgetobject(ins, vmap):
    util.log('SGetObject : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sget-boolean vAA ( 8b )
def sgetboolean(ins, vmap):
    util.log('SGetBoolean : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sget-byte vAA ( 8b )
def sgetbyte(ins, vmap):
    util.log('SGetByte : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sget-char vAA ( 8b )
def sgetchar(ins, vmap):
    util.log('SGetChar : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sget-short vAA ( 8b )
def sgetshort(ins, vmap):
    util.log('SGetShort : %s' % ins.get_output(), 'debug')
    klass, atype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    exp = StaticExpression(klass, atype, name)
    a = get_variables(vmap, ins.AA)
    return AssignExpression(a, exp)


# sput vAA ( 8b )
def sput(ins, vmap):
    util.log('SPut : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# sput-wide vAA ( 8b )
def sputwide(ins, vmap):
    util.log('SPutWide : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# sput-object vAA ( 8b )
def sputobject(ins, vmap):
    util.log('SPutObject : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# sput-boolean vAA ( 8b )
def sputboolean(ins, vmap):
    util.log('SPutBoolean : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# sput-wide vAA ( 8b )
def sputbyte(ins, vmap):
    util.log('SPutByte : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# sput-char vAA ( 8b )
def sputchar(ins, vmap):
    util.log('SPutChar : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# sput-short vAA ( 8b )
def sputshort(ins, vmap):
    util.log('SPutShort : %s' % ins.get_output(), 'debug')
    klass, ftype, name = ins.cm.get_field(ins.BBBB)
    klass = util.get_type(klass)
    a = get_variables(vmap, ins.AA)
    return StaticInstruction(a, klass, ftype, name)


# invoke-virtual {vD, vE, vF, vG, vA} ( 4b each )
def invokevirtual(ins, vmap, ret):
    util.log('InvokeVirtual : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.A - 1
    largs = [ins.D, ins.E, ins.F, ins.G]
    args = get_variables(vmap, *largs)[:nbargs]
    c = get_variables(vmap, ins.C)
    exp = InvokeInstruction(cls_name, name, c, ret_type,
                            param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-super {vD, vE, vF, vG, vA} ( 4b each )
def invokesuper(ins, vmap, ret):
    util.log('InvokeSuper : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.A - 1
    largs = [ins.D, ins.E, ins.F, ins.G]
    args = get_variables(vmap, *largs)[:nbargs]
    superclass = BaseClass('super')
    exp = InvokeInstruction(cls_name, name, superclass, ret_type,
                            param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-direct {vD, vE, vF, vG, vA} ( 4b each )
def invokedirect(ins, vmap, ret):
    util.log('InvokeDirect : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
#    nbargs = ins.A
    nbargs = ins.A - 1
#    largs = [ins.C, ins.D, ins.E, ins.F, ins.G]
    largs = [ins.D, ins.E, ins.F, ins.G]
    args = get_variables(vmap, *largs)[:nbargs]
    c = get_variables(vmap, ins.C)
    ret.set_to(c)
#    exp = InvokeDirectInstruction(cls_name, name, ret_type,
#                                    param_type, nbargs, args)
#    return AssignExpression(c, exp)
    exp = InvokeDirectInstruction(cls_name, name, c, ret_type,
                            param_type, nbargs, args)
    return AssignExpression(c, exp)


# invoke-static {vD, vE, vF, vG, vA} ( 4b each )
def invokestatic(ins, vmap, ret):
    util.log('InvokeStatic : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.A
    largs = [ins.C, ins.D, ins.E, ins.F, ins.G]
    args = get_variables(vmap, *largs)[:nbargs]
    base = BaseClass(util.get_type(cls_name))
    exp = InvokeStaticInstruction(cls_name, name, base, ret_type,
                                    param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-interface {vD, vE, vF, vG, vA} ( 4b each )
def invokeinterface(ins, vmap, ret):
    util.log('InvokeInterface : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.A - 1
    largs = [ins.D, ins.E, ins.F, ins.G]
    args = get_variables(vmap, *largs)[:nbargs]
    c = get_variables(vmap, ins.C)
    exp = InvokeInstruction(cls_name, name, c, ret_type,
                            param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-virtual/range {vCCCC..vNNNN} ( 16b each )
def invokevirtualrange(ins, vmap, ret):
    util.log('InvokeVirtualRange : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.AA
    largs = range(ins.CCCC, ins.NNNN + 1)
    args = get_variables(vmap, *largs)
    if len(largs) == 1:
        args = [args]
    exp = InvokeRangeInstruction(cls_name, name, ret_type,
                                 param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-super/range {vCCCC..vNNNN} ( 16b each )
def invokesuperrange(ins, vmap, ret):
    util.log('InvokeSuperRange : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.AA
    largs = range(ins.CCCC, ins.NNNN + 1)
    args = get_variables(vmap, *largs)
    if len(largs) == 1:
        args = [args]
    exp = InvokeRangeInstruction(cls_name, name, ret_type,
                                param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-direct/range {vCCCC..vNNNN} ( 16b each )
def invokedirectrange(ins, vmap, ret):
    util.log('InvokeDirectRange : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.AA
    largs = range(ins.CCCC, ins.NNNN + 1)
    args = get_variables(vmap, *largs)
    if len(largs) == 1:
        args = [args]
    c = get_variables(vmap, ins.CCCC)
    ret.set_to(c)
    exp = InvokeRangeInstruction(cls_name, name, ret_type,
                                param_type, nbargs, args)
    return AssignExpression(c, exp)


# invoke-static/range {vCCCC..vNNNN} ( 16b each )
def invokestaticrange(ins, vmap, ret):
    util.log('InvokeStaticRange : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.AA
    largs = range(ins.CCCC, ins.NNNN + 1)
    args = get_variables(vmap, *largs)
    if len(largs) == 1:
        args = [args]
    base = BaseClass(util.get_type(cls_name))
    exp = InvokeStaticInstruction(cls_name, name, base, ret_type,
                                param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# invoke-interface/range {vCCCC..vNNNN} ( 16b each )
def invokeinterfacerange(ins, vmap, ret):
    util.log('InvokeInterfaceRange : %s' % ins.get_output(), 'debug')
    method = ins.cm.get_method_ref(ins.BBBB)
    cls_name = util.get_type(method.get_class_name())
    name = method.get_name()
    param_type, ret_type = method.get_proto()
    ret_type = util.get_type(ret_type)
    param_type = util.get_params_type(param_type)
    nbargs = ins.AA
    largs = range(ins.CCCC, ins.NNNN + 1)
    args = get_variables(vmap, *largs)
    if len(largs) == 1:
        args = [args]
    exp = InvokeRangeInstruction(cls_name, name, ret_type,
                                param_type, nbargs, args)
    return AssignExpression(ret.new(), exp)


# neg-int vA, vB ( 4b, 4b )
def negint(ins, vmap):
    util.log('NegInt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = UnaryExpression(Op.NEG, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# not-int vA, vB ( 4b, 4b )
def notint(ins, vmap):
    util.log('NotInt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = UnaryExpression(Op.NOT, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# neg-long vA, vB ( 4b, 4b )
def neglong(ins, vmap):
    util.log('NegLong : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = UnaryExpression(Op.NEG, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# not-long vA, vB ( 4b, 4b )
def notlong(ins, vmap):
    util.log('NotLong : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = UnaryExpression(Op.NOT, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# neg-float vA, vB ( 4b, 4b )
def negfloat(ins, vmap):
    util.log('NegFloat : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = UnaryExpression(Op.NEG, b)
    exp.type = 'F'
    return AssignExpression(a, exp)


# neg-double vA, vB ( 4b, 4b )
def negdouble(ins, vmap):
    util.log('NegDouble : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = UnaryExpression(Op.NEG, b)
    exp.type = 'D'
    return AssignExpression(a, exp)


# int-to-long vA, vB ( 4b, 4b )
def inttolong(ins, vmap):
    util.log('IntToLong : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(long)', 'J', b)
    return AssignExpression(a, exp)


# int-to-float vA, vB ( 4b, 4b )
def inttofloat(ins, vmap):
    util.log('IntToFloat : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(float)', 'F', b)
    return AssignExpression(a, exp)


# int-to-double vA, vB ( 4b, 4b )
def inttodouble(ins, vmap):
    util.log('IntToDouble : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(double)', 'D', b)
    return AssignExpression(a, exp)


# long-to-int vA, vB ( 4b, 4b )
def longtoint(ins, vmap):
    util.log('LongToInt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(int)', 'I', b)
    return AssignExpression(a, exp)


# long-to-float vA, vB ( 4b, 4b )
def longtofloat(ins, vmap):
    util.log('LongToFloat : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(float)', 'F', b)
    return AssignExpression(a, exp)


# long-to-double vA, vB ( 4b, 4b )
def longtodouble(ins, vmap):
    util.log('LongToDouble : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(double)', 'D', b)
    return AssignExpression(a, exp)


# float-to-int vA, vB ( 4b, 4b )
def floattoint(ins, vmap):
    util.log('FloatToInt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(int)', 'I', b)
    return AssignExpression(a, exp)


# float-to-long vA, vB ( 4b, 4b )
def floattolong(ins, vmap):
    util.log('FloatToLong : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(long)', 'J', b)
    return AssignExpression(a, exp)


# float-to-double vA, vB ( 4b, 4b )
def floattodouble(ins, vmap):
    util.log('FloatToDouble : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(double)', 'D', b)
    return AssignExpression(a, exp)


# double-to-int vA, vB ( 4b, 4b )
def doubletoint(ins, vmap):
    util.log('DoubleToInt : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(int)', 'I', b)
    return AssignExpression(a, exp)


# double-to-long vA, vB ( 4b, 4b )
def doubletolong(ins, vmap):
    util.log('DoubleToLong : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(long)', 'J', b)
    return AssignExpression(a, exp)


# double-to-float vA, vB ( 4b, 4b )
def doubletofloat(ins, vmap):
    util.log('DoubleToFloat : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(float)', 'F', b)
    return AssignExpression(a, exp)


# int-to-byte vA, vB ( 4b, 4b )
def inttobyte(ins, vmap):
    util.log('IntToByte : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(byte)', 'B', b)
    return AssignExpression(a, exp)


# int-to-char vA, vB ( 4b, 4b )
def inttochar(ins, vmap):
    util.log('IntToChar : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(char)', 'C', b)
    return AssignExpression(a, exp)


# int-to-short vA, vB ( 4b, 4b )
def inttoshort(ins, vmap):
    util.log('IntToShort : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = CastExpression('(short)', 'S', b)
    return AssignExpression(a, exp)


# add-int vAA, vBB, vCC ( 8b, 8b, 8b )
def addint(ins, vmap):
    util.log('AddInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.ADD, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# sub-int vAA, vBB, vCC ( 8b, 8b, 8b )
def subint(ins, vmap):
    util.log('SubInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.SUB, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# mul-int vAA, vBB, vCC ( 8b, 8b, 8b )
def mulint(ins, vmap):
    util.log('MulInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MUL, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# div-int vAA, vBB, vCC ( 8b, 8b, 8b )
def divint(ins, vmap):
    util.log('DivInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.DIV, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# rem-int vAA, vBB, vCC ( 8b, 8b, 8b )
def remint(ins, vmap):
    util.log('RemInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MOD, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# and-int vAA, vBB, vCC ( 8b, 8b, 8b )
def andint(ins, vmap):
    util.log('AndInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.AND, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# or-int vAA, vBB, vCC ( 8b, 8b, 8b )
def orint(ins, vmap):
    util.log('OrInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.OR, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# xor-int vAA, vBB, vCC ( 8b, 8b, 8b )
def xorint(ins, vmap):
    util.log('XorInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.XOR, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# shl-int vAA, vBB, vCC ( 8b, 8b, 8b )
def shlint(ins, vmap):
    util.log('ShlInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.INTSHL, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# shr-int vAA, vBB, vCC ( 8b, 8b, 8b )
def shrint(ins, vmap):
    util.log('ShrInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.INTSHR, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# ushr-int vAA, vBB, vCC ( 8b, 8b, 8b )
def ushrint(ins, vmap):
    util.log('UShrInt : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.INTSHR, b, c)
    exp.type = 'I'
    return AssignExpression(a, exp)


# add-long vAA, vBB, vCC ( 8b, 8b, 8b )
def addlong(ins, vmap):
    util.log('AddLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.ADD, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# sub-long vAA, vBB, vCC ( 8b, 8b, 8b )
def sublong(ins, vmap):
    util.log('SubLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.SUB, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# mul-long vAA, vBB, vCC ( 8b, 8b, 8b )
def mullong(ins, vmap):
    util.log('MulLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MUL, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# div-long vAA, vBB, vCC ( 8b, 8b, 8b )
def divlong(ins, vmap):
    util.log('DivLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.DIV, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# rem-long vAA, vBB, vCC ( 8b, 8b, 8b )
def remlong(ins, vmap):
    util.log('RemLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MOD, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# and-long vAA, vBB, vCC ( 8b, 8b, 8b )
def andlong(ins, vmap):
    util.log('AndLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.AND, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# or-long vAA, vBB, vCC ( 8b, 8b, 8b )
def orlong(ins, vmap):
    util.log('OrLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.OR, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# xor-long vAA, vBB, vCC ( 8b, 8b, 8b )
def xorlong(ins, vmap):
    util.log('XorLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.XOR, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# shl-long vAA, vBB, vCC ( 8b, 8b, 8b )
def shllong(ins, vmap):
    util.log('ShlLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.LONGSHL, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# shr-long vAA, vBB, vCC ( 8b, 8b, 8b )
def shrlong(ins, vmap):
    util.log('ShrLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.LONGSHR, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# ushr-long vAA, vBB, vCC ( 8b, 8b, 8b )
def ushrlong(ins, vmap):
    util.log('UShrLong : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.LONGSHR, b, c)
    exp.type = 'J'
    return AssignExpression(a, exp)


# add-float vAA, vBB, vCC ( 8b, 8b, 8b )
def addfloat(ins, vmap):
    util.log('AddFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.ADD, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# sub-float vAA, vBB, vCC ( 8b, 8b, 8b )
def subfloat(ins, vmap):
    util.log('SubFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.SUB, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# mul-float vAA, vBB, vCC ( 8b, 8b, 8b )
def mulfloat(ins, vmap):
    util.log('MulFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MUL, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# div-float vAA, vBB, vCC ( 8b, 8b, 8b )
def divfloat(ins, vmap):
    util.log('DivFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.DIV, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# rem-float vAA, vBB, vCC ( 8b, 8b, 8b )
def remfloat(ins, vmap):
    util.log('RemFloat : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MOD, b, c)
    exp.type = 'F'
    return AssignExpression(a, exp)


# add-double vAA, vBB, vCC ( 8b, 8b, 8b )
def adddouble(ins, vmap):
    util.log('AddDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.ADD, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# sub-double vAA, vBB, vCC ( 8b, 8b, 8b )
def subdouble(ins, vmap):
    util.log('SubDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.SUB, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# mul-double vAA, vBB, vCC ( 8b, 8b, 8b )
def muldouble(ins, vmap):
    util.log('MulDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MUL, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# div-double vAA, vBB, vCC ( 8b, 8b, 8b )
def divdouble(ins, vmap):
    util.log('DivDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.DIV, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# rem-double vAA, vBB, vCC ( 8b, 8b, 8b )
def remdouble(ins, vmap):
    util.log('RemDouble : %s' % ins.get_output(), 'debug')
    a, b, c = get_variables(vmap, ins.AA, ins.BB, ins.CC)
    exp = BinaryExpression(Op.MOD, b, c)
    exp.type = 'D'
    return AssignExpression(a, exp)


# add-int/2addr vA, vB ( 4b, 4b )
def addint2addr(ins, vmap):
    util.log('AddInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.ADD, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# sub-int/2addr vA, vB ( 4b, 4b )
def subint2addr(ins, vmap):
    util.log('SubInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.SUB, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# mul-int/2addr vA, vB ( 4b, 4b )
def mulint2addr(ins, vmap):
    util.log('MulInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MUL, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# div-int/2addr vA, vB ( 4b, 4b )
def divint2addr(ins, vmap):
    util.log('DivInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.DIV, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# rem-int/2addr vA, vB ( 4b, 4b )
def remint2addr(ins, vmap):
    util.log('RemInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MOD, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# and-int/2addr vA, vB ( 4b, 4b )
def andint2addr(ins, vmap):
    util.log('AndInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.AND, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# or-int/2addr vA, vB ( 4b, 4b )
def orint2addr(ins, vmap):
    util.log('OrInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.OR, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# xor-int/2addr vA, vB ( 4b, 4b )
def xorint2addr(ins, vmap):
    util.log('XorInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.XOR, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# shl-int/2addr vA, vB ( 4b, 4b )
def shlint2addr(ins, vmap):
    util.log('ShlInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.INTSHL, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# shr-int/2addr vA, vB ( 4b, 4b )
def shrint2addr(ins, vmap):
    util.log('ShrInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.INTSHR, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# ushr-int/2addr vA, vB ( 4b, 4b )
def ushrint2addr(ins, vmap):
    util.log('UShrInt2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.INTSHR, a, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# add-long/2addr vA, vB ( 4b, 4b )
def addlong2addr(ins, vmap):
    util.log('AddLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.ADD, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# sub-long/2addr vA, vB ( 4b, 4b )
def sublong2addr(ins, vmap):
    util.log('SubLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.SUB, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# mul-long/2addr vA, vB ( 4b, 4b )
def mullong2addr(ins, vmap):
    util.log('MulLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MUL, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# div-long/2addr vA, vB ( 4b, 4b )
def divlong2addr(ins, vmap):
    util.log('DivLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.DIV, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# rem-long/2addr vA, vB ( 4b, 4b )
def remlong2addr(ins, vmap):
    util.log('RemLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MUL, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# and-long/2addr vA, vB ( 4b, 4b )
def andlong2addr(ins, vmap):
    util.log('AndLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.AND, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# or-long/2addr vA, vB ( 4b, 4b )
def orlong2addr(ins, vmap):
    util.log('OrLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.OR, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# xor-long/2addr vA, vB ( 4b, 4b )
def xorlong2addr(ins, vmap):
    util.log('XorLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.XOR, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# shl-long/2addr vA, vB ( 4b, 4b )
def shllong2addr(ins, vmap):
    util.log('ShlLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.LONGSHL, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# shr-long/2addr vA, vB ( 4b, 4b )
def shrlong2addr(ins, vmap):
    util.log('ShrLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.LONGSHR, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# ushr-long/2addr vA, vB ( 4b, 4b )
def ushrlong2addr(ins, vmap):
    util.log('UShrLong2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.LONGSHR, a, b)
    exp.type = 'J'
    return AssignExpression(a, exp)


# add-float/2addr vA, vB ( 4b, 4b )
def addfloat2addr(ins, vmap):
    util.log('AddFloat2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.ADD, a, b)
    exp.type = 'F'
    return AssignExpression(a, exp)


# sub-float/2addr vA, vB ( 4b, 4b )
def subfloat2addr(ins, vmap):
    util.log('SubFloat2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.SUB, a, b)
    exp.type = 'F'
    return AssignExpression(a, exp)


# mul-float/2addr vA, vB ( 4b, 4b )
def mulfloat2addr(ins, vmap):
    util.log('MulFloat2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MUL, a, b)
    exp.type = 'F'
    return AssignExpression(a, exp)


# div-float/2addr vA, vB ( 4b, 4b )
def divfloat2addr(ins, vmap):
    util.log('DivFloat2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.DIV, a, b)
    exp.type = 'F'
    return AssignExpression(a, exp)


# rem-float/2addr vA, vB ( 4b, 4b )
def remfloat2addr(ins, vmap):
    util.log('RemFloat2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MOD, a, b)
    exp.type = 'F'
    return AssignExpression(a, exp)


# add-double/2addr vA, vB ( 4b, 4b )
def adddouble2addr(ins, vmap):
    util.log('AddDouble2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.ADD, a, b)
    exp.type = 'D'
    return AssignExpression(a, exp)


# sub-double/2addr vA, vB ( 4b, 4b )
def subdouble2addr(ins, vmap):
    util.log('subDouble2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.SUB, a, b)
    exp.type = 'D'
    return AssignExpression(a, exp)


# mul-double/2addr vA, vB ( 4b, 4b )
def muldouble2addr(ins, vmap):
    util.log('MulDouble2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MUL, a, b)
    exp.type = 'D'
    return AssignExpression(a, exp)


# div-double/2addr vA, vB ( 4b, 4b )
def divdouble2addr(ins, vmap):
    util.log('DivDouble2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.DIV, a, b)
    exp.type = 'D'
    return AssignExpression(a, exp)


# rem-double/2addr vA, vB ( 4b, 4b )
def remdouble2addr(ins, vmap):
    util.log('RemDouble2Addr : %s' % ins.get_output(), 'debug')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpression2Addr(Op.MOD, a, b)
    exp.type = 'D'
    return AssignExpression(a, exp)


# add-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def addintlit16(ins, vmap):
    util.log('AddIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.ADD, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# rsub-int vA, vB, #+CCCC ( 4b, 4b, 16b )
def rsubint(ins, vmap):
    util.log('RSubInt : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.SUB, cst, b)
    exp.type = 'I'
    return AssignExpression(a, exp)


# mul-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def mulintlit16(ins, vmap):
    util.log('MulIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.MUL, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# div-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def divintlit16(ins, vmap):
    util.log('DivIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.DIV, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# rem-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def remintlit16(ins, vmap):
    util.log('RemIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.MOD, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# and-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def andintlit16(ins, vmap):
    util.log('AndIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.AND, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# or-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def orintlit16(ins, vmap):
    util.log('OrIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.OR, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# xor-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
def xorintlit16(ins, vmap):
    util.log('XorIntLit16 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CCCC, 'I')
    a, b = get_variables(vmap, ins.A, ins.B)
    exp = BinaryExpressionLit(Op.XOR, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# add-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def addintlit8(ins, vmap):
    util.log('AddIntLit8 : %s' % ins.get_output(), 'debug')
    # TODO: generalize this to other operators ?
    if ins.CC < 0:
        literal = -ins.CC
        op = Op.SUB
    else:
        literal = ins.CC
        op = Op.ADD
    cst = Constant(literal, 'I')
    a, b = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(op, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# rsub-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def rsubintlit8(ins, vmap):
    util.log('RSubIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.SUB, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# mul-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def mulintlit8(ins, vmap):
    util.log('MulIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.MUL, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# div-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def divintlit8(ins, vmap):
    util.log('DivIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.DIV, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# rem-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def remintlit8(ins, vmap):
    util.log('RemIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.MOD, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# and-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def andintlit8(ins, vmap):
    util.log('AndIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.ADD, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# or-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def orintlit8(ins, vmap):
    util.log('OrIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b, = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.OR, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# xor-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def xorintlit8(ins, vmap):
    util.log('XorIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b, = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.XOR, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# shl-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def shlintlit8(ins, vmap):
    util.log('ShlIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b, = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.INTSHL, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# shr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def shrintlit8(ins, vmap):
    util.log('ShrIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b, = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.INTSHR, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


# ushr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
def ushrintlit8(ins, vmap):
    util.log('UShrIntLit8 : %s' % ins.get_output(), 'debug')
    cst = Constant(ins.CC, 'I')
    a, b, = get_variables(vmap, ins.AA, ins.BB)
    exp = BinaryExpressionLit(Op.INTSHR, b, cst)
    exp.type = 'I'
    return AssignExpression(a, exp)


INSTRUCTION_SET = {
    'nop':                    nop,
    'move':                   move,
    'move/from16':            movefrom16,
    'move/16':                move16,
    'move-wide':              movewide,
    'move-wide/from16':       movewidefrom16,
    'move-wide/16':           movewide16,
    'move-object':            moveobject,
    'move-object/from16':     moveobjectfrom16,
    'move-object/16':         moveobject16,
    'move-result':            moveresult,
    'move-result-wide':       moveresultwide,
    'move-result-object':     moveresultobject,
    'move-exception':         moveexception,
    'return-void':            returnvoid,
    'return':                 return_reg,
    'return-wide':            returnwide,
    'return-object':          returnobject,
    'const/4':                const4,
    'const/16':               const16,
    'const':                  const,
    'const/high16':           consthigh16,
    'const-wide/16':          constwide16,
    'const-wide/32':          constwide32,
    'const-wide':             constwide,
    'const-wide/high16':      constwidehigh16,
    'const-string':           conststring,
    'const-string/jumbo':     conststringjumbo,
    'const-class':            constclass,
    'monitor-enter':          monitorenter,
    'monitor-exit':           monitorexit,
    'check-cast':             checkcast,
    'instance-of':            instanceof,
    'array-length':           arraylength,
    'new-instance':           newinstance,
    'new-array':              newarray,
    'filled-new-array':       fillednewarray,
    'filled-new-array/range': fillednewarrayrange,
    'fill-array-data':        fillarraydata,
    'fill-array-data-payload': fillarraydatapayload,
    'throw':                  throw,
    'goto':                   goto,
    'goto/16':                goto16,
    'goto/32':                goto32,
    'packed-switch':          packedswitch,
    'sparse-switch':          sparseswitch,
    'cmpl-float':             cmplfloat,
    'cmpg-float':             cmpgfloat,
    'cmpl-double':            cmpldouble,
    'cmpg-double':            cmpgdouble,
    'cmp-long':               cmplong,
    'if-eq':                  ifeq,
    'if-ne':                  ifne,
    'if-lt':                  iflt,
    'if-ge':                  ifge,
    'if-gt':                  ifgt,
    'if-le':                  ifle,
    'if-eqz':                 ifeqz,
    'if-nez':                 ifnez,
    'if-ltz':                 ifltz,
    'if-gez':                 ifgez,
    'if-gtz':                 ifgtz,
    'if-lez':                 iflez,
    'aget':                   aget,
    'aget-wide':              agetwide,
    'aget-object':            agetobject,
    'aget-boolean':           agetboolean,
    'aget-byte':              agetbyte,
    'aget-char':              agetchar,
    'aget-short':             agetshort,
    'aput':                   aput,
    'aput-wide':              aputwide,
    'aput-object':            aputobject,
    'aput-boolean':           aputboolean,
    'aput-byte':              aputbyte,
    'aput-char':              aputchar,
    'aput-short':             aputshort,
    'iget':                   iget,
    'iget-wide':              igetwide,
    'iget-object':            igetobject,
    'iget-boolean':           igetboolean,
    'iget-byte':              igetbyte,
    'iget-char':              igetchar,
    'iget-short':             igetshort,
    'iput':                   iput,
    'iput-wide':              iputwide,
    'iput-object':            iputobject,
    'iput-boolean':           iputboolean,
    'iput-byte':              iputbyte,
    'iput-char':              iputchar,
    'iput-short':             iputshort,
    'sget':                   sget,
    'sget-wide':              sgetwide,
    'sget-object':            sgetobject,
    'sget-boolean':           sgetboolean,
    'sget-byte':              sgetbyte,
    'sget-char':              sgetchar,
    'sget-short':             sgetshort,
    'sput':                   sput,
    'sput-wide':              sputwide,
    'sput-object':            sputobject,
    'sput-boolean':           sputboolean,
    'sput-byte':              sputbyte,
    'sput-char':              sputchar,
    'sput-short':             sputshort,
    'invoke-virtual':         invokevirtual,
    'invoke-super':           invokesuper,
    'invoke-direct':          invokedirect,
    'invoke-static':          invokestatic,
    'invoke-interface':       invokeinterface,
    'invoke-virtual/range':   invokevirtualrange,
    'invoke-super/range':     invokesuperrange,
    'invoke-direct/range':    invokedirectrange,
    'invoke-static/range':    invokestaticrange,
    'invoke-interface/range': invokeinterfacerange,
    'neg-int':                negint,
    'not-int':                notint,
    'neg-long':               neglong,
    'not-long':               notlong,
    'neg-float':              negfloat,
    'neg-double':             negdouble,
    'int-to-long':            inttolong,
    'int-to-float':           inttofloat,
    'int-to-double':          inttodouble,
    'long-to-int':            longtoint,
    'long-to-float':          longtofloat,
    'long-to-double':         longtodouble,
    'float-to-int':           floattoint,
    'float-to-long':          floattolong,
    'float-to-double':        floattodouble,
    'double-to-int':          doubletoint,
    'double-to-long':         doubletolong,
    'double-to-float':        doubletofloat,
    'int-to-byte':            inttobyte,
    'int-to-char':            inttochar,
    'int-to-short':           inttoshort,
    'add-int':                addint,
    'sub-int':                subint,
    'mul-int':                mulint,
    'div-int':                divint,
    'rem-int':                remint,
    'and-int':                andint,
    'or-int':                 orint,
    'xor-int':                xorint,
    'shl-int':                shlint,
    'shr-int':                shrint,
    'ushr-int':               ushrint,
    'add-long':               addlong,
    'sub-long':               sublong,
    'mul-long':               mullong,
    'div-long':               divlong,
    'rem-long':               remlong,
    'and-long':               andlong,
    'or-long':                orlong,
    'xor-long':               xorlong,
    'shl-long':               shllong,
    'shr-long':               shrlong,
    'ushr-long':              ushrlong,
    'add-float':              addfloat,
    'sub-float':              subfloat,
    'mul-float':              mulfloat,
    'div-float':              divfloat,
    'rem-float':              remfloat,
    'add-double':             adddouble,
    'sub-double':             subdouble,
    'mul-double':             muldouble,
    'div-double':             divdouble,
    'rem-double':             remdouble,
    'add-int/2addr':          addint2addr,
    'sub-int/2addr':          subint2addr,
    'mul-int/2addr':          mulint2addr,
    'div-int/2addr':          divint2addr,
    'rem-int/2addr':          remint2addr,
    'and-int/2addr':          andint2addr,
    'or-int/2addr':           orint2addr,
    'xor-int/2addr':          xorint2addr,
    'shl-int/2addr':          shlint2addr,
    'shr-int/2addr':          shrint2addr,
    'ushr-int/2addr':         ushrint2addr,
    'add-long/2addr':         addlong2addr,
    'sub-long/2addr':         sublong2addr,
    'mul-long/2addr':         mullong2addr,
    'div-long/2addr':         divlong2addr,
    'rem-long/2addr':         remlong2addr,
    'and-long/2addr':         andlong2addr,
    'or-long/2addr':          orlong2addr,
    'xor-long/2addr':         xorlong2addr,
    'shl-long/2addr':         shllong2addr,
    'shr-long/2addr':         shrlong2addr,
    'ushr-long/2addr':        ushrlong2addr,
    'add-float/2addr':        addfloat2addr,
    'sub-float/2addr':        subfloat2addr,
    'mul-float/2addr':        mulfloat2addr,
    'div-float/2addr':        divfloat2addr,
    'rem-float/2addr':        remfloat2addr,
    'add-double/2addr':       adddouble2addr,
    'sub-double/2addr':       subdouble2addr,
    'mul-double/2addr':       muldouble2addr,
    'div-double/2addr':       divdouble2addr,
    'rem-double/2addr':       remdouble2addr,
    'add-int/lit16':          addintlit16,
    'rsub-int':               rsubint,
    'mul-int/lit16':          mulintlit16,
    'div-int/lit16':          divintlit16,
    'rem-int/lit16':          remintlit16,
    'and-int/lit16':          andintlit16,
    'or-int/lit16':           orintlit16,
    'xor-int/lit16':          xorintlit16,
    'add-int/lit8':           addintlit8,
    'rsub-int/lit8':          rsubintlit8,
    'mul-int/lit8':           mulintlit8,
    'div-int/lit8':           divintlit8,
    'rem-int/lit8':           remintlit8,
    'and-int/lit8':           andintlit8,
    'or-int/lit8':            orintlit8,
    'xor-int/lit8':           xorintlit8,
    'shl-int/lit8':           shlintlit8,
    'shr-int/lit8':           shrintlit8,
    'ushr-int/lit8':          ushrintlit8,
}
