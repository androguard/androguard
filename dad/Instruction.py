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


CONDS = {
    '==' : '!=',
    '!=' : '==',
    '<' : '>=',
    '<=' : '>',
    '>=' : '<',
    '>' : '<='
}

EXPR = 0
INST = 1
COND = 2


def get_invoke_params(params, params_type, memory):
    res = []
    i = 0
    while i < len(params_type):
        param = params[i]
        res.append(memory[param])
        i += Util.get_type_size(params_type[i])
    return res


class Instruction(object):
    def __init__(self, ins):
        self.ins = ins
        self.ops = ins.get_operands()

    def get_reg(self):
        return [self.register]


class AssignInstruction(Instruction):
    def __init__(self, ins):
        super(AssignInstruction, self).__init__(ins)
        self.lhs = self.ops[0][1]
        if len(self.ops) > 1:
            self.rhs = int(self.ops[1][1])
        else:
            self.rhs = None

    def symbolic_process(self, memory, tabsymb, varsgen):
        Util.log('Default symbolic processing for this binary expression.',
                 'debug')
        if self.rhs is None:
            self.rhs = memory.get('heap')
            memory['heap'] = None
            Util.log('value :: %s' % self.rhs, 'debug')
        else:
            self.rhs = memory[self.rhs]
        var = varsgen.newVar(self.rhs.get_type(), self.rhs)
        tabsymb[var.get_name()] = var
        memory[self.lhs] = var
        self.lhs = var
        Util.log('Ins : %s = %s' % (var.get_name(), self.rhs), 'debug')

    def get_reg(self):
        return [self.lhs]

    def value(self):
        return '%s = %s' % (self.lhs.get_name(), self.rhs.value())

    def get_type(self):
        return self.rhs.get_type()


class StaticInstruction(Instruction):
    def __init__(self, ins):
        super(StaticInstruction, self).__init__(ins)
        self.register = self.ops[0][1] 
        self.loc = Util.get_type(self.ops[1][2]) #FIXME remove name of class
        self.type = self.ops[1][3]
        self.name = self.ops[1][4]
        self.op = '%s.%s = %s'

    def get_reg(self):
        pass

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.register = memory[self.register]

    def value(self):
        return self.op % (self.loc, self.name, self.register.value())


class InstanceInstruction(Instruction):
    def __init__(self, ins):
        super(InstanceInstruction, self).__init__(ins)
        self.rhs = self.ops[0][1]
        self.lhs = self.ops[1][1]
        self.name = self.ops[2][4]
        self.location = self.ops[2][2]  # [1:-1].replace( '/', '.' )
        self.type = 'V'
        self.op = '%s.%s = %s'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.rhs = memory[self.rhs]
        self.lhs = memory[self.lhs]

    def get_reg(self):
        Util.log('%s has no dest register.' % repr(self), 'debug')

    def value(self):
        return self.op % (self.lhs.value(), self.name,
                            self.rhs.value())

    def get_type(self):
        return self.type


class InvokeInstruction(Instruction):
    def __init__(self, ins):
        super(InvokeInstruction, self).__init__(ins)
        self.register = self.ops[0][1]
        self.type = Util.get_type(self.ops[-1][2])
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = Util.get_type(self.ops[-1][4])
        self.methCalled = self.ops[-1][-1]

    def get_type(self):
        return self.returnType


class ArrayInstruction(Instruction):
    def __init__(self, ins):
        super(ArrayInstruction, self).__init__(ins)
        self.source = self.ops[0][1]
        self.array = self.ops[1][1]
        self.index = self.ops[2][1]
        self.op = '%s[%s] = %s'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.source = memory[self.source]
        self.array = memory[self.array]
        self.index = memory[self.index]

    def value(self):
        if self.index.get_type() != 'I':
            return self.op % (self.array.value(),
                              self.index.int_value(),
                              self.source.value())
        else:
            return self.op % (self.array.value(), self.index.value(),
                              self.source.value())
    
    def get_reg(self):
        Util.log('%s has no dest register.' % repr(self), 'debug')


class ReturnInstruction(Instruction):
    def __init__(self, ins):
        super(ReturnInstruction, self).__init__(ins)
        if len(self.ops) > 0:
            self.register = self.ops[0][1]
        else:
            self.register = None

    def symbolic_process(self, memory, tabsymb, varsgen):
        if self.register is None:
            self.type = 'V'
        else:
            self.returnValue = memory[self.register]
            self.type = self.returnValue.get_type()

    def get_type(self):
        return self.type

    def value(self):
        if self.register is None:
            return 'return'
        else:
            return 'return %s' % self.returnValue.value()


class Expression(object):
    def __init__(self, ins):
        self.ins = ins
        self.ops = ins.get_operands()

    def get_reg(self):
        return [self.register]

    def value(self):
        return '(expression %s has no value implemented)' % repr(self)

    def get_type(self):
        return '(expression %s has no type defined)' % repr(self)

    def symbolic_process(self, memory, tabsymb, varsgen):
        Util.log('Symbolic processing not implemented for this expression.',
                 'debug')


class RefExpression(Expression):
    def __init__(self, ins):
        super(RefExpression, self).__init__(ins)
        self.register = self.ops[0][1]


