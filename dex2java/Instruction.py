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
    def __init__(self, name, type, size, content):
        self.name = name
        self.type = type
        self.size = size
        self.content = content
        self.used = False
        self.param = False
    
    def get_content(self):
        self.used = True
        return self.content

    def get_type(self):
        return self.type

    def get_value(self):
        if self.content:
            return self.content.get_value()
        return self.name

    def dump(self):
        if self.content.get_value().startswith('ret'):
            return self.content.get_value() + ';'
        return '%s = %s;' % (self.name, self.content.get_value())

    def decl(self):
        return '%s %s' % (self.type, self.name)
     
    def __repr__(self):
        if self.content:
            return '%s %s %s' % (self.type, self.name, self.content)
        return '%s %s' % (self.type, self.name)

    def __deepcopy__(self, dic=None):
        d = dic.get(self, None)
        if d is None:
            r = Var(self.name, self.type, self.size)
            dic[self] = r
            return r
        return d

class Variable():
    def __init__(self):
        self.nbVars = {}
        self.vars = []

    def newVar(self, type, content=None):
        n = self.nbVars.setdefault(type, 1)
        self.nbVars[type] += 1
        size = Util.get_type_size(type)
        _type = Util.get_type(type)
        if _type:
            type = _type.split('.')[-1]
        if type.endswith('[]'):
            name = '%sArray%d' % (type.strip('[]'), n)
        else:
            name = '%sVar%d' % (type, n)
        var = Var(name, type, size, content)
        self.vars.append(var)
        return var

    def startBlock(self):
        self.varscopy = copy.deepcopy(self.nbVars)

    def endBlock(self):
        self.nbVars = self.varscopy

class Instruction(object):
    def __init__(self, args):
        self.args = args
        self.register = args[0][1]

#    def set_dest_dump(self, ins):
#        self.dump = ins

    def get_reg(self):
        return [self.register]

    def get_value(self):
        return '(get_value not implemented) %s' % self

    def get_type(self):
        return '(no type defined) %s' % self

    def emulate(self, memory):
        Util.log('emulation not implemented for this instruction.', 'debug')


# nop
class Nop(Instruction):
    def __init__(self, args):
        Util.log('Nop %s' % args, 'debug')

    def get_reg(self):
        Util.log('Nop has no dest register', 'debug')

    def get_value(self):
        return ''


