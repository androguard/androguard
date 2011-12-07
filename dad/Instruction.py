#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
# All rights reserved.
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

import struct
import Util
import copy


def get_invoke_params(params, params_type, memory):
    res = []
    i = 0
    while i < len(params_type):
        param = params[i]
        res.append(memory[param].get_content())
        i += Util.get_type_size(params_type[i])
    return res


class Var():
    def __init__(self, name, typeDesc, type, size, content):
        self.name = name
        self.type = type
        self.size = size
        self.content = content
        self.param = False
        self.typeDesc = typeDesc
        self.used = 0
    
    def get_content(self):
        return self.content

    def get_type(self):
        return self.typeDesc

    def get_value(self):
        if self.content:
            return self.content.get_value()
        self.used += 1
        return self.name

    def get_name(self):
        if self.type is 'void':
            return self.content.get_value()
        self.used += 1
        return self.name

    def neg(self):
        return self.content.neg()

    def dump(self, indent):
        if str(self.content.get_value()).startswith('ret'):
            return '   ' * indent + self.content.get_value() + ';\n'
            #return '   ' * indent + self.content.get_value() + ';(%d)\n' % self.used

        #if self.type is 'void':
        #    if self.content.get_value() != 'this':
        #        return '   ' * indent + '%s;(%d)\n' % (self.content.get_value(), self.used)
        #    return ''

        return '   ' * indent + '%s %s = %s;\n' % (self.type, self.name,
                                                   self.content.get_value())

        #return '   ' * indent + '%s %s = %s;(%d)\n' % (self.type, self.name,
        #                        self.content.get_value(), self.used)
    
    def decl(self):
        return '%s %s' % (self.type, self.name)
     
    def __repr__(self):
        if self.content:
            return 'var(%s==%s==%s)' % (self.type, self.name, self.content)
        return 'var(%s===%s)' % (self.type, self.name)


class Variable():
    def __init__(self):
        self.nbVars = {}
        self.vars = []

    def newVar(self, typeDesc, content=None):
        n = self.nbVars.setdefault(typeDesc, 1)
        self.nbVars[typeDesc] += 1
        size = Util.get_type_size(typeDesc)
        _type = Util.get_type(typeDesc)
        if _type:
            type = _type.split('.')[-1]
        #Util.log('typeDesc : %s' % typeDesc, 'debug')
        if type.endswith('[]'):
            name = '%sArray%d' % (type.strip('[]'), n)
        else:
            name = '%sVar%d' % (type, n)
        var = Var(name, typeDesc, type, size, content)
        self.vars.append(var)
        return var

    def startBlock(self):
        self.varscopy = copy.deepcopy(self.nbVars)

    def endBlock(self):
        self.nbVars = self.varscopy


class Expression(object):
    def __init__(self, ins):
        self.ins = ins

    def get_reg(self):
        return [self.register]

    def get_value(self):
        return '(expression %s has no get_value implemented)' % self

    def get_type(self):
        return '(expression %s has no type defined)' % self

    def symbolic_process(self, memory):
        Util.log('Symbolic processing not implemented for this expression.',
                 'debug')


class BinaryExpression(Expression):
    def __init__(self, ins):
        self.ins = ins
        self.ops = ins.get_operands()
        self.register = self.ops[0][1]

    def get_reg(self):
        return [self.register]

    def get_value(self):
        return '(binary get_value not implemented) %s' % self

    def get_type(self):
        return self.type

    def symbolic_process(self, memory):
        Util.log('Symbolic processing for this binary expression.',
                 'debug')


class UnaryExpression(Expression):
    def __init__(self, ins):
        self.ins = ins
        self.ops = ins.get_operands()
        self.register = self.ops[0][1]
    
    def get_value(self):
        return '(unary expression %s has no get_value implemented)' % self

    def get_type(self):
        return self.type

    def symbolic_process(self, memory):
        Util.log('Symbolic processing not implemented for this' \
                 'unary expression.', 'debug')


class IdentifierExpression(Expression):
    def __init__(self, ins):
        self.ins = ins
        self.ops = ins.get_operands()
        self.register = self.ops[0][1]

    def get_reg(self):
        return [self.register]

    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def symbolic_process(self, memory):
        Util.log('Symbolic processing not implemented for this' \
                 'constant expression.', 'debug')

class ConditionalExpression(Expression):
    def __init__(self, ins):
        self.ins = ins
        self.ops = ins.get_operands()
    
    def get_reg(self):
        return '(condition expression %s has no dest register.)' % self
        
    def get_value(self):
        return '(condition expression %s has no get_value implemented)' % self

    def get_type(self):
        return 'V'

    def symbolic_process(self, memory):
        Util.log('Symbolic processing not implemented for this' \
                 'condition expression.', 'debug')


# nop
class Nop(UnaryExpression):
    def __init__(self, ins):
        Util.log('Nop %s' % ins, 'debug')

    def get_value(self):
        return ''