class BinaryExpression(Expression):
    def __init__(self, ins):
        super(BinaryExpression, self).__init__(ins)
        if len(self.ops) < 3:
            self.lhs = self.ops[0][1]
            self.rhs = self.ops[1][1]
        else:
            self.lhs = self.ops[1][1]
            self.rhs = self.ops[2][1]
        self.register = self.ops[0][1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        Util.log('Default symbolic processing for this binary expression.',
                 'debug')
        self.lhs = memory[self.lhs]
        self.rhs = memory[self.rhs]
        var = varsgen.newVar(self.type, self)
        tabsymb[var.get_name()] = var
        memory[self.register] = var
        Util.log('Ins : %s' % self.op, 'debug')

    def value(self):
        return '(%s %s %s)' % (self.lhs.value(), self.op, self.rhs.value())

    def get_type(self):
        return self.type


class BinaryExpressionLit(Expression):
    def __init__(self, ins):
        super(BinaryExpressionLit, self).__init__(ins)
        self.register = self.ops[0][1]
        self.lhs = self.ops[1][1]
        self.rhs = self.ops[2][1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        Util.log('Default symbolic processing for this binary expression.',
                 'debug')
        self.lhs = memory[self.lhs]
        var = varsgen.newVar(self.type, self)
        tabsymb[var.get_name()] = var
        memory[self.register] = var
        Util.log('Ins : %s' % self.op, 'debug')

    def value(self):
        return '(%s %s %s)' % (self.lhs.value(), self.op, self.rhs)

    def get_type(self):
        return self.type


class UnaryExpression(Expression):
    def __init__(self, ins):
        super(UnaryExpression, self).__init__(ins)
        self.register = self.ops[0][1] 
        self.source = int(self.ops[1][1])

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.source = memory[self.source]
        var = varsgen.newVar(self.type, self)
        tabsymb[var.get_name()] = var
        memory[self.register] = var

    def value(self):
        if self.op.startswith('('):
            return self.source.value() #TEMP to avoir to much parenthesis
        return '(%s %s)' % (self.op, self.source.value())

    def get_type(self):
        return self.type


class IdentifierExpression(Expression):
    def __init__(self, ins):
        super(IdentifierExpression, self).__init__(ins)
        self.register = self.ops[0][1]

    def get_reg(self):
        return [self.register]
    
    def symbolic_process(self, memory, tabsymb, varsgen):
        var = varsgen.newVar(self.type, self)
        tabsymb[var.get_name()] = var
        memory[self.register] = var
        self.register = var

    def value(self):
        return '%s = %s' % (self.register.name, self.val)

    def get_type(self):
        return self.type


class ConditionalExpression(Expression):
    def __init__(self, ins):
        super(ConditionalExpression, self).__init__(ins)
        self.lhs = self.ops[0][1]
        self.rhs = self.ops[1][1]
    
    def neg(self):
        self.op = CONDS[self.op]
    
    def get_reg(self):
        return '(condition expression %s has no dest register.)' % self    

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.lhs = memory[self.lhs]
        self.rhs = memory[self.rhs]
    
    def value(self):
        return '(%s %s %s)' % (self.lhs.value(), self.op, self.rhs.value())


class ConditionalZExpression(Expression):
    def __init__(self, ins):
        super(ConditionalZExpression, self).__init__(ins)
        self.test = int(self.ops[0][1])
    
    def get_reg(self):
        return '(zcondition expression %s has no dest register.)' % self
    
    def neg(self):
        self.op = CONDS[self.op]
        
    def symbolic_process(self, memory, tabsymb, varsgen):
        self.test = memory[self.test]

    def value(self):
        if self.test.get_type() == 'Z':
            return '(%s %s %s)' % (self.test.lhs.value(), self.op,
                                   self.test.rhs.value())
        return '(%s %s 0)' % (self.test.value(), self.op)

    def get_type(self):
        return 'V'


class ArrayExpression(Expression):
    def __init__(self, ins):
        super(ArrayExpression, self).__init__(ins)
        self.register = self.ops[0][1]
        self.ref = self.ops[1][1]
        self.idx = self.ops[2][1]
        self.op = '%s[%s]'
    
    def symbolic_process(self, memory, tabsymb, varsgen):
        self.ref = memory[self.ref]
        self.idx = memory[self.idx]
        self.type = self.ref.get_type()[1:]
        memory[self.register] = self
        Util.log('Ins : %s' % self.op, 'debug')

    def get_type(self):
        return self.type

    def value(self):
        return self.op % (self.ref.value(), self.idx.value())


class InstanceExpression(Expression):
    def __init__(self, ins):
        super(InstanceExpression, self).__init__(ins)
        self.register = self.ops[0][1]
        self.location = self.ops[-1][2]
        self.type = self.ops[-1][3]
        self.name = self.ops[-1][4]
        self.retType = self.ops[-1][-1]
        self.objreg = self.ops[1][1]
        self.op = '%s.%s'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.obj = memory[self.objreg]
        memory[self.register] = self
        Util.log('Ins : %s' % self.op, 'debug')

    def value(self):
        return self.op % (self.obj.value(), self.name)

    def get_type(self):
        return self.type


class StaticExpression(Expression):
    def __init__(self, ins):
        super(StaticExpression, self).__init__(ins)
        self.register = self.ops[0][1]
        location = self.ops[1][2][1:-1] #FIXME
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = self.ops[1][3] #[1:-1].replace('/', '.')
        self.name = self.ops[1][4]
        self.op = '%s.%s'
    
    def symbolic_process(self, memory, tabsymb, varsgen):
        memory[self.register] = self
    
    def value(self):
        return self.op % (self.location, self.name)

    def get_type(self):
        return self.type


# nop
class Nop(UnaryExpression):
    def __init__(self, ins):
        Util.log('Nop %s' % ins, 'debug')
        self.op = ''

    def symbolic_process(self, memory, tabsymb, varsgen):
        pass

    def value(self):
        return ''


# move vA, vB ( 4b, 4b )
class Move(AssignInstruction):
    def __init__(self, ins):
        super(Move, self).__init__(ins)
        Util.log('Move %s' % self.ops, 'debug')


# move/from16 vAA, vBBBB ( 8b, 16b )
class MoveFrom16(AssignInstruction):
    def __init__(self, ins):
        super(MoveFrom16, self).__init__(ins)
        Util.log('MoveFrom16 %s' % self.ops, 'debug')


# move/16 vAAAA, vBBBB ( 16b, 16b )
class Move16(AssignInstruction):
    def __init__(self, ins):
        super(Move16, self).__init__(ins)
        Util.log('Move16 %s' % self.ops, 'debug')


# move-wide vA, vB ( 4b, 4b )
class MoveWide(AssignInstruction):
    def __init__(self, ins):
        super(MoveWide, self).__init__(ins)
        Util.log('MoveWide %s' % self.ops, 'debug')


# move-wide/from16 vAA, vBBBB ( 8b, 16b )
class MoveWideFrom16(AssignInstruction):
    def __init__(self, ins):
        super(MoveWideFrom16, self).__init__(ins)
        Util.log('MoveWideFrom16 : %s' % self.ops, 'debug')


# move-wide/16 vAAAA, vBBBB ( 16b, 16b )
class MoveWide16(AssignInstruction):
    def __init__(self, ins):
        super(MoveWide16, self).__init__(ins)
        Util.log('MoveWide16 %s' % self.ops, 'debug')


# move-object vA, vB ( 4b, 4b )
class MoveObject(AssignInstruction):
    def __init__(self, ins):
        super(MoveObject, self).__init__(ins)
        Util.log('MoveObject %s' % self.ops, 'debug')


# move-object/from16 vAA, vBBBB ( 8b, 16b )
class MoveObjectFrom16(AssignInstruction):
    def __init__(self, ins):
        super(MoveObjectFrom16, self).__init__(ins)
        Util.log('MoveObjectFrom16 : %s' % self.ops, 'debug')


# move-object/16 vAAAA, vBBBB ( 16b, 16b )
class MoveObject16(AssignInstruction):
    def __init__(self, ins):
        super(MoveObject16, self).__init__(ins)
        Util.log('MoveObject16 : %s' % self.ops, 'debug')


# move-result vAA ( 8b )
class MoveResult(AssignInstruction):
    def __init__(self, ins):
        super(MoveResult, self).__init__(ins)
        Util.log('MoveResult : %s' % self.ops, 'debug')

    def __str__(self):
        return 'Move res in v' + str(self.ops[0][1])


# move-result-wide vAA ( 8b )
class MoveResultWide(AssignInstruction):
    def __init__(self, ins):
        super(MoveResultWide, self).__init__(ins)
        Util.log('MoveResultWide : %s' % self.ops, 'debug')

    def __str__(self):
        return 'MoveResultWide in v' + str(self.ops[0][1])


# move-result-object vAA ( 8b )
class MoveResultObject(AssignInstruction):
    def __init__(self, ins):
        super(MoveResultObject, self).__init__(ins)
        Util.log('MoveResultObject : %s' % self.ops, 'debug')

    def __str__(self):
        return 'MoveResObj in v' + str(self.ops[0][1])


# move-exception vAA ( 8b )
class MoveException(Expression):
    def __init__(self, ins):
        super(MoveException, self).__init__(ins)
        Util.log('MoveException : %s' % self.ops, 'debug')


# return-void
class ReturnVoid(ReturnInstruction):
    def __init__(self, ins):
        super(ReturnVoid, self).__init__(ins)
        Util.log('ReturnVoid', 'debug')
    
    def __str__(self):
        return 'Return'


# return vAA ( 8b )
class Return(ReturnInstruction):
    def __init__(self, ins):
        super(Return, self).__init__(ins)
        Util.log('Return : %s' % self.ops, 'debug')

    def __str__(self):
        return 'Return (%s)' % str(self.returnValue)


# return-wide vAA ( 8b )
class ReturnWide(ReturnInstruction):
    def __init__(self, ins):
        super(ReturnWide, self).__init__(ins)
        Util.log('ReturnWide : %s' % self.ops, 'debug')
 
    def __str__(self):
        return 'ReturnWide (%s)' % str(self.returnValue)


# return-object vAA ( 8b )
class ReturnObject(ReturnInstruction):
    def __init__(self, ins):
        super(ReturnObject, self).__init__(ins)
        Util.log('ReturnObject : %s' % self.ops, 'debug')
 
    def __str__(self):
        return 'ReturnObject (%s)' % str(self.returnValue)


# const/4 vA, #+B ( 4b, 4b )
class Const4(IdentifierExpression):
    def __init__(self, ins):
        super(Const4, self).__init__(ins)
        Util.log('Const4 : %s' % self.ops, 'debug')
        self.val = int(self.ops[1][1])
        self.type = 'I'
        Util.log('==> %s' % self.val, 'debug')

    def __str__(self):
        return 'Const4 : %s' % str(self.val)


# const/16 vAA, #+BBBB ( 8b, 16b )
class Const16(IdentifierExpression):
    def __init__(self, ins):
        super(Const16, self).__init__(ins)
        Util.log('Const16 : %s' % self.ops, 'debug')
        self.val = int(self.ops[1][1])
        self.type = 'I'
        Util.log('==> %s' % self.val, 'debug')

    def __str__(self):
        return 'Const16 : %s' % str(self.val)


# const vAA, #+BBBBBBBB ( 8b, 32b )
class Const(IdentifierExpression):
    def __init__(self, ins):
        super(Const, self).__init__(ins)
        Util.log('Const : %s' % self.ops, 'debug')
        self.val = ((0xFFFF & self.ops[2][1]) << 16) | ((0xFFFF & self.ops[1][1]))
        self.type = 'F'
        Util.log('==> %s' % self.val, 'debug')

    def value(self):
        return struct.unpack('f', struct.pack('L', self.val))[0]

    def int_value(self):
        return self.val

    def __str__(self):
        return 'Const : ' + str(self.val)


# const/high16 vAA, #+BBBB0000 ( 8b, 16b )
class ConstHigh16(IdentifierExpression):
    def __init__(self, ins):
        super(ConstHigh16, self).__init__(ins)
        Util.log('ConstHigh16 : %s' % self.ops, 'debug')
        self.val = struct.unpack('f',
                                   struct.pack('i', self.ops[1][1] << 16))[0]
        self.type = 'F'
        Util.log('==> %s' % self.val, 'debug')

    def __str__(self):
        return 'ConstHigh16 : %s' % str(self.val)


# const-wide/16 vAA, #+BBBB ( 8b, 16b )
class ConstWide16(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWide16, self).__init__(ins)
        Util.log('ConstWide16 : %s' % self.ops, 'debug')
        self.type = 'J'
        self.val = struct.unpack('d', struct.pack('d', self.ops[1][1]))[0]
        Util.log('==> %s' % self.val, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'Constwide16 : %s' % str(self.val)


# const-wide/32 vAA, #+BBBBBBBB ( 8b, 32b )
class ConstWide32(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWide32, self).__init__(ins)
        Util.log('ConstWide32 : %s' % self.ops, 'debug')
        self.type = 'J'
        val = ((0xFFFF & self.ops[2][1]) << 16) | ((0xFFFF & self.ops[1][1]))
        self.val = struct.unpack('d', struct.pack('d', val))[0]
        Util.log('==> %s' % self.val, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'Constwide32 : %s' % str(self.val)


# const-wide vAA, #+BBBBBBBBBBBBBBBB ( 8b, 64b )
class ConstWide(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWide, self).__init__(ins)
        Util.log('ConstWide : %s' % self.ops, 'debug')
        val = self.ops[1:]
        val = (0xFFFF & val[0][1]) | ((0xFFFF & val[1][1]) << 16) | (\
              (0xFFFF & val[2][1]) << 32) | ((0xFFFF & val[3][1]) << 48)
        self.type = 'D'
        self.val = struct.unpack('d', struct.pack('Q', val))[0]
        Util.log('==> %s' % self.val, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'ConstWide : %s' % str(self.val)


# const-wide/high16 vAA, #+BBBB000000000000 ( 8b, 16b )
class ConstWideHigh16(IdentifierExpression):
    def __init__(self, ins):
        super(ConstWideHigh16, self).__init__(ins)
        Util.log('ConstWideHigh16 : %s' % self.ops, 'debug')
        self.val = struct.unpack('d',
                         struct.pack('Q', 0xFFFFFFFFFFFFFFFF
                                          & int(self.ops[1][1]) << 48))[0]
        self.type = 'D'
        Util.log('==> %s' % self.val, 'debug')

    def get_reg(self):
        return [self.register, self.register + 1]

    def __str__(self):
        return 'ConstWide : %s' % str(self.val)


# const-string vAA ( 8b )
class ConstString(IdentifierExpression):
    def __init__(self, ins):
        super(ConstString, self).__init__(ins)
        Util.log('ConstString : %s' % self.ops, 'debug')
        self.val = '%s' % self.ops[1][2]
        self.type = 'STR'
        Util.log('==> %s' % self.val, 'debug')

    def __str__(self):
        return 'ConstString : %s' % str(self.val)


# const-string/jumbo vAA ( 8b )
class ConstStringJumbo(IdentifierExpression):
    pass


# const-class vAA ( 8b )
class ConstClass(IdentifierExpression):
    def __init__(self, ins):
        super(ConstClass, self).__init__(ins)
        Util.log('ConstClass : %s' % self.ops, 'debug')
        self.type = '%s' % self.ops[1][2]
        self.val = self.type
        Util.log('==> %s' % self.val, 'debug')

    def __str__(self):
        return 'ConstClass : %s' % str(self.val)


# monitor-enter vAA ( 8b )
class MonitorEnter(RefExpression):
    def __init__(self, ins):
        super(MonitorEnter, self).__init__(ins)
        Util.log('MonitorEnter : %s' % self.ops, 'debug')
        self.op = 'synchronized( %s )'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.register = memory[self.register]

    def get_type(self):
        return self.register.get_type()

    def get_reg(self):
        Util.log('MonitorEnter has no dest register', 'debug')

    def value(self):
        return self.op % self.register.value()


# monitor-exit vAA ( 8b )
class MonitorExit(RefExpression):
    def __init__(self, ins):
        super(MonitorExit, self).__init__(ins)
        Util.log('MonitorExit : %s' % self.ops, 'debug')
        self.op = ''

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.register = memory[self.register]

    def get_type(self):
        return self.register.get_type()

    def get_reg(self):
        Util.log('MonitorExit has no dest register', 'debug')

    def value(self):
        return '' 


# check-cast vAA ( 8b )
class CheckCast(RefExpression):
    def __init__(self, ins):
        super(CheckCast, self).__init__(ins)
        Util.log('CheckCast: %s' % self.ops, 'debug')
        self.register = self.ops[0][1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.register = memory[self.register]

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
class ArrayLength(RefExpression):
    def __init__(self, ins):
        super(ArrayLength, self).__init__(ins)
        Util.log('ArrayLength: %s' % self.ops, 'debug')
        self.src = self.ops[1][1]
        self.op = '%s.length'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.src = memory[self.src]
        memory[self.register] = self

    def value(self):
        return self.op % self.src.value()

    def get_type(self):
        return self.src.get_type()


# new-instance vAA ( 8b )
class NewInstance(RefExpression):
    def __init__(self, ins):
        super(NewInstance, self).__init__(ins)
        Util.log('NewInstance : %s' % self.ops, 'debug')
        self.type = self.ops[-1][-1]
        self.op = 'new %s'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.type = Util.get_type(self.type)
        memory[self.register] = self

    def value(self):
        return self.op % self.type

    def get_type(self):
        return self.type

    def __str__(self):
        return 'New ( %s )' % self.type


# new-array vA, vB ( 8b, size )
class NewArray(RefExpression):
    def __init__(self, ins):
        super(NewArray, self).__init__(ins)
        Util.log('NewArray : %s' % self.ops, 'debug')
        self.size = int(self.ops[1][1])
        self.type = self.ops[-1][-1]
        self.op = 'new %s'

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.size = memory[self.size]
        memory[self.register] = self

    def value(self):
        return self.op % Util.get_type(self.type, self.size.value())

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

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.type = memory[self.register].get_type()

    def value(self):
        return self.ins.get_op_value()

    def get_type(self):
        return self.type

    def get_reg(self):
        Util.log('FillArrayData has no dest register.', 'debug')


# throw vAA ( 8b )
class Throw(RefExpression):
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
class PackedSwitch(Instruction):
    def __init__(self, ins):
        super(PackedSwitch, self).__init__(ins)
        Util.log('PackedSwitch : %s' % self.ops, 'debug')
        self.register = self.ops[0][1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.register = memory[self.register]

    def value(self):
        return self.register.value()

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
        self.op = '=='
        self.type = 'F'

    def __str__(self):
        return 'CmplFloat (%s < %s ?)' % (self.rhs.value(),
                                           self.lhs.value())


# cmpg-float vAA, vBB, vCC ( 8b, 8b, 8b )
class CmpgFloat(BinaryExpression):
    def __init__(self, ins):
        super(CmpgFloat, self).__init__(ins)
        Util.log('CmpgFloat : %s' % self.ops, 'debug')
        self.op = '=='
        self.type = 'F'

    def __str__(self):
        return 'CmpgFloat (%s > %s ?)' % (self.rhs.value(), self.lhs.value())


# cmpl-double vAA, vBB, vCC ( 8b, 8b, 8b )
class CmplDouble(BinaryExpression):
    def __init__(self, ins):
        super(CmplDouble, self).__init__(ins)
        Util.log('CmplDouble : %s' % self.ops, 'debug')
        self.op = '=='
        self.type = 'D'

    def __str__(self):
        return 'CmplDouble (%s < %s ?)' % (self.rhs.value(), self.lhs.value())


# cmpg-double vAA, vBB, vCC ( 8b, 8b, 8b )
class CmpgDouble(BinaryExpression):
    def __init__(self, ins):
        super(CmpgDouble, self).__init__(ins)
        Util.log('CmpgDouble : %s' % self.ops, 'debug')
        self.op = '=='
        self.type = 'D'

    def __str__(self):
        return 'CmpgDouble (%s > %s ?)' % (self.rhs.value(), self.lhs.value())


# cmp-long vAA, vBB, vCC ( 8b, 8b, 8b )
class CmpLong(BinaryExpression):
    def __init__(self, ins):
        super(CmpLong, self).__init__(ins)
        Util.log('CmpLong : %s' % self.ops, 'debug')
        self.op = '=='
        self.type = 'J'

    def __str__(self):
        return 'CmpLong (%s == %s ?)' % (self.rhs.value(), self.lhs.value())



# if-eq vA, vB, +CCCC ( 4b, 4b, 16b )
class IfEq(ConditionalExpression):
    def __init__(self, ins):
        super(IfEq, self).__init__(ins)
        Util.log('IfEq : %s' % self.ops, 'debug')
        self.op = '=='

    def __str__(self):
        return 'IfEq (%s %s %s)' % (self.lhs.value(), self.op,
                                    self.rhs.value())


# if-ne vA, vB, +CCCC ( 4b, 4b, 16b )
class IfNe(ConditionalExpression):
    def __init__(self, ins):
        super(IfNe, self).__init__(ins)
        Util.log('IfNe : %s' % self.ops, 'debug')
        self.op = '!='

    def __str__(self):
        return 'IfNe (%s %s %s)' % (self.lhs.value(), self.op,
                                    self.rhs.value())


# if-lt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLt(ConditionalExpression):
    def __init__(self, ins):
        super(IfLt,  self).__init__(ins)
        Util.log('IfLt : %s' % self.ops, 'debug')
        self.op = '<'

    def __str__(self):
        return 'IfLt (%s %s %s)' % (self.lhs.value(), self.op,
                                    self.rhs.value())


# if-ge vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGe(ConditionalExpression):
    def __init__(self, ins):
        super(IfGe, self).__init__(ins)
        Util.log('IfGe : %s' % self.ops, 'debug')
        self.op = '>='

    def __str__(self):
        return 'IfGe (%s %s %s)' % (self.lhs.value(), self.op,
                                    self.rhs.value())


# if-gt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGt(ConditionalExpression):
    def __init__(self, ins):
        super(IfGt, self).__init__(ins)
        Util.log('IfGt : %s' % self.ops, 'debug')
        self.op = '>'

    def __str__(self):
        return 'IfGt (%s %s %s)' % (self.lhs.value(), self.op,
                                    self.rhs.value())


# if-le vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLe(ConditionalExpression):
    def __init__(self, ins):
        super(IfLe, self).__init__(ins)
        Util.log('IfLe : %s' % self.ops, 'debug')
        self.op = '<='

    def __str__(self):
        return 'IfLe (%s %s %s)' % (self.lhs.value(), self.op,
                                    self.rhs.value())

# if-eqz vAA, +BBBB ( 8b, 16b )
class IfEqz(ConditionalZExpression):
    def __init__(self, ins):
        super(IfEqz, self).__init__(ins)
        Util.log('IfEqz : %s' % self.ops, 'debug')
        self.op = '=='

    def get_reg(self):
        Util.log('IfEqz has no dest register', 'debug')

    def value(self):
        if self.test.get_type() == 'Z':
            if self.op == '==':
                return '!%s' % self.test.value()
            else:
                return '%s' % self.test.value()
        return '%s %s 0' % (self.test.value(), self.op)

    def __str__(self):
        return 'IfEqz (%s)' % (self.test.value())


# if-nez vAA, +BBBB ( 8b, 16b )
class IfNez(ConditionalZExpression):
    def __init__(self, ins):
        super(IfNez, self).__init__(ins)
        Util.log('IfNez : %s' % self.ops, 'debug')
        self.op = '!='

    def get_reg(self):
        Util.log('IfNez has no dest register', 'debug')

    def value(self):
        if self.test.get_type() == 'Z':
            if self.op == '==':
                return '%s' % self.test.value()
            else:
                return '!%s' % self.test.value()
        return '%s %s 0' % (self.test.value(), self.op)
    
    def __str__(self):
        return 'IfNez (%s)' % self.test.value()


# if-ltz vAA, +BBBB ( 8b, 16b )
class IfLtz(ConditionalZExpression):
    def __init__(self, ins):
        super(IfLtz, self).__init__(ins)
        Util.log('IfLtz : %s' % self.ops, 'debug')
        self.op = '<'

    def get_reg(self):
        Util.log('IfLtz has no dest register', 'debug')
    
    def value(self):
        if self.test.get_type() == 'Z':
            return '(%s %s %s)' % (self.test.content.first.value(),
                                   self.op,
                                   self.test.content.second.value())
        return '(%s %s 0)' % (self.test.value(), self.op)
    def __str__(self):
        return 'IfLtz (%s)' % self.test.value()


# if-gez vAA, +BBBB ( 8b, 16b )
class IfGez(ConditionalZExpression):
    def __init__(self, ins):
        super(IfGez, self).__init__(ins)
        Util.log('IfGez : %s' % self.ops, 'debug')
        self.op = '>='

    def get_reg(self):
        Util.log('IfGez has no dest register', 'debug')
    
    def value(self):
        if self.test.get_type() == 'Z':
            return '(%s %s %s)' % (self.test.content.first.value(),
                                   self.op,
                                   self.test.content.second.value())
        return '(%s %s 0)' % (self.test.value(), self.op)
    
    def __str__(self):
        return 'IfGez (%s)' % self.test.value()


# if-gtz vAA, +BBBB ( 8b, 16b )
class IfGtz(ConditionalZExpression):
    def __init__(self, ins):
        super(IfGtz, self).__init__(ins)
        Util.log('IfGtz : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '>'

    def get_reg(self):
        Util.log('IfGtz has no dest register', 'debug')
    
    def value(self):
        if self.test.get_type() == 'Z':
            return '(%s %s %s)' % (self.test.content.first.value(),
                                 self.op,
                                 self.test.content.second.value())
        return '(%s %s 0)' % (self.test.value(), self.op)
    
    def __str__(self):
        return 'IfGtz (%s)' % self.test.value()


# if-lez vAA, +BBBB (8b, 16b )
class IfLez(ConditionalZExpression):
    def __init__(self, ins):
        super(IfLez, self).__init__(ins)
        Util.log('IfLez : %s' % self.ops, 'debug')
        self.test = int(self.ops[0][1])
        self.op = '<='

    def get_reg(self):
        Util.log('IfLez has no dest register', 'debug')
    
    def value(self):
        if self.test.get_type() == 'Z':
            return '(%s %s %s)' % (self.test.content.first.value(),
                                 self.op,
                                 self.test.content.second.value())
        return '(%s %s 0)' % (self.test.value(), self.op)

    def __str__(self):
        return 'IfLez (%s)' % self.test.value()


#FIXME: check type all aget
# aget vAA, vBB, vCC ( 8b, 8b, 8b )
class AGet(ArrayExpression):
    def __init__(self, ins):
        super(AGet, self).__init__(ins)
        Util.log('AGet : %s' % self.ops, 'debug')


# aget-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetWide(ArrayExpression):
    def __init__(self, ins):
        super(AGetWide, self).__init__(ins)
        Util.log('AGetWide : %s' % self.ops, 'debug') 


# aget-object vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetObject(ArrayExpression):
    def __init__(self, ins):
        super(AGetObject, self).__init__(ins)
        Util.log('AGetObject : %s' % self.ops, 'debug')


# aget-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetBoolean(ArrayExpression):
    def __init__(self, ins):
        super(AGetBoolean, self).__init__(ins)
        Util.log('AGetBoolean : %s' % self.ops, 'debug')


# aget-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetByte(ArrayExpression):
    def __init__(self, ins):
        super(AGetByte, self).__init__(ins)
        Util.log('AGetByte : %s' % self.ops, 'debug')


# aget-char vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetChar(ArrayExpression):
    def __init__(self, ins):
        super(AGetChar, self).__init__(ins)
        Util.log('AGetChar : %s' % self.ops, 'debug')


# aget-short vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetShort(ArrayExpression):
    def __init__(self, ins):
        super(AGetShort, self).__init__(ins)
        Util.log('AGetShort : %s' % self.ops, 'debug')


# aput vAA, vBB, vCC 
class APut(ArrayInstruction):
    def __init__(self, ins):
        super(APut, self).__init__(ins)
        Util.log('APut : %s' % self.ops, 'debug')


# aput-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class APutWide(ArrayInstruction):
    def __init__(self, ins):
        super(APutWide, self).__init__(ins)
        Util.log('APutWide : %s' % self.ops, 'debug')


# aput-object vAA, vBB, vCC ( 8b, 8b, 8b )
class APutObject(ArrayInstruction):
    def __init__(self, ins):
        super(APutObject, self).__init__(ins)
        Util.log('APutObject : %s' % self.ops, 'debug')


# aput-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class APutBoolean(ArrayInstruction):
    def __init__(self, ins):
        super(APutBoolean, self).__init__(ins)
        Util.log('APutBoolean : %s' % self.ops, 'debug')


# aput-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class APutByte(ArrayInstruction):
    def __init__(self, ins):
        super(APutByte, self).__init__(ins)
        Util.log('APutByte : %s' % self.ops, 'debug')



# aput-char vAA, vBB, vCC ( 8b, 8b, 8b )
class APutChar(ArrayInstruction):
    def __init__(self, ins):
        super(APutChar, self).__init__(ins)
        Util.log('APutChar : %s' % self.ops, 'debug')


# aput-short vAA, vBB, vCC ( 8b, 8b, 8b )
class APutShort(ArrayInstruction):
    def __init__(self, ins):
        super(APutShort, self).__init__(ins)
        Util.log('APutShort : %s' % self.ops, 'debug')


# iget vA, vB ( 4b, 4b )
class IGet(InstanceExpression):
    def __init__(self, ins):
        super(IGet, self).__init__(ins)
        Util.log('IGet : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-wide vA, vB ( 4b, 4b )
class IGetWide(InstanceExpression):
    def __init__(self, ins):
        super(IGetWide, self).__init__(ins)
        Util.log('IGetWide : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-object vA, vB ( 4b, 4b )
class IGetObject(InstanceExpression):
    def __init__(self, ins):
        super(IGetObject, self).__init__(ins)
        Util.log('IGetObject : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-boolean vA, vB ( 4b, 4b )
class IGetBoolean(InstanceExpression):
    def __init__(self, ins):
        super(IGetBoolean, self).__init__(ins)
        Util.log('IGetBoolean : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-byte vA, vB ( 4b, 4b )
class IGetByte(InstanceExpression):
    def __init__(self, ins):
        super(IGetByte, self).__init__(ins)
        Util.log('IGetByte : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-char vA, vB ( 4b, 4b )
class IGetChar(InstanceExpression):
    def __init__(self, ins):
        super(IGetChar, self).__init__(ins)
        Util.log('IGetChar : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-short vA, vB ( 4b, 4b )
class IGetShort(InstanceExpression):
    def __init__(self, ins):
        super(IGetShort, self).__init__(ins)
        Util.log('IGetShort : %s' % self.ops, 'debug')

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iput vA, vB ( 4b, 4b )
class IPut(InstanceInstruction):
    def __init__(self, ins):
        super(IPut, self).__init__(ins)
        Util.log('IPut %s' % self.ops, 'debug')


# iput-wide vA, vB ( 4b, 4b )
class IPutWide(InstanceInstruction):
    def __init__(self, ins):
        super(IPutWide, self).__init__(ins)
        Util.log('IPutWide %s' % self.ops, 'debug')
    

# iput-object vA, vB ( 4b, 4b )
class IPutObject(InstanceInstruction):
    def __init__(self, ins):
        super(IPutObject, self).__init__(ins)
        Util.log('IPutObject %s' % self.ops, 'debug')


# iput-boolean vA, vB ( 4b, 4b )
class IPutBoolean(InstanceInstruction):
    def __init__(self, ins):
        super(IPutBoolean, self).__init__(ins)
        Util.log('IPutBoolean %s' % self.ops, 'debug')
    

# iput-byte vA, vB ( 4b, 4b )
class IPutByte(InstanceInstruction):
    def __init__(self, ins):
        super(IPutBoolean, self).__init__(ins)
        Util.log('IPutByte %s' % self.ops, 'debug')


# iput-char vA, vB ( 4b, 4b )
class IPutChar(InstanceInstruction):
    def __init__(self, ins):
        super(IPutBoolean, self).__init__(ins)
        Util.log('IPutChar %s' % self.ops, 'debug')
    

# iput-short vA, vB ( 4b, 4b )
class IPutShort(InstanceInstruction):
    def __init__(self, ins):
        super(IPutBoolean, self).__init__(ins)
        Util.log('IPutShort %s' % self.ops, 'debug')
    

# sget vAA ( 8b )
class SGet(StaticExpression):
    def __init__(self, ins):
        super(SGet, self).__init__(ins)
        Util.log('SGet : %s' % self.ops, 'debug')

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sget-wide vAA ( 8b )
class SGetWide(StaticExpression):
    def __init__(self, ins):
        super(SGetWide, self).__init__(ins)
        Util.log('SGetWide : %s' % self.ops, 'debug')


# sget-object vAA ( 8b )
class SGetObject(StaticExpression):
    def __init__(self, ins):
        super(SGetObject, self).__init__(ins)
        Util.log('SGetObject : %s' % self.ops, 'debug')

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sget-boolean vAA ( 8b )
class SGetBoolean(StaticExpression):
    def __init__(self, ins):
        super(SGetBoolean, self).__init__(ins)
        Util.log('SGetBoolean : %s' % self.ops, 'debug')


# sget-byte vAA ( 8b )
class SGetByte(StaticExpression):
    def __init__(self, ins):
        super(SGetByte, self).__init__(ins)
        Util.log('SGetByte : %s' % self.ops, 'debug')


# sget-char vAA ( 8b )
class SGetChar(StaticExpression):
    def __init__(self, ins):
        super(SGetChar, self).__init__(ins)
        Util.log('SGetChar : %s' % self.ops, 'debug')


# sget-short vAA ( 8b )
class SGetShort(StaticExpression):
    def __init__(self, ins):
        super(SGetShort, self).__init__(ins)
        Util.log('SGetShort : %s' % self.ops, 'debug')


# sput vAA ( 8b )
class SPut(StaticInstruction):
    def __init__(self, ins):
        super(SPut, self).__init__(ins)
        Util.log('SPut : %s' % self.ops, 'debug') 

    def __str__(self):
        if self.loc:
            return '(%s) %s.%s' % (self.type, self.loc, self.name)
        return '(%s) %s' % (self.type, self.name)


# sput-wide vAA ( 8b )
class SPutWide(StaticInstruction):
    def __init__(self, ins):
        super(SPutWide, self).__init__(ins)
        Util.log('SPutWide : %s' % self.ops, 'debug') 


# sput-object vAA ( 8b )
class SPutObject(StaticInstruction):
    def __init__(self, ins):
        super(SPutObject, self).__init__(ins)
        Util.log('SPutObject : %s' % self.ops, 'debug')

    def __str__(self):
        if self.loc:
            return '(%s) %s.%s' % (self.type, self.loc, self.name)
        return '(%s) %s' % (self.type, self.name)


# sput-boolean vAA ( 8b )
class SPutBoolean(StaticInstruction):
    def __init__(self, ins):
        super(SPutBoolean, self).__init__(ins)
        Util.log('SPutBoolean : %s' % self.ops, 'debug')


# sput-wide vAA ( 8b )
class SPutByte(StaticInstruction):
    def __init__(self, ins):
        super(SPutByte, self).__init__(ins)
        Util.log('SPutByte : %s' % self.ops, 'debug')


# sput-char vAA ( 8b )
class SPutChar(StaticInstruction):
    def __init__(self, ins):
        super(SPutChar, self).__init__(ins)
        Util.log('SPutChar : %s' % self.ops, 'debug')


# sput-short vAA ( 8b )
class SPutShort(StaticInstruction):
    def __init__(self, ins):
        super(SPutShort, self).__init__(ins)
        Util.log('SPutShort : %s' % self.ops, 'debug')


# invoke-virtual {vD, vE, vF, vG, vA} ( 4b each )
class InvokeVirtual(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeVirtual, self).__init__(ins)
        Util.log('InvokeVirtual : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.base = memory[self.register]
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.value() == 'this':
            self.op = '%s(%s)'
        else:
            self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def value(self):
        for param in self.params:
            param.used = 1
        if self.base.value() == 'this':
            return self.op % (self.methCalled, ', '.join([str(
                               param.value()) for param in self.params]))
        return self.op % (self.base.value(), self.methCalled, ', '.join([
                           str(param.value()) for param in self.params]))

    def get_reg(self):
        Util.log('InvokeVirtual has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeVirtual (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-super {vD, vE, vF, vG, vA} ( 4b each )
class InvokeSuper(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeSuper, self).__init__(ins)
        Util.log('InvokeSuper : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = 'super.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def value(self):
        return self.op % (self.methCalled, ', '.join(
            [str(param.value()) for param in self.params]))

    def get_reg(self):
        Util.log('InvokeSuper has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeSuper (%s) %s (%s ; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-direct {vD, vE, vF, vG, vA} ( 4b each )
class InvokeDirect(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeDirect, self).__init__(ins)
        Util.log('InvokeDirect : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.base = memory[self.register]
        if self.base.value() == 'this':
            self.op = None
        else:
            self.params = get_invoke_params(self.params, self.paramsType,
                                                                   memory)
            self.op = '%s %s(%s)'

    def value(self):
        if self.op is None:
            return self.base.value()
        return self.op % (self.base.value(), self.type, ', '.join(
            [str(param.value()) for param in self.params]))

    def __str__(self):
        return 'InvokeDirect (%s) %s (%s)' % (self.returnType,
                                            self.methCalled, str(self.params))


# invoke-static {vD, vE, vF, vG, vA} ( 4b each )
class InvokeStatic(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeStatic, self).__init__(ins)
        Util.log('InvokeStatic : %s' % self.ops, 'debug')
        if len(self.ops) > 1:
            self.params = [int(i[1]) for i in self.ops[0:-1]]
        else:
            self.params = []
        Util.log('Parameters = %s' % self.params, 'debug')

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def value(self):
        return self.op % (self.type, self.methCalled, ', '.join([
                          str(param.value()) for param in self.params]))

    def get_reg(self):
        Util.log('InvokeStatic has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeStatic (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-interface {vD, vE, vF, vG, vA} ( 4b each )
class InvokeInterface(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeInterface, self).__init__(ins)
        Util.log('InvokeInterface : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.base = memory[self.register]
        if self.base.value() == 'this':
            self.op = None
        else:
            self.params = get_invoke_params(self.params, self.paramsType,
                                                                   memory)
            self.op = '%s %s(%s)'

    def value(self):
        if self.op is None:
            return self.base.value()
        return self.op % (self.base.value(), self.type, ', '.join(
            [str(param.value()) for param in self.params]))

    def __str__(self):
        return 'InvokeInterface (%s) %s (%s)' % (self.returnType,
                                            self.methCalled, str(self.params))


# invoke-virtual/range {vCCCC..vNNNN} ( 16b each )
class InvokeVirtualRange(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeVirtualRange, self).__init__(ins)
        Util.log('InvokeVirtualRange : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = self.ops[-1][2]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.base = memory[self.register]
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.value() == 'this':
            self.op = '%s(%s)'
        else:
            self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def value(self):
        if self.base.value() == 'this':
            return self.op % (self.methCalled, ', '.join(
            [str(param.value()) for param in self.params]))
        return self.op % (self.base.value(), self.methCalled, ', '.join(
            [str(param.value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeVirtualRange has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeVirtualRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-super/range {vCCCC..vNNNN} ( 16b each )
class InvokeSuperRange(InvokeInstruction):
    pass


# invoke-direct/range {vCCCC..vNNNN} ( 16b each )
class InvokeDirectRange(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeDirectRange, self).__init__(ins)
        Util.log('InvokeDirectRange : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        self.base = memory[self.register]
        self.type = self.base.get_type()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = '%s %s(%s)'

    def value(self):
        return self.op % (self.base.value(), self.type, ', '.join(
        [str(param.value()) for param in self.params]))

    def get_type(self):
        return self.type

    def __str__(self):
        return 'InvokeDirectRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, str(self.paramsType), str(self.params))


# invoke-static/range {vCCCC..vNNNN} ( 16b each )
class InvokeStaticRange(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeStaticRange, self).__init__(ins)
        Util.log('InvokeStaticRange : %s' % self.ops, 'debug')
        if len(self.ops) > 1:
            self.params = [int(i[1]) for i in self.ops[0:-1]]
        else:
            self.params = []
        Util.log('Parameters = %s' % self.params, 'debug')

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def value(self):
        return self.op % (self.type, self.methCalled, ', '.join([
                          str(param.value()) for param in self.params]))

    def get_reg(self):
        Util.log('InvokeStaticRange has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeStaticRange (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-interface/range {vCCCC..vNNNN} ( 16b each )
class InvokeInterfaceRange(InvokeInstruction):
    def __init__(self, ins):
        super(InvokeInterfaceRange, self).__init__(ins)
        Util.log('InvokeInterfaceRange : %s' % self.ops, 'debug')
        self.params = [int(i[1]) for i in self.ops[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = self.ops[-1][2]
        self.paramsType = Util.get_params_type(self.ops[-1][3])
        self.returnType = self.ops[-1][4]
        self.methCalled = self.ops[-1][-1]

    def symbolic_process(self, memory, tabsymb, varsgen):
        memory['heap'] = True
        self.base = memory[self.register]
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.value() == 'this':
            self.op = '%s(%s)'
        else:
            self.op = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.op, 'debug')

    def value(self):
        if self.base.value() == 'this':
            return self.op % (self.methCalled, ', '.join(
            [str(param.value()) for param in self.params]))
        return self.op % (self.base.value(), self.methCalled, ', '.join(
            [str(param.value()) for param in self.params]))

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
        self.op = '-'
        self.type = 'I'

    def __str__(self):
        return 'NegInt (%s)' % self.source


# not-int vA, vB ( 4b, 4b )
class NotInt(UnaryExpression):
    def __init__(self, ins):
        super(NotInt, self).__init__(ins)
        Util.log('NotInt : %s' % self.ops, 'debug')
        self.op = '~'
        self.type = 'I'

    def __str__(self):
        return 'NotInt (%s)' % self.source


# neg-long vA, vB ( 4b, 4b )
class NegLong(UnaryExpression):
    def __init__(self, ins):
        super(NegLong, self).__init__(ins)
        Util.log('NegLong : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'J'

    def __str__(self):
        return 'NegLong (%s)' % self.source


# not-long vA, vB ( 4b, 4b )
class NotLong(UnaryExpression):
    def __init__(self, ins):
        super(NotLong, self).__init__(ins)
        Util.log('NotLong : %s' % self.ops, 'debug')
        self.op = '~'
        self.type = 'J'

    def __str__(self):
        return 'NotLong (%s)' % self.source


# neg-float vA, vB ( 4b, 4b )
class NegFloat(UnaryExpression):
    def __init__(self, ins):
        super(NegFloat, self).__init__(ins)
        Util.log('NegFloat : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'F'

    def __str__(self):
        return 'NegFloat (%s)' % self.source


# neg-double vA, vB ( 4b, 4b )
class NegDouble(UnaryExpression):
    def __init__(self, ins):
        super(NegDouble, self).__init__(ins)
        Util.log('NegDouble : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'D'

    def __str__(self):
        return 'NegDouble (%s)' % self.source


# int-to-long vA, vB ( 4b, 4b )
class IntToLong(UnaryExpression):
    def __init__(self, ins):
        super(IntToLong, self).__init__(ins)
        Util.log('IntToLong : %s' % self.ops, 'debug')
        self.op = '(long)'
        self.type = 'J'

    def __str__(self):
        return 'IntToLong (%s)' % self.source


# int-to-float vA, vB ( 4b, 4b )
class IntToFloat(UnaryExpression):
    def __init__(self, ins):
        super(IntToFloat, self).__init__(ins)
        Util.log('IntToFloat : %s' % self.ops, 'debug')
        self.op = '(float)'
        self.type = 'F'

    def __str__(self):
        return 'IntToFloat (%s)' % self.source


# int-to-double vA, vB ( 4b, 4b )
class IntToDouble(UnaryExpression):
    def __init__(self, ins):
        super(IntToDouble, self).__init__(ins)
        Util.log('IntToDouble : %s' % self.ops, 'debug')
        self.op = '(double)'
        self.type = 'D'

    def __str__(self):
        return 'IntToDouble (%s)' % self.source


# long-to-int vA, vB ( 4b, 4b )
class LongToInt(UnaryExpression):
    def __init__(self, ins):
        super(LongToInt, self).__init__(ins)
        Util.log('LongToInt : %s' % self.ops, 'debug')
        self.op = '(int)'
        self.type = 'I'

    def __str__(self):
        return 'LongToInt (%s)' % self.source


# long-to-float vA, vB ( 4b, 4b )
class LongToFloat(UnaryExpression):
    def __init__(self, ins):
        super(LongToFloat, self).__init__(ins)
        Util.log('LongToFloat : %s' % self.ops, 'debug')
        self.op = '(float)'
        self.type = 'F'

    def __str__(self):
        return 'LongToFloat (%s)' % self.source


# long-to-double vA, vB ( 4b, 4b )
class LongToDouble(UnaryExpression):
    def __init__(self, ins):
        super(LongToDouble, self).__init__(ins)
        Util.log('LongToDouble : %s' % self.ops, 'debug')
        self.op = '(double)'
        self.type = 'D'

    def __str__(self):
        return 'LongToDouble (%s)' % self.source


# float-to-int vA, vB ( 4b, 4b )
class FloatToInt(UnaryExpression):
    def __init__(self, ins):
        super(FloatToInt, self).__init__(ins)
        Util.log('FloatToInt : %s' % self.ops, 'debug')
        self.op = '(int)'
        self.type = 'I'

    def __str__(self):
        return 'FloatToInt (%s)' % self.source


# float-to-long vA, vB ( 4b, 4b )
class FloatToLong(UnaryExpression):
    def __init__(self, ins):
        super(FloatToLong, self).__init__(ins)
        Util.log('FloatToLong : %s' % self.ops, 'debug')
        self.op = '(long)'
        self.type = 'J'

    def __str__(self):
        return 'FloatToLong (%s)' % self.source


# float-to-double vA, vB ( 4b, 4b )
class FloatToDouble(UnaryExpression):
    def __init__(self, ins):
        super(FloatToDouble, self).__init__(ins)
        Util.log('FloatToDouble : %s' % self.ops, 'debug')
        self.op = '(double)'
        self.type = 'D'

    def __str__(self):
        return 'FloatToDouble (%s)' % self.source


# double-to-int vA, vB ( 4b, 4b )
class DoubleToInt(UnaryExpression):
    def __init__(self, ins):
        super(DoubleToInt, self).__init__(ins)
        Util.log('DoubleToInt : %s' % self.ops, 'debug')
        self.op = '(int)'
        self.type = 'I'

    def __str__(self):
        return 'DoubleToInt (%s)' % self.source


# double-to-long vA, vB ( 4b, 4b )
class DoubleToLong(UnaryExpression):
    def __init__(self, ins):
        super(DoubleToLong, self).__init__(ins)
        Util.log('DoubleToLong : %s' % self.ops, 'debug')
        self.op = '(long)'
        self.type = 'J'

    def __str__(self):
        return 'DoubleToLong (%s)' % self.source


# double-to-float vA, vB ( 4b, 4b )
class DoubleToFloat(UnaryExpression):
    def __init__(self, ins):
        super(DoubleToFloat, self).__init__(ins)
        Util.log('DoubleToFloat : %s' % self.ops, 'debug')
        self.op = '(float)'
        self.type = 'F'

    def __str__(self):
        return 'DoubleToFloat (%s)' % self.source


# int-to-byte vA, vB ( 4b, 4b )
class IntToByte(UnaryExpression):
    def __init__(self, ins):
        super(IntToByte, self).__init__(ins)
        Util.log('IntToByte : %s' % self.ops, 'debug')
        self.op = '(byte)'
        self.type = 'B'

    def __str__(self):
        return 'IntToByte (%s)' % self.source


# int-to-char vA, vB ( 4b, 4b )
class IntToChar(UnaryExpression):
    def __init__(self, ins):
        super(IntToChar, self).__init__(ins)
        Util.log('IntToChar : %s' % self.ops, 'debug')
        self.op = '(char)'
        self.type = 'C'

    def __str__(self):
        return 'IntToChar (%s)' % self.source


# int-to-short vA, vB ( 4b, 4b )
class IntToShort(UnaryExpression):
    def __init__(self, ins):
        super(IntToShort, self).__init__(ins)
        Util.log('IntToShort : %s' % self.ops, 'debug')
        self.op = '(short)'
        self.type = 'S'

    def __str__(self):
        return 'IntToShort (%s)' % self.source


# add-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AddInt(BinaryExpression):
    def __init__(self, ins):
        super(AddInt, self).__init__(ins)
        Util.log('AddInt : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'I'

    def __str__(self):
        return 'AddInt (%s, %s)' % (self.lhs, self.rhs)


# sub-int vAA, vBB, vCC ( 8b, 8b, 8b )
class SubInt(BinaryExpression):
    def __init__(self, ins):
        super(SubInt, self).__init__(ins)
        Util.log('SubInt : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'I'

    def __str__(self):
        return 'AddInt (%s, %s)' % (self.lhs, self.rhs)


# mul-int vAA, vBB, vCC ( 8b, 8b, 8b )
class MulInt(BinaryExpression):
    def __init__(self, ins):
        super(MulInt, self).__init__(ins)
        Util.log('MulInt : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'I'

    def __str__(self):
        return 'MulInt (%s, %s)' % (self.lhs, self.rhs)


# div-int vAA, vBB, vCC ( 8b, 8b, 8b )
class DivInt(BinaryExpression):
    def __init__(self, ins):
        super(DivInt, self).__init__(ins)
        Util.log('DivInt : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'I'

    def __str__(self):
        return 'DivInt (%s, %s)' % (self.lhs, self.rhs)


# rem-int vAA, vBB, vCC ( 8b, 8b, 8b )
class RemInt(BinaryExpression):
    def __init__(self, ins):
        super(RemInt, self).__init__(ins)
        Util.log('RemInt : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'I'

    def __str__(self):
        return 'RemInt (%s, %s)' % (self.lhs, self.rhs)


# and-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AndInt(BinaryExpression):
    def __init__(self, ins):
        super(AndInt, self).__init__(ins)
        Util.log('AndInt : %s' % self.ops, 'debug')
        self.op = '&'
        self.type = 'I'

    def __str__(self):
        return 'AndInt (%s, %s)' % (self.lhs, self.rhs)


# or-int vAA, vBB, vCC ( 8b, 8b, 8b )
class OrInt(BinaryExpression):
    def __init__(self, ins):
        super(OrInt, self).__init__(ins)
        Util.log('OrInt : %s' % self.ops, 'debug')
        self.op = '|'
        self.type = 'I'

    def __str__(self):
        return 'OrInt (%s, %s)' % (self.lhs, self.rhs)


# xor-int vAA, vBB, vCC ( 8b, 8b, 8b )
class XorInt(BinaryExpression):
    def __init__(self, ins):
        super(XorInt, self).__init__(ins)
        Util.log('XorInt : %s' % self.ops, 'debug')
        self.op = '^'
        self.type = 'I'

    def __str__(self):
        return 'XorInt (%s, %s)' % (self.lhs, self.rhs)


# shl-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlInt(BinaryExpression):
    def __init__(self, ins):
        super(ShlInt, self).__init__(ins)
        Util.log('ShlInt : %s' % self.ops, 'debug')
        self.op = '(%s << ( %s & 0x1f ))'
        self.type = 'I'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'ShlInt (%s, %s)' % (self.lhs, self.rhs)


# shr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrInt(BinaryExpression):
    def __init__(self, ins):
        super(ShrInt, self).__init__(ins)
        Util.log('ShrInt : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'I'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'ShrInt (%s, %s)' % (self.lhs, self.rhs)


# ushr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrInt(BinaryExpression):
    def __init__(self, ins):
        super(UShrInt, self).__init__(ins)
        Util.log('UShrInt : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'I'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'UShrInt (%s, %s)' % (self.lhs, self.rhs)


# add-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AddLong(BinaryExpression):
    def __init__(self, ins):
        super(AddLong, self).__init__(ins)
        Util.log('AddLong : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'J'

    def __str__(self):
        return 'AddLong (%s, %s)' % (self.lhs, self.rhs)


# sub-long vAA, vBB, vCC ( 8b, 8b, 8b )
class SubLong(BinaryExpression):
    def __init__(self, ins):
        super(SubLong, self).__init__(ins)
        Util.log('SubLong : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'J'

    def __str__(self):
        return 'SubLong (%s, %s)' % (self.lhs, self.rhs)


# mul-long vAA, vBB, vCC ( 8b, 8b, 8b )
class MulLong(BinaryExpression):
    def __init__(self, ins):
        super(MulLong, self).__init__(ins)
        Util.log('MulLong : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'J'

    def __str__(self):
        return 'MulLong (%s, %s)' % (self.lhs, self.rhs)


# div-long vAA, vBB, vCC ( 8b, 8b, 8b )
class DivLong(BinaryExpression):
    def __init__(self, ins):
        super(DivLong, self).__init__(ins)
        Util.log('DivLong : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'J'

    def __str__(self):
        return 'DivLong (%s, %s)' % (self.lhs, self.rhs)


# rem-long vAA, vBB, vCC ( 8b, 8b, 8b )
class RemLong(BinaryExpression):
    def __init__(self, ins):
        super(RemLong, self).__init__(ins)
        Util.log('RemLong : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'J'

    def __str__(self):
        return 'RemLong (%s, %s)' % (self.lhs, self.rhs)


# and-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AndLong(BinaryExpression):
    def __init__(self, ins):
        super(AndLong, self).__init__(ins)
        Util.log('AndLong : %s' % self.ops, 'debug')
        self.op = '&'
        self.type = 'J'

    def __str__(self):
        return 'AndLong (%s, %s)' % (self.lhs, self.rhs)


# or-long vAA, vBB, vCC ( 8b, 8b, 8b )
class OrLong(BinaryExpression):
    def __init__(self, ins):
        super(OrLong, self).__init__(ins)
        Util.log('OrLong : %s' % self.ops, 'debug')
        self.op = '|'
        self.type = 'J'

    def __str__(self):
        return 'OrLong (%s, %s)' % (self.lhs, self.rhs)


# xor-long vAA, vBB, vCC ( 8b, 8b, 8b )
class XorLong(BinaryExpression):
    def __init__(self, ins):
        super(XorLong, self).__init__(ins)
        Util.log('XorLong : %s' % self.ops, 'debug')
        self.op = '^'
        self.type = 'J'

    def __str__(self):
        return 'XorLong (%s, %s)' % (self.lhs, self.rhs)


# shl-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlLong(BinaryExpression):
    def __init__(self, ins):
        super(ShlLong, self).__init__(ins)
        Util.log('ShlLong : %s' % self.ops, 'debug')
        self.op = '(%s << ( %s & 0x1f ))'
        self.type = 'J'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'ShlLong (%s, %s)' % (self.lhs, self.rhs)


# shr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrLong(BinaryExpression):
    def __init__(self, ins):
        super(ShrLong, self).__init__(ins)
        Util.log('ShrLong : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'J'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'ShrLong (%s, %s)' % (self.lhs, self.rhs)


# ushr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrLong(BinaryExpression):
    def __init__(self, ins):
        super(UShrLong, self).__init__(ins)
        Util.log('UShrLong : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'J'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'UShrLong (%s, %s)' % (self.lhs, self.rhs)


# add-float vAA, vBB, vCC ( 8b, 8b, 8b )
class AddFloat(BinaryExpression):
    def __init__(self, ins):
        super(AddFloat, self).__init__(ins)
        Util.log('AddFloat : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'F'

    def __str__(self):
        return 'AddFloat (%s, %s)' % (self.lhs, self.rhs)


# sub-float vAA, vBB, vCC ( 8b, 8b, 8b )
class SubFloat(BinaryExpression):
    def __init__(self, ins):
        super(SubFloat, self).__init__(ins)
        Util.log('SubFloat : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'F'

    def __str__(self):
        return 'SubFloat (%s, %s)' % (self.lhs, self.rhs)


# mul-float vAA, vBB, vCC ( 8b, 8b, 8b )
class MulFloat(BinaryExpression):
    def __init__(self, ins):
        super(MulFloat, self).__init__(ins)
        Util.log('MulFloat : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'F'

    def __str__(self):
        return 'MulFloat (%s, %s)' % (self.lhs, self.rhs)


# div-float vAA, vBB, vCC ( 8b, 8b, 8b )
class DivFloat(BinaryExpression):
    def __init__(self, ins):
        super(DivFloat, self).__init__(ins)
        Util.log('DivFloat : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'F'

    def __str__(self):
        return 'DivFloat (%s, %s)' % (self.lhs, self.rhs)


# rem-float vAA, vBB, vCC ( 8b, 8b, 8b )
class RemFloat(BinaryExpression):
    def __init__(self, ins):
        super(RemFloat, self).__init__(ins)
        Util.log('RemFloat : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'F'

    def __str__(self):
        return 'RemFloat (%s, %s)' % (self.lhs, self.rhs)


# add-double vAA, vBB, vCC ( 8b, 8b, 8b )
class AddDouble(BinaryExpression):
    def __init__(self, ins):
        super(AddDouble, self).__init__(ins)
        Util.log('AddDouble : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'D'

    def __str__(self):
        return 'AddDouble (%s, %s)' % (self.lhs, self.rhs)


# sub-double vAA, vBB, vCC ( 8b, 8b, 8b )
class SubDouble(BinaryExpression):
    def __init__(self, ins):
        super(SubDouble, self).__init__(ins)
        Util.log('SubDouble : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'D'

    def __str__(self):
        return 'SubDouble (%s, %s)' % (self.lhs, self.rhs)


# mul-double vAA, vBB, vCC ( 8b, 8b, 8b )
class MulDouble(BinaryExpression):
    def __init__(self, ins):
        super(MulDouble, self).__init__(ins)
        Util.log('MulDouble : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'D'

    def __str__(self):
        return 'MulDouble (%s, %s)' % (self.lhs, self.rhs)


# div-double vAA, vBB, vCC ( 8b, 8b, 8b )
class DivDouble(BinaryExpression):
    def __init__(self, ins):
        super(DivDouble, self).__init__(ins)
        Util.log('DivDouble : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'D'

    def __str__(self):
        return 'DivDouble (%s, %s)' % (self.lhs, self.rhs)


# rem-double vAA, vBB, vCC ( 8b, 8b, 8b )
class RemDouble(BinaryExpression):
    def __init__(self, ins):
        super(RemDouble, self).__init__(ins)
        Util.log('RemDouble : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'D'

    def __str__(self):
        return 'DivDouble (%s, %s)' % (self.lhs, self.rhs)


# add-int/2addr vA, vB ( 4b, 4b )
class AddInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddInt2Addr, self).__init__(ins)
        Util.log('AddInt2Addr : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'I'

    def __str__(self):
        return 'AddInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# sub-int/2addr vA, vB ( 4b, 4b )
class SubInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(SubInt2Addr, self).__init__(ins)
        Util.log('SubInt2Addr : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'I'

    def __str__(self):
        return 'SubInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# mul-int/2addr vA, vB ( 4b, 4b )
class MulInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulInt2Addr, self).__init__(ins)
        Util.log('MulInt2Addr : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'I'

    def __str__(self):
        return 'MulInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# div-int/2addr vA, vB ( 4b, 4b )
class DivInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivInt2Addr, self).__init__(ins)
        Util.log('DivInt2Addr : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'I'

    def __str__(self):
        return 'DivInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# rem-int/2addr vA, vB ( 4b, 4b )
class RemInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(RemInt2Addr, self).__init__(ins)
        Util.log('RemInt2Addr : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'I'

    def __str__(self):
        return 'RemInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# and-int/2addr vA, vB ( 4b, 4b )
class AndInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AndInt2Addr, self).__init__(ins)
        Util.log('AndInt2Addr : %s' % self.ops, 'debug')
        self.op = '&'
        self.type = 'I'

    def __str__(self):
        return 'AndInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# or-int/2addr vA, vB ( 4b, 4b )
class OrInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(OrInt2Addr, self).__init__(ins)
        Util.log('OrInt2Addr : %s' % self.ops, 'debug')
        self.op = '|'
        self.type = 'I'

    def __str__(self):
        return 'OrInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# xor-int/2addr vA, vB ( 4b, 4b )
class XorInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(XorInt2Addr, self).__init__(ins)
        Util.log('XorInt2Addr : %s' % self.ops, 'debug')
        self.op = '^'
        self.type = 'I'

    def __str__(self):
        return 'XorInt2Addr (%s, %s)' % (self.lhs, self.rhs)
    

# shl-int/2addr vA, vB ( 4b, 4b )
class ShlInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShlInt2Addr, self).__init__(ins)
        Util.log('ShlInt2Addr : %s' % self.ops, 'debug')
        self.op = '(%s << ( %s & 0x1f ))'
        self.type = 'I'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'ShlInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# shr-int/2addr vA, vB ( 4b, 4b )
class ShrInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShrInt2Addr, self).__init__(ins)
        Util.log('ShrInt2Addr : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'I'
    
    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'ShrInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# ushr-int/2addr vA, vB ( 4b, 4b )
class UShrInt2Addr(BinaryExpression):
    def __init__(self, ins):
        super(UShrInt2Addr, self).__init__(ins)
        Util.log('UShrInt2Addr : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'I'

    def value(self):
        return self.op % (self.lhs.value(), self.rhs.value())

    def __str__(self):
        return 'UShrInt2Addr (%s, %s)' % (self.lhs, self.rhs)


# add-long/2addr vA, vB ( 4b, 4b )
class AddLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddLong2Addr, self).__init__(ins)
        Util.log('AddLong2Addr : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'J'

    def __str__(self):
        return 'AddLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# sub-long/2addr vA, vB ( 4b, 4b )
class SubLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(SubLong2Addr, self).__init__(ins)
        Util.log('SubLong2Addr : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'J'

    def __str__(self):
        return 'SubLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# mul-long/2addr vA, vB ( 4b, 4b )
class MulLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulLong2Addr, self).__init__(ins)
        Util.log('MulLong2Addr : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'J'

    def __str__(self):
        return 'MulLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# div-long/2addr vA, vB ( 4b, 4b )
class DivLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivLong2Addr, self).__init__(ins)
        Util.log('DivLong2Addr : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'J'

    def __str__(self):
        return 'DivLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# rem-long/2addr vA, vB ( 4b, 4b )
class RemLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(RemLong2Addr, self).__init__(ins)
        Util.log('RemLong2Addr : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'J'

    def __str__(self):
        return 'RemLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# and-long/2addr vA, vB ( 4b, 4b )
class AndLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AndLong2Addr, self).__init__(ins)
        Util.log('AddLong2Addr : %s' % self.ops, 'debug')
        self.op = '&'
        self.type = 'J'

    def __str__(self):
        return 'AndLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# or-long/2addr vA, vB ( 4b, 4b )
class OrLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(OrLong2Addr, self).__init__(ins)
        Util.log('OrLong2Addr : %s' % self.ops, 'debug')
        self.op = '|'
        self.type = 'J'

    def __str__(self):
        return 'OrLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# xor-long/2addr vA, vB ( 4b, 4b )
class XorLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(XorLong2Addr, self).__init__(ins)
        Util.log('XorLong2Addr : %s' % self.ops, 'debug')
        self.op = '^'
        self.type = 'J'

    def __str__(self):
        return 'XorLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# shl-long/2addr vA, vB ( 4b, 4b )
class ShlLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShlLong2Addr, self).__init__(ins)
        Util.log('ShlLong2Addr : %s' % self.ops, 'debug')
        self.op = '(%s << ( %s & 0x1f ))'
        self.type = 'J'

    def value(self):
        return self.op % (self.rhs.value(), self.lhs.value())

    def __str__(self):
        return 'ShlLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# shr-long/2addr vA, vB ( 4b, 4b )
class ShrLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(ShrLong2Addr, self).__init__(ins)
        Util.log('ShrLong2Addr : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'J'

    def value(self):
        return self.op % (self.rhs.value(), self.lhs.value())

    def __str__(self):
        return 'ShrLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# ushr-long/2addr vA, vB ( 4b, 4b )
class UShrLong2Addr(BinaryExpression):
    def __init__(self, ins):
        super(UShrLong2Addr, self).__init__(ins)
        Util.log('UShrLong2Addr : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'J'

    def value(self):
        return self.op % (self.rhs.value(), self.lhs.value())

    def __str__(self):
        return 'UShrLong2Addr (%s, %s)' % (self.lhs, self.rhs)


# add-float/2addr vA, vB ( 4b, 4b )
class AddFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddFloat2Addr, self).__init__(ins)
        Util.log('AddFloat2Addr : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'F'

    def __str__(self):
        return 'AddFloat2Addr (%s, %s)' % (self.lhs, self.rhs)


# sub-float/2addr vA, vB ( 4b, 4b )
class SubFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(SubFloat2Addr, self).__init__(ins)
        Util.log('SubFloat2Addr : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'F'

    def __str__(self):
        return 'SubFloat2Addr (%s, %s)' % (self.lhs, self.rhs)


# mul-float/2addr vA, vB ( 4b, 4b )
class MulFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulFloat2Addr, self).__init__(ins)
        Util.log('MulFloat2Addr : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'F'

    def __str__(self):
        return 'MulFloat2Addr (%s, %s)' % (self.lhs, self.rhs)


# div-float/2addr vA, vB ( 4b, 4b )
class DivFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivFloat2Addr, self).__init__(ins)
        Util.log('DivFloat2Addr : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'F'

    def __str__(self):
        return 'DivFloat2Addr (%s, %s)' % (self.lhs, self.rhs)


# rem-float/2addr vA, vB ( 4b, 4b )
class RemFloat2Addr(BinaryExpression):
    def __init__(self, ins):
        super(RemFloat2Addr, self).__init__(ins)
        Util.log('RemFloat2Addr : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'F'
    
    def __str__(self):
        return 'RemFloat2Addr (%s, %s)' % (self.lhs, self.rhs)


# add-double/2addr vA, vB ( 4b, 4b )
class AddDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(AddDouble2Addr, self).__init__(ins)
        Util.log('AddDouble2Addr : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'D'
    
    def __str__(self):
        return 'AddDouble2Addr (%s, %s)' % (self.lhs, self.rhs)


# sub-double/2addr vA, vB ( 4b, 4b )
class SubDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(SubDouble2Addr, self).__init__(ins)
        Util.log('subDouble2Addr : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'D'
    
    def __str__(self):
        return 'SubDouble2Addr (%s, %s)' % (self.lhs, self.rhs)


# mul-double/2addr vA, vB ( 4b, 4b )
class MulDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(MulDouble2Addr, self).__init__(ins)
        Util.log('MulDouble2Addr : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'D'
    
    def __str__(self):
        return 'MulDouble2Addr (%s, %s)' % (self.lhs, self.rhs)


# div-double/2addr vA, vB ( 4b, 4b )
class DivDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(DivDouble2Addr, self).__init__(ins)
        Util.log('DivDouble2Addr : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'D'
    
    def __str__(self):
        return 'DivDouble2Addr (%s, %s)' % (self.lhs, self.rhs)


# rem-double/2addr vA, vB ( 4b, 4b )
class RemDouble2Addr(BinaryExpression):
    def __init__(self, ins):
        super(RemDouble2Addr, self).__init__(ins)
        Util.log('RemDouble2Addr : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'D'
    
    def __str__(self):
        return 'RemDouble2Addr (%s, %s)' % (self.lhs, self.rhs)


# add-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AddIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(AddIntLit16, self).__init__(ins)
        Util.log('AddIntLit16 : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'I'

    def __str__(self):
        return 'AddIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# rsub-int vA, vB, #+CCCC ( 4b, 4b, 16b )
class RSubInt(BinaryExpressionLit):
    pass
    #TODO inverse lhs & rhs


# mul-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class MulIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(MulIntLit16, self).__init__(ins)
        Util.log('MulIntLit16 : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'I'

    def __str__(self):
        return 'MulIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# div-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class DivIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(DivIntLit16, self).__init__(ins)
        Util.log('DivIntLit16 : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'I'

    def __str__(self):
        return 'DivIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# rem-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class RemIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(RemIntLit16, self).__init__(ins)
        Util.log('RemIntLit16 : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'I'

    def __str__(self):
        return 'RemIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# and-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AndIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(AndIntLit16, self).__init__(ins)
        Util.log('AndIntLit16 : %s' % self.ops, 'debug')
        self.op = 'a'
        self.type = 'I'

    def __str__(self):
        return 'AndIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# or-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class OrIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(OrIntLit16, self).__init__(ins)
        Util.log('OrIntLit16 : %s' % self.ops, 'debug')
        self.op = '|'
        self.type = 'I'

    def __str__(self):
        return 'OrIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# xor-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class XorIntLit16(BinaryExpressionLit):
    def __init__(self, ins):
        super(XorIntLit16, self).__init__(ins)
        Util.log('XorIntLit16 : %s' % self.ops, 'debug')
        self.op = '^'
        self.type = 'I'

    def __str__(self):
        return 'XorIntLit16 (%s, %s)' % (self.lhs, self.rhs)


# add-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AddIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(AddIntLit8, self).__init__(ins)
        Util.log('AddIntLit8 : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'I'

    def __str__(self):
        return 'AddIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# rsub-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RSubIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(RSubIntLit8, self).__init__(ins)
        Util.log('RSubIntLit8 : %s' % self.ops, 'debug')
        self.op = '-'
        self.type = 'I'
    
    def __str__(self):
        return 'AddIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# mul-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class MulIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(MulIntLit8, self).__init__(ins)
        Util.log('MulIntLit8 : %s' % self.ops, 'debug')
        self.op = '*'
        self.type = 'I'

    def __str__(self):
        return 'MulIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# div-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class DivIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(DivIntLit8, self).__init__(ins)
        Util.log('DivIntLit8 : %s' % self.ops, 'debug')
        self.op = '/'
        self.type = 'I'
    
    def __str__(self):
        return 'DivIntLit8 (%s, %s)' % (self.lhs, self.rhs)
    

# rem-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RemIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(RemIntLit8, self).__init__(ins)
        Util.log('RemIntLit8 : %s' % self.ops, 'debug')
        self.op = '%%'
        self.type = 'I'

    def __str__(self):
        return 'RemIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# and-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AndIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(AddIntLit8, self).__init__(ins)
        Util.log('AddIntLit8 : %s' % self.ops, 'debug')
        self.op = '+'
        self.type = 'I'

    def __str__(self):
        return 'AddIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# or-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class OrIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(OrIntLit8, self).__init__(ins)
        Util.log('OrIntLit8 : %s' % self.ops, 'debug')
        self.op = '|'
        self.type = 'I'

    def __str__(self):
        return 'OrIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# xor-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class XorIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(XorIntLit8, self).__init__(ins)
        Util.log('XorIntLit8 : %s' % self.ops, 'debug')
        self.op = '^'
        self.type = 'I'

    def __str__(self):
        return 'XorIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# shl-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShlIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(ShlIntLit8, self).__init__(ins)
        Util.log('ShlIntLit8 : %s' % self.ops, 'debug')
        self.op = '(%s << ( %s & 0x1f ))'
        self.type = 'I'

    def value(self):
        return self.op % (self.rhs.value(), self.lhs)

    def __str__(self):
        return 'ShlIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# shr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShrIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(ShrIntLit8, self).__init__(ins)
        Util.log('ShrIntLit8 : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'I'

    def value(self):
        return self.op % (self.rhs.value(), self.lhs)

    def __str__(self):
        return 'ShrIntLit8 (%s, %s)' % (self.lhs, self.rhs)


# ushr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class UShrIntLit8(BinaryExpressionLit):
    def __init__(self, ins):
        super(UShrIntLit8, self).__init__(ins)
        Util.log('UShrIntLit8 : %s' % self.ops, 'debug')
        self.op = '(%s >> ( %s & 0x1f ))'
        self.type = 'I'

    def value(self):
        return self.op % (self.rhs.value(), self.lhs)

    def __str__(self):
        return 'UShrIntLit8 (%s, %s)' % (self.lhs, self.rhs)


INSTRUCTION_SET = {
    'nop'                   : (EXPR, Nop),
    'move'                  : (INST, Move),
    'move/from16'           : (INST, MoveFrom16),
    'move/16'               : (INST, Move16),
    'move-wide'             : (INST, MoveWide),
    'move-wide/from16'      : (INST, MoveWideFrom16),
    'move-wide/16'          : (INST, MoveWide16),
    'move-object'           : (INST, MoveObject),
    'move-object/from16'    : (INST, MoveObjectFrom16),
    'move-object/16'        : (INST, MoveObject16),
    'move-result'           : (INST, MoveResult),
    'move-result-wide'      : (INST, MoveResultWide),
    'move-result-object'    : (INST, MoveResultObject),
    'move-exception'        : (EXPR, MoveException),
    'return-void'           : (INST, ReturnVoid),
    'return'                : (INST, Return),
    'return-wide'           : (INST, ReturnWide),
    'return-object'         : (INST, ReturnObject),
    'const/4'               : (EXPR, Const4),
    'const/16'              : (EXPR, Const16),
    'const'                 : (EXPR, Const),
    'const/high16'          : (EXPR, ConstHigh16),
    'const-wide/16'         : (EXPR, ConstWide16),
    'const-wide/32'         : (EXPR, ConstWide32),
    'const-wide'            : (EXPR, ConstWide),
    'const-wide/high16'     : (EXPR, ConstWideHigh16),
    'const-string'          : (EXPR, ConstString),
    'const-string/jumbo'    : (EXPR, ConstStringJumbo),
    'const-class'           : (EXPR, ConstClass),
    'monitor-enter'         : (EXPR, MonitorEnter),
    'monitor-exit'          : (EXPR, MonitorExit),
    'check-cast'            : (EXPR, CheckCast),
    'instance-of'           : (EXPR, InstanceOf),
    'array-length'          : (EXPR, ArrayLength),
    'new-instance'          : (EXPR, NewInstance),
    'new-array'             : (EXPR, NewArray),
    'filled-new-array'      : (EXPR, FilledNewArray),
    'filled-new-array/range': (EXPR, FilledNewArrayRange),
    'fill-array-data'       : (EXPR, FillArrayData),
    'throw'                 : (EXPR, Throw),
    'goto'                  : (EXPR, Goto),
    'goto/16'               : (EXPR, Goto16),
    'goto/32'               : (EXPR, Goto32),
    'packed-switch'         : (INST, PackedSwitch),
    'sparse-switch'         : (EXPR, SparseSwitch),
    'cmpl-float'            : (EXPR, CmplFloat),
    'cmpg-float'            : (EXPR, CmpgFloat),
    'cmpl-double'           : (EXPR, CmplDouble),
    'cmpg-double'           : (EXPR, CmpgDouble),
    'cmp-long'              : (EXPR, CmpLong),
    'if-eq'                 : (COND, IfEq),
    'if-ne'                 : (COND, IfNe),
    'if-lt'                 : (COND, IfLt),
    'if-ge'                 : (COND, IfGe),
    'if-gt'                 : (COND, IfGt),
    'if-le'                 : (COND, IfLe),
    'if-eqz'                : (COND, IfEqz),
    'if-nez'                : (COND, IfNez),
    'if-ltz'                : (COND, IfLtz),
    'if-gez'                : (COND, IfGez),
    'if-gtz'                : (COND, IfGtz),
    'if-lez'                : (COND, IfLez),
    'aget'                  : (EXPR, AGet),
    'aget-wide'             : (EXPR, AGetWide),
    'aget-object'           : (EXPR, AGetObject),
    'aget-boolean'          : (EXPR, AGetBoolean),
    'aget-byte'             : (EXPR, AGetByte),
    'aget-char'             : (EXPR, AGetChar),
    'aget-short'            : (EXPR, AGetShort),
    'aput'                  : (INST, APut),
    'aput-wide'             : (INST, APutWide),
    'aput-object'           : (INST, APutObject),
    'aput-boolean'          : (INST, APutBoolean),
    'aput-byte'             : (INST, APutByte),
    'aput-char'             : (INST, APutChar),
    'aput-short'            : (INST, APutShort),
    'iget'                  : (EXPR, IGet),
    'iget-wide'             : (EXPR, IGetWide),
    'iget-object'           : (EXPR, IGetObject),
    'iget-boolean'          : (EXPR, IGetBoolean),
    'iget-byte'             : (EXPR, IGetByte),
    'iget-char'             : (EXPR, IGetChar),
    'iget-short'            : (EXPR, IGetShort),
    'iput'                  : (INST, IPut),
    'iput-wide'             : (INST, IPutWide),
    'iput-object'           : (INST, IPutObject),
    'iput-boolean'          : (INST, IPutBoolean),
    'iput-byte'             : (INST, IPutByte),
    'iput-char'             : (INST, IPutChar),
    'iput-short'            : (INST, IPutShort),
    'sget'                  : (EXPR, SGet),
    'sget-wide'             : (EXPR, SGetWide),
    'sget-object'           : (EXPR, SGetObject),
    'sget-boolean'          : (EXPR, SGetBoolean),
    'sget-byte'             : (EXPR, SGetByte),
    'sget-char'             : (EXPR, SGetChar),
    'sget-short'            : (EXPR, SGetShort),
    'sput'                  : (INST, SPut),
    'sput-wide'             : (INST, SPutWide),
    'sput-object'           : (INST, SPutObject),
    'sput-boolean'          : (INST, SPutBoolean),
    'sput-byte'             : (INST, SPutByte),
    'sput-char'             : (INST, SPutChar),
    'sput-short'            : (INST, SPutShort),
    'invoke-virtual'        : (INST, InvokeVirtual),
    'invoke-super'          : (INST, InvokeSuper),
    'invoke-direct'         : (INST, InvokeDirect),
    'invoke-static'         : (INST, InvokeStatic),
    'invoke-interface'      : (INST, InvokeInterface),
    'invoke-virtual/range'  : (INST, InvokeVirtualRange),
    'invoke-super/range'    : (INST, InvokeSuperRange),
    'invoke-direct/range'   : (INST, InvokeDirectRange),
    'invoke-static/range'   : (INST, InvokeStaticRange),
    'invoke-interface/range': (INST, InvokeInterfaceRange),
    'neg-int'               : (EXPR, NegInt),
    'not-int'               : (EXPR, NotInt),
    'neg-long'              : (EXPR, NegLong),
    'not-long'              : (EXPR, NotLong),
    'neg-float'             : (EXPR, NegFloat),
    'neg-double'            : (EXPR, NegDouble),
    'int-to-long'           : (EXPR, IntToLong),
    'int-to-float'          : (EXPR, IntToFloat),
    'int-to-double'         : (EXPR, IntToDouble),
    'long-to-int'           : (EXPR, LongToInt),
    'long-to-float'         : (EXPR, LongToFloat),
    'long-to-double'        : (EXPR, LongToDouble),
    'float-to-int'          : (EXPR, FloatToInt),
    'float-to-long'         : (EXPR, FloatToLong),
    'float-to-double'       : (EXPR, FloatToDouble),
    'double-to-int'         : (EXPR, DoubleToInt),
    'double-to-long'        : (EXPR, DoubleToLong),
    'double-to-float'       : (EXPR, DoubleToFloat),
    'int-to-byte'           : (EXPR, IntToByte),
    'int-to-char'           : (EXPR, IntToChar),
    'int-to-short'          : (EXPR, IntToShort),
    'add-int'               : (EXPR, AddInt),
    'sub-int'               : (EXPR, SubInt),
    'mul-int'               : (EXPR, MulInt),
    'div-int'               : (EXPR, DivInt),
    'rem-int'               : (EXPR, RemInt),
    'and-int'               : (EXPR, AndInt),
    'or-int'                : (EXPR, OrInt),
    'xor-int'               : (EXPR, XorInt),
    'shl-int'               : (EXPR, ShlInt),
    'shr-int'               : (EXPR, ShrInt),
    'ushr-int'              : (EXPR, UShrInt),
    'add-long'              : (EXPR, AddLong),
    'sub-long'              : (EXPR, SubLong),
    'mul-long'              : (EXPR, MulLong),
    'div-long'              : (EXPR, DivLong),
    'rem-long'              : (EXPR, RemLong),
    'and-long'              : (EXPR, AndLong),
    'or-long'               : (EXPR, OrLong),
    'xor-long'              : (EXPR, XorLong),
    'shl-long'              : (EXPR, ShlLong),
    'shr-long'              : (EXPR, ShrLong),
    'ushr-long'             : (EXPR, UShrLong),
    'add-float'             : (EXPR, AddFloat),
    'sub-float'             : (EXPR, SubFloat),
    'mul-float'             : (EXPR, MulFloat),
    'div-float'             : (EXPR, DivFloat),
    'rem-float'             : (EXPR, RemFloat),
    'add-double'            : (EXPR, AddDouble),
    'sub-double'            : (EXPR, SubDouble),
    'mul-double'            : (EXPR, MulDouble),
    'div-double'            : (EXPR, DivDouble),
    'rem-double'            : (EXPR, RemDouble),
    'add-int/2addr'         : (EXPR, AddInt2Addr),
    'sub-int/2addr'         : (EXPR, SubInt2Addr),
    'mul-int/2addr'         : (EXPR, MulInt2Addr),
    'div-int/2addr'         : (EXPR, DivInt2Addr),
    'rem-int/2addr'         : (EXPR, RemInt2Addr),
    'and-int/2addr'         : (EXPR, AndInt2Addr),
    'or-int/2addr'          : (EXPR, OrInt2Addr),
    'xor-int/2addr'         : (EXPR, XorInt2Addr),
    'shl-int/2addr'         : (EXPR, ShlInt2Addr),
    'shr-int/2addr'         : (EXPR, ShrInt2Addr),
    'ushr-int/2addr'        : (EXPR, UShrInt2Addr),
    'add-long/2addr'        : (EXPR, AddLong2Addr),
    'sub-long/2addr'        : (EXPR, SubLong2Addr),
    'mul-long/2addr'        : (EXPR, MulLong2Addr),
    'div-long/2addr'        : (EXPR, DivLong2Addr),
    'rem-long/2addr'        : (EXPR, RemLong2Addr),
    'and-long/2addr'        : (EXPR, AndLong2Addr),
    'or-long/2addr'         : (EXPR, OrLong2Addr),
    'xor-long/2addr'        : (EXPR, XorLong2Addr),
    'shl-long/2addr'        : (EXPR, ShlLong2Addr),
    'shr-long/2addr'        : (EXPR, ShrLong2Addr),
    'ushr-long/2addr'       : (EXPR, UShrLong2Addr),
    'add-float/2addr'       : (EXPR, AddFloat2Addr),
    'sub-float/2addr'       : (EXPR, SubFloat2Addr),
    'mul-float/2addr'       : (EXPR, MulFloat2Addr),
    'div-float/2addr'       : (EXPR, DivFloat2Addr),
    'rem-float/2addr'       : (EXPR, RemFloat2Addr),
    'add-double/2addr'      : (EXPR, AddDouble2Addr),
    'sub-double/2addr'      : (EXPR, SubDouble2Addr),
    'mul-double/2addr'      : (EXPR, MulDouble2Addr),
    'div-double/2addr'      : (EXPR, DivDouble2Addr),
    'rem-double/2addr'      : (EXPR, RemDouble2Addr),
    'add-int/lit16'         : (EXPR, AddIntLit16),
    'rsub-int'              : (EXPR, RSubInt),
    'mul-int/lit16'         : (EXPR, MulIntLit16),
    'div-int/lit16'         : (EXPR, DivIntLit16),
    'rem-int/lit16'         : (EXPR, RemIntLit16),
    'and-int/lit16'         : (EXPR, AndIntLit16),
    'or-int/lit16'          : (EXPR, OrIntLit16),
    'xor-int/lit16'         : (EXPR, XorIntLit16),
    'add-int/lit8'          : (EXPR, AddIntLit8),
    'rsub-int/lit8'         : (EXPR, RSubIntLit8),
    'mul-int/lit8'          : (EXPR, MulIntLit8),
    'div-int/lit8'          : (EXPR, DivIntLit8),
    'rem-int/lit8'          : (EXPR, RemIntLit8),
    'and-int/lit8'          : (EXPR, AndIntLit8),
    'or-int/lit8'           : (EXPR, OrIntLit8),
    'xor-int/lit8'          : (EXPR, XorIntLit8),
    'shl-int/lit8'          : (EXPR, ShlIntLit8),
    'shr-int/lit8'          : (EXPR, ShrIntLit8),
    'ushr-int/lit8'         : (EXPR, UShrIntLit8)
}