# move vA, vB ( 4b, 4b )
class Move(Instruction):
    def __init__(self, args):
        Util.log('Move %s' % args, 'debug')
        super(Move, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        Util.log('value : %s' % (self.source), 'debug')

    def get_type(self):
        return self.source.get_type()

    def get_value(self):
        return self.source.get_value()


# move/from16 vAA, vBBBB ( 8b, 16b )
class MoveFrom16(Instruction):
    def __init__(self, args):
        Util.log('MoveFrom16 %s' % args, 'debug')
        super(MoveFrom16, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move/16 vAAAA, vBBBB ( 16b, 16b )
class Move16(Instruction):
    pass


# move-wide vA, vB ( 4b, 4b )
class MoveWide(Instruction):
    pass


# move-wide/from16 vAA, vBBBB ( 8b, 16b )
class MoveWideFrom16(Instruction):
    def __init__(self, args):
        Util.log('MoveWideFrom16 : %s' % args, 'debug')
        super(MoveWideFrom16, self).__init__(args)


# move-wide/16 vAAAA, vBBBB ( 16b, 16b )
class MoveWide16(Instruction):
    pass


# move-object vA, vB ( 4b, 4b )
class MoveObject(Instruction):
    def __init__(self, args):
        Util.log('MoveObject %s' % args, 'debug')
        super(MoveObject, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move-object/from16 vAA, vBBBB ( 8b, 16b )
class MoveObjectFrom16(Instruction):
    def __init__(self, args):
        Util.log('MoveObjectFrom16 : %s' % args, 'debug')
        super(MoveObjectFrom16, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.value = memory[self.source].get_content()
        Util.log('value : %s' % self.value, 'debug')

    def get_type(self):
        return self.value.get_type()

    def get_value(self):
        return self.value.get_value()


# move-object/16 vAAAA, vBBBB ( 16b, 16b )
class MoveObject16(Instruction):
    pass


# move-result vAA ( 8b )
class MoveResult(Instruction):
    def __init__(self, args):
        Util.log('MoveResult : %s' % args, 'debug')
        super(MoveResult, self).__init__(args)

    def emulate(self, memory):
#        self.value = memory['heap']
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
class MoveResultWide(Instruction):
    pass


# move-result-object ( 8b )
class MoveResultObject(Instruction):
    def __init__(self, args):
        Util.log('MoveResultObject : %s' % args, 'debug')
        super(MoveResultObject, self).__init__(args)

    def emulate(self, memory):
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
class MoveException(Instruction):
    def __init__(self, args):
        Util.log('MoveException : %s' % args, 'debug')
        super(MoveException, self).__init__(args)


# return-void
class ReturnVoid(Instruction):
    def __init__(self, args):
        Util.log('ReturnVoid', 'debug')

    def get_reg(self):
        Util.log('ReturnVoid has no dest register', 'debug')

    def emulate(self, memory):
        pass
#        heap = memory.get('heap')
#        if heap:
#            self.dump.append(heap.get_value())
#            memory['heap'] = None
#        self.dump.append('return')

    def get_type(self):
        return 'V'

    def __str__(self):
        return 'Return'


# return vAA ( 8b )
class Return(Instruction):
    def __init__(self, args):
        Util.log('Return : %s' % args, 'debug')
        self.returnRegister = args[0][1]

    def get_reg(self):
        Util.log('Return has no dest register', 'debug')

    def emulate(self, memory):
        self.returnValue = memory[self.returnRegister].get_content()
        self.ins = 'return %s' % self.returnValue.name#get_value()
#        self.dump.append(ins)

    def get_type(self):
        return self.returnValue.get_type()

    def get_value(self):
        return self.ins

    def __str__(self):
        return 'Return (%s)' % str(self.returnValue)


# return-wide vAA ( 8b )
class ReturnWide(Instruction):
    pass


# return-object vAA ( 8b )
class ReturnObject(Instruction):
    def __init__(self, args):
        Util.log('ReturnObject : %s' % args, 'debug')
        self.returnRegister = args[0][1]

    def get_reg(self):
        Util.log('ReturnObject has no dest register', 'debug')

    def emulate(self, memory):
        self.returnValue = memory[self.returnRegister].get_content()
        self.ins = 'return %s' % self.returnValue.get_value()
        #self.dump.append(self.ins)

    def get_type(self):
        return self.returnValue.get_type()

    def get_value(self):
        return self.ins

    def __str__(self):
        return 'ReturnObject (%s)' % str(self.returnValue)


# const/4 vA, #+B ( 4b, 4b )
class Const4(Instruction):
    def __init__(self, args):
        Util.log('Const4 : %s' % args, 'debug')
        super(Const4, self).__init__(args)
        self.value = int(args[1][1])
        self.type = 'I'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Const4 : %s' % str(self.value)


# const/16 vAA, #+BBBB ( 8b, 16b )
class Const16(Instruction):
    def __init__(self, args):
        Util.log('Const16 : %s' % args, 'debug')
        super(Const16, self).__init__(args)
        self.value = int(args[1][1])
        self.type = 'I'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Const16 : %s' % str(self.value)


# const vAA, #+BBBBBBBB ( 8b, 32b )
class Const(Instruction):
    def __init__(self, args):
        Util.log('Const : %s' % args, 'debug')
        super(Const, self).__init__(args)
        val = ((0xFFFF & args[2][1]) << 16) | ((0xFFFF & args[1][1]))
        self.value = struct.unpack('f', struct.pack('L', val))[0]
        self.type = 'I'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Const : ' + str(self.value)


# const/high16 vAA, #+BBBB0000 ( 8b, 16b )
class ConstHigh16(Instruction):
    def __init__(self, args):
        Util.log('ConstHigh16 : %s' % args, 'debug')
        super(ConstHigh16, self).__init__(args)
        self.value = struct.unpack('f', struct.pack('i', args[1][1]))[0]
        self.type = 'F'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_type(self):
        return self.type

    def __str__(self):
        return 'ConstHigh16 : %s' % str(self.value)


# const-wide/16 vAA, #+BBBB ( 8b, 16b )
class ConstWide16(Instruction):
    def __init__(self, args):
        Util.log('ConstWide16 : %s' % args, 'debug')
        super(ConstWide16, self).__init__(args)
        self.type = 'J'
        self.value = struct.unpack('d', struct.pack('d', args[1][1]))[0]
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_reg(self):
        return [self.register, self.register + 1]

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Constwide16 : %s' % str(self.value)


# const-wide/32 vAA, #+BBBBBBBB ( 8b, 32b )
class ConstWide32(Instruction):
    def __init__(self, args):
        Util.log('ConstWide32 : %s' % args, 'debug')
        super(ConstWide32, self).__init__(args)
        self.type = 'J'
        val = ((0xFFFF & args[2][1]) << 16) | ((0xFFFF & args[1][1]))
        self.value = struct.unpack('d', struct.pack('d', val))[0]
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_reg(self):
        return [self.register, self.register + 1]

    def get_type(self):
        return self.type

    def __str__(self):
        return 'Constwide32 : %s' % str(self.value)


# const-wide vAA, #+BBBBBBBBBBBBBBBB ( 8b, 64b )
class ConstWide(Instruction):
    def __init__(self, args):
        Util.log('ConstWide : %s' % args, 'debug')
        super(ConstWide, self).__init__(args)
        val = args[1:]
        val = (0xFFFF & val[0][1]) | ((0xFFFF & val[1][1]) << 16) | (\
              (0xFFFF & val[2][1]) << 32) | ((0xFFFF & val[3][1]) << 48)
        self.type = 'D'
        self.value = struct.unpack('d', struct.pack('Q', val))[0]
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_reg(self):
        return [self.register, self.register + 1]

    def get_type(self):
        return self.type

    def __str__(self):
        return 'ConstWide : %s' % str(self.value)


# const-wide/high16 vAA, #+BBBB000000000000 ( 8b, 16b )
class ConstWideHigh16(Instruction):
    def __init__(self, args):
        Util.log('ConstWideHigh16 : %s' % args, 'debug')
        super(ConstWideHigh16, self).__init__(args)
        self.value = struct.unpack('d', struct.pack('q', int(args[1][1])))[0]
        self.type = 'D'
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_reg(self):
        return [self.register, self.register + 1]

    def get_type(self):
        return self.type

    def __str__(self):
        return 'ConstWide : %s' % str(self.value)


# const-string vAA ( 8b )
class ConstString(Instruction):
    def __init__(self, args):
        Util.log('ConstString : %s' % args, 'debug')
        super(ConstString, self).__init__(args)
        self.value = '%s' % args[1][2]
        Util.log('==> %s' % self.value, 'debug')

    def get_value(self):
        return self.value

    def get_type(self):
        #FIXME
        return 'String'

    def __str__(self):
        return self.value


# const-string/jumbo vAA ( 8b )
class ConstStringJumbo(Instruction):
    pass


# const-class vAA ( 8b )
class ConstClass(Instruction):
    pass


# monitor-enter vAA ( 8b )
class MonitorEnter(Instruction):
    def __init__(self, args):
        Util.log('MonitorEnter : %s' % args, 'debug')
        self.sync = args[0][1]

    def emulate(self, memory):
        self.sync = memory[self.sync].get_content()
        self.ins = 'synchronized( %s )'

    def get_reg(self):
        Util.log('MonitorEnter has no dest register', 'debug')

    def get_value(self):
        return self.ins % self.sync.get_value()

# monitor-exit vAA ( 8b )
class MonitorExit(Instruction):
    pass


# check-cast vAA ( 8b )
class CheckCast(Instruction):
    def __init__(self, args):
        Util.log('CheckCast: %s' % args, 'debug')
        self.type = args[0][1]

    def emulate(self, memory):
        self.type = memory[self.type].get_content().get_type()

    def get_type(self):
        print "type :", self.type
        return self.type

    def get_reg(self):
        Util.log('CheckCast has no dest register', 'debug')

# instance-of vA, vB ( 4b, 4b )
class InstanceOf(Instruction):
    pass


# array-length vA, vB ( 4b, 4b )
class ArrayLength(Instruction):
    def __init__(self, args):
        Util.log('ArrayLength: %s' % args, 'debug')
        super(ArrayLength, self).__init__(args)
        self.src = args[1][1]

    def emulate(self, memory):
        self.src = memory[self.src].get_content()
        self.ins = '%s.length'

    def get_value(self):
        return self.ins % self.src.get_value()


# new-instance vAA ( 8b )
class NewInstance(Instruction):
    def __init__(self, args):
        Util.log('NewInstance : %s' % args, 'debug')
        super(NewInstance, self).__init__(args)
        self.type = args[1][2]

    def emulate(self, memory):
        self.ins = 'new'  # %s()' % ( self.type[1:-1].replace( '/', '.' ) )

    def get_value(self):
        return self.ins

    def get_type(self):
        return self.type

    def __str__(self):
        return 'New ( %s )' % self.type


# new-array vA, vB ( 8b, size )
class NewArray(Instruction):
    def __init__(self, args):
        Util.log('NewArray : %s' % args, 'debug')
        super(NewArray, self).__init__(args)
        self.size = int(args[1][1])
        self.type = args[-1][-1]

    def emulate(self, memory):
        self.size = memory[self.size].get_content()
        self.ins = 'new %s'

    def get_value(self):
        return self.ins % Util.get_type(self.type, self.size.get_value())

    def __str__(self):
        return 'NewArray( %s )' % self.type

# filled-new-array {vD, vE, vF, vG, vA} ( 4b each )
class FilledNewArray(Instruction):
    pass


# filled-new-array/range {vCCCC..vNNNN} ( 16b )
class FilledNewArrayRange(Instruction):
    pass


# fill-array-data vAA, +BBBBBBBB ( 8b, 32b )
class FillArrayData(Instruction):
    def __init__(self, args):
        Util.log('FillArrayData : %s' % args, 'debug')
        self.data = args

    def get_reg(self):
        Util.log('FillArrayData has no dest register.', 'debug')


# throw vAA ( 8b )
class Throw(Instruction):
    pass


# goto +AA ( 8b )
class Goto(Instruction):
    def __init__(self, args):
        Util.log('Goto : %s' % args, 'debug')
        super(Goto, self).__init__(args)

    def get_reg(self):
        Util.log('Goto has no dest register', 'debug')


# goto/16 +AAAA ( 16b )
class Goto16(Instruction):
    pass


# goto/32 +AAAAAAAA ( 32b )
class Goto32(Instruction):
    pass


# packed-switch vAA, +BBBBBBBB ( reg to test, 32b )
class PackedSwitch(Instruction):
    def __init__(self, args):
        Util.log('PackedSwitch : %s' % args, 'debug')
        super(PackedSwitch, self).__init__(args)

#    def emulate(self, memory):
#        self.switch = memory[self.register].get_content()
#        self.dump.append('switch( %s )' % self.switch.get_value())

    def get_reg(self):
        Util.log('PackedSwitch has no dest register.', 'debug')


# sparse-switch vAA, +BBBBBBBB ( reg to test, 32b )
class SparseSwitch(Instruction):
    pass


# cmp-float ( 8b, 8b, 8b )
class CmplFloat(Instruction):
    pass


# cmpg-float ( 8b, 8b, 8b )
class CmpgFloat(Instruction):
    pass


# cmpl-double ( 8b, 8b, 8b )
class CmplDouble(Instruction):
    pass


# cmpg-double ( 8b, 8b, 8b )
class CmpgDouble(Instruction):
    def __init__(self, args):
        Util.log('CmpgDouble : %s' % args, 'debug')
        super(CmpgDouble, self).__init__(args)
        self.first = int(args[0][1])
        self.second = int(args[1][1])

    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def __str__(self):
        return 'CmpgDouble (%s > %s ?)' % (self.first.get_value(),
        self.second.get_value())

# cmp-long ( 8b, 8b, 8b )
class CmpLong(Instruction):
    pass


# if-eq vA, vB, +CCCC ( 4b, 4b, 16b )
class IfEq(Instruction):
    def __init__(self, args):
        Util.log('IfEq : %s' % args, 'debug')
        self.first = int(args[0][1])
        self.second = int(args[1][1])
        self.branch = int(args[2][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfEq has no dest register', 'debug')

    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfEq (%s, %s) : %s' % (self.first.get_value(),
        self.second.get_value(), self.branch)


# if-ne vA, vB, +CCCC ( 4b, 4b, 16b )
class IfNe(Instruction):
    def __init__(self, args):
        Util.log('IfNe : %s' % args, 'debug')
        self.first = int(args[0][1])
        self.second = int(args[1][1])
        self.branch = int(args[2][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfNe has no dest register', 'debug')

    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_type(self):
        return self.type

    def get_value(self):
        return '%s != %s' % (self.first.get_value(), self.second.get_value())

    def __str__(self):
        return 'IfNe (%s, %s) : %s' % (self.first.get_value(),
        self.second.get_value(), self.branch)


# if-lt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLt(Instruction):
    def __init__(self, args):
        Util.log('IfLt : %s' % args, 'debug')
        self.first = int(args[0][1])
        self.second = int(args[1][1])
        self.branch = int(args[2][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfLt has no dest register', 'debug')
    
    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfLt (%s, %s) : %s' % (self.first.get_value(),
        self.second.get_value(), self.branch)


# if-ge vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGe(Instruction):
    def __init__(self, args):
        Util.log('IfGe : %s' % args, 'debug')
        self.first = int(args[0][1])
        self.second = int(args[1][1])
        self.branch = int(args[2][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfGe has no dest register', 'debug')

    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfGe (%s, %s) : %s' % (self.first.get_value(),
        self.second.get_value(), self.branch)


# if-gt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGt(Instruction):
    def __init__(self, args):
        Util.log('IfGt : %s' % args, 'debug')
        self.first = int(args[0][1])
        self.second = int(args[1][1])
        self.branch = int(args[2][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfGt has no dest register', 'debug')

    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfGt (%s, %s) : %s' % (self.first.get_value(),
        self.second.get_value(), self.branch)


# if-le vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLe(Instruction):
    def __init__(self, args):
        Util.log('IfLe : %s' % args, 'debug')
        self.first = int(args[0][1])
        self.second = int(args[1][1])
        self.branch = int(args[2][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfLe has no dest register', 'debug')

    def emulate(self, memory):
        self.first = memory[self.first].get_content()
        self.second = memory[self.second].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfLe (%s, %s) : %s' % (self.first.get_value(),
        self.second.get_value(), self.branch)

# if-eqz vAA, +BBBB ( 8b, 16b )
class IfEqz(Instruction):
    pass


# if-nez vAA, +BBBB ( 8b, 16b )
class IfNez(Instruction):
    def __init__(self, args):
        Util.log('IfNez : %s' % args, 'debug')
        self.test = int(args[0][1])
        self.branch = int(args[1][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfNez has no dest register', 'debug')

    def emulate(self, memory):
        self.test = memory[self.test].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfNez (%s) : %s' % (self.test.get_value(), self.branch)


# if-ltz vAA, +BBBB ( 8b, 16b )
class IfLtz(Instruction):
    def __init__(self, args):
        Util.log('IfLtz : %s' % args, 'debug')
        self.test = int(args[0][1])
        self.branch = int(args[1][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfLtz has no dest register', 'debug')
    
    def emulate(self, memory):
        self.test = memory[self.test].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfLtz (%s) : %s' % (self.test.get_value(), self.branch)


# if-gez vAA, +BBBB ( 8b, 16b )
class IfGez(Instruction):
    def __init__(self, args):
        Util.log('IfGez : %s' % args, 'debug')
        self.test = int(args[0][1])
        self.branch = int(args[1][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfGez has no dest register', 'debug')
    
    def emulate(self, memory):
        self.test = memory[self.test].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfGez (%s) : %s' % (self.test.get_value(), self.branch)


# if-gtz vAA, +BBBB ( 8b, 16b )
class IfGtz(Instruction):
    def __init__(self, args):
        Util.log('IfGtz : %s' % args, 'debug')
        self.test = int(args[0][1])
        self.branch = int(args[1][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfGtz has no dest register', 'debug')
    
    def emulate(self, memory):
        self.test = memory[self.test].get_content()

    def get_type(self):
        return self.type

    def __str__(self):
        return 'IfGtz (%s) : %s' % (self.test.get_value(), self.branch)


# if-lez vAA, +BBBB (8b, 16b )
class IfLez(Instruction):
    def __init__(self, args):
        Util.log('IfLez : %s' % args, 'debug')
        self.test = int(args[0][1])
        self.branch = int(args[1][1])
        self.type = 'Z'

    def get_reg(self):
        Util.log('IfLez has no dest register', 'debug')

    def emulate(self, memory):
        self.test = memory[self.test].get_content()

    def get_type(self):
        return self.type

    def get_value(self):
        return '%s <= 0' % self.test.get_value()

    def __str__(self):
        return 'IfLez (%s) : %s' % (self.test.get_value(), self.branch)


# aget vAA, vBB, vCC ( 8b, 8b, 8b )
class AGet(Instruction):
    def __init__(self, args):
        Util.log('AGet : %s' % args, 'debug')
        super(AGet, self).__init__(args)
        self.array = int(args[1][1])
        self.index = int(args[2][1])
        
    def emulate(self, memory):
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.ins = '%s[%s]'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_value(self):
        return self.ins % (self.array.get_value(), self.index.get_value())


# aget-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetWide(Instruction):
    pass


# aget-object vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetObject(Instruction):
    pass


# aget-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetBoolean(Instruction):
    pass


# aget-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetByte(Instruction):
    pass


# aget-char vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetChar(Instruction):
    pass


# aget-short vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetShort(Instruction):
    pass


# aput vAA, vBB, vCC ( 8b, 8b, 8b )
class APut(Instruction):
    def __init__(self, args):
        Util.log('APut : %s' % args, 'debug')
        super(APut, self).__init__(args)


# aput-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class APutWide(Instruction):
    pass


# aput-object vAA, vBB, vCC ( 8b, 8b, 8b )
class APutObject(Instruction):
    pass


# aput-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class APutBoolean(Instruction):
    pass


# aput-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class APutByte(Instruction):
    def __init__(self, args):
        Util.log('APutByte : %s' % args, 'debug')
        super(APutByte, self).__init__(args)
        self.source = int(args[0][1])
        self.array = int(args[1][1])
        self.index = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.array = memory[self.array].get_content()
        self.index = memory[self.index].get_content()
        self.ins = '%s[%s] = %s'

    def get_value(self):
        ins = self.ins % (self.array.get_value(), self.index.get_value(), self.source.get_value())
        return ins

# aput-char vAA, vBB, vCC ( 8b, 8b, 8b )
class APutChar(Instruction):
    pass


# aput-short vAA, vBB, vCC ( 8b, 8b, 8b )
class APutShort(Instruction):
    pass


# iget vA, vB ( 4b, 4b )
class IGet(Instruction):
    def __init__(self, args):
        Util.log('IGet : %s' % args, 'debug')
        super(IGet, self).__init__(args)
        self.location = args[-1][2]
        self.type = args[-1][3]
        self.name = args[-1][4]
        self.retType = args[-1][-1]
        self.objreg = args[1][1]

    def emulate(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.ins = '%s.%s'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return self.type

    def get_value(self):
        return self.ins % (self.obj.get_value(), self.name)

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-wide vA, vB ( 4b, 4b )
class IGetWide(Instruction):
    pass


# iget-object vA, vB ( 4b, 4b )
class IGetObject(Instruction):
    def __init__(self, args):
        Util.log('IGetObject : %s' % args, 'debug')
        super(IGetObject, self).__init__(args)
        self.location = args[-1][2]
        self.type = args[-1][3]
        self.name = args[-1][4]
        self.retType = args[-1][-1]
        self.objreg = args[1][1]

    def emulate(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.ins = '%s.%s'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return self.type

    def get_value(self):
        return self.ins % (self.obj.get_value(), self.name)

    def __str__(self):
        return '( %s ) %s.%s' % (self.type, self.location, self.name)


# iget-boolean vA, vB ( 4b, 4b )
class IGetBoolean(Instruction):
    pass


# iget-byte vA, vB ( 4b, 4b )
class IGetByte(Instruction):
    pass


# iget-char vA, vB ( 4b, 4b )
class IGetChar(Instruction):
    pass


# iget-short vA, vB ( 4b, 4b )
class IGetShort(Instruction):
    pass


# iput vA, vB ( 4b, 4b )
class IPut(Instruction):
    def __init__(self, args):
        Util.log('IPut %s' % args, 'debug')
        self.src = int(args[0][1])
        self.dest = int(args[1][1])
        self.location = args[2][2]  # [1:-1].replace( '/', '.' )
        self.type = args[2][3] #.replace('/', '.')
        self.name = args[2][4]

    def emulate(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        # FIXME ?
#        self.dump.append('%s.%s = %s' % (self.dest.get_value(), self.name,
#        self.src.get_value()))

    def get_type(self):
        return self.type

    def get_reg(self):
        Util.log('IPut has no dest register.', 'debug')


# iput-wide vA, vB ( 4b, 4b )
class IPutWide(Instruction):
    pass


# iput-object vA, vB ( 4b, 4b )
class IPutObject(Instruction):
    def __init__(self, args):
        Util.log('IPutObject %s' % args, 'debug')
        self.src = int(args[0][1])
        self.dest = int(args[1][1])
        self.location = args[2][2]
        self.type = args[2][3] #[1:-1].replace('/', '.')
        self.name = args[2][4]

    def emulate(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        # FIXME ?
#        self.dump.append('%s.%s = %s' % (self.dest.get_value(), self.name,
#        self.src.get_value()))

    def get_type(self):
        return self.type

    def get_reg(self):
        Util.log('IPutObject has no dest register.', 'debug')


# iput-boolean vA, vB ( 4b, 4b )
class IPutBoolean(Instruction):
    pass


# iput-byte vA, vB ( 4b, 4b )
class IPutByte(Instruction):
    pass


# iput-char vA, vB ( 4b, 4b )
class IPutChar(Instruction):
    pass


# iput-short vA, vB ( 4b, 4b )
class IPutShort(Instruction):
    pass


# sget vAA ( 8b )
class SGet(Instruction):
    pass


# sget-wide vAA ( 8b )
class SGetWide(Instruction):
    pass


# sget-object vAA ( 8b )
class SGetObject(Instruction):
    def __init__(self, args):
        Util.log('SGetObject : %s' % args, 'debug')
        super(SGetObject, self).__init__(args)
        location = args[1][2][1:-1]
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = args[1][3] #[1:-1].replace('/', '.')
        self.name = args[1][4]

    def get_type(self):
        return self.type

    def get_value(self):
        if self.location:
            return '%s.%s' % (self.location, self.name)
        return self.name

    def __str__(self):
        if self.location:
            return '(%s) %s.%s' % (self.type, self.location, self.name)
        return '(%s) %s' % (self.type, self.name)


# sget-boolean vAA ( 8b )
class SGetBoolean(Instruction):
    pass


# sget-byte vAA ( 8b )
class SGetByte(Instruction):
    pass


# sget-char vAA ( 8b )
class SGetChar(Instruction):
    pass


# sget-short vAA ( 8b )
class SGetShort(Instruction):
    pass


# sput vAA ( 8b )
class SPut(Instruction):
    pass


# sput-wide vAA ( 8b )
class SPutWide(Instruction):
    pass


# sput-object vAA ( 8b )
class SPutObject(Instruction):
    pass


# sput-boolean vAA ( 8b )
class SPutBoolean(Instruction):
    pass


# sput-wide vAA ( 8b )
class SPutByte(Instruction):
    pass


# sput-char vAA ( 8b )
class SPutChar(Instruction):
    pass


# sput-short vAA ( 8b )
class SPutShort(Instruction):
    pass


# invoke-virtual {vD, vE, vF, vG, vA} ( 4b each )
class InvokeVirtual(Instruction):
    def __init__(self, args):
        Util.log('InvokeVirtual : %s' % args, 'debug')
        super(InvokeVirtual, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = args[-1][2]
        self.paramsType = Util.get_params_type(args[-1][3])
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        self.base = memory[self.register].get_content()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        if self.base.get_value() == 'this':
            self.ins = '%s(%s)'
        else:
            self.ins = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.ins, 'debug')

    def get_value(self):
        if self.base.get_value() == 'this':
            return self.ins % (self.methCalled, ', '.join([str(
            param.get_value()) for param in self.params]))
        return self.ins % (self.base.get_value(), self.methCalled, ', '.join([
        str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeVirtual has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeVirtual (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-super {vD, vE, vF, vG, vA} ( 4b each )
class InvokeSuper(Instruction):
    def __init__(self, args):
        Util.log('InvokeSuper : %s' % args, 'debug')
        super(InvokeSuper, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        self.type = args[-1][2]
        self.paramsType = Util.get_params_type(args[-1][3])
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        #self.base = memory[self.register].get_content_dbg() # <-- this
        self.ins = 'super.%s(%s)'
        Util.log('Ins :: %s' % self.ins, 'debug')

    def get_value(self):
        return self.ins % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeSuper has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeSuper (%s) %s (%s ; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-direct {vD, vE, vF, vG, vA} ( 4b each )
class InvokeDirect(Instruction):
    def __init__(self, args):
        Util.log('InvokeDirect : %s' % args, 'debug')
        super(InvokeDirect, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        type = args[-1][2][1:-1]
        if 'java/lang' in type:
            self.type = type.split('/')[-1]
        else:
            self.type = type.replace('/', '.')
        self.paramsType = Util.get_params_type(args[-1][3])
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        self.base = memory[self.register].get_content()
        if self.base.get_value() == 'this':
            self.ins = None
            return
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.ins = '%s %s(%s)'
#        self.ins = '%s %s( %s )' % (self.ins, self.type, ', '.join(params))
#        print 'Ins : %s' % self.ins

    def get_value(self):
        if self.ins is None:
            return self.base.get_value()
        return self.ins % (self.base.get_value(), self.type, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def __str__(self):
        return 'InvokeDirect (%s) %s (%s)' % (self.returnType,
                self.methCalled, str(self.params))  #str(self.paramsType), str(self.params))


# invoke-static {vD, vE, vF, vG, vA} ( 4b each )
class InvokeStatic(Instruction):
    def __init__(self, args):
        Util.log('InvokeStatic : %s' % args, 'debug')
        if len(args) > 1:
            self.params = [int(i[1]) for i in args[0:-1]]
        else:
            self.params = []
        Util.log('Parameters = %s' % self.params, 'debug')
        self.type = args[-1][2][1:-1].replace('/', '.')
        self.paramsType = Util.get_params_type(args[-1][3])
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.ins = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.ins, 'debug')

    def get_value(self):
        return self.ins % (self.type, self.methCalled, ', '.join([
            str(param.get_value()) for param in self.params]))

    def get_type(self):
        return self.returnType

    def get_reg(self):
        Util.log('InvokeStatic has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeStatic (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-interface {vD, vE, vF, vG, vA} ( 4b each )
class InvokeInterface(Instruction):
    pass


# invoke-virtual/range {vCCCC..vNNNN} ( 16b each )
class InvokeVirtualRange(Instruction):
    def __init__(self, args):
        Util.log('InvokeVirtualRange : %s' % args, 'debug')
        super(InvokeVirtualRange, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        self.type = args[-1][2]
        self.paramsType = Util.get_params_type(args[-1][3])
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.base = memory[self.register].get_content()
        if self.base.get_value() == 'this':
            self.ins = '%s(%s)'
        else:
            self.ins = '%s.%s(%s)'
        Util.log('Ins :: %s' % self.ins, 'debug')

    def get_value(self):
        if self.base.get_value() == 'this':
            return self.ins % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))
        return self.ins % (self.base.get_value(), self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_reg(self):
        Util.log('InvokeVirtual has no dest register.', 'debug')

    def __str__(self):
        return 'InvokeVirtualRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-super/range {vCCCC..vNNNN} ( 16b each )
class InvokeSuperRange(Instruction):
    pass


# invoke-direct/range {vCCCC..vNNNN} ( 16b each )
class InvokeDirectRange(Instruction):
    def __init__(self, args):
        Util.log('InvokeDirectRange : %s' % args, 'debug')
        super(InvokeDirectRange, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        self.type = args[-1][2][1:-1].replace('/', '.')
        self.paramsType = Util.get_params_type(args[-1][3])
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        self.base = memory[self.register].get_content()
        self.params = get_invoke_params(self.params, self.paramsType, memory)
        self.ins = '%s %s(%s)'

    def get_value(self):
        return self.ins % (self.base.get_value(), self.type, ', '.join(
        [str(param.get_value()) for param in self.params]))

    def __str__(self):
        return 'InvokeDirectRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, str(self.paramsType), str(self.params))


# invoke-static/range {vCCCC..vNNNN} ( 16b each )
class InvokeStaticRange(Instruction):
    pass


# invoke-interface/range {vCCCC..vNNNN} ( 16b each )
class InvokeInterfaceRange(Instruction):
    pass


# neg-int vA, vB ( 4b, 4b )
class NegInt(Instruction):
    def __init__(self, args):
        Util.log('NegInt : %s' % args, 'debug')
        super(NegInt, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '-(%s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source.get_value())


# not-int vA, vB ( 4b, 4b )
class NotInt(Instruction):
    pass


# neg-long vA, vB ( 4b, 4b )
class NegLong(Instruction):
    pass


# not-long vA, vB ( 4b, 4b )
class NotLong(Instruction):
    pass


# neg-float vA, vB ( 4b, 4b )
class NegFloat(Instruction):
    pass


# neg-double vA, vB ( 4b, 4b )
class NegDouble(Instruction):
    pass


# int-to-long vA, vB ( 4b, 4b )
class IntToLong(Instruction):
    def __init__(self, args):
        Util.log('IntToLong : %s' % args, 'debug')
        super(IntToLong, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((long) %s)' % self.source.get_value()


# int-to-float vA, vB ( 4b, 4b )
class IntToFloat(Instruction):
    def __init__(self, args):
        Util.log('IntToFloat : %s' % args, 'debug')
        super(IntToFloat, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((float) %s)' % self.source.get_value()


# int-to-double vA, vB ( 4b, 4b )
class IntToDouble(Instruction):
    def __init__(self, args):
        Util.log('IntToDouble : %s' % args, 'debug')
        super(IntToDouble, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((double) %s)' % self.source.get_value()

# long-to-int vA, vB ( 4b, 4b )
class LongToInt(Instruction):
    def __init__(self, args):
        Util.log('LongToInt : %s' % args, 'debug')
        super(LongToInt, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((int) %s)' % self.source.get_value()


# long-to-float vA, vB ( 4b, 4b )
class LongToFloat(Instruction):
    def __init__(self, args):
        Util.log('LongToFloat : %s' % args, 'debug')
        super(LongToFloat, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((float) %s)' % self.source.get_value()


# long-to-double vA, vB ( 4b, 4b )
class LongToDouble(Instruction):
    def __init__(self, args):
        Util.log('LongToDouble : %s' % args, 'debug')
        super(LongToDouble, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((double) %s)' % self.source.get_value()


# float-to-int vA, vB ( 4b, 4b )
class FloatToInt(Instruction):
    def __init__(self, args):
        Util.log('FloatToInt : %s' % args, 'debug')
        super(FloatToInt, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((int) %s)' % self.source.get_value()


# float-to-long vA, vB ( 4b, 4b )
class FloatToLong(Instruction):
    def __init__(self, args):
        Util.log('FloatToLong : %s' % args, 'debug')
        super(FloatToLong, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((long) %s)' % self.source.get_value()


# float-to-double vA, vB ( 4b, 4b )
class FloatToDouble(Instruction):
    def __init__(self, args):
        Util.log('FloatToDouble : %s' % args, 'debug')
        super(FloatToDouble, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((double) %s)' % self.source.get_value()


# double-to-int vA, vB ( 4b, 4b )
class DoubleToInt(Instruction):
    def __init__(self, args):
        super(DoubleToInt, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((int) %s)' % self.source.get_value()


# double-to-long vA, vB ( 4b, 4b )
class DoubleToLong(Instruction):
    def __init__(self, args):
        Util.log('DoubleToLong : %s' % args, 'debug')
        super(DoubleToLong, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((long) %s)' % self.source.get_value()
    pass


# double-to-float vA, vB ( 4b, 4b )
class DoubleToFloat(Instruction):
    def __init__(self, args):
        Util.log('DoubleToFloat : %s' % args, 'debug')
        super(DoubleToFloat, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((float) %s)' % self.source.get_value()


# int-to-byte vA, vB ( 4b, 4b )
class IntToByte(Instruction):
    def __init__(self, args):
        Util.log('IntToByte : %s' % args, 'debug')
        super(IntToByte, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((byte) %s)' % self.source.get_value()


# int-to-char vA, vB ( 4b, 4b )
class IntToChar(Instruction):
    def __init__(self, args):
        Util.log('IntToChar : %s' % args, 'debug')
        super(IntToChar, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()

    def get_value(self):
        return '((char) %s)' % self.source.get_value()


# int-to-short vA, vB ( 4b, 4b )
class IntToShort(Instruction):
    pass


# add-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AddInt(Instruction):
    def __init__(self, args):
        Util.log('AddInt : %s' % args, 'debug')
        super(AddInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.ins = '(%s + %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source1.get_value(), self.source2.get_value())


# sub-int vAA, vBB, vCC ( 8b, 8b, 8b )
class SubInt(Instruction):
    def __init__(self, args):
        Util.log('SubInt : %s' % args, 'debug')
        super(SubInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.ins = '(%s - %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source1.get_value(), self.source2.get_value())


# mul-int vAA, vBB, vCC ( 8b, 8b, 8b )
class MulInt(Instruction):
    def __init__(self, args):
        Util.log('MulInt : %s' % args, 'debug')
        super(MulInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.ins = '(%s * %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source1.get_value(), self.source2.get_value())


# div-int vAA, vBB, vCC ( 8b, 8b, 8b )
class DivInt(Instruction):
    def __init__(self, args):
        Util.log('DivInt : %s' % args, 'debug')
        super(DivInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
        self.ins = '(%s / %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source1.get_value(), self.source2.get_value())


# rem-int vAA, vBB, vCC ( 8b, 8b, 8b )
class RemInt(Instruction):
    pass


# and-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AndInt(Instruction):
    pass


# or-int vAA, vBB, vCC ( 8b, 8b, 8b )
class OrInt(Instruction):
    pass


# xor-int vAA, vBB, vCC ( 8b, 8b, 8b )
class XorInt(Instruction):
    pass


# shl-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlInt(Instruction):
    pass


# shr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrInt(Instruction):
    pass


# ushr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrInt(Instruction):
    pass


# add-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AddLong(Instruction):
    pass


# sub-long vAA, vBB, vCC ( 8b, 8b, 8b )
class SubLong(Instruction):
    pass


# mul-long vAA, vBB, vCC ( 8b, 8b, 8b )
class MulLong(Instruction):
    pass


# div-long vAA, vBB, vCC ( 8b, 8b, 8b )
class DivLong(Instruction):
    pass


# rem-long vAA, vBB, vCC ( 8b, 8b, 8b )
class RemLong(Instruction):
    pass


# and-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AndLong(Instruction):
    pass


# or-long vAA, vBB, vCC ( 8b, 8b, 8b )
class OrLong(Instruction):
    pass


# xor-long vAA, vBB, vCC ( 8b, 8b, 8b )
class XorLong(Instruction):
    pass


# shl-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlLong(Instruction):
    pass


# shr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrLong(Instruction):
    pass


# ushr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrLong(Instruction):
    pass


# add-float vAA, vBB, vCC ( 8b, 8b, 8b )
class AddFloat(Instruction):
    pass


# sub-float vAA, vBB, vCC ( 8b, 8b, 8b )
class SubFloat(Instruction):
    pass


# mul-float vAA, vBB, vCC ( 8b, 8b, 8b )
class MulFloat(Instruction):
    pass


# div-float vAA, vBB, vCC ( 8b, 8b, 8b )
class DivFloat(Instruction):
    pass


# rem-float vAA, vBB, vCC ( 8b, 8b, 8b )
class RemFloat(Instruction):
    pass


# add-double vAA, vBB, vCC ( 8b, 8b, 8b )
class AddDouble(Instruction):
    def __init__(self, args):
        Util.log('AddDouble : %s' % args, 'debug')
        super(AddDouble, self).__init__(args)


# sub-double vAA, vBB, vCC ( 8b, 8b, 8b )
class SubDouble(Instruction):
    def __init__(self, args):
        Util.log('SubDouble : %s' % args, 'debug')
        super(SubDouble, self).__init__(args)


# mul-double vAA, vBB, vCC ( 8b, 8b, 8b )
class MulDouble(Instruction):
    def __init__(self, args):
        Util.log('MulDouble : %s' % args, 'debug')
        super(MulDouble, self).__init__(args)


# div-double vAA, vBB, vCC ( 8b, 8b, 8b )
class DivDouble(Instruction):
    pass


# rem-double vAA, vBB, vCC ( 8b, 8b, 8b )
class RemDouble(Instruction):
    pass


# add-int/2addr vA, vB ( 4b, 4b )
class AddInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('AddInt2Addr : %s' % args, 'debug')
        super(AddInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.op1 = memory[self.register].get_content()
        self.op2 = memory[self.source].get_content()
        self.ins = '(%s + %s)'

    def get_type(self):
        return 'I'

    def get_value(self):
        return '%s + %s' % (self.op1.get_value(), self.op2.get_value())


# sub-int/2addr vA, vB ( 4b, 4b )
class SubInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('SubInt2Addr : %s' % args, 'debug')
        super(SubInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s - %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# mul-int/2addr vA, vB ( 4b, 4b )
class MulInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('MulInt2Addr : %s' % args, 'debug')
        super(MulInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s * %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# div-int/2addr vA, vB ( 4b, 4b )
class DivInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('DivInt2Addr : %s' % args, 'debug')
        super(DivInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s / %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# rem-int/2addr vA, vB ( 4b, 4b )
class RemInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('RemInt2Addr : %s' % args, 'debug')
        super(RemInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s %% %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# and-int/2addr vA, vB ( 4b, 4b )
class AndInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('AndInt2Addr : %s' % args, 'debug')
        super(AndInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s & %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# or-int/2addr vA, vB ( 4b, 4b )
class OrInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('OrInt2Addr : %s' % args, 'debug')
        super(OrInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s | %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# xor-int/2addr vA, vB ( 4b, 4b )
class XorInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('XorInt2Addr : %s' % args, 'debug')
        super(XorInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s ^ %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shl-int/2addr vA, vB ( 4b, 4b )
class ShlInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('ShlInt2Addr : %s' % args, 'debug')
        super(ShlInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s << ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shr-int/2addr vA, vB ( 4b, 4b )
class ShrInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('ShrInt2Addr : %s' % args, 'debug')
        super(ShrInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# ushr-int/2addr vA, vB ( 4b, 4b )
class UShrInt2Addr(Instruction):
    def __init__(self, args):
        Util.log('UShrInt2Addr : %s' % args, 'debug')
        super(UShrInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# add-long/2addr vA, vB ( 4b, 4b )
class AddLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('AddLong2Addr : %s' % args, 'debug')
        super(AddLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s + %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# sub-long/2addr vA, vB ( 4b, 4b )
class SubLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('SubLong2Addr : %s' % args, 'debug')
        super(SubLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s - %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# mul-long/2addr vA, vB ( 4b, 4b )
class MulLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('MulLong2Addr : %s' % args, 'debug')
        super(MulLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s * %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# div-long/2addr vA, vB ( 4b, 4b )
class DivLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('DivLong2Addr : %s' % args, 'debug')
        super(DivLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s / %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# rem-long/2addr vA, vB ( 4b, 4b )
class RemLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('RemLong2Addr : %s' % args, 'debug')
        super(RemLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s %% %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# and-long/2addr vA, vB ( 4b, 4b )
class AndLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('AddLong2Addr : %s' % args, 'debug')
        super(AndLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s & %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# or-long/2addr vA, vB ( 4b, 4b )
class OrLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('OrLong2Addr : %s' % args, 'debug')
        super(OrLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s | %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# xor-long/2addr vA, vB ( 4b, 4b )
class XorLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('XorLong2Addr : %s' % args, 'debug')
        super(XorLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s ^ %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shl-long/2addr vA, vB ( 4b, 4b )
class ShlLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('ShlLong2Addr : %s' % args, 'debug')
        super(ShlLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s << ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shr-long/2addr vA, vB ( 4b, 4b )
class ShrLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('ShrLong2Addr : %s' % args, 'debug')
        super(ShrLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# ushr-long/2addr vA, vB ( 4b, 4b )
class UShrLong2Addr(Instruction):
    def __init__(self, args):
        Util.log('UShrLong2Addr : %s' % args, 'debug')
        super(UShrLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s >> ( %s & 0x1f ))'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'J'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# add-float/2addr vA, vB ( 4b, 4b )
class AddFloat2Addr(Instruction):
    def __init__(self, args):
        Util.log('AddFloat2Addr : %s' % args, 'debug')
        super(AddFloat2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '(%s + %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'F'

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# sub-float/2addr vA, vB ( 4b, 4b )
class SubFloat2Addr(Instruction):
    pass


# mul-float/2addr vA, vB ( 4b, 4b )
class MulFloat2Addr(Instruction):
    pass


# div-float/2addr vA, vB ( 4b, 4b )
class DivFloat2Addr(Instruction):
    pass


# rem-float/2addr vA, vB ( 4b, 4b )
class RemFloat2Addr(Instruction):
    pass


# add-double/2addr vA, vB ( 4b, 4b )
class AddDouble2Addr(Instruction):
    pass


# sub-double/2addr vA, vB ( 4b, 4b )
class SubDouble2Addr(Instruction):
    pass


# mul-double/2addr vA, vB ( 4b, 4b )
class MulDouble2Addr(Instruction):
    pass


# div-double/2addr vA, vB ( 4b, 4b )
class DivDouble2Addr(Instruction):
    pass


# rem-double/2addr vA, vB ( 4b, 4b )
class RemDouble2Addr(Instruction):
    pass


# add-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AddIntLit16(Instruction):
    pass


# rsub-int vA, vB, #+CCCC ( 4b, 4b, 16b )
class RSubInt(Instruction):
    pass


# mul-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class MulIntLit16(Instruction):
    def __init__(self, args):
        Util.log('MulIntLit16 : %s' % args, 'debug')
        super(MulIntLit16, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.ins = '(%s * %s)' % (memory[self.source].get_content().get_value(),
        self.const)
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins


# div-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class DivIntLit16(Instruction):
    pass


# rem-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class RemIntLit16(Instruction):
    pass


# and-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AndIntLit16(Instruction):
    pass


# or-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class OrIntLit16(Instruction):
    pass


# xor-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class XorIntLit16(Instruction):
    pass


# add-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AddIntLit8(Instruction):
    def __init__(self, args):
        Util.log('AddIntLit8 : %s' % args, 'debug')
        super(AddIntLit8, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '(%s + %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source.get_value(), self.const)

    def __str__(self):
        return 'AddIntLit8 (%s, %s)' % (self.source, self.const)


# rsub-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RSubIntLit8(Instruction):
    pass


# mul-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class MulIntLit8(Instruction):
    def __init__(self, args):
        Util.log('MulIntLit8 : %s' % args, 'debug')
        super(MulIntLit8, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '(%s * %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source.get_value(), self.const)

    def __str__(self):
        return 'MulIntLit8 (%s, %s)' % (self.source, self.const)


# div-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class DivIntLit8(Instruction):
    def __init__(self, args):
        Util.log('DivIntLit8 : %s' % args, 'debug')
        super(DivIntLit8, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '(%s / %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source.get_value(), self.const)


# rem-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RemIntLit8(Instruction):
    def __init__(self, args):
        Util.log('RemIntLit8 : %s' % args, 'debug')
        super(RemIntLit8, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '(%s %% %s)'
        Util.log('Ins : %s' % self.ins, 'debug')

    def get_type(self):
        return 'I'

    def get_value(self):
        return self.ins % (self.source.get_value(), self.const)


# and-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AndIntLit8(Instruction):
    pass


# or-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class OrIntLit8(Instruction):
    pass


# xor-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class XorIntLit8(Instruction):
    pass


# shl-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShlIntLit8(Instruction):
    pass


# shr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShrIntLit8(Instruction):
    pass


# ushr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class UShrIntLit8(Instruction):
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
    'goto/16'               : Goto,#16,
    'goto/32'               : Goto,#32,
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