# move vA, vB ( 4b, 4b )
class Move(UnaryExpression):
    def __init__(self, ins):
        super(Move, self).__init__(ins)
        Util.log('Move %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        Util.log('value : %s' % (self.source), 'debug')

    def get_type(self):
        return self.source.get_type()

    def get_value(self):
        return self.source.get_value()


# move/from16 vAA, vBBBB ( 8b, 16b )
class MoveFrom16(UnaryExpression):
    def __init__(self, ins):
        super(MoveFrom16, self).__init__(ins)
        Util.log('MoveFrom16 %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move/16 vAAAA, vBBBB ( 16b, 16b )
class Move16(UnaryExpression):
    pass


# move-wide vA, vB ( 4b, 4b )
class MoveWide(UnaryExpression):
    pass


# move-wide/from16 vAA, vBBBB ( 8b, 16b )
class MoveWideFrom16(UnaryExpression):
    def __init__(self, ins):
        super(MoveWideFrom16, self).__init__(ins)
        Util.log('MoveWideFrom16 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move-wide/16 vAAAA, vBBBB ( 16b, 16b )
class MoveWide16(UnaryExpression):
    pass


# move-object vA, vB ( 4b, 4b )
class MoveObject(UnaryExpression):
    def __init__(self, ins):
        super(MoveObject, self).__init__(ins)
        Util.log('MoveObject %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move-object/from16 vAA, vBBBB ( 8b, 16b )
class MoveObjectFrom16(UnaryExpression):
    def __init__(self, ins):
        super(MoveObjectFrom16, self).__init__(ins)
        Util.log('MoveObjectFrom16 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move-object/16 vAAAA, vBBBB ( 16b, 16b )
class MoveObject16(UnaryExpression):
    pass


# move-result vAA ( 8b )
class MoveResult(UnaryExpression):
    def __init__(self, ins):
        super(MoveResult, self).__init__(ins)
        Util.log('MoveResult : %s' % self.ops, 'debug')

    def symbolic_process(self, memory):
        self.value = memory.get('heap')
        memory['heap'] = None
        Util.log('value :: %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        if self.value:
            return self.value.get_value()

    def __str__(self):
        return 'Move res in v' + str(self.register)


# move-result-wide vAA ( 8b )
class MoveResultWide(UnaryExpression):
    def __init__(self, ins):
        super(MoveResultWide, self).__init__(ins)
        Util.log('MoveResultWide : %s' % self.ops, 'debug')

    def symbolic_process(self, memory):
        self.value = memory.get('heap')
        memory['heap'] = None
        Util.log('value :: %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        if self.value is not None:
            return self.value.get_value()

    def __str__(self):
        return 'MoveResultWide in v' + str(self.register)


# move-result-object ( 8b )
class MoveResultObject(UnaryExpression):
    def __init__(self, ins):
        super(MoveResultObject, self).__init__(ins)
        Util.log('MoveResultObject : %s' % self.ops, 'debug')

    def symbolic_process(self, memory):
        self.value = memory.get('heap')
        memory['heap'] = None
        Util.log('value :: %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        if self.value is not None:
            return self.value.get_value()

    def __str__(self):
        return 'MoveResObj in v' + str(self.register)


# move-exception vAA ( 8b )
class MoveException(UnaryExpression):
    def __init__(self, ins):
        super(MoveException, self).__init__(ins)
        Util.log('MoveException : %s' % self.ops, 'debug')


# return-void
class ReturnVoid(Expression):
    def __init__(self, ins):
        super(ReturnVoid, self).__init__(ins)
        Util.log('ReturnVoid', 'debug')
        self.type = 'V'

    def get_reg(self):
        Util.log('ReturnVoid has no dest register', 'debug')

    def symbolic_process(self, memory):
        pass

    def get_value(self):
        return 'return'

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Return'


# return vAA ( 8b )
class Return(IdentifierExpression):
    def __init__(self, ins):
        super(Return, self).__init__(ins)
        Util.log('Return : %s' % self.ops, 'debug')
        self.op = 'return %s'

    def get_reg(self):
        Util.log('Return has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.returnValue = memory[self.register].get_content()

    def get_type(self):
        return self.returnValue.get_type()

    def get_value(self):
        return self.op % self.returnValue.get_name() # FIXME

    def __str__(self):
        return 'Return (%s)' % str(self.returnValue)


# return-wide vAA ( 8b )
class ReturnWide(IdentifierExpression):
    pass


# return-object vAA ( 8b )
class ReturnObject(IdentifierExpression):
    def __init__(self, ins):
        super(ReturnObject, self).__init__(ins)
        Util.log('ReturnObject : %s' % self.ops, 'debug')

    def get_reg(self):
        Util.log('ReturnObject has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.returnValue = memory[self.register].get_content()
        self.op = 'return %s' % self.returnValue.get_value()

    def get_type(self):
        return self.returnValue.get_type()

    def get_value(self):
        return self.op

    def __str__(self):
        return 'ReturnObject (%s)' % str(self.returnValue)


# const/4 vA, #+B ( 4b, 4b )
class Const4(IdentifierExpression):
    def __init__(self, ins):
        super(Const4, self).__init__(ins)
        Util.log('Const4 : %s' % self.ops, 'debug')
        self.value = int(self.ops[1][1])
        self.type = 'I'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Const4 : %s' % str(self.value)


# const/16 vAA, #+BBBB ( 8b, 16b )
class Const16(IdentifierExpression):
    def __init__(self, ins):
        super(Const16, self).__init__(ins)
        Util.log('Const16 : %s' % self.ops, 'debug')
        self.value = int(self.ops[1][1])
        self.type = 'I'
        Util.log('==> %s' % self.value, 'debug')

    def __str__(self):
        return 'Const16 : %s' % str(self.value)


# const vAA, #+BBBBBBBB ( 8b, 32b )
class Const(IdentifierExpression):
    def __init__(self, ins):
        super(Const, self).__init__(ins)
        Util.log('Const : %s' % self.ops, 'debug')
        self.value = ((0xFFFF & self.ops[2][1]) << 16) | ((0xFFFF & self.ops[1][1]))
        self.type = 'F'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return struct.unpack('f', struct.pack('L', self.value))[0]

    def get_int_value(self):
        return self.value

    def __str__(self):
        return 'Const : ' + str(self.value)


# const/high16 vAA, #+BBBB0000 ( 8b, 16b )
class ConstHigh16(IdentifierExpression):
    def __init__(self, ins):
        super(ConstHigh16, self).__init__(ins)
        Util.log('ConstHigh16 : %s' % self.ops, 'debug')
        self.value = struct.unpack('f',
                                   struct.pack('i', self.ops[1][1] << 16))[0]
        self.type = 'F'
        Util.log('==> %s' % self.value, 'debug')

    def __str__(self):
        return 'ConstHigh16 : %s' % str(self.value)


# const-wide/16 vAA, #+BBBB ( 8b, 16b )
class ConstWide16(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWide16, self).__init__(ins)
        Util.log('ConstWide16 : %s' % self.ops, 'debug')
        self.type = 'J'
        self.value = struct.unpack('d', struct.pack('d', self.ops[1][1]))[0]
        Util.log('==> %s' % self.value, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'Constwide16 : %s' % str(self.value)


# const-wide/32 vAA, #+BBBBBBBB ( 8b, 32b )
class ConstWide32(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWide32, self).__init__(ins)
        Util.log('ConstWide32 : %s' % self.ops, 'debug')
        self.type = 'J'
        val = ((0xFFFF & self.ops[2][1]) << 16) | ((0xFFFF & self.ops[1][1]))
        self.value = struct.unpack('d', struct.pack('d', val))[0]
        Util.log('==> %s' % self.value, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'Constwide32 : %s' % str(self.value)


# const-wide vAA, #+BBBBBBBBBBBBBBBB ( 8b, 64b )
class ConstWide(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWide, self).__init__(ins)
        Util.log('ConstWide : %s' % self.ops, 'debug')
        val = self.ops[1:]
        val = (0xFFFF & val[0][1]) | ((0xFFFF & val[1][1]) << 16) | (\
              (0xFFFF & val[2][1]) << 32) | ((0xFFFF & val[3][1]) << 48)
        self.type = 'D'
        self.value = struct.unpack('d', struct.pack('Q', val))[0]
        Util.log('==> %s' % self.value, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'ConstWide : %s' % str(self.value)


# const-wide/high16 vAA, #+BBBB000000000000 ( 8b, 16b )
class ConstWideHigh16(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWideHigh16, self).__init__(ins)
        Util.log('ConstWideHigh16 : %s' % self.ops, 'debug')
        self.value = struct.unpack('d',
                         struct.pack('Q', 0xFFFFFFFFFFFFFFFF
                                          & int(self.ops[1][1]) << 48))[0]
        self.type = 'D'
        Util.log('==> %s' % self.value, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'ConstWide : %s' % str(self.value)


# const-string vAA ( 8b )
class ConstString(IdentifierExpression):
    def __init__(self, ins):
        super(ConstString, self).__init__(ins)
        Util.log('ConstString : %s' % self.ops, 'debug')
        self.value = '%s' % self.ops[1][2]
        self.type = 'STR'
        Util.log('==> %s' % self.value, 'debug')

    def __str__(self):
        return self.value


# const-string/jumbo vAA ( 8b )
class ConstStringJumbo(IdentifierExpression):
    pass


# const-class vAA ( 8b )
class ConstClass(IdentifierExpression):
    def __init__(self, ins):
        super(ConstClass, self).__init__(ins)
        Util.log('ConstClass : %s' % self.ops, 'debug')
        self.type = '%s' % self.ops[1][2]
        self.value = self.type
        Util.log('==> %s' % self.value, 'debug')

    def __str__(self):
        return self.value


# monitor-enter vAA ( 8b )
class MonitorEnter(UnaryExpression):
    def __init__(self, ins):
        super(MonitorEnter, self).__init__(ins)
        Util.log('MonitorEnter : %s' % self.ops, 'debug')

    def symbolic_process(self, memory):
        self.register = memory[self.register].get_content()
        self.op = 'synchronized( %s )'

    def get_type(self):
        return self.register.get_type()

    def get_reg(self):
        Util.log('MonitorEnter has no dest register', 'debug')

    def get_value(self):
        return self.op % self.register.get_value()


# monitor-exit vAA ( 8b )
class MonitorExit(UnaryExpression):
    def __init__(self, ins):
        super(MonitorExit, self).__init__(ins)
        Util.log('MonitorExit : %s' % self.ops, 'debug')

    def symbolic_process(self, memory):
        self.register = memory[self.register].get_content()
        self.op = ''

    def get_type(self):
        return self.register.get_type()

    def get_reg(self):
        Util.log('MonitorExit has no dest register', 'debug')

    def get_value(self):
        return '' 


# check-cast vAA ( 8b )
class CheckCast(UnaryExpression):
    def __init__(self, ins):
        super(CheckCast, self).__init__(ins)
        Util.log('CheckCast: %s' % self.ops, 'debug')
        self.register = self.ops[0][1]

    def symbolic_process(self, memory):
        self.register = memory[self.register].get_content()

    def get_type(self):
        Util.log('type : %s ' % self.register, 'debug')
        return self.register.get_type()

    def get_reg(self):
        Util.log('CheckCast has no dest register', 'debug')


# instance-of vA, vB ( 4b, 4b )
class InstanceOf(BinaryExpression):
    def __init__(self, ins):
        super(InstanceOf, self).__init__(ins)
        Util.log('InstanceOf : %s' % self.ops, 'debug')


# array-length vA, vB ( 4b, 4b )
class ArrayLength(UnaryExpression):
    def __init__(self, ins):
        super(ArrayLength, self).__init__(ins)
        Util.log('ArrayLength: %s' % self.ops, 'debug')
        self.src = self.ops[1][1]

    def symbolic_process(self, memory):
        self.src = memory[self.src].get_content()
        self.op = '%s.length'

    def get_value(self):
        return self.op % self.src.get_value()

    def get_type(self):
        return self.src.get_type()


# new-instance vAA ( 8b )
class NewInstance(UnaryExpression):
    def __init__(self, ins):
        super(NewInstance, self).__init__(ins)
        Util.log('NewInstance : %s' % self.ops, 'debug')
        self.type = self.ops[-1][-1]

    def symbolic_process(self, memory):
        self.op = 'new %s()'  # %s()' % ( self.type[1:-1].replace( '/', '.' ) )

    def get_value(self):
        return self.op % Util.get_type(self.type)

    def __str__(self):
        return 'New ( %s )' % self.type


# new-array vA, vB ( 8b, size )
class NewArray(UnaryExpression):
    def __init__(self, ins):
        super(NewArray, self).__init__(ins)
        Util.log('NewArray : %s' % self.ops, 'debug')
        self.size = int(self.ops[1][1])
        self.type = self.ops[-1][-1]

    def symbolic_process(self, memory):
        self.size = memory[self.size].get_content()
        self.op = 'new %s'

    def get_value(self):
        return self.op % Util.get_type(self.type, self.size.get_value())

    def get_type(self):
        return self.type

    def __str__(self):
        return 'NewArray( %s )' % self.type

# filled-new-array {vD, vE, vF, vG, vA} ( 4b each )
class FilledNewArray(UnaryExpression):
    pass


# filled-new-array/range {vCCCC..vNNNN} ( 16b )
class FilledNewArrayRange(UnaryExpression):
    pass


# fill-array-data vAA, +BBBBBBBB ( 8b, 32b )
class FillArrayData(UnaryExpression):
    def __init__(self, ins):
        super(FillArrayData, self).__init__(ins)
        Util.log('FillArrayData : %s' % self.ops, 'debug')

    def symbolic_process(self, memory):
        self.type = memory[self.register].get_content().get_type()

    def get_value(self):
        return self.ins.get_op_value()

    def get_type(self):
        return self.type

    def get_reg(self):
        Util.log('FillArrayData has no dest register.', 'debug')


# throw vAA ( 8b )
class Throw(UnaryExpression):
    pass


# goto +AA ( 8b )
class Goto(Expression):
    pass

# goto/16 +AAAA ( 16b )
class Goto16(Expression):
    pass

# goto/32 +AAAAAAAA ( 32b )
class Goto32(Expression):
    pass

# packed-switch vAA, +BBBBBBBB ( reg to test, 32b )
class PackedSwitch(UnaryExpression):
    def __init__(self, ins):
        super(PackedSwitch, self).__init__(ins)
        Util.log('PackedSwitch : %s' % self.ops, 'debug')

#    def symbolic_process(self, memory):
#        self.switch = memory[self.register].get_content()

    def get_reg(self):
        Util.log('PackedSwitch has no dest register.', 'debug')


# sparse-switch vAA, +BBBBBBBB ( reg to test, 32b )
class SparseSwitch(UnaryExpression):
    pass


# cmpl-float vAA, vBB, vCC ( 8b, 8b, 8b )
class CmplFloat(BinaryExpression):
    def __init__(self, ins):
        super(CmplFloat, self).__init__(ins)
        Util.log('CmpglFloat : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.type = 'Z'

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s == %s' % (self.first, self.second)

    def __str__(self):
        return 'CmplFloat (%s < %s ?)' % (self.first.get_value(),
                                           self.second.get_value())


# cmpg-float vAA, vBB, vCC ( 8b, 8b, 8b )
class CmpgFloat(BinaryExpression):
    pass


# cmpl-double vAA, vBB, vCC ( 8b, 8b, 8b )
class CmplDouble(BinaryExpression):
    pass


# cmpg-double vAA, vBB, vCC ( 8b, 8b, 8b )
class CmpgDouble(BinaryExpression):
    def __init__(self, ins):
        super(CmpgDouble, self).__init__(ins)
        Util.log('CmpgDouble : %s' % self.ops, 'debug')
        self.first = int(self.ops[1][1])
        self.second = int(self.ops[2][1])
        self.type = 'Z'

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()
    
    def get_value(self):
        return '%s == %s' % (self.first, self.second)

    def __str__(self):
        return 'CmpgDouble (%s > %s ?)' % (self.first.get_value(),
                                           self.second.get_value())

# cmp-long vAA, vBB, vCC ( 8b, 8b, 8b )
class CmpLong(BinaryExpression):
    pass


CONDS = {
    '==' : '!=',
    '!=' : '==',
    '<' : '>=',
    '<=' : '>',
    '>=' : '<',
    '>' : '<='
}

# if-eq vA, vB, +CCCC ( 4b, 4b, 16b )
class IfEq(ConditionalExpression):
    def __init__(self, ins):
        super(IfEq, self).__init__(ins)
        Util.log('IfEq : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.op = '=='

    def get_reg(self):
        Util.log('IfEq has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s %s %s' % (self.first.get_value(), self.op,
                             self.second.get_value())

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfEq (%s %s %s)' % (self.first.get_value(), self.op,
                                    self.second.get_value())


# if-ne vA, vB, +CCCC ( 4b, 4b, 16b )
class IfNe(ConditionalExpression):
    def __init__(self, ins):
        super(IfNe, self).__init__(ins)
        Util.log('IfNe : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.op = '!='

    def get_reg(self):
        Util.log('IfNe has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s %s %s' % (self.first.get_value(), self.op,
                             self.second.get_value())

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfNe (%s %s %s)' % (self.first.get_value(), self.op,
                                  self.second.get_value())


# if-lt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLt(ConditionalExpression):
    def __init__(self, ins):
        super(IfLt,  self).__init__(ins)
        Util.log('IfLt : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.op = '<'

    def get_reg(self):
        Util.log('IfLt has no dest register', 'debug')
    
    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s %s %s' % (self.first.get_value(), self.op,
                             self.second.get_value())

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfLt (%s %s %s)' % (self.first.get_value(), self.op,
                                    self.second.get_value())


# if-ge vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGe(ConditionalExpression):
    def __init__(self, ins):
        super(IfGe, self).__init__(ins)
        Util.log('IfGe : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.op = '>='
    
    def get_reg(self):
        Util.log('IfGe has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s %s %s' % (self.first.get_value(), self.op,
                             self.second.get_value())

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfGe (%s %s %s)' % (self.first.get_value(), self.op,
                                    self.second.get_value())


# if-gt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGt(ConditionalExpression):
    def __init__(self, ins):
        super(IfGt, self).__init__(ins)
        Util.log('IfGt : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.op = '>'

    def get_reg(self):
        Util.log('IfGt has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s %s %s' % (self.first.get_value(), self.op,
                             self.second.get_value())

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfGt (%s %s %s)' % (self.first.get_value(), self.op,
                                    self.second.get_value())


# if-le vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLe(ConditionalExpression):
    def __init__(self, ins):
        super(IfLe, self).__init__(ins)
        Util.log('IfLe : %s' % self.ops, 'debug')
        self.first = int(self.ops[0][1])
        self.second = int(self.ops[1][1])
        self.op = '<='

    def get_reg(self):
        Util.log('IfLe has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_value(self):
        return '%s %s %s' % (self.first.get_value(), self.op,
                             self.second.get_value())

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfLe (%s %s %s)' % (self.first.get_value(), self.op,
                                    self.second.get_value())

# if-eqz vAA, +BBBB ( 8b, 16b )
class IfEqz(ConditionalExpression):
    def __init__(self, ins):
        super(IfEqz, self).__init__(ins)
        Util.log('IfEqz : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '=='

    def get_reg(self):
        Util.log('IfEqz has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.test = memory[self.test].get_content()

    def get_value(self):
        if self.test.get_type() == 'Z':
            if self.op == '==':
                return '%s' % self.test.get_value()
            else:
                return '!%s' % self.test.get_value()
        return '%s %s 0' % (self.test.get_value(), self.op)

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfEqz (%s)' % (self.test.get_value())


# if-nez vAA, +BBBB ( 8b, 16b )
class IfNez(ConditionalExpression):
    def __init__(self, ins):
        super(IfNez, self).__init__(ins)
        Util.log('IfNez : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '!='

    def get_reg(self):
        Util.log('IfNez has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.test = memory[self.test].get_content()

    def get_value(self):
        if self.test.get_type() == 'Z':
            if self.op == '==':
                return '%s' % self.test.get_value()
            else:
                return '!%s' % self.test.get_value()
            #return '%s %s %s' % (self.test.content.first.get_value(),
            #                     self.op,
            #                     self.test.content.second.get_value())
        return '%s %s 0' % (self.test.get_value(), self.op)

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfNez (%s)' % self.test.get_value()


# if-ltz vAA, +BBBB ( 8b, 16b )
class IfLtz(ConditionalExpression):
    def __init__(self, ins):
        super(IfLtz, self).__init__(ins)
        Util.log('IfLtz : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '<'

    def get_reg(self):
        Util.log('IfLtz has no dest register', 'debug')
    
    def symbolic_process(self, memory):
        self.test = memory[self.test].get_content()

    def get_value(self):
        if self.test.get_type() == 'Z':
            return '%s %s %s' % (self.test.content.first.get_value(),
                                 self.op,
                                 self.test.content.second.get_value())
        return '%s %s 0' % (self.test.get_value(), self.op)

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfLtz (%s)' % self.test.get_value()


# if-gez vAA, +BBBB ( 8b, 16b )
class IfGez(ConditionalExpression):
    def __init__(self, ins):
        super(IfGez, self).__init__(ins)
        Util.log('IfGez : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '>='

    def get_reg(self):
        Util.log('IfGez has no dest register', 'debug')
    
    def symbolic_process(self, memory):
        self.test = memory[self.test].get_content()

    def get_value(self):
        if self.test.get_type() == 'Z':
            return '%s %s %s' % (self.test.content.first.get_value(),
                                 self.op,
                                 self.test.content.second.get_value())
        return '%s %s 0' % (self.test.get_value(), self.op)

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfGez (%s)' % self.test.get_value()


# if-gtz vAA, +BBBB ( 8b, 16b )
class IfGtz(ConditionalExpression):
    def __init__(self, ins):
        super(IfGtz, self).__init__(ins)
        Util.log('IfGtz : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '>'

    def get_reg(self):
        Util.log('IfGtz has no dest register', 'debug')
    
    def symbolic_process(self, memory):
        self.test = memory[self.test].get_content()

    def get_value(self):
        if self.test.get_type() == 'Z':
            return '%s %s %s' % (self.test.content.first.get_value(),
                                 self.op,
                                 self.test.content.second.get_value())
        return '%s %s 0' % (self.test.get_value(), self.op)

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfGtz (%s)' % self.test.get_value()


# if-lez vAA, +BBBB (8b, 16b )
class IfLez(ConditionalExpression):
    def __init__(self, ins):
        super(IfLez, self).__init__(ins)
        Util.log('IfLez : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '<='

    def get_reg(self):
        Util.log('IfLez has no dest register', 'debug')

    def symbolic_process(self, memory):
        self.test = memory[self.test].get_content()

    def get_value(self):
        if self.test.get_type() == 'Z':
            return '%s %s %s' % (self.test.content.first.get_value(),
                                 self.op,
                                 self.test.content.second.get_value())
        return '%s %s 0' % (self.test.get_value(), self.op)

    def neg(self):
        self.op = CONDS[self.op]

    def __str__(self):
        return 'IfLez (%s)' % self.test.get_value()

#FIXME: check type all aget
# aget vAA, vBB, vCC ( 8b, 8b, 8b )
class AGet(UnaryExpression):
    def __init__(self, ins):
        super(AGet, self).__init__(ins)
        Util.log('AGet : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aget-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetWide(UnaryExpression):
    def __init__(self, ins):
        super(AGetWide, self).__init__(ins)
        Util.log('AGetWide : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aget-object vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetObject(UnaryExpression):
    def __init__(self, ins):
        super(AGetObject, self).__init__(ins)
        Util.log('AGetObject : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aget-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetBoolean(UnaryExpression):
    def __init__(self, ins):
        super(AGetBoolean, self).__init__(ins)
        Util.log('AGetBoolean : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aget-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetByte(UnaryExpression):
    def __init__(self, ins):
        super(AGetByte, self).__init__(ins)
        Util.log('AGetByte : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aget-char vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetChar(UnaryExpression):
    def __init__(self, ins):
        super(AGetChar, self).__init__(ins)
        Util.log('AGetChar : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aget-short vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetShort(UnaryExpression):
    def __init__(self, ins):
        super(AGetShort, self).__init__(ins)
        Util.log('AGetShort : %s' % self.ops, 'debug')
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        
    def symbolic_process(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.type = self.array.get_type().strip('[')
        self.op = '%s[%s]'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.array.get_value(), self.index.get_value())


# aput vAA, vBB, vCC 
class APut(UnaryExpression):
    def __init__(self, ins):
        super(APut, self).__init__(ins)
        Util.log('APut : %s' % self.ops, 'debug')
        self.source = int(self.ops[0][1])
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        self.type = 'V'

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.op = '%s[%s] = %s'

    def get_value(self):
        if self.index.get_type() != 'I':
            return self.op % (self.array.get_value(),
                              self.index.get_content().get_int_value(),
                              self.source.get_value())
        else:
            return self.op % (self.array.get_value(), self.index.get_value(),
                              self.source.get_value())

    def get_reg(self):
        Util.log('APut has no dest register.', 'debug')


# aput-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class APutWide(UnaryExpression):
    pass


# aput-object vAA, vBB, vCC ( 8b, 8b, 8b )
class APutObject(UnaryExpression):
    def __init__(self, ins):
        super(APutObject, self).__init__(ins)
        Util.log('APutObject : %s' % self.ops, 'debug')
        self.source = int(self.ops[0][1])
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        self.type = 'V'

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.op = '%s[%s] = %s'

    def get_value(self):
        if self.index.get_type() != 'I':
            return self.op % (self.array.get_value(),
                              self.index.get_content().get_int_value(),
                              self.source.get_value())
        else:
            return self.op % (self.array.get_value(), self.index.get_value(),
                              self.source.get_value())

    def get_reg(self):
        Util.log('APutObject has no dest register.', 'debug')


# aput-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class APutBoolean(UnaryExpression):
    pass


# aput-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class APutByte(UnaryExpression):
    def __init__(self, ins):
        super(APutByte, self).__init__(ins)
        Util.log('APutByte : %s' % self.ops, 'debug')
        self.source = int(self.ops[0][1])
        self.array = int(self.ops[1][1])
        self.index = int(self.ops[2][1])
        self.type = 'V'

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.op = '%s[%s] = %s'

    def get_value(self):
        if self.index.get_type() != 'I':
            return self.op % (self.array.get_value(),
                              self.index.get_content().get_int_value(),
                              self.source.get_value())
        else:
            return self.op % (self.array.get_value(), self.index.get_value(),
                              self.source.get_value())

    def get_reg(self):
        Util.log('APutByte has no dest register.', 'debug')


# aput-char vAA, vBB, vCC ( 8b, 8b, 8b )
class APutChar(UnaryExpression):
    pass


# aput-short vAA, vBB, vCC ( 8b, 8b, 8b )
class APutShort(UnaryExpression):
    pass


# iget vA, vB ( 4b, 4b )
class IGet(UnaryExpression):
    def __init__(self, ins):
        super(IGet, self).__init__(ins)
        Util.log('IGet : %s' % self.ops, 'debug')
        self.location = self.ops[-1][2]
        self.type = self.ops[-1][3]
        self.name = self.ops[-1][4]
        self.retType = self.ops[-1][-1]
        self.objreg = self.ops[1][1]

    def symbolic_process(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.op = '%s.%s'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.obj.get_value(), self.name)

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-wide vA, vB ( 4b, 4b )
class IGetWide(UnaryExpression):
    def __init__(self, ins):
        super(IGetWide, self).__init__(ins)
        Util.log('IGetWide : %s' % self.ops, 'debug')
        self.location = self.ops[-1][2]
        self.type = self.ops[-1][3]
        self.name = self.ops[-1][4]
        self.retType = self.ops[-1][-1]
        self.objreg = self.ops[1][1]

    def symbolic_process(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.op = '%s.%s'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.obj.get_value(), self.name)

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-object vA, vB ( 4b, 4b )
class IGetObject(UnaryExpression):
    def __init__(self, ins):
        super(IGetObject, self).__init__(ins)
        Util.log('IGetObject : %s' % self.ops, 'debug')
        self.location = self.ops[-1][2]
        self.type = self.ops[-1][3]
        self.name = self.ops[-1][4]
        self.retType = self.ops[-1][-1]
        self.objreg = self.ops[1][1]

    def symbolic_process(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.op = '%s.%s'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.obj.get_value(), self.name)

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-boolean vA, vB ( 4b, 4b )
class IGetBoolean(UnaryExpression):
    def __init__(self, ins):
        super(IGetBoolean, self).__init__(ins)
        Util.log('IGetBoolean : %s' % self.ops, 'debug')
        self.location = self.ops[-1][2]
        self.type = self.ops[-1][3]
        self.name = self.ops[-1][4]
        self.retType = self.ops[-1][-1]
        self.objreg = self.ops[1][1]

    def symbolic_process(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.op = '%s.%s'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.obj.get_value(), self.name)

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-byte vA, vB ( 4b, 4b )
class IGetByte(UnaryExpression):
    pass


# iget-char vA, vB ( 4b, 4b )
class IGetChar(UnaryExpression):
    pass


# iget-short vA, vB ( 4b, 4b )
class IGetShort(UnaryExpression):
    pass


# iput vA, vB ( 4b, 4b )
class IPut(UnaryExpression):
    def __init__(self, ins):
        super(IPut, self).__init__(ins)
        Util.log('IPut %s' % self.ops, 'debug')
        self.src = int(self.ops[0][1])
        self.dest = int(self.ops[1][1])
        self.location = self.ops[2][2]  # [1:-1].replace( '/', '.' )
        self.type = 'V'
        self.name = self.ops[2][4]

    def symbolic_process(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        self.op = '%s.%s = %s'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.name,
                            self.src.get_value())

    def get_reg(self):
        Util.log('IPut has no dest register.', 'debug')


# iput-wide vA, vB ( 4b, 4b )
class IPutWide(UnaryExpression):
    def __init__(self, ins):
        super(IPutWide, self).__init__(ins)
        Util.log('IPutWide %s' % self.ops, 'debug')
        self.src = int(self.ops[0][1])
        self.dest = int(self.ops[1][1])
        self.location = self.ops[2][2]
        self.type = 'V'
        self.name = self.ops[2][4]

    def symbolic_process(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        self.op = '%s.%s = %s'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.name,
                            self.src.get_value())
    def get_reg(self):
        Util.log('IPutWide has no dest register.', 'debug')


# iput-object vA, vB ( 4b, 4b )
class IPutObject(UnaryExpression):
    def __init__(self, ins):
        super(IPutObject, self).__init__(ins)
        Util.log('IPutObject %s' % self.ops, 'debug')
        self.src = int(self.ops[0][1])
        self.dest = int(self.ops[1][1])
        self.location = self.ops[2][2]
        self.type = 'V'
        self.name = self.ops[2][4]

    def symbolic_process(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        self.op = '%s.%s = %s'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.name,
                            self.src.get_value())
    def get_reg(self):
        Util.log('IPutObject has no dest register.', 'debug')


# iput-boolean vA, vB ( 4b, 4b )
class IPutBoolean(UnaryExpression):
    def __init__(self, ins):
        super(IPutBoolean, self).__init__(ins)
        Util.log('IPutBoolean %s' % self.ops, 'debug')
        self.src = int(self.ops[0][1])
        self.dest = int(self.ops[1][1])
        self.location = self.ops[2][2]
        self.type = 'V'
        self.name = self.ops[2][4]

    def symbolic_process(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        self.op = '%s.%s = %s'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.name,
                            self.src.get_value())
    def get_reg(self):
        Util.log('IPutObject has no dest register.', 'debug')


# iput-byte vA, vB ( 4b, 4b )
class IPutByte(UnaryExpression):
    pass


# iput-char vA, vB ( 4b, 4b )
class IPutChar(UnaryExpression):
    pass


# iput-short vA, vB ( 4b, 4b )
class IPutShort(UnaryExpression):
    pass


# sget vAA ( 8b )
class SGet(UnaryExpression):
    def __init__(self, ins):
        super(SGet, self).__init__(ins)
        Util.log('SGet : %s' % self.ops, 'debug')
        location = self.ops[1][2][1:-1]
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = self.ops[1][3] #[1:-1].replace('/', '.')
        self.name = self.ops[1][4]

    def get_type(self):
        return self.type

    def get_value(self):
        return '%s.%s' % (self.location, self.name)

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sget-wide vAA ( 8b )
class SGetWide(UnaryExpression):
    pass


# sget-object vAA ( 8b )
class SGetObject(UnaryExpression):
    def __init__(self, ins):
        super(SGetObject, self).__init__(ins)
        Util.log('SGetObject : %s' % self.ops, 'debug')
        location = self.ops[1][2][1:-1]
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = self.ops[1][3] #[1:-1].replace('/', '.')
        self.name = self.ops[1][4]

    def get_type(self):
        return self.type

    def get_value(self):
        return '%s.%s' % (self.location, self.name)

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sget-boolean vAA ( 8b )
class SGetBoolean(UnaryExpression):
    pass


# sget-byte vAA ( 8b )
class SGetByte(UnaryExpression):
    pass


# sget-char vAA ( 8b )
class SGetChar(UnaryExpression):
    pass


# sget-short vAA ( 8b )
class SGetShort(UnaryExpression):
    pass


# sput vAA ( 8b )
class SPut(UnaryExpression):
    def __init__(self, ins):
        super(SPut, self).__init__(ins)
        Util.log('SPut : %s' % self.ops, 'debug')
        location = self.ops[1][2][1:-1]
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = self.ops[1][3]
        self.name = self.ops[1][4]
    
    def symbolic_process(self, memory):
        self.register = memory[self.register].get_content()

    def get_type(self):
        return 'V'

    def get_value(self):
        return '%s.%s = %s' % (self.location, self.name,
                               self.register.get_value())
    
    def get_reg(self):
        Util.log('SPut has no dest register.', 'debug')

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sput-wide vAA ( 8b )
class SPutWide(UnaryExpression):
    pass


# sput-object vAA ( 8b )
class SPutObject(UnaryExpression):
    def __init__(self, ins):
        super(SPutObject, self).__init__(ins)
        Util.log('SPutObject : %s' % self.ops, 'debug')
        location = self.ops[1][2][1:-1]
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = self.ops[1][3]
        self.name = self.ops[1][4]
    
    def symbolic_process(self, memory):
        self.register = memory[self.register].get_content()

    def get_type(self):
        return 'V'

    def get_value(self):
        return '%s.%s = %s' % (self.location, self.name,
                               self.register.get_value())
    
    def get_reg(self):
        Util.log('SPutObject has no dest register.', 'debug')

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sput-boolean vAA ( 8b )
class SPutBoolean(UnaryExpression):
    pass


# sput-wide vAA ( 8b )
class SPutByte(UnaryExpression):
    pass


# sput-char vAA ( 8b )
class SPutChar(UnaryExpression):
    pass


# sput-short vAA ( 8b )
class SPutShort(UnaryExpression):
    pass


# invoke-virtual {vD, vE, vF, vG, vA} ( 4b each )
class InvokeVirtual(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeVirtual, self).__init__(ins)
        Util.log('InvokeVirtual : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = self.ops[-1][2]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.base = memory[self.register].get_content()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.get_value() == 'this':
            self.op = '%s(%s)'
        else:
            self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def get_value(self):
        for param in self.params:
            param.used = 1
        if self.base.get_value() == 'this':
            return self.op % (self.methCalled, ', '.join([str(
                               param.get_value()) for param in self.params]))
        return self.op % (self.base.get_value(), self.methCalled, ', '.join([
                           str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeVirtual has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeVirtual (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-super {vD, vE, vF, vG, vA} ( 4b each )
class InvokeSuper(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeSuper, self).__init__(ins)
        Util.log('InvokeSuper : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        self.type = self.ops[-1][2]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = 'super.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeSuper has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeSuper (%s) %s (%s ; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-direct {vD, vE, vF, vG, vA} ( 4b each )
class InvokeDirect(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeDirect, self).__init__(ins)
        Util.log('InvokeDirect : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        type = self.ops[-1][2][1:-1]
        if 'java/lang' in type:
            self.type = type.split('/')[-1]
        else:
            self.type = type.replace('/', '.')
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.base = memory[self.register].get_content()
        if self.base.get_value() == 'this':
            self.op = None
        else:
            self.params = get_invoke_params(self.params, self.paramsType,
                                                                   memory)
            self.op = '%s %s(%s)'

    def get_value(self):
        if self.op is None:
            return self.base.get_value()
        return self.op % (self.base.get_value(), self.type, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def __str__(self):
        return 'InvokeDirect (%s) %s (%s)' % (self.returnType,
                                            self.methCalled, str(self.params))


# invoke-static {vD, vE, vF, vG, vA} ( 4b each )
class InvokeStatic(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeStatic, self).__init__(ins)
        Util.log('InvokeStatic : %s' % self.ops, 'debug')
        if len(self.ops) > 1:
            self.params = [int(i[1]) for i in self.ops[0:-1]]
        else:
            self.params = []
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = self.ops[-1][2][1:-1].replace('/', '.')
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def get_value(self):
        return self.op % (self.type, self.methCalled, ', '.join([
                          str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeStatic has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeStatic (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-interface {vD, vE, vF, vG, vA} ( 4b each )
class InvokeInterface(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeInterface, self).__init__(ins)
        Util.log('InvokeInterface : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        type = self.ops[-1][2][1:-1]
        self.type = type.replace('/', '.')
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.base = memory[self.register].get_content()
        if self.base.get_value() == 'this':
            self.op = None
        else:
            self.params = get_invoke_params(self.params, self.paramsType,
                                                                   memory)
            self.op = '%s %s(%s)'

    def get_value(self):
        if self.op is None:
            return self.base.get_value()
        return self.op % (self.base.get_value(), self.type, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def __str__(self):
        return 'InvokeInterface (%s) %s (%s)' % (self.returnType,
                                            self.methCalled, str(self.params))


# invoke-virtual/range {vCCCC..vNNNN} ( 16b each )
class InvokeVirtualRange(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeVirtualRange, self).__init__(ins)
        Util.log('InvokeVirtualRange : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = self.ops[-1][2]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.base = memory[self.register].get_content()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.get_value() == 'this':
            self.op = '%s(%s)'
        else:
            self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def get_value(self):
        if self.base.get_value() == 'this':
            return self.op % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))
        return self.op % (self.base.get_value(), self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeVirtualRange has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeVirtualRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-super/range {vCCCC..vNNNN} ( 16b each )
class InvokeSuperRange(IdentifierExpression):
    pass


# invoke-direct/range {vCCCC..vNNNN} ( 16b each )
class InvokeDirectRange(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeDirectRange, self).__init__(ins)
        Util.log('InvokeDirectRange : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        self.base = memory[self.register].get_content()
        self.type = self.base.get_type()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = '%s %s(%s)'

    def get_value(self):
        return self.op % (self.base.get_value(), self.type, ', '.join(
        [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.type

    def __str__(self):
        return 'InvokeDirectRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, str(self.paramsType), str(self.params))


# invoke-static/range {vCCCC..vNNNN} ( 16b each )
class InvokeStaticRange(IdentifierExpression):
    pass


# invoke-interface/range {vCCCC..vNNNN} ( 16b each )
class InvokeInterfaceRange(IdentifierExpression):
    def __init__(self, ins):
        super(InvokeInterfaceRange, self).__init__(ins)
        Util.log('InvokeInterfaceRange : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = self.ops[-1][2]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory):
        memory['heap'] = True
        self.base = memory[self.register].get_content()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.get_value() == 'this':
            self.op = '%s(%s)'
        else:
            self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def get_value(self):
        if self.base.get_value() == 'this':
            return self.op % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))
        return self.op % (self.base.get_value(), self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeInterfaceRange has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeInterfaceRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# neg-int vA, vB ( 4b, 4b )
class NegInt(UnaryExpression):
    def __init__(self, ins):
        super(NegInt, self).__init__(ins)
        Util.log('NegInt : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.op = '-(%s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source.get_value())


# not-int vA, vB ( 4b, 4b )
class NotInt(UnaryExpression):
    pass


# neg-long vA, vB ( 4b, 4b )
class NegLong(UnaryExpression):
    pass


# not-long vA, vB ( 4b, 4b )
class NotLong(UnaryExpression):
    pass


# neg-float vA, vB ( 4b, 4b )
class NegFloat(UnaryExpression):
    pass


# neg-double vA, vB ( 4b, 4b )
class NegDouble(UnaryExpression):
    pass


# int-to-long vA, vB ( 4b, 4b )
class IntToLong(UnaryExpression):
    def __init__(self, ins):
        super(IntToLong, self).__init__(ins)
        Util.log('IntToLong : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((long) %s)' % self.source.get_value()

    def get_type(self):
        return 'J'

# int-to-float vA, vB ( 4b, 4b )
class IntToFloat(UnaryExpression):
    def __init__(self, ins):
        super(IntToFloat, self).__init__(ins)
        Util.log('IntToFloat : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((float) %s)' % self.source.get_value()

    def get_type(self):
        return 'F'


# int-to-double vA, vB ( 4b, 4b )
class IntToDouble(UnaryExpression):
    def __init__(self, ins):
        super(IntToDouble, self).__init__(ins)
        Util.log('IntToDouble : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((double) %s)' % self.source.get_value()

    def get_type(self):
        return 'D'

# long-to-int vA, vB ( 4b, 4b )
class LongToInt(UnaryExpression):
    def __init__(self, ins):
        super(LongToInt, self).__init__(ins)
        Util.log('LongToInt : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((int) %s)' % self.source.get_value()

    def get_type(self):
        return 'I'


# long-to-float vA, vB ( 4b, 4b )
class LongToFloat(UnaryExpression):
    def __init__(self, ins):
        super(LongToFloat, self).__init__(ins)
        Util.log('LongToFloat : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((float) %s)' % self.source.get_value()

    def get_type(self):
        return 'F'

# long-to-double vA, vB ( 4b, 4b )
class LongToDouble(UnaryExpression):
    def __init__(self, ins):
        super(LongToDouble, self).__init__(ins)
        Util.log('LongToDouble : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((double) %s)' % self.source.get_value()

    def get_type(self):
        return 'D'


# float-to-int vA, vB ( 4b, 4b )
class FloatToInt(UnaryExpression):
    def __init__(self, ins):
        super(FloatToInt, self).__init__(ins)
        Util.log('FloatToInt : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((int) %s)' % self.source.get_value()

    def get_type(self):
        return 'I'


# float-to-long vA, vB ( 4b, 4b )
class FloatToLong(UnaryExpression):
    def __init__(self, ins):
        super(FloatToLong, self).__init__(ins)
        Util.log('FloatToLong : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((long) %s)' % self.source.get_value()

    def get_type(self):
        return 'J'


# float-to-double vA, vB ( 4b, 4b )
class FloatToDouble(UnaryExpression):
    def __init__(self, ins):
        super(FloatToDouble, self).__init__(ins)
        Util.log('FloatToDouble : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((double) %s)' % self.source.get_value()
    
    def get_type(self):
        return 'D'


# double-to-int vA, vB ( 4b, 4b )
class DoubleToInt(UnaryExpression):
    def __init__(self, ins):
        super(DoubleToInt, self).__init__(ins)
        Util.log('DoubleToInt : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((int) %s)' % self.source.get_value()

    def get_type(self):
        return 'I'


# double-to-long vA, vB ( 4b, 4b )
class DoubleToLong(UnaryExpression):
    def __init__(self, ins):
        super(DoubleToLong, self).__init__(ins)
        Util.log('DoubleToLong : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((long) %s)' % self.source.get_value()

    def get_type(self):
        return 'J'


# double-to-float vA, vB ( 4b, 4b )
class DoubleToFloat(UnaryExpression):
    def __init__(self, ins):
        super(DoubleToFloat, self).__init__(ins)
        Util.log('DoubleToFloat : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((float) %s)' % self.source.get_value()

    def get_type(self):
        return 'F'

# int-to-byte vA, vB ( 4b, 4b )
class IntToByte(UnaryExpression):
    def __init__(self, ins):
        super(IntToByte, self).__init__(ins)
        Util.log('IntToByte : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((byte) %s)' % self.source.get_value()

    def get_type(self):
        return 'B'


# int-to-char vA, vB ( 4b, 4b )
class IntToChar(UnaryExpression):
    def __init__(self, ins):
        super(IntToChar, self).__init__(ins)
        Util.log('IntToChar : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((char) %s)' % self.source.get_value()

    def get_type(self):
        return 'C'


# int-to-short vA, vB ( 4b, 4b )
class IntToShort(UnaryExpression):
    def __init__(self, ins):
        super(IntToShort, self).__init__(ins)
        Util.log('IntToShort : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((short) %s)' % self.source.get_value()

    def get_type(self):
        return 'S'


# add-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AddInt(BinaryExpression):
    def __init__(self, ins):
        super(AddInt, self).__init__(ins)
        Util.log('AddInt : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])
        self.op = '+'

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return '%s %s %s' % (self.source1.get_value(), self.op,
                            self.source2.get_value())


# sub-int vAA, vBB, vCC ( 8b, 8b, 8b )
class SubInt(BinaryExpression):
    def __init__(self, ins):
        super(SubInt, self).__init__(ins)
        Util.log('SubInt : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s - %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# mul-int vAA, vBB, vCC ( 8b, 8b, 8b )
class MulInt(BinaryExpression):
    def __init__(self, ins):
        super(MulInt, self).__init__(ins)
        Util.log('MulInt : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# div-int vAA, vBB, vCC ( 8b, 8b, 8b )
class DivInt(BinaryExpression):
    def __init__(self, ins):
        super(DivInt, self).__init__(ins)
        Util.log('DivInt : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])
        self.op = '/'

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return '%s %s %s' % (self.source1.get_value(), self.op,
                             self.source2.get_value())


# rem-int vAA, vBB, vCC ( 8b, 8b, 8b )
class RemInt(BinaryExpression):
    pass


# and-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AndInt(BinaryExpression):
    def __init__(self, ins):
        super(AndInt, self).__init__(ins)
        Util.log('AndInt : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])
        self.op = '&'

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return '%s %s %s' % (self.source1.get_value(), self.op,
                             self.source2.get_value())


# or-int vAA, vBB, vCC ( 8b, 8b, 8b )
class OrInt(BinaryExpression):
    pass


# xor-int vAA, vBB, vCC ( 8b, 8b, 8b )
class XorInt(BinaryExpression):
    pass


# shl-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlInt(BinaryExpression):
    pass


# shr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrInt(BinaryExpression):
    pass


# ushr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrInt(BinaryExpression):
    pass


# add-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AddLong(BinaryExpression):
    pass


# sub-long vAA, vBB, vCC ( 8b, 8b, 8b )
class SubLong(BinaryExpression):
    def __init__(self, ins):
        super(SubLong, self).__init__(ins)
        Util.log('SubLong : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s - %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# mul-long vAA, vBB, vCC ( 8b, 8b, 8b )
class MulLong(BinaryExpression):
    pass


# div-long vAA, vBB, vCC ( 8b, 8b, 8b )
class DivLong(BinaryExpression):
    pass


# rem-long vAA, vBB, vCC ( 8b, 8b, 8b )
class RemLong(BinaryExpression):
    pass


# and-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AndLong(BinaryExpression):
    pass


# or-long vAA, vBB, vCC ( 8b, 8b, 8b )
class OrLong(BinaryExpression):
    pass


# xor-long vAA, vBB, vCC ( 8b, 8b, 8b )
class XorLong(BinaryExpression):
    pass


# shl-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlLong(BinaryExpression):
    pass


# shr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrLong(BinaryExpression):
    pass


# ushr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrLong(BinaryExpression):
    pass


# add-float vAA, vBB, vCC ( 8b, 8b, 8b )
class AddFloat(BinaryExpression):
    def __init__(self, ins):
        super(AddFloat, self).__init__(ins)
        Util.log('AddFloat : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s + %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'F'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# sub-float vAA, vBB, vCC ( 8b, 8b, 8b )
class SubFloat(BinaryExpression):
    pass


# mul-float vAA, vBB, vCC ( 8b, 8b, 8b )
class MulFloat(BinaryExpression):
    pass


# div-float vAA, vBB, vCC ( 8b, 8b, 8b )
class DivFloat(BinaryExpression):
    def __init__(self, ins):
        super(DivFloat, self).__init__(ins)
        Util.log('DivFloat : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s / %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'F'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# rem-float vAA, vBB, vCC ( 8b, 8b, 8b )
class RemFloat(BinaryExpression):
    pass


# add-double vAA, vBB, vCC ( 8b, 8b, 8b )
class AddDouble(BinaryExpression):
    def __init__(self, ins):
        super(AddDouble, self).__init__(ins)
        Util.log('AddDouble : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s + %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# sub-double vAA, vBB, vCC ( 8b, 8b, 8b )
class SubDouble(BinaryExpression):
    def __init__(self, ins):
        super(SubDouble, self).__init__(ins)
        Util.log('SubDouble : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s - %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# mul-double vAA, vBB, vCC ( 8b, 8b, 8b )
class MulDouble(BinaryExpression):
    def __init__(self, ins):
        super(MulDouble, self).__init__(ins)
        Util.log('MulDouble : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# div-double vAA, vBB, vCC ( 8b, 8b, 8b )
class DivDouble(BinaryExpression):
    def __init__(self, ins):
        super(DivDouble, self).__init__(ins)
        Util.log('DivDouble : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s / %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# rem-double vAA, vBB, vCC ( 8b, 8b, 8b )
class RemDouble(BinaryExpression):
    def __init__(self, ins):
        super(RemDouble, self).__init__(ins)
        Util.log('RemDouble : %s' % self.ops, 'debug')
        self.source1 = int(self.ops[1][1])
        self.source2 = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.op = '(%s % %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.source1.get_value(), self.source2.get_value())


# add-int/2addr vA, vB ( 4b, 4b )
class AddInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddInt2Addr, self).__init__(ins)
        Util.log('AddInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.op = '+'

    def symbolic_process(self, memory):
        self.op1 = memory[self.register].get_content()
        self.op2 = memory[self.source].get_content()

    def get_type(self):
        return 'I'

    def get_value(self):
        return '%s %s %s' % (self.op1.get_value(), self.op,
                             self.op2.get_value())


# sub-int/2addr vA, vB ( 4b, 4b )
class SubInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(SubInt2Addr, self).__init__(ins)
        Util.log('SubInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s - %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# mul-int/2addr vA, vB ( 4b, 4b )
class MulInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulInt2Addr, self).__init__(ins)
        Util.log('MulInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# div-int/2addr vA, vB ( 4b, 4b )
class DivInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivInt2Addr, self).__init__(ins)
        Util.log('DivInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s / %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# rem-int/2addr vA, vB ( 4b, 4b )
class RemInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(RemInt2Addr, self).__init__(ins)
        Util.log('RemInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s %% %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# and-int/2addr vA, vB ( 4b, 4b )
class AndInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AndInt2Addr, self).__init__(ins)
        Util.log('AndInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s & %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# or-int/2addr vA, vB ( 4b, 4b )
class OrInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(OrInt2Addr, self).__init__(ins)
        Util.log('OrInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s | %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# xor-int/2addr vA, vB ( 4b, 4b )
class XorInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(XorInt2Addr, self).__init__(ins)
        Util.log('XorInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s ^ %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# shl-int/2addr vA, vB ( 4b, 4b )
class ShlInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShlInt2Addr, self).__init__(ins)
        Util.log('ShlInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s << ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# shr-int/2addr vA, vB ( 4b, 4b )
class ShrInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShrInt2Addr, self).__init__(ins)
        Util.log('ShrInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# ushr-int/2addr vA, vB ( 4b, 4b )
class UShrInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(UShrInt2Addr, self).__init__(ins)
        Util.log('UShrInt2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# add-long/2addr vA, vB ( 4b, 4b )
class AddLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddLong2Addr, self).__init__(ins)
        Util.log('AddLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s + %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# sub-long/2addr vA, vB ( 4b, 4b )
class SubLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(SubLong2Addr, self).__init__(ins)
        Util.log('SubLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s - %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# mul-long/2addr vA, vB ( 4b, 4b )
class MulLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulLong2Addr, self).__init__(ins)
        Util.log('MulLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# div-long/2addr vA, vB ( 4b, 4b )
class DivLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivLong2Addr, self).__init__(ins)
        Util.log('DivLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s / %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# rem-long/2addr vA, vB ( 4b, 4b )
class RemLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(RemLong2Addr, self).__init__(ins)
        Util.log('RemLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s %% %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# and-long/2addr vA, vB ( 4b, 4b )
class AndLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AndLong2Addr, self).__init__(ins)
        Util.log('AddLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s & %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# or-long/2addr vA, vB ( 4b, 4b )
class OrLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(OrLong2Addr, self).__init__(ins)
        Util.log('OrLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s | %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# xor-long/2addr vA, vB ( 4b, 4b )
class XorLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(XorLong2Addr, self).__init__(ins)
        Util.log('XorLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s ^ %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# shl-long/2addr vA, vB ( 4b, 4b )
class ShlLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShlLong2Addr, self).__init__(ins)
        Util.log('ShlLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s << ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# shr-long/2addr vA, vB ( 4b, 4b )
class ShrLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShrLong2Addr, self).__init__(ins)
        Util.log('ShrLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# ushr-long/2addr vA, vB ( 4b, 4b )
class UShrLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(UShrLong2Addr, self).__init__(ins)
        Util.log('UShrLong2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# add-float/2addr vA, vB ( 4b, 4b )
class AddFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddFloat2Addr, self).__init__(ins)
        Util.log('AddFloat2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s + %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'F'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# sub-float/2addr vA, vB ( 4b, 4b )
class SubFloat2Addr(BinaryExpression):
    pass


# mul-float/2addr vA, vB ( 4b, 4b )
class MulFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulFloat2Addr, self).__init__(ins)
        Util.log('MulFloat2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'F'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())



# div-float/2addr vA, vB ( 4b, 4b )
class DivFloat2Addr(BinaryExpression):
    pass


# rem-float/2addr vA, vB ( 4b, 4b )
class RemFloat2Addr(BinaryExpression):
    pass


# add-double/2addr vA, vB ( 4b, 4b )
class AddDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddDouble2Addr, self).__init__(ins)
        Util.log('AddDouble2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s + %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# sub-double/2addr vA, vB ( 4b, 4b )
class SubDouble2Addr(BinaryExpression):
    pass


# mul-double/2addr vA, vB ( 4b, 4b )
class MulDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulDouble2Addr, self).__init__(ins)
        Util.log('MulDouble2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# div-double/2addr vA, vB ( 4b, 4b )
class DivDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivDouble2Addr, self).__init__(ins)
        Util.log('DivDouble2Addr : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.op = '(%s / %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'D'

    def get_value(self):
        return self.op % (self.dest.get_value(), self.source.get_value())


# rem-double/2addr vA, vB ( 4b, 4b )
class RemDouble2Addr(BinaryExpression):
    pass


# add-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AddIntLit16(BinaryExpression):
    pass


# rsub-int vA, vB, #+CCCC ( 4b, 4b, 16b )
class RSubInt(BinaryExpression):
    pass


# mul-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class MulIntLit16(BinaryExpression):
    def __init__(self, ins):
        super(MulIntLit16, self).__init__(ins)
        Util.log('MulIntLit16 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.const = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.op = '(%s * %s)' % (memory[self.source].get_content().get_value(),
        self.const)
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op


# div-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class DivIntLit16(BinaryExpression):
    pass


# rem-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class RemIntLit16(BinaryExpression):
    pass


# and-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AndIntLit16(BinaryExpression):
    pass


# or-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class OrIntLit16(BinaryExpression):
    pass


# xor-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class XorIntLit16(BinaryExpression):
    pass


# add-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AddIntLit8(BinaryExpression):
    def __init__(self, ins):
        super(AddIntLit8, self).__init__(ins)
        Util.log('AddIntLit8 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.const = int(self.ops[2][1])
        self.op = '+'

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return '%s %s %s' % (self.source.get_value(), self.op, self.const)

    def __str__(self):
        return 'AddIntLit8 (%s, %s)' % (self.source, self.const)


# rsub-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RSubIntLit8(BinaryExpression):
    def __init__(self, ins):
        super(RSubIntLit8, self).__init__(ins)
        Util.log('RSubIntLit8 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.const = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.op = '(%s - %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source.get_value(), self.const)

    def __str__(self):
        return 'AddIntLit8 (%s, %s)' % (self.source, self.const)


# mul-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class MulIntLit8(BinaryExpression):
    def __init__(self, ins):
        super(MulIntLit8, self).__init__(ins)
        Util.log('MulIntLit8 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.const = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.op = '(%s * %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source.get_value(), self.const)

    def __str__(self):
        return 'MulIntLit8 (%s, %s)' % (self.source, self.const)


# div-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class DivIntLit8(BinaryExpression):
    def __init__(self, ins):
        super(DivIntLit8, self).__init__(ins)
        Util.log('DivIntLit8 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.const = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.op = '(%s / %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source.get_value(), self.const)


# rem-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RemIntLit8(BinaryExpression):
    def __init__(self, ins):
        super(RemIntLit8, self).__init__(ins)
        Util.log('RemIntLit8 : %s' % self.ops, 'debug')
        self.source = int(self.ops[1][1])
        self.const = int(self.ops[2][1])

    def symbolic_process(self, memory):
        self.source = memory[self.source].get_content()
        self.op = '(%s %% %s)'
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.op % (self.source.get_value(), self.const)


# and-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AndIntLit8(BinaryExpression):
    pass


# or-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class OrIntLit8(BinaryExpression):
    pass


# xor-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class XorIntLit8(BinaryExpression):
    pass


# shl-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShlIntLit8(BinaryExpression):
    pass


# shr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShrIntLit8(BinaryExpression):
    pass


# ushr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class UShrIntLit8(BinaryExpression):
    pass


INSTRUCTION_SET = {
    'nop'                   : Nop,
    'move'                  : Move,
    'move/from16'           : MoveFrom16,
    'move/16'               : Move16,
    'move-wide'             : MoveWide,
    'move-wide/from16'      : MoveWideFrom16,
    'move-wide/16'          : MoveWide16,
    'move-object'           : MoveObject,
    'move-object/from16'    : MoveObjectFrom16,
    'move-object/16'        : MoveObject16,
    'move-result'           : MoveResult,
    'move-result-wide'      : MoveResultWide,
    'move-result-object'    : MoveResultObject,
    'move-exception'        : MoveException,
    'return-void'           : ReturnVoid,
    'return'                : Return,
    'return-wide'           : ReturnWide,
    'return-object'         : ReturnObject,
    'const/4'               : Const4,
    'const/16'              : Const16,
    'const'                 : Const,
    'const/high16'          : ConstHigh16,
    'const-wide/16'         : ConstWide16,
    'const-wide/32'         : ConstWide32,
    'const-wide'            : ConstWide,
    'const-wide/high16'     : ConstWideHigh16,
    'const-string'          : ConstString,
    'const-string/jumbo'    : ConstStringJumbo,
    'const-class'           : ConstClass,
    'monitor-enter'         : MonitorEnter,
    'monitor-exit'          : MonitorExit,
    'check-cast'            : CheckCast,
    'instance-of'           : InstanceOf,
    'array-length'          : ArrayLength,
    'new-instance'          : NewInstance,
    'new-array'             : NewArray,
    'filled-new-array'      : FilledNewArray,
    'filled-new-array/range': FilledNewArrayRange,
    'fill-array-data'       : FillArrayData,
    'throw'                 : Throw,
    'goto'                  : Goto,
    'goto/16'               : Goto16,
    'goto/32'               : Goto32,
    'packed-switch'         : PackedSwitch,
    'sparse-switch'         : SparseSwitch,
    'cmpl-float'            : CmplFloat,
    'cmpg-float'            : CmpgFloat,
    'cmpl-double'           : CmplDouble,
    'cmpg-double'           : CmpgDouble,
    'cmp-long'              : CmpLong,
    'if-eq'                 : IfEq,
    'if-ne'                 : IfNe,
    'if-lt'                 : IfLt,
    'if-ge'                 : IfGe,
    'if-gt'                 : IfGt,
    'if-le'                 : IfLe,
    'if-eqz'                : IfEqz,
    'if-nez'                : IfNez,
    'if-ltz'                : IfLtz,
    'if-gez'                : IfGez,
    'if-gtz'                : IfGtz,
    'if-lez'                : IfLez,
    'aget'                  : AGet,
    'aget-wide'             : AGetWide,
    'aget-object'           : AGetObject,
    'aget-boolean'          : AGetBoolean,
    'aget-byte'             : AGetByte,
    'aget-char'             : AGetChar,
    'aget-short'            : AGetShort,
    'aput'                  : APut,
    'aput-wide'             : APutWide,
    'aput-object'           : APutObject,
    'aput-boolean'          : APutBoolean,
    'aput-byte'             : APutByte,
    'aput-char'             : APutChar,
    'aput-short'            : APutShort,
    'iget'                  : IGet,
    'iget-wide'             : IGetWide,
    'iget-object'           : IGetObject,
    'iget-boolean'          : IGetBoolean,
    'iget-byte'             : IGetByte,
    'iget-char'             : IGetChar,
    'iget-short'            : IGetShort,
    'iput'                  : IPut,
    'iput-wide'             : IPutWide,
    'iput-object'           : IPutObject,
    'iput-boolean'          : IPutBoolean,
    'iput-byte'             : IPutByte,
    'iput-char'             : IPutChar,
    'iput-short'            : IPutShort,
    'sget'                  : SGet,
    'sget-wide'             : SGetWide,
    'sget-object'           : SGetObject,
    'sget-boolean'          : SGetBoolean,
    'sget-byte'             : SGetByte,
    'sget-char'             : SGetChar,
    'sget-short'            : SGetShort,
    'sput'                  : SPut,
    'sput-wide'             : SPutWide,
    'sput-object'           : SPutObject,
    'sput-boolean'          : SPutBoolean,
    'sput-byte'             : SPutByte,
    'sput-char'             : SPutChar,
    'sput-short'            : SPutShort,
    'invoke-virtual'        : InvokeVirtual,
    'invoke-super'          : InvokeSuper,
    'invoke-direct'         : InvokeDirect,
    'invoke-static'         : InvokeStatic,
    'invoke-interface'      : InvokeInterface,
    'invoke-virtual/range'  : InvokeVirtualRange,
    'invoke-super/range'    : InvokeSuperRange,
    'invoke-direct/range'   : InvokeDirectRange,
    'invoke-static/range'   : InvokeStaticRange,
    'invoke-interface/range': InvokeInterfaceRange,
    'neg-int'               : NegInt,
    'not-int'               : NotInt,
    'neg-long'              : NegLong,
    'not-long'              : NotLong,
    'neg-float'             : NegFloat,
    'neg-double'            : NegDouble,
    'int-to-long'           : IntToLong,
    'int-to-float'          : IntToFloat,
    'int-to-double'         : IntToDouble,
    'long-to-int'           : LongToInt,
    'long-to-float'         : LongToFloat,
    'long-to-double'        : LongToDouble,
    'float-to-int'          : FloatToInt,
    'float-to-long'         : FloatToLong,
    'float-to-double'       : FloatToDouble,
    'double-to-int'         : DoubleToInt,
    'double-to-long'        : DoubleToLong,
    'double-to-float'       : DoubleToFloat,
    'int-to-byte'           : IntToByte,
    'int-to-char'           : IntToChar,
    'int-to-short'          : IntToShort,
    'add-int'               : AddInt,
    'sub-int'               : SubInt,
    'mul-int'               : MulInt,
    'div-int'               : DivInt,
    'rem-int'               : RemInt,
    'and-int'               : AndInt,
    'or-int'                : OrInt,
    'xor-int'               : XorInt,
    'shl-int'               : ShlInt,
    'shr-int'               : ShrInt,
    'ushr-int'              : UShrInt,
    'add-long'              : AddLong,
    'sub-long'              : SubLong,
    'mul-long'              : MulLong,
    'div-long'              : DivLong,
    'rem-long'              : RemLong,
    'and-long'              : AndLong,
    'or-long'               : OrLong,
    'xor-long'              : XorLong,
    'shl-long'              : ShlLong,
    'shr-long'              : ShrLong,
    'ushr-long'             : UShrLong,
    'add-float'             : AddFloat,
    'sub-float'             : SubFloat,
    'mul-float'             : MulFloat,
    'div-float'             : DivFloat,
    'rem-float'             : RemFloat,
    'add-double'            : AddDouble,
    'sub-double'            : SubDouble,
    'mul-double'            : MulDouble,
    'div-double'            : DivDouble,
    'rem-double'            : RemDouble,
    'add-int/2addr'         : AddInt2Addr,
    'sub-int/2addr'         : SubInt2Addr,
    'mul-int/2addr'         : MulInt2Addr,
    'div-int/2addr'         : DivInt2Addr,
    'rem-int/2addr'         : RemInt2Addr,
    'and-int/2addr'         : AndInt2Addr,
    'or-int/2addr'          : OrInt2Addr,
    'xor-int/2addr'         : XorInt2Addr,
    'shl-int/2addr'         : ShlInt2Addr,
    'shr-int/2addr'         : ShrInt2Addr,
    'ushr-int/2addr'        : UShrInt2Addr,
    'add-long/2addr'        : AddLong2Addr,
    'sub-long/2addr'        : SubLong2Addr,
    'mul-long/2addr'        : MulLong2Addr,
    'div-long/2addr'        : DivLong2Addr,
    'rem-long/2addr'        : RemLong2Addr,
    'and-long/2addr'        : AndLong2Addr,
    'or-long/2addr'         : OrLong2Addr,
    'xor-long/2addr'        : XorLong2Addr,
    'shl-long/2addr'        : ShlLong2Addr,
    'shr-long/2addr'        : ShrLong2Addr,
    'ushr-long/2addr'       : UShrLong2Addr,
    'add-float/2addr'       : AddFloat2Addr,
    'sub-float/2addr'       : SubFloat2Addr,
    'mul-float/2addr'       : MulFloat2Addr,
    'div-float/2addr'       : DivFloat2Addr,
    'rem-float/2addr'       : RemFloat2Addr,
    'add-double/2addr'      : AddDouble2Addr,
    'sub-double/2addr'      : SubDouble2Addr,
    'mul-double/2addr'      : MulDouble2Addr,
    'div-double/2addr'      : DivDouble2Addr,
    'rem-double/2addr'      : RemDouble2Addr,
    'add-int/lit16'         : AddIntLit16,
    'rsub-int'              : RSubInt,
    'mul-int/lit16'         : MulIntLit16,
    'div-int/lit16'         : DivIntLit16,
    'rem-int/lit16'         : RemIntLit16,
    'and-int/lit16'         : AndIntLit16,
    'or-int/lit16'          : OrIntLit16,
    'xor-int/lit16'         : XorIntLit16,
    'add-int/lit8'          : AddIntLit8,
    'rsub-int/lit8'         : RSubIntLit8,
    'mul-int/lit8'          : MulIntLit8,
    'div-int/lit8'          : DivIntLit8,
    'rem-int/lit8'          : RemIntLit8,
    'and-int/lit8'          : AndIntLit8,
    'or-int/lit8'           : OrIntLit8,
    'xor-int/lit8'          : XorIntLit8,
    'shl-int/lit8'          : ShlIntLit8,
    'shr-int/lit8'          : ShrIntLit8,
    'ushr-int/lit8'         : UShrIntLit8
}
