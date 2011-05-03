import sys
sys.path.append('./')

import androguard
import analysis
import struct


class Instruction(object):
    def __init__(self, args):
        self.args = args
        self.register = args[0][1]

    def set_dest_dump(self, ins):
        self.dump = ins

    def get_reg(self):
        return self.register

    def get_value(self):
        return None

    def get_type(self):
        return 'no type defined'

    def emulate(self, memory):
        print 'emulation not implemented for this instruction.'


# nop
class Nop(Instruction):
    def __init__(self, args):
        print 'Nop', args

    def get_reg(self):
        print 'Nop has no dest register'

    def get_value(self):
        return ''


# move vA, vB ( 4b, 4b )
class Move(Instruction):
    def __init__(self, args):
        print 'Move', args
        super(Move, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        print 'value :', self.source, '(', self.source.get_value(), ')'

    def get_value(self):
        return self.source.get_value()


# move/from16 vAA, vBBBB ( 8b, 16b )
class MoveFrom16(Instruction):
    def __init__(self, args):
        print 'MoveFrom16', args
        super(MoveFrom16, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.value = memory[self.source].get_content()
        print 'value :', self.value

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
        print 'MoveWideFrom16 :', args
        super(MoveWideFrom16, self).__init__(args)


# move-wide/16 vAAAA, vBBBB ( 16b, 16b )
class MoveWide16(Instruction):
    pass


# move-object vA, vB ( 4b, 4b )
class MoveObject(Instruction):
    def __init__(self, args):
        print 'MoveObject', args
        super(MoveObject, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.value = memory[self.source].get_content()
        print 'value :', self.value

    def get_value(self):
        return self.value.get_value()


# move-object/from16 vAA, vBBBB ( 8b, 16b )
class MoveObjectFrom16(Instruction):
    def __init__(self, args):
        print 'MoveObjectFrom16 :', args
        super(MoveObjectFrom16, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        # FIXME ? : vBBBB peut addresser 64k registres max, et vAA 256 max
        self.value = memory[self.source].get_content()
        print 'value :', self.value

    def get_value(self):
        return self.value.get_value()


# move-object/16 vAAAA, vBBBB ( 16b, 16b )
class MoveObject16(Instruction):
    pass


# move-result vAA ( 8b )
class MoveResult(Instruction):
    def __init__(self, args):
        print 'MoveResult :', args
        super(MoveResult, self).__init__(args)

    def emulate(self, memory):
        self.value = memory['heap']
        memory['heap'] = None
        print 'value ::', self.value

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
        print 'MoveResultObject :', args
        super(MoveResultObject, self).__init__(args)

    def emulate(self, memory):
        self.value = memory.get('heap')
        memory['heap'] = None
        print 'value ::', self.value

    def get_value(self):
        if self.value is not None:
            return self.value.get_value()

    def __str__(self):
        return 'MoveResObj in v' + str(self.register)


# move-exception vAA ( 8b )
class MoveException(Instruction):
    def __init__(self, args):
        print 'MoveException :', args
        super(MoveException, self).__init__(args)


# return-void
class ReturnVoid(Instruction):
    def __init__(self, args):
        print 'ReturnVoid'

    def get_reg(self):
        print 'ReturnVoid has no dest register'

    def emulate(self, memory):
        heap = memory.get('heap')
        if heap:
            self.dump.append(heap.get_value())
            memory['heap'] = None
        self.dump.append('return')

    def __str__(self):
        return 'Return'


# return vAA ( 8b )
class Return(Instruction):
    def __init__(self, args):
        print 'Return :', args
        self.returnRegister = args[0][1]

    def get_reg(self):
        print 'Return has no dest register'

    def emulate(self, memory):
        self.returnValue = memory[self.returnRegister]
        ins = 'return %s' % self.returnValue.get_content().get_value()
        self.dump.append(ins)

    def __str__(self):
        return 'Return (%s)' % str(self.returnValue)


# return-wide vAA ( 8b )
class ReturnWide(Instruction):
    pass


# return-object vAA ( 8b )
class ReturnObject(Instruction):
    pass


# const/4 vA, #+B ( 4b, 4b )
class Const4(Instruction):
    def __init__(self, args):
        print 'Const4 :', args
        super(Const4, self).__init__(args)
        self.value = int(args[1][1])
        self.type = 'I'
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'Const4 : %s' % str(self.value)


# const/16 vAA, #+BBBB ( 8b, 16b )
class Const16(Instruction):
    def __init__(self, args):
        print 'Const16 :', args
        super(Const16, self).__init__(args)
        self.value = int(args[1][1])
        self.type = 'I'
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'Const16 : %s' % str(self.value)


# const vAA, #+BBBBBBBB ( 8b, 32b )
class Const(Instruction):
    def __init__(self, args):
        print 'Const :', args
        super(Const, self).__init__(args)
        val = ((0xFFFF & args[2][1]) << 16) | ((0xFFFF & args[1][1]))
        self.value = struct.unpack('f', struct.pack('L', val))[0]
        self.type = 'I'
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'Const : ' + str(self.value)


# const/high16 vAA, #+BBBB0000 ( 8b, 16b )
class ConstHigh16(Instruction):
    def __init__(self, args):
        print 'ConstHigh16 :', args
        super(ConstHigh16, self).__init__(args)
        self.value = struct.unpack('f', struct.pack('i', args[1][1]))[0]
        self.type = 'F'
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'ConstHigh16 : %s' % str(self.value)


# const-wide/16 vAA, #+BBBB ( 8b, 16b )
class ConstWide16(Instruction):
    def __init__(self, args):
        print 'ConstWide16 :', args
        super(ConstWide16, self).__init__(args)
        self.type = 'J'
        self.value = struct.unpack('d', struct.pack('d', args[1][1]))[0]
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'Constwide16 : %s' % str(self.value)


# const-wide/32 vAA, #+BBBBBBBB ( 8b, 32b )
class ConstWide32(Instruction):
    def __init__(self, args):
        print 'ConstWide32 :', args
        super(ConstWide32, self).__init__(args)
        self.type = 'J'
        val = ((0xFFFF & args[2][1]) << 16) | ((0xFFFF & args[1][1]))
        self.value = struct.unpack('d', struct.pack('d', val))[0]
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'Constwide32 : %s' % str(self.value)


# const-wide vAA, #+BBBBBBBBBBBBBBBB ( 8b, 64b )
class ConstWide(Instruction):
    def __init__(self, args):
        print 'ConstWide :', args
        super(ConstWide, self).__init__(args)
        val = args[1:]
        val = (0xFFFF & val[0][1]) | ((0xFFFF & val[1][1]) << 16) | (\
              (0xFFFF & val[2][1]) << 32) | ((0xFFFF & val[3][1]) << 48)
        self.type = 'D'
        self.value = struct.unpack('d', struct.pack('Q', val))[0]
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'ConstWide : %s' % str(self.value)


# const-wide/high16 vAA, #+BBBB000000000000 ( 8b, 16b )
class ConstWideHigh16(Instruction):
    def __init__(self, args):
        print 'ConstWideHigh16 :', args
        super(ConstWideHigh16, self).__init__(args)
        self.value = struct.unpack('d', struct.pack('q', int(args[1][1])))[0]
        self.type = 'D'
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

    def getType(self):
        return self.type

    def __str__(self):
        return 'ConstWide : %s' % str(self.value)


# const-string vAA ( 8b )
class ConstString(Instruction):
    def __init__(self, args):
        print 'ConstString :', args
        super(ConstString, self).__init__(args)
        self.value = '"%s"' % args[1][2]
        print '==>', self.value

    def emulate(self, memory):
        pass

    def get_value(self):
        return self.value

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
    pass


# monitor-exit vAA ( 8b )
class MonitorExit(Instruction):
    pass


# check-cast vAA ( 8b )
class CheckCast(Instruction):
    pass


# instance-of vA, vB ( 4b, 4b )
class InstanceOf(Instruction):
    pass


# array-length vA, vB ( 4b, 4b )
class ArrayLength(Instruction):
    pass


# new-instance vAA ( 8b )
class NewInstance(Instruction):
    def __init__(self, args):
        print 'NewInstance :', args
        super(NewInstance, self).__init__(args)
        self.type = args[1][2]

    def emulate(self, memory):
        self.ins = 'new'  # %s()' % ( self.type[1:-1].replace( '/', '.' ) )

    def get_value(self):
        return self.ins

    def getType(self):
        return self.type

    def __str__(self):
        return 'New ( %s )' % self.type


# new-array vA, vB ( 8b, size )
class NewArray(Instruction):
    def __init__(self, args):
        print 'NewArray :', args
        super(NewArray, self).__init__(args)


# filled-new-array {vD, vE, vF, vG, vA} ( 4b each )
class FilledNewArray(Instruction):
    pass


# filled-new-array/range {vCCCC..vNNNN} ( 16b )
class FilledNewArrayRange(Instruction):
    pass


# fill-array-data vAA, +BBBBBBBB ( 8b, 32b )
class FillArrayData(Instruction):
    def __init__(self, args):
        print 'FillArrayData :', args
        self.data = args

    def get_reg(self):
        print 'FillArrayData has no dest register.'


# throw vAA ( 8b )
class Throw(Instruction):
    pass


# goto +AA ( 8b )
class Goto(Instruction):
    def __init__(self, args):
        print 'Goto :', args
        super(Goto, self).__init__(args)

    def get_reg(self):
        print 'Goto has no dest register'


# goto/16 +AAAA ( 16b )
class Goto16(Instruction):
    pass


# goto/32 +AAAAAAAA ( 32b )
class Goto32(Instruction):
    pass


# packed-switch vAA, +BBBBBBBB ( reg to test, 32b )
class PackedSwitch(Instruction):
    def __init__(self, args):
        print 'PackedSwitch :', args
        #super(PackedSwitch, self).__init__(args)

    def get_reg(self):
        print 'PackedSwitch has no dest register.'


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
    pass


# cmp-long ( 8b, 8b, 8b )
class CmpLong(Instruction):
    pass


# if-eq vA, vB, +CCCC ( 4b, 4b, 16b )
class IfEq(Instruction):
    pass


# if-ne vA, vB, +CCCC ( 4b, 4b, 16b )
class IfNe(Instruction):
    pass


# if-lt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLt(Instruction):
    def __init__(self, args):
        print 'IfLt :', args
        self.test = int(args[0][1])
        self.branch = int(args[1][1])

    def emulate(self, memory):
        self.test = memory[self.test].get_content()
        # FIXME : creation de blocks (pile?)

    def get_value(self):
        # FIXME if / while / for... ?
        return '%s' % self.test.get_value()

    def get_reg(self):
        print 'IfLt has no dest register'

    def __str__(self):
        return 'IfLt...'


# if-ge vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGe(Instruction):
    def __init__(self, args):
        print 'IfGe :', args
        self.firstTest = int(args[0][1])
        self.secondTest = int(args[1][1])
        self.branch = int(args[2][1])

    def get_reg(self):
        print 'IfGe has no dest register'

    def __str__(self):
        return 'IfGe...'


# if-gt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGt(Instruction):
    pass


# if-le vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLe(Instruction):
    pass


# if-eqz vAA, +BBBB ( 8b, 16b )
class IfEqz(Instruction):
    pass


# if-nez vAA, +BBBB ( 8b, 16b )
class IfNez(Instruction):
    def __init__(self, args):
        print 'IfNez :', args
        self.test = int(args[0][1])
        self.branch = int(args[1][1])

    def get_reg(self):
        print 'IfNez has no dest register'

    def __str__(self):
        return 'IfNez...'


# if-ltz vAA, +BBBB ( 8b, 16b )
class IfLtz(Instruction):
    pass


# if-gez vAA, +BBBB ( 8b, 16b )
class IfGez(Instruction):
    pass


# if-gtz vAA, +BBBB ( 8b, 16b )
class IfGtz(Instruction):
    pass


# if-lez vAA, +BBBB (8b, 16b )
class IfLez(Instruction):
    def __init__(self, args):
        print 'IfLez :', args
        super(IfLez, self).__init__(args)


# aget vAA, vBB, vCC ( 8b, 8b, 8b )
class AGet(Instruction):
    pass


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
        print 'APut :', args
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
    pass


# aput-char vAA, vBB, vCC ( 8b, 8b, 8b )
class APutChar(Instruction):
    pass


# aput-short vAA, vBB, vCC ( 8b, 8b, 8b )
class APutShort(Instruction):
    pass


# iget vA, vB ( 4b, 4b )
class IGet(Instruction):
    def __init__(self, args):
        print 'IGet :', args
        super(IGet, self).__init__(args)
        self.location = args[-1][2]
        self.type = args[-1][3]
        self.name = args[-1][4]
        self.retType = args[-1][-1]
        self.objreg = args[1][1]

    def emulate(self, memory):
        self.obj = memory[self.objreg].get_content()
        self.ins = '%s.%s'
        print 'Ins : %s' % self.ins

    def getType(self):
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
    pass


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
        print 'IPut', args
        #super(IPut, self).__init__(args)
        self.src = int(args[0][1])
        self.dest = int(args[1][1])
        self.location = args[2][2]  # [1:-1].replace( '/', '.' )
        self.type = args[2][3][1:-1].replace('/', '.')
        self.name = args[2][4]

    def emulate(self, memory):
        self.src = memory[self.src].get_content()
        self.dest = memory[self.dest].get_content()
        # FIXME ?
        self.dump.append('%s.%s = %s' % (self.dest.get_value(), self.name,
        self.src.get_value()))

    def get_reg(self):
        print 'IPut has no dest register.'

#    def get_value(self):
#        return '%s.%s = %s' % ( self.dest.get_value(), self.name,
#        self.src.get_value() )

    def getName(self):
        return self.name


# iput-wide vA, vB ( 4b, 4b )
class IPutWide(Instruction):
    pass


# iput-object vA, vB ( 4b, 4b )
class IPutObject(Instruction):
    pass


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
        print 'SGetObject :', args
        super(SGetObject, self).__init__(args)
        location = args[1][2][1:-1]
        if 'java/lang' in location:
            self.location = location.split('/')[-1]
        else:
            self.location = location.replace('/', '.')
        self.type = args[1][3][1:-1].replace('/', '.')
        self.name = args[1][4]

    def emulate(self, memory):
        pass

    def getType(self):
        return self.type

    def get_value(self):
        if self.location:
            return '%s.%s' % (self.location, self.name)
        return self.name

    def getName(self):
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
        print 'InvokeVirtual :', args
        super(InvokeVirtual, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        print 'Parameters =', self.params
        self.type = args[-1][2]
        self.paramsType = args[-1][3]
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        params = []
        for param in self.params:
            print 'param : ', param, '=',
            memory[param].get_content().get_value(), 'str :',
            print str(memory[param].get_content().get_value())
            params.append(memory[param].get_content())
        self.base = memory[self.register].get_content()
        self.params = params
        if self.base.get_value() == 'this':
            self.ins = '%s(%s)'
        else:
            self.ins = '%s.%s(%s)'
        print 'Ins :: %s' % self.ins

    def get_value(self):
        if self.base.get_value() == 'this':
            return self.ins % (self.methCalled, ', '.join([str(
            param.get_value()) for param in self.params]))
        return self.ins % (self.base.get_value(), self.methCalled, ', '.join([
        str(param.get_value()) for param in self.params]))

    def get_reg(self):
        print 'InvokeVirtual has no dest register.'

    def __str__(self):
        return 'InvokeVirtual (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-super {vD, vE, vF, vG, vA} ( 4b each )
class InvokeSuper(Instruction):
    def __init__(self, args):
        print 'InvokeSuper :', args
        super(InvokeSuper, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        self.type = args[-1][2]
        self.paramsType = args[-1][3]
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        params = []
        for param in self.params:
            print 'param : ', memory[param].get_content().get_value(), 'str :',
            print str(memory[param].get_content().get_value())
            params.append(memory[param].get_content())
        self.params = params
        #self.base = memory[self.register].get_content() # <-- this
        self.ins = 'super.%s(%s)'
        print 'Ins :: %s' % self.ins

    def get_value(self):
        return self.ins % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_reg(self):
        print 'InvokeSuper has no dest register.'

    def __str__(self):
        return 'InvokeSuper (%s) %s (%s ; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-direct {vD, vE, vF, vG, vA} ( 4b each )
class InvokeDirect(Instruction):
    def __init__(self, args):
        print 'InvokeDirect :', args
        super(InvokeDirect, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        type = args[-1][2][1:-1]
        if 'java/lang' in type:
            self.type = type.split('/')[-1]
        else:
            self.type = type.replace('/', '.')
#        self.paramsType = args[-1][3][1:-1].split()
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        self.base = memory[self.register].get_content()
        if self.base.get_value() == 'this':
            self.ins = None
            return
        params = []
        for param in self.params:
            print 'param : ', memory[param].get_content().get_value(), 'str :',
            print str(memory[param].get_content().get_value())
            params.append(memory[param].get_content())
        self.params = params
        self.ins = '%s %s(%s)'
#        self.ins = '%s %s( %s )' % (self.ins, self.type, ', '.join(params))
#        print 'Ins : %s' % self.ins

    def get_value(self):
        if self.ins is None:
            return self.base.get_value()
        return self.ins % (self.base.get_value(), self.type, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def __str__(self):
        return 'InvokeDirect (%s) %s (%s)' % (self.returnType,
                self.methCalled, str(self.params))  #str(self.paramsType), str(self.params))


# invoke-static {vD, vE, vF, vG, vA} ( 4b each )
class InvokeStatic(Instruction):
    def __init__(self, args):
        print 'InvokeStatic :', args
        if len(args) > 1:
            self.params = [int(i[1]) for i in args[0:-1]]
        else:
            self.params = []
        print 'Parameters =', self.params
        self.type = args[-1][2][1:-1].replace('/', '.')
        self.paramsType = args[-1][3]
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        params = []
        for param in self.params:
            print 'param : ', param, '--',
            memory[param].get_content().get_value(), 'str :',
            print str(memory[param].get_content().get_value())
            params.append(memory[param].get_content())
        self.params = params
        self.ins = '%s.%s(%s)'
        print 'Ins :: %s' % self.ins

    def get_value(self):
        return self.ins % (self.type, self.methCalled, ', '.join([
            str(param.get_value()) for param in self.params]))

    def get_reg(self):
        print 'InvokeStatic has no dest register.'

    def __str__(self):
        return 'InvokeStatic (%s) %s (%s ; %s)' % (self.returnType,
                 self.methCalled, self.paramsType, str(self.params))


# invoke-interface {vD, vE, vF, vG, vA} ( 4b each )
class InvokeInterface(Instruction):
    pass


# invoke-virtual/range {vCCCC..vNNNN} ( 16b each )
class InvokeVirtualRange(Instruction):
    def __init__(self, args):
        print 'InvokeVirtualRange :', args
        super(InvokeVirtualRange, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        self.type = args[-1][2]
        self.paramsType = args[-1][3]
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        memory['heap'] = self
        params = []
        for param in self.params:
            print 'param : ', memory[param].get_content().get_value(), 'str :',
            print str(memory[param].get_content().get_value())
            params.append(memory[param].get_content())
        self.params = params
        self.base = memory[self.register].get_content()
        if self.base.get_value() == 'this':
            self.ins = '%s(%s)'
        else:
            self.ins = '%s.%s(%s)'
        print 'Ins :: %s' % self.ins

    def get_value(self):
        if self.base.get_value() == 'this':
            return self.ins % (self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))
        return self.ins % (self.base.get_value(), self.methCalled, ', '.join(
            [str(param.get_value()) for param in self.params]))

    def get_reg(self):
        print 'InvokeVirtual has no dest register.'

    def __str__(self):
        return 'InvokeVirtualRange (%s) %s (%s; %s)' % (self.returnType,
                self.methCalled, self.paramsType, str(self.params))


# invoke-super/range {vCCCC..vNNNN} ( 16b each )
class InvokeSuperRange(Instruction):
    pass


# invoke-direct/range {vCCCC..vNNNN} ( 16b each )
class InvokeDirectRange(Instruction):
    def __init__(self, args):
        print 'InvokeDirectRange :', args
        super(InvokeDirectRange, self).__init__(args)
        self.params = [int(i[1]) for i in args[1:-1]]
        self.type = args[-1][2][1:-1].replace('/', '.')
        self.paramsType = args[-1][3][1:-1].split()
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate(self, memory):
        self.base = memory[self.register].get_content()
        params = []
        for param in self.params:
            print 'param : ', memory[param].get_content().get_value(), 'str :',
            print str(memory[param].get_content().get_value())
            params.append(memory[param].get_content())
        self.params = params
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
    pass


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
    pass


# int-to-float vA, vB ( 4b, 4b )
class IntToFloat(Instruction):
    pass


# int-to-double vA, vB ( 4b, 4b )
class IntToDouble(Instruction):
    def __init__(self, args):
        print 'IntToDouble :', args
        super(IntToDouble, self).__init__(args)


# long-to-int vA, vB ( 4b, 4b )
class LongToInt(Instruction):
    pass


# long-to-float vA, vB ( 4b, 4b )
class LongToFloat(Instruction):
    pass


# long-to-double vA, vB ( 4b, 4b )
class LongToDouble(Instruction):
    pass


# float-to-int vA, vB ( 4b, 4b )
class FloatToInt(Instruction):
    pass


# float-to-long vA, vB ( 4b, 4b )
class FloatToLong(Instruction):
    pass


# float-to-double vA, vB ( 4b, 4b )
class FloatToDouble(Instruction):
    def __init__(self, args):
        print 'FloatToDouble :', args
        super(FloatToDouble, self).__init__(args)


# double-to-int vA, vB ( 4b, 4b )
class DoubleToInt(Instruction):
    pass


# double-to-long vA, vB ( 4b, 4b )
class DoubleToLong(Instruction):
    pass


# double-to-float vA, vB ( 4b, 4b )
class DoubleToFloat(Instruction):
    pass


# int-to-byte vA, vB ( 4b, 4b )
class IntToByte(Instruction):
    pass


# int-to-char vA, vB ( 4b, 4b )
class IntToChar(Instruction):
    pass


# int-to-short vA, vB ( 4b, 4b )
class IntToShort(Instruction):
    pass


# add-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AddInt(Instruction):
    def __init__(self, args):
        print 'AddInt :', args
        super(AddInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
#        try :
#            source1 = int(self.source1.get_value())
#            source2 = int(self.source2.get_value())
#            self.ins = '%s' % (source1 + source2)
#        except :
#            self.ins = '%s + %s'
        self.ins = '%s + %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
#        if self.ins.isdigit():
#            return self.ins
        return '%s + %s' % (self.source1.get_value(), self.source2.get_value())
        #  [ self.source1, self.source2 ]


# sub-int vAA, vBB, vCC ( 8b, 8b, 8b )
class SubInt(Instruction):
    def __init__(self, args):
        print 'SubInt :', args
        super(SubInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
#        try :
#            source1 = int(self.source1.get_value())
#            source2 = int(self.source2.get_value())
#            self.ins = '%s' % (source1 - source2)
#        except :
#            self.ins = '%s - %s'
        self.ins = '%s - %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
#        if self.ins.isdigit():
#            return self.ins
        return self.ins % (self.source1.get_value(), self.source2.get_value())


# mul-int vAA, vBB, vCC ( 8b, 8b, 8b )
class MulInt(Instruction):
    def __init__(self, args):
        print 'MulInt :', args
        super(MulInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
#        try :
#            source1 = int(self.source1.get_value())
#            source2 = int(self.source2.get_value())
#            self.ins = '%s' % (source1 * source2)
#        except :
#            self.ins = '%s * %s'
        self.ins = '%s * %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
#        if self.ins.isdigit():
#            return self.ins
        return self.ins % (self.source1.get_value(), self.source2.get_value())


# div-int vAA, vBB, vCC ( 8b, 8b, 8b )
class DivInt(Instruction):
    def __init__(self, args):
        print 'DivInt :', args
        super(DivInt, self).__init__(args)
        self.source1 = int(args[1][1])
        self.source2 = int(args[2][1])

    def emulate(self, memory):
        self.source1 = memory[self.source1].get_content()
        self.source2 = memory[self.source2].get_content()
#        try :
#            source1 = int(self.source1.get_value())
#            source2 = int(self.source2.get_value())
#            self.ins = '%s' % (source1 / float(source2))
#        except :
#            self.ins = '%s / %s'
        self.ins = '%s / %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
#        if self.ins.isdigit():
#            return self.ins
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
        print 'AddDouble :', args
        super(AddDouble, self).__init__(args)


# sub-double vAA, vBB, vCC ( 8b, 8b, 8b )
class SubDouble(Instruction):
    def __init__(self, args):
        print 'SubDouble :', args
        super(SubDouble, self).__init__(args)


# mul-double vAA, vBB, vCC ( 8b, 8b, 8b )
class MulDouble(Instruction):
    def __init__(self, args):
        print 'MulDouble :', args
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
        print 'AddInt2Addr :', args
        super(AddInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
    #self.ins = '%s + %s' % (memory[self.register].get_content().get_value(),
    #memory[self.source].get_content().get_value() )
    #print 'Ins : %s' % self.ins
        self.op1 = memory[self.register].get_content()
        self.op2 = memory[self.source].get_content()
        self.ins = '%s + %s'

    def get_value(self):
        #return self.ins
        return '%s + %s' % (self.op1.get_value(), self.op2.get_value())


# sub-int/2addr vA, vB ( 4b, 4b )
class SubInt2Addr(Instruction):
    def __init__(self, args):
        print 'SubInt2Addr :', args
        super(SubInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s - %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# mul-int/2addr vA, vB ( 4b, 4b )
class MulInt2Addr(Instruction):
    def __init__(self, args):
        print 'MulInt2Addr :', args
        super(MulInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s * %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# div-int/2addr vA, vB ( 4b, 4b )
class DivInt2Addr(Instruction):
    def __init__(self, args):
        print 'DivInt2Addr :', args
        super(DivInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s / %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# rem-int/2addr vA, vB ( 4b, 4b )
class RemInt2Addr(Instruction):
    def __init__(self, args):
        print 'RemInt2Addr :', args
        super(RemInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s %% %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# and-int/2addr vA, vB ( 4b, 4b )
class AndInt2Addr(Instruction):
    def __init__(self, args):
        print 'AndInt2Addr :', args
        super(AndInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s & %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# or-int/2addr vA, vB ( 4b, 4b )
class OrInt2Addr(Instruction):
    def __init__(self, args):
        print 'OrInt2Addr :', args
        super(OrInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s | %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# xor-int/2addr vA, vB ( 4b, 4b )
class XorInt2Addr(Instruction):
    def __init__(self, args):
        print 'XorInt2Addr :', args
        super(XorInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s ^ %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shl-int/2addr vA, vB ( 4b, 4b )
class ShlInt2Addr(Instruction):
    def __init__(self, args):
        print 'ShlInt2Addr :', args
        super(ShlInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s << ( %s & 0x1f )'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shr-int/2addr vA, vB ( 4b, 4b )
class ShrInt2Addr(Instruction):
    def __init__(self, args):
        print 'ShrInt2Addr :', args
        super(ShrInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s >> ( %s & 0x1f )'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# ushr-int/2addr vA, vB ( 4b, 4b )
class UShrInt2Addr(Instruction):
    def __init__(self, args):
        print 'UShrInt2Addr :', args
        super(UShrInt2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s >> ( %s & 0x1f )'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# add-long/2addr vA, vB ( 4b, 4b )
class AddLong2Addr(Instruction):
    def __init__(self, args):
        print 'AddLong2Addr :', args
        super(AddLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s + %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# sub-long/2addr vA, vB ( 4b, 4b )
class SubLong2Addr(Instruction):
    def __init__(self, args):
        print 'SubLong2Addr :', args
        super(SubLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s - %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# mul-long/2addr vA, vB ( 4b, 4b )
class MulLong2Addr(Instruction):
    def __init__(self, args):
        print 'MulLong2Addr :', args
        super(MulLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s * %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# div-long/2addr vA, vB ( 4b, 4b )
class DivLong2Addr(Instruction):
    def __init__(self, args):
        print 'DivLong2Addr :', args
        super(DivLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s / %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# rem-long/2addr vA, vB ( 4b, 4b )
class RemLong2Addr(Instruction):
    def __init__(self, args):
        print 'RemLong2Addr :', args
        super(RemLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s %% %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# and-long/2addr vA, vB ( 4b, 4b )
class AndLong2Addr(Instruction):
    def __init__(self, args):
        print 'AddLong2Addr :', args
        super(AndLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s & %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# or-long/2addr vA, vB ( 4b, 4b )
class OrLong2Addr(Instruction):
    def __init__(self, args):
        print 'OrLong2Addr :', args
        super(OrLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s | %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# xor-long/2addr vA, vB ( 4b, 4b )
class XorLong2Addr(Instruction):
    def __init__(self, args):
        print 'XorLong2Addr :', args
        super(XorLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s ^ %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shl-long/2addr vA, vB ( 4b, 4b )
class ShlLong2Addr(Instruction):
    def __init__(self, args):
        print 'ShlLong2Addr :', args
        super(ShlLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s << ( %s & 0x1f )'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# shr-long/2addr vA, vB ( 4b, 4b )
class ShrLong2Addr(Instruction):
    def __init__(self, args):
        print 'ShrLong2Addr :', args
        super(ShrLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s >> ( %s & 0x1f )'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# ushr-long/2addr vA, vB ( 4b, 4b )
class UShrLong2Addr(Instruction):
    def __init__(self, args):
        print 'UShrLong2Addr :', args
        super(UShrLong2Addr, self).__init__(args)
        self.source = int(args[1][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.dest = memory[self.register].get_content()
        self.ins = '%s >> ( %s & 0x1f )'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.dest.get_value(), self.source.get_value())


# add-float/2addr vA, vB ( 4b, 4b )
class AddFloat2Addr(Instruction):
    pass


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
        print 'MulIntLit16 :', args
        super(MulIntLit16, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.ins = '%s * %s' % (memory[self.source].get_content().get_value(),
        self.const)
        print 'Ins : %s' % self.ins

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
        print 'AddIntLit8 :', args
        super(AddIntLit8, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '%s + %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.source.get_value(), self.const)


# rsub-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RSubIntLit8(Instruction):
    pass


# mul-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class MulIntLit8(Instruction):
    def __init__(self, args):
        print 'MulIntLit8 :', args
        super(MulIntLit8, self).__init__(args)
        self.source = int(args[1][1])
        self.const = int(args[2][1])

    def emulate(self, memory):
        self.source = memory[self.source].get_content()
        self.ins = '%s * %s'
        print 'Ins : %s' % self.ins

    def get_value(self):
        return self.ins % (self.source.get_value(), self.const)


# div-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class DivIntLit8(Instruction):
    pass


# rem-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RemIntLit8(Instruction):
    pass


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


class This():
    def __init__(self, cls):
        self.cls = cls

    def get_content(self):
        return self

    def set_field(self, field, value):
        if self.cls.fields.get(field) is None:
            print 'Error, field %s does not exist. (value : %s).' % (field,
            value)
            return
        self.cls.fields[field] = value

    def get_field(self, field):
        res = self.cls.fields.get(field)
        if res is None:
            print 'Error, field %s does not exist.' % field
        return res

    def get_value(self):
        return 'this'


class Param():
    def __init__(self, name):
        self.name = name

    def get_content(self):
        return self

    def get_value(self):
        return self.name

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

TYPE_DESCRIPTOR = {
    'V': 'void',
    'Z': 'boolean',
    'B': 'byte',
    'S': 'short',
    'C': 'char',
    'I': 'int',
    'J': 'long',
    'F': 'float',
    'D': 'double'
}

ACCESS_FLAGS_CLASSES = {
    0x1   : 'public', #'ACC_PUBLIC',
    0x2   : 'private', #'ACC_PRIVATE',
    0x4   : 'protected', #'ACC_PROTECTED',
    0x8   : 'static', #'ACC_STATIC',
    0x10  : 'final', #'ACC_FINAL',
    0x200 : 'intefface', #'ACC_INTERFACE',
    0x400 : 'abstract', #'ACC_ABSTRACT',
    0x1000: 'synthetic', #'ACC_SYNTHETIC',
    0x2000: 'annotation', #'ACC_ANNOTATION',
    0x4000: 'enum'  #'ACC_ENUM'
}

ACCESS_FLAGS_FIELDS = {
    0x1   : 'public', #'ACC_PUBLIC',
    0x2   : 'private', #'ACC_PRIVATE',
    0x4   : 'protected', #'ACC_PROTECTED',
    0x8   : 'static', #'ACC_STATIC',
    0x10  : 'final', #'ACC_FINAL',
    0x40  : 'volatile', #'ACC_VOLATILE',
    0x80  : 'transient', #'ACC_TRANSIENT',
    0x1000: 'synthetic', #'ACC_SYNTHETIC',
    0x4000: 'enum'  #'ACC_ENUM'
}

ACCESS_FLAGS_METHODS = {
    0x1    : 'public', #'ACC_PUBLIC',
    0x2    : 'private', #'ACC_PRIVATE',
    0x4    : 'protected', #'ACC_PROTECTED',
    0x8    : 'static', #'ACC_STATIC',
    0x10   : 'final', #'ACC_FINAL',
    0x20   : 'synchronized', #'ACC_SYNCHRONIZED',
    0x40   : 'bridge', #'ACC_BRIDGE',
    0x80   : 'varargs', #'ACC_VARARGS',
    0x100  : 'native', #'ACC_NATIVE',
    0x400  : 'abstract', #'ACC_ABSTRACT',
    0x800  : 'strict', #'ACC_STRICT',
    0x1000 : 'synthetic', #'ACC_SYNTHETIC',
    0x10000: '', #'ACC_CONSTRUCTOR',
    0x20000: 'synchronized'  #'ACC_DECLARED_SYNCHRONIZED'
}


def getType(atype):
    res = TYPE_DESCRIPTOR.get(atype)
    if res is None:
        if atype[0] == 'L':
            res = atype[1:-1].replace('/', '.')
        elif atype[0] == '[':
            res = '%s[]' % getType(atype[1:])
        else:
            print 'Unknown descriptor: "%s".' % atype
    return res


class Register():
    def __init__(self, content, num):
        self.content = content
        self.used = False
        self.num = num

    def modify(self, ins):
        if self.used:
            self.dump(ins)
        self.content = ins
        self.used = False

    def get_content(self):
        self.used = True
        return self.content

    def dump(self, ins):
        print 'Register #%d Dump :' % self.num
        print '---------------'
        print 'Old value :'
        print self.content
        print '-> %s' % self.content.get_value()
        print '-------'
        print 'New value :'
        print ins
        print '-> %s' % ins.get_value()
        print '---------------'

    def __deepcopy__(self, dic=None):
        d = dic.get(self)
        if d is None:
            r = Register(self.content, self.num)
            r.used = self.used
            return r
        return d

    def __str__(self):
        return 'Register number %d :\n\tused : %s\n\tcontent : %s.' % (\
        self.num, self.used, str(self.content.get_value()))


class DvMethod():
    def __init__(self, methanalysis, this):
        self.memory = {}
        self.analysis = methanalysis
        self.method = self.analysis.get_method()
        self.name = self.method.get_name()
        if self.name == '<init>':
            self.name = self.method.get_class_name()[1:-1].split('/')[-1]
        self.basic_blocks = self.analysis.basic_blocks.bb
        code = self.method.get_code()

        access = self.method.get_access()
        self.access = []
        for flag in ACCESS_FLAGS_METHODS:
            if flag & access:
                self.access.append(flag)

        if code is None:
            self.nbregisters = 0
            self.nbparams = 0
            self.this = 0
            print 'CODE NONE :', self.name, self.method.get_class_name()
        else:
            self.nbregisters = code.registers_size.get_value()
            self.nbparams = code.ins_size.get_value()
            self.this = self.nbregisters - self.nbparams
            #print 'THIS ( %s ) : %d' % ( method.get_name(), self.this )
            self.memory[self.this] = Register(this, self.this)
            # FIXME : static method case
            for i in xrange(1, self.nbparams):
                num = self.this + i
                self.memory[num] = Register(Param('param%s' % i), num)

        self.ins = []
        self.cur = 0
        desc = self.method.get_descriptor()
        self.type = getType(desc.split(')')[-1])
        params = desc.split(')')[0][1:].split()
        if params:
            self.paramsType = [getType(param) for param in params]
        else:
            self.paramsType = None

    def process(self):
        if len(self.basic_blocks) < 1:
            return
        self.blocks = set(self.basic_blocks)
        start = self.basic_blocks[0]
        self._process_blocks(start)
        return self.debug()

    def _process_blocks(self, start):
        import copy
        self.blocks.remove(start)
        lins = start.get_ins()
        cur = 0
        while self._process_next_ins(cur, lins):
            cur += 1
            print '========================'
        print
        if len(start.childs) < 1:
            return
        savedmemory = copy.deepcopy(self.memory)
        if len(start.childs) > 1:
            for child in start.childs:
                if child[2] in self.blocks:
                    print 'restoring memory :'
                    print 'memory :', self.memory
                    self.memory = copy.deepcopy(savedmemory)
                    print 'memory :', self.memory
                    self._process_blocks(child[2])
        else:
            if start.childs[0][2] in self.blocks:
                print 'restoring memory :'
                print 'memory :', self.memory
                self.memory = copy.deepcopy(savedmemory)
                print 'memory :', self.memory
                self._process_blocks(start.childs[0][2])

    def _process_next_ins(self, cur, lins):
        if cur < len(lins):
            heap = self.memory.get('heap')
            ins = lins[cur]
            print 'Name :', ins.get_name(), 'Operands :', ins.get_operands()
            newIns = INSTRUCTION_SET.get(ins.get_name().lower())
            if newIns is None:
                print 'Unknown instruction : %s.' % ins.get_name().lower()
                return False
            newIns = newIns(ins.get_operands())
            newIns.set_dest_dump(self.ins)
            newIns.emulate(self.memory)
            regnum = newIns.get_reg()
            if regnum is not None:
                register = self.memory.get(regnum)
                if register is None:
                    self.memory[newIns.get_reg()] = Register(newIns, regnum)
                else:
                    register.modify(newIns)
            print '---> newIns : %s, register : %s.' % (ins.get_name(), regnum)
            heapaft = self.memory.get('heap')
            if heap is not None and heapaft is not None:
                print 'Append :', heap.get_value()
                self.ins.append(heap.get_value())
                if heap == heapaft:
                    print 'HEAP = ', heap
                    print 'HEAPAFT =', heapaft
                    self.memory['heap'] = None
            return True
        return False

    def debug(self, code=None):
        if code is None:
            code = []
        print 'Dump of method :'
        for j in self.memory.values():
            print j
        print
        print 'Registers :', self.memory
        print 'Dump of ins :'
        acc = []
        for i in self.access:
            if i == 0x10000:
                self.type = ''
            else:
                acc.append(ACCESS_FLAGS_METHODS.get(i))
        if self.type:
            proto = '%s %s %s(' % (' '.join(acc), self.type, self.name)
        else:
            proto = '%s %s(' % (' '.join(acc), self.name)
        if self.paramsType:
            proto += ', '.join(['%s %s' % (i, j) for (i, j) in zip(
            self.paramsType, [self.memory[self.this +
            i].get_content().get_value() for i in xrange(1, self.nbparams)])])
        proto += ') {'
        print proto
        code.append(proto)
        for i in self.ins:
            print '%s;' % i
            code.append('    %s;' % i)
        print '}'
        code.append('}')
        return '\n'.join(code)


class DvClass():
    def __init__(self, dvclass, bca):
        self.dvclass = dvclass
        self.bca = bca
        self.name = dvclass.get_name()[1:-1].split('/')[-1]
        self.package = dvclass.get_name().rsplit('/', 1)[0][1:].replace('/',
        '.')
        self.code = []
        self.this = This(self)
        lmethods = [(method.get_idx(), DvMethod(bca.get_method(method), self.this))
                    for method in dvclass.get_methods()]
        self.methods = dict(lmethods)
        print 'Class :', self.name
        print 'Methods added :'
        for index, meth in self.methods.iteritems():
            print '%s (%s, %s)' % (index, meth.method.get_class_name(),
                                   meth.name)
        print

        self.fields = {}
        for field in dvclass.get_fields():
            self.fields[field.get_name()] = field

    def select_method(self, meth):
        for method in self.methods.values():
            if method == meth:
                break
        if method != meth:
            print 'Method %s not found.' % meth.name
            return
        self.code.append(method.process())

    def show_code(self):
        for ins in self.code:
            print ins

    def __str__(self):
        return 'Class name : %s.' % self.name


class DvMachine():
    def __init__(self, name):
        vm = androguard.AndroguardS(name)
        self.vm = vm.get_vm()
        self.bca = analysis.VM_BCA(self.vm)
        ldict = [(dvclass.get_name(), DvClass(dvclass, self.bca))
                 for dvclass in self.vm.get_classes()]
        self.classes = dict(ldict)

    def get_class(self, className):
        for name, cls in self.classes.iteritems():
            if className in name:
                return cls

    def process_class(self, cls):
        if cls is None:
            print 'Error, no class to process.'
            return
        for method in cls.methods.values():
            cls.select_method(method)

    def show_code(self, cls):
        if cls is None:
            print 'Class not found.'
            return
        cls.show_code()

if __name__ == '__main__':

    TEST = 'examples/android/TestsAndroguard/bin/classes.dex'
    #TEST = '/tmp/classes.dex'

    MACHINE = DvMachine(TEST)

    from pprint import pprint
    print '==========================='
    print 'Classes :'
    pprint(MACHINE.classes)
    print '==========================='

    #CLS = raw_input('Choose a class: ')
    for CLS in MACHINE.classes:
        CLS = MACHINE.get_class(CLS)
        if CLS is None:
            print '%s not found.' % CLS
        else:
            MACHINE.process_class(CLS)

    print
    print 'Dump of code:'
    print '==========================='
    for CLS in MACHINE.classes:
        MACHINE.show_code(MACHINE.get_class(CLS))
        print '==========================='
