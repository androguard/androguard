import sys
sys.path.append( './' )

import androguard
import analysis
import struct

class Instruction( ) :
    def __init__( self, args ) :
	self.args = args
        self.register = args[0][1]

    def setDestDump( self, ins ) :
        self.dump = ins

    def getReg( self ) :
        return self.register

    def getValue( self ) :
        return None

    def getType( self ) :
        return 'no type defined'

    def emulate( self, memory ) :
        print 'emulation not implemented for this instruction.'

# nop
class Nop( Instruction ) :
    def __init__( self, args ) :
        print 'Nop', args

    def getReg( self ) :
        print 'Nop has no dest register'

    def getValue( self ) :
        return ''

# move vA, vB ( 4b, 4b )
class Move( Instruction ) :
    def __init__( self, args ) :
        print 'Move', args
        Instruction.__init__( self, args )

# move/from16 vAA, vBBBB ( 8b, 16b )
class MoveFrom16( Instruction ) :
    def __init__( self, args ) :
        print 'MoveFrom16', args
        Instruction.__init__( self, args )

# move/16 vAAAA, vBBBB ( 16b, 16b )
class Move16( Instruction ) :
    pass

# move-wide vA, vB ( 4b, 4b )
class MoveWide( Instruction ) :
    pass

# move-wide/from16 vAA, vBBBB ( 8b, 16b )
class MoveWideFrom16( Instruction ) :
    def __init__( self, args ) :
        print 'MoveWideFrom16 :', args
        Instruction.__init__( self, args )

# move-wide/16 vAAAA, vBBBB ( 16b, 16b )
class MoveWide16( Instruction ) :
    pass

# move-object vA, vB ( 4b, 4b )
class MoveObject( Instruction ) :
    pass

# move-object/from16 vAA, vBBBB ( 8b, 16b )
class MoveObjectFrom16( Instruction ) :
    def __init__( self, args ) :
        print 'MoveObjectFrom16 :', args
        Instruction.__init__( self, args )

    def emulate( self, memory ) :
        # FIXME ? : vBBBB peut addresser 64k registres max, et vAA 256 max
        self.value = memory.get( 'heap' )
        memory['heap'] = None
        print 'value :', self.value

    def getValue( self ) :
        return self.value.getValue( )

# move-object/16 vAAAA, vBBBB ( 16b, 16b )
class MoveObject16( Instruction ) :
    pass

# move-result vAA ( 8b )
class MoveResult( Instruction ) :
    def __init__( self, args ) :
        print 'MoveResult :', args
        Instruction.__init__( self, args )

    def emulate( self, memory ) :
        self.value = memory['heap']
        memory['heap'] = None
        print 'value ::', self.value

    def getValue( self ) :
        return self.value.getValue( )

    def __str__( self ) :
        return 'Move res in v' + str( self.register ) 

# move-result-wide vAA ( 8b )
class MoveResultWide( Instruction ) :
    pass

# move-result-object ( 8b )
class MoveResultObject( Instruction ) :
    def __init__( self, args ) :
        print 'MoveResultObject :', args
        Instruction.__init__( self, args )

    def emulate( self, memory ) :
        self.value = memory['heap']
        memory['heap'] = None
        print 'value ::', self.value

    def getValue( self ) :
        return self.value.getValue( )

    def __str__( self ) :
        return 'MoveResObj in v' + str( self.register )

# move-exception vAA ( 8b )
class MoveException( Instruction ) :
    def __init__( self, args ) :
        print 'MoveException :', args
        Instruction.__init__( self, args )

# return-void
class ReturnVoid( Instruction ) :
    def __init__( self, args ) :
        print 'ReturnVoid'

    def getReg( self ) :
        print 'ReturnVoid has no dest register'

    def emulate( self, memory ) :
        heap = memory.get( 'heap' )
        if heap :
            self.dump.append( heap.getValue( ) )
            memory['heap'] = None
        self.dump.append( 'return' )

    def __str__( self ) :
        return 'Return'

# return vAA ( 8b )
class Return( Instruction ) :
    def __init__( self, args ) :
        print 'Return :', args
        self.returnRegister = args[0][1]

    def getReg( self ) :
        print 'Return has no dest register'

    def emulate( self, memory ) :
        self.returnValue = memory[self.returnRegister]
        self.dump.append( 'return %s' % self.returnValue.getContent( ).getValue( ) )

    def __str__( self ) :
        return 'Return (' + str( self.returnValue ) + ')'

# return-wide vAA ( 8b )
class ReturnWide( Instruction ) :
    pass

# return-object vAA ( 8b )
class ReturnObject( Instruction ) :
    pass

# const/4 vA, #+B ( 4b, 4b )
class Const4( Instruction ) :
    def __init__( self, args ) :
        print 'Const4 :', args
        Instruction.__init__( self, args )
        self.value = int( args[1][1] )
        self.type = 'I'
        print '==>', self.value

    def getValue( self ) :
        return self.value
        
    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'Const4 : ' + str( self.value )

# const/16 vAA, #+BBBB ( 8b, 16b )
class Const16( Instruction ) :
    def __init__( self, args ) :
        print 'Const16 :', args
        Instruction.__init__( self, args )
        self.value = int( args[1][1] )
        self.type = 'I'
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'Const16 : ' + str( self.value )

# const vAA, #+BBBBBBBB ( 8b, 32b )
class Const( Instruction ) :
    def __init__( self, args ) :
        print 'Const :', args
        Instruction.__init__( self, args )
        self.value = int( args[1][1] )
        self.type = 'I'
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'Const : ' + str( self.value )

# const/high16 vAA, #+BBBB0000 ( 8b, 16b )
class ConstHigh16( Instruction ) :
    def __init__( self, args ) :
        print 'ConstHigh16 :', args
        Instruction.__init__( self, args )
        self.value = int( args[1][1] )
        self.type = 'F'
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'ConstHigh16 : ' + str( self.value )

# const-wide/16 vAA, #+BBBB ( 8b, 16b )
class ConstWide16( Instruction ) :
    def __init__( self, args ) :
        print 'ConstWide16 :', args
        Instruction.__init__( self, args )
        self.type = 'J'
        self.value = struct.unpack( 'd', struct.pack( 'd', args[1][1] ) )[0]
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'Constwide16 : ' + str( self.value )

# const-wide/32 vAA, #+BBBBBBBB ( 8b, 32b )
class ConstWide32( Instruction ) :
    def __init__( self, args ) :
        print 'ConstWide32 :', args
        Instruction.__init__( self, args )
        self.type = 'J'
        val = ( ( 0xFFFF & args[2][1] ) << 16 ) | ( ( 0xFFFF & args[1][1] ) )
        self.value = struct.unpack( 'd', struct.pack( 'd', val ) )[0]
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'Constwide32 : ' + str( self.value )

# const-wide vAA, #+BBBBBBBBBBBBBBBB ( 8b, 64b )
class ConstWide( Instruction ) :
    def __init__( self, args ) :
        print 'ConstWide :', args
        Instruction.__init__( self, args )
        val = args[1:]
        val = ( 0xFFFF & val[0][1] ) | ( ( 0xFFFF & val[1][1] ) << 16 ) | ( \
              ( 0xFFFF & val[2][1] ) << 32 ) | ( ( 0xFFFF & val[3][1] ) << 48 )
        self.type = 'D'
        self.value = struct.unpack( 'd', struct.pack( 'q', val ) )[0]
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'ConstWide : ' + str( self.value )

# const-wide/high16 vAA, #+BBBB000000000000 ( 8b, 16b )
class ConstWideHigh16( Instruction ) :
    def __init__( self, args ) :
        print 'ConstWideHigh16 :', args
        Instruction.__init__( self, args )
        self.value = struct.unpack( 'd', struct.pack( 'q', int( args[1][1] ) ) )[0]
        self.type = 'D'
        print '==>', self.value
    
    def getValue( self ) :
        return self.value

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'ConstWide : ' + str( self.value )

# const-string vAA ( 8b )
class ConstString( Instruction ) :
    def __init__( self, args ) :
        print 'ConstString :', args
        Instruction.__init__( self, args )
        self.value = '"' + args[1][2] + '"'
        print '==>', self.value

    def getValue( self ) :
        return self.value

    def __str__( self ) :
        return self.value

# const-string/jumbo vAA ( 8b )
class ConstStringJumbo( Instruction ) :
    pass

# const-class vAA ( 8b )
class ConstClass( Instruction ) :
    pass

# monitor-enter vAA ( 8b )
class MonitorEnter( Instruction ) :
    pass

# monitor-exit vAA ( 8b )
class MonitorExit( Instruction ) :
    pass

# check-cast vAA ( 8b )
class CheckCast( Instruction ) :
    pass

# instance-of vA, vB ( 4b, 4b )
class InstanceOf( Instruction ) :
    pass

# array-length vA, vB ( 4b, 4b )
class ArrayLength( Instruction ) :
    pass

# new-instance vAA ( 8b )
class NewInstance( Instruction ) :
    def __init__( self, args ) :
        print 'NewInstance :', args
        Instruction.__init__( self, args )
        self.type = args[1][2]

    def emulate( self, memory ) :
        self.ins = 'new' # %s( )' % ( self.type[1:-1].replace( '/', '.' ) )

    def getValue( self ) :
        return self.ins

    def getType( self ) :
        return self.type

    def __str__( self ) :
        return 'New (' + self.type + ')'

# new-array vA, vB ( 8b, size )
class NewArray( Instruction ) :
    def __init__( self, args ) :
        print 'NewArray :', args
        Instruction.__init__( self, args )

# filled-new-array {vD, vE, vF, vG, vA} ( 4b each )
class FilledNewArray( Instruction ) :
    pass

# filled-new-array/range {vCCCC..vNNNN} ( 16b )
class FilledNewArrayRange( Instruction ) :
    pass

# fill-array-data vAA, +BBBBBBBB ( 8b, 32b )
class FillArrayData( Instruction ) :
    pass

# throw vAA ( 8b )
class Throw( Instruction ) :
    pass

# goto +AA ( 8b )
class Goto( Instruction ) :
    def __init__( self, args ) :
        print 'Goto :', args
        Instruction.__init__( self, args )

    def getReg( self ) :
        print 'Goto has no dest register'

# goto/16 +AAAA ( 16b )
class Goto16( Instruction ) :
    pass

# goto/32 +AAAAAAAA ( 32b )
class Goto32( Instruction ) :
    pass

# packed-switch vAA, +BBBBBBBB ( reg to test, 32b )
class PackedSwitch( Instruction ) :
    def __init__( self, args ) :
        print 'PackedSwitch :', args
        #Instruction.__init__( self, args )

    def getReg( self ) :
        print 'PackedSwitch has no dest register.'

# sparse-switch vAA, +BBBBBBBB ( reg to test, 32b )
class SparseSwitch( Instruction ) :
    pass

# cmp-float ( 8b, 8b, 8b )
class CmplFloat( Instruction ) :
    pass

# cmpg-float ( 8b, 8b, 8b )
class CmpgFloat( Instruction ) :
    pass

# cmpl-double ( 8b, 8b, 8b )
class CmplDouble( Instruction ) :
    pass

# cmpg-double ( 8b, 8b, 8b )
class CmpgDouble( Instruction ) :
    pass

# cmp-long ( 8b, 8b, 8b )
class CmpLong( Instruction ) :
    pass

# if-eq vA, vB, +CCCC ( 4b, 4b, 16b )
class IfEq( Instruction ) :
    pass

# if-ne vA, vB, +CCCC ( 4b, 4b, 16b )
class IfNe( Instruction ) :
    pass

# if-lt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLt( Instruction ) :
    def __init__( self, args ) :
        print 'IfLt :', args
        Instruction.__init__( self, args )

# if-ge vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGe( Instruction ) :
    def __init__( self, args ) :
        print 'IfGe :', args
        #Instruction.__init__( self, args )
        self.firstTest = int( args[0][1] )
        self.secondTest = int( args[1][1] )
        self.branch = int( args[2][1] )

    def getReg( self ) :
        print 'IfGe has no dest register'
        return None

    def __str__( self ) :
        return 'IfGe : ' + str( self.value )

# if-gt vA, vB, +CCCC ( 4b, 4b, 16b )
class IfGt( Instruction ) :
    pass

# if-le vA, vB, +CCCC ( 4b, 4b, 16b )
class IfLe( Instruction ) :
    pass

# if-eqz vAA, +BBBB ( 8b, 16b )
class IfEqz( Instruction ) :
    pass

# if-nez vAA, +BBBB ( 8b, 16b )
class IfNez( Instruction ) :
    pass

# if-ltz vAA, +BBBB ( 8b, 16b )
class IfLtz( Instruction ) :
    pass

# if-gez vAA, +BBBB ( 8b, 16b )
class IfGez( Instruction ) :
    pass

# if-gtz vAA, +BBBB ( 8b, 16b )
class IfGtz( Instruction ) :
    pass

# if-lez vAA, +BBBB (8b, 16b )
class IfLez( Instruction ) :
    def __init__( self, args ) :
        print 'IfLez :', args
        Instruction.__init__( self, args )

# aget vAA, vBB, vCC ( 8b, 8b, 8b )
class AGet( Instruction ) :
    pass

# aget-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetWide( Instruction ) :
    pass

# aget-object vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetObject( Instruction ) :
    pass

# aget-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetBoolean( Instruction ) :
    pass

# aget-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetByte( Instruction ) :
    pass

# aget-char vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetChar( Instruction ) :
    pass

# aget-short vAA, vBB, vCC ( 8b, 8b, 8b )
class AGetShort( Instruction ) :
    pass

# aput vAA, vBB, vCC ( 8b, 8b, 8b )
class APut( Instruction ) :
    def __init__( self, args ) :
        print 'APut :', args
        Instruction.__init__( self, args )

# aput-wide vAA, vBB, vCC ( 8b, 8b, 8b )
class APutWide( Instruction ) :
    pass

# aput-object vAA, vBB, vCC ( 8b, 8b, 8b )
class APutObject( Instruction ) :
    pass

# aput-boolean vAA, vBB, vCC ( 8b, 8b, 8b )
class APutBoolean( Instruction ) :
    pass

# aput-byte vAA, vBB, vCC ( 8b, 8b, 8b )
class APutByte( Instruction ) :
    pass

# aput-char vAA, vBB, vCC ( 8b, 8b, 8b )
class APutChar( Instruction ) :
    pass

# aput-short vAA, vBB, vCC ( 8b, 8b, 8b )
class APutShort( Instruction ) :
    pass

# iget vA, vB ( 4b, 4b )
class IGet( Instruction ) :
    def __init__( self, args ) :
        print 'IGet :', args
        Instruction.__init__( self, args )
        self.location = args[-1][2]
        self.type = args[-1][3]
        self.name = args[-1][4]
        self.retType = args[-1][-1]
        self.objreg = args[1][1]

    def emulate( self, memory ) :
        self.ins = '%s.%s' % ( memory[self.objreg].getContent( ).getValue( ), self.name )
        print 'Ins : %s' % self.ins

    def getType( self ) :
        return self.type

    def getValue( self ) :
        return self.ins

    def __str__( self ) :
        return '(' + self.type + ') ' + self.location + '.' + self.name

# iget-wide vA, vB ( 4b, 4b )
class IGetWide( Instruction ) :
    pass

# iget-object vA, vB ( 4b, 4b )
class IGetObject( Instruction ) :
    pass

# iget-boolean vA, vB ( 4b, 4b )
class IGetBoolean( Instruction ) :
    pass

# iget-byte vA, vB ( 4b, 4b )
class IGetByte( Instruction ) :
    pass

# iget-char vA, vB ( 4b, 4b )
class IGetChar( Instruction ) :
    pass

# iget-short vA, vB ( 4b, 4b )
class IGetShort( Instruction ) :
    pass

# iput vA, vB ( 4b, 4b )
class IPut( Instruction ) :
    def __init__( self, args ) :
        print 'IPut', args
        Instruction.__init__( self, args )

# iput-wide vA, vB ( 4b, 4b )
class IPutWide( Instruction ) :
    pass

# iput-object vA, vB ( 4b, 4b )
class IPutObject( Instruction ) :
    pass

# iput-boolean vA, vB ( 4b, 4b )
class IPutBoolean( Instruction ) :
    pass

# iput-byte vA, vB ( 4b, 4b )
class IPutByte( Instruction ) :
    pass

# iput-char vA, vB ( 4b, 4b )
class IPutChar( Instruction ) :
    pass

# iput-short vA, vB ( 4b, 4b )
class IPutShort( Instruction ) :
    pass

# sget vAA ( 8b )
class SGet( Instruction ) :
    pass

# sget-wide vAA ( 8b )
class SGetWide( Instruction ) :
    pass

# sget-object vAA ( 8b )
class SGetObject( Instruction ) :
    def __init__( self, args ) :
        print 'SGetObject :', args
        Instruction.__init__( self, args )
        self.location = args[1][2][1:-1].replace( '/', '.' )
        self.type = args[1][3][1:-1].replace( '/', '.' )
        self.name = args[1][4]

    def getType( self ) :
        return self.type

    def getValue( self ) :
        return '%s.%s' % ( self.location, self.name )

    def getName( self ) :
        return self.name

    def __str__( self ) :
        return '(' + self.type + ') ' + self.location + '.' + self.name

# sget-boolean vAA ( 8b )
class SGetBoolean( Instruction ) :
    pass

# sget-byte vAA ( 8b )
class SGetByte( Instruction ) :
    pass

# sget-char vAA ( 8b )
class SGetChar( Instruction ) :
    pass

# sget-short vAA ( 8b )
class SGetShort( Instruction ) :
    pass

# sput vAA ( 8b )
class SPut( Instruction ) :
    pass

# sput-wide vAA ( 8b )
class SPutWide( Instruction ) :
    pass

# sput-object vAA ( 8b )
class SPutObject( Instruction ) :
    pass

# sput-boolean vAA ( 8b )
class SPutBoolean( Instruction ) :
    pass

# sput-wide vAA ( 8b )
class SPutByte( Instruction ) :
    pass

# sput-char vAA ( 8b )
class SPutChar( Instruction ) :
    pass

# sput-short vAA ( 8b )
class SPutShort( Instruction ) :
    pass

# invoke-virtual {vD, vE, vF, vG, vA} ( 4b each )
class InvokeVirtual( Instruction ) :
    def __init__( self, args ) :
        print 'InvokeVirtual :', args
        Instruction.__init__( self, args )
        self.params = [ int( i[1] ) for i in args[1:-1] ]
        self.type = args[-1][2]
        self.paramsType = args[-1][3]
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate( self, memory ) :
        memory['heap'] = self
        params = []
        for param in self.params :
            # FIXME ? : Le parametre n'existe pas forcement avec invokeVirtual
            # e.g : InvokeVirtual : [['v', 2], ['v', 0], ['v', 1], ['meth@', 5,
            # 'Ljava/io/PrintStream;', '(D)', 'V', 'println']]
            # ici v1 existe pas.
            # ====> A cause des registres wide (== 2 registres)
            par = memory.get( param )
            if par :
                print 'param : ', memory[param].getContent().getValue(), 'str :',
                print str( memory[param].getContent().getValue())
                params.append( memory[param].getContent( ) )
            else :
                print 'Error, register %d does not exist.' % param
        self.ins = '%s.%s( %s )' % ( memory[self.register].getContent( \
        ).getValue( ), self.methCalled, ', '.join( [ str( param.getValue( ) ) for
        param in params ] ) )
        print 'Ins :: %s' % self.ins

    def getValue( self ) :
        return self.ins

    def getReg( self ) :
        print 'InvokeVirtual has no dest register.'
        return None

    def __str__( self ) :
        return 'InvokeVirtual (' + self.returnType + ')' + self.methCalled +\
        '(' + self.paramsType + str( self.params ) + ' )'

# invoke-super {vD, vE, vF, vG, vA} ( 4b each )
class InvokeSuper( Instruction ) :
    pass

# invoke-direct {vD, vE, vF, vG, vA} ( 4b each )
class InvokeDirect( Instruction ) :
    def __init__( self, args ) :
        print 'InvokeDirect :', args
        Instruction.__init__( self, args )
        self.params = [ int( i[1] ) for i in args[1:-1] ]
        self.type = args[-1][2][1:-1].replace( '/', '.' )
        self.paramsType = args[-1][3][1:-1].split( )
        self.returnType = args[-1][4]
        self.methCalled = args[-1][-1]

    def emulate( self, memory ) :
        self.ins =  memory[self.register].getContent( )
        params = []
        for param in self.params :
            print 'param : ', memory[param].getContent().getValue(), 'str :',
            print str( memory[param].getContent().getValue())
            params.append( memory[ param ].getContent( ) )
        self.params = params
#        self.ins = '%s %s( %s )' % ( self.ins, self.type, ', '.join( params ) )
#        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return '%s %s( %s )' % ( self.ins.getValue( ), self.type, ', '.join(
        [ str( param.getValue( ) ) for param in self.params ] ) )

#    def getReg( self ) :
#        print 'InvokeDirect has no dest register.'
#        return None

    def __str__( self ) :
        return 'InvokeDirect (' + self.returnType + ')' + self.methCalled + '(\
        ' + str( self.paramsType ) + ', ' + str( self.params ) + ' )'

# invoke-static {vD, vE, vF, vG, vA} ( 4b each )
class InvokeStatic( Instruction ) :
    pass

# invoke-interface {vD, vE, vF, vG, vA} ( 4b each )
class InvokeInterface( Instruction ) :
    pass

# invoke-virtual/range {vCCCC..vNNNN} ( 16b each )
class InvokeVirtualRange( Instruction ) :
    def __init__( self, args ) :
        print 'InvokeVirtualRange :', args
        Instruction.__init__( self, args )

# invoke-super/range {vCCCC..vNNNN} ( 16b each )
class InvokeSuperRange( Instruction ) :
    pass

# invoke-direct/range {vCCCC..vNNNN} ( 16b each )
class InvokeDirectRange( Instruction ) :
    def __init__( self, args ) :
        print 'InvokeDirectRange :', args
        Instruction.__init__( self, args )

# invoke-static/range {vCCCC..vNNNN} ( 16b each )
class InvokeStaticRange( Instruction ) :
    pass

# invoke-interface/range {vCCCC..vNNNN} ( 16b each )
class InvokeInterfaceRange( Instruction ) :
    pass

# neg-int vA, vB ( 4b, 4b )
class NegInt( Instruction ) :
    pass

# not-int vA, vB ( 4b, 4b )
class NotInt( Instruction ) :
    pass

# neg-long vA, vB ( 4b, 4b )
class NegLong( Instruction ) :
    pass

# not-long vA, vB ( 4b, 4b )
class NotLong( Instruction ) :
    pass

# neg-float vA, vB ( 4b, 4b )
class NegFloat( Instruction ) :
    pass

# neg-double vA, vB ( 4b, 4b )
class NegDouble( Instruction ) :
    pass

# int-to-long vA, vB ( 4b, 4b )
class IntToLong( Instruction ) :
    pass

# int-to-float vA, vB ( 4b, 4b )
class IntToFloat( Instruction ) :
    pass

# int-to-double vA, vB ( 4b, 4b )
class IntToDouble( Instruction ) :
    def __init__( self, args ) :
        print 'IntToDouble :', args
        Instruction.__init__( self, args )

# long-to-int vA, vB ( 4b, 4b )
class LongToInt( Instruction ) :
    pass

# long-to-float vA, vB ( 4b, 4b )
class LongToFloat( Instruction ) :
    pass

# long-to-double vA, vB ( 4b, 4b )
class LongToDouble( Instruction ) :
    pass

# float-to-int vA, vB ( 4b, 4b )
class FloatToInt( Instruction ) :
    pass

# float-to-long vA, vB ( 4b, 4b )
class FloatToLong( Instruction ) :
    pass

# float-to-double vA, vB ( 4b, 4b )
class FloatToDouble( Instruction ) :
    def __init__( self, args ) :
        print 'FloatToDouble :', args
        Instruction.__init__( self, args )

# double-to-int vA, vB ( 4b, 4b )
class DoubleToInt( Instruction ) :
    pass

# double-to-long vA, vB ( 4b, 4b )
class DoubleToLong( Instruction ) :
    pass

# double-to-float vA, vB ( 4b, 4b )
class DoubleToFloat( Instruction ) :
    pass

# int-to-byte vA, vB ( 4b, 4b )
class IntToByte( Instruction ) :
    pass

# int-to-char vA, vB ( 4b, 4b )
class IntToChar( Instruction ) :
    pass

# int-to-short vA, vB ( 4b, 4b )
class IntToShort( Instruction ) :
    pass

# add-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AddInt( Instruction ) :
    def __init__( self, args ) :
        print 'AddInt :', args
        Instruction.__init__( self, args )
        self.firstSource = int( args[1][1] )
        self.secondSource = int( args[2][1] )

    def emulate( self, memory ) :
        self.source1 = memory[self.firstSource].getContent( )
        self.source2 = memory[self.secondSource].getContent( )
#        try :
#            source1 = int( source1 )
#            source2 = int( source2 )
#            self.ins = '%s' % ( source1 + source2 )
#        except :
#            self.ins = '%s + %s' % ( source1, source2 )
#        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return '%s + %s' % ( self.source1.getValue( ), self.source2.getValue())
        #[ self.source1, self.source2 ]

# sub-int vAA, vBB, vCC ( 8b, 8b, 8b )
class SubInt( Instruction ) :
    def __init__( self, args ) :
        print 'SubInt :', args
        Instruction.__init__( self, args )
        self.firstSource = int( args[1][1] )
        self.secondSource = int( args[2][1] )

    def emulate( self, memory ) :
        source1 = memory[self.firstSource].getContent( )
        source2 = memory[self.secondSource].getContent( )
#        try :
#            source1 = int( source1 )
#            source2 = int( source2 )
#            self.ins = '%s' % ( source1 - source2 )
#        except :
#            self.ins = '%s - %s' % ( source1, source2 )
#        print 'Ins : %s' % self.ins

#    def getValue( self ) :
#        return self.ins

# mul-int vAA, vBB, vCC ( 8b, 8b, 8b )
class MulInt( Instruction ) :
    def __init__( self, args ) :
        print 'MulInt :', args
        Instruction.__init__( self, args )
        self.firstSource = int( args[1][1] )
        self.secondSource = int( args[2][1] )

    def emulate( self, memory ) :
        source1 = memory[self.firstSource].getContent( )
        source2 = memory[self.secondSource].getContent( )
#        try :
#            source1 = int( source1 )
#            source2 = int( source2 )
#            self.ins = '%s' % ( source1 * source2 )
#        except :
#            self.ins = '%s * %s' % ( source1, source2 )
#        print 'Ins : %s' % self.ins

#    def getValue( self ) :
#        return self.value

# div-int vAA, vBB, vCC ( 8b, 8b, 8b )
class DivInt( Instruction ) :
    def __init__( self, args ) :
        print 'DivInt :', args
        Instruction.__init__( self, args )
        self.firstSource = int( args[1][1] )
        self.secondSource = int( args[2][1] )

    def emulate( self, memory ) :
        source1 = memory[self.firstSource].getContent( )
        source2 = memory[self.secondSource].getContent( )
#        try :
#            source1 = int( source1 )
#            source2 = int( source2 )
#            self.ins = '%s' % ( source1 / float( source2 ) )
#        except :
#            self.ins = '%s / %s' % ( source1, source2 )
#        print 'Ins : %s' % self.ins

#    def getValue( self ) :
#        return self.value

# rem-int vAA, vBB, vCC ( 8b, 8b, 8b )
class RemInt( Instruction ) :
    pass

# and-int vAA, vBB, vCC ( 8b, 8b, 8b )
class AndInt( Instruction ) :
    pass

# or-int vAA, vBB, vCC ( 8b, 8b, 8b )
class OrInt( Instruction ) :
    pass

# xor-int vAA, vBB, vCC ( 8b, 8b, 8b )
class XorInt( Instruction ) :
    pass

# shl-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlInt( Instruction ) :
    pass

# shr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrInt( Instruction ) :
    pass

# ushr-int vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrInt( Instruction ) :
    pass

# add-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AddLong( Instruction ) :
    pass

# sub-long vAA, vBB, vCC ( 8b, 8b, 8b )
class SubLong( Instruction ) :
    pass

# mul-long vAA, vBB, vCC ( 8b, 8b, 8b )
class MulLong( Instruction ) :
    pass

# div-long vAA, vBB, vCC ( 8b, 8b, 8b )
class DivLong( Instruction ) :
    pass

# rem-long vAA, vBB, vCC ( 8b, 8b, 8b )
class RemLong( Instruction ) :
    pass

# and-long vAA, vBB, vCC ( 8b, 8b, 8b )
class AndLong( Instruction ) :
    pass

# or-long vAA, vBB, vCC ( 8b, 8b, 8b )
class OrLong( Instruction ) :
    pass

# xor-long vAA, vBB, vCC ( 8b, 8b, 8b )
class XorLong( Instruction ) :
    pass

# shl-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShlLong( Instruction ) :
    pass

# shr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class ShrLong( Instruction ) :
    pass

# ushr-long vAA, vBB, vCC ( 8b, 8b, 8b )
class UShrLong( Instruction ) :
    pass

# add-float vAA, vBB, vCC ( 8b, 8b, 8b )
class AddFloat( Instruction ) :
    pass

# sub-float vAA, vBB, vCC ( 8b, 8b, 8b )
class SubFloat( Instruction ) :
    pass

# mul-float vAA, vBB, vCC ( 8b, 8b, 8b )
class MulFloat( Instruction ) :
    pass

# div-float vAA, vBB, vCC ( 8b, 8b, 8b )
class DivFloat( Instruction ) :
    pass

# rem-float vAA, vBB, vCC ( 8b, 8b, 8b )
class RemFloat( Instruction ) :
    pass

# add-double vAA, vBB, vCC ( 8b, 8b, 8b )
class AddDouble( Instruction ) :
    def __init__( self, args ) :
        print 'AddDouble :', args
        Instruction.__init__( self, args )

# sub-double vAA, vBB, vCC ( 8b, 8b, 8b )
class SubDouble( Instruction ) :
    def __init__( self, args ) :
        print 'SubDouble :', args
        Instruction.__init__( self, args )

# mul-double vAA, vBB, vCC ( 8b, 8b, 8b )
class MulDouble( Instruction ) :
    def __init__( self, args ) :
        print 'MulDouble :', args
        Instruction.__init__( self, args )

# div-double vAA, vBB, vCC ( 8b, 8b, 8b )
class DivDouble( Instruction ) :
    pass

# rem-double vAA, vBB, vCC ( 8b, 8b, 8b )
class RemDouble( Instruction ) :
    pass

# add-int/2addr vA, vB ( 4b, 4b )
class AddInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'AddInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        #self.ins = '%s + %s' % ( memory[self.register].getContent( ).getValue( ),
        #memory[self.source].getContent( ).getValue( ) )
        #print 'Ins : %s' % self.ins
        self.op1 = memory[self.register].getContent( )
        self.op2 = memory[self.source].getContent( )

    def getValue( self ) :
        #return self.ins
        return [ self.op1, self.op2 ]

# sub-int/2addr vA, vB ( 4b, 4b )
class SubInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'SubInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s - %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# mul-int/2addr vA, vB ( 4b, 4b )
class MulInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'MulInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s * %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# div-int/2addr vA, vB ( 4b, 4b )
class DivInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'DivInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s / %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# rem-int/2addr vA, vB ( 4b, 4b )
class RemInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'RemInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s %% %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# and-int/2addr vA, vB ( 4b, 4b )
class AndInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'AndInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s & %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# or-int/2addr vA, vB ( 4b, 4b )
class OrInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'OrInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s | %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# xor-int/2addr vA, vB ( 4b, 4b )
class XorInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'XorInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s ^ %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# shl-int/2addr vA, vB ( 4b, 4b )
class ShlInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'ShlInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s << ( %s & 0x1f )' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# shr-int/2addr vA, vB ( 4b, 4b )
class ShrInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'ShrInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s >> ( %s & 0x1f )' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# ushr-int/2addr vA, vB ( 4b, 4b )
class UShrInt2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'UShrInt2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s >> ( %s & 0x1f )' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# add-long/2addr vA, vB ( 4b, 4b )
class AddLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'AddLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s + %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# sub-long/2addr vA, vB ( 4b, 4b )
class SubLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'SubLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s - %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# mul-long/2addr vA, vB ( 4b, 4b )
class MulLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'MulLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s * %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# div-long/2addr vA, vB ( 4b, 4b )
class DivLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'DivLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s / %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# rem-long/2addr vA, vB ( 4b, 4b )
class RemLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'RemLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s % %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# and-long/2addr vA, vB ( 4b, 4b )
class AndLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'AddLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s & %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# or-long/2addr vA, vB ( 4b, 4b )
class OrLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'OrLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s | %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# xor-long/2addr vA, vB ( 4b, 4b )
class XorLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'XorLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s ^ %s' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# shl-long/2addr vA, vB ( 4b, 4b )
class ShlLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'ShlLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s << ( %s & 0x1f )' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# shr-long/2addr vA, vB ( 4b, 4b )
class ShrLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'ShrLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s >> ( %s & 0x1f )' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# ushr-long/2addr vA, vB ( 4b, 4b )
class UShrLong2Addr( Instruction ) :
    def __init__( self, args ) :
        print 'UShrLong2Addr :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )

    def emulate( self, memory ) :
        self.ins = '%s >> ( %s & 0x1f )' % ( memory[self.register].getContent( ).getValue( ),
        memory[self.source].getContent( ).getValue( ) )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# add-float/2addr vA, vB ( 4b, 4b )
class AddFloat2Addr( Instruction ) :
    pass

# sub-float/2addr vA, vB ( 4b, 4b )
class SubFloat2Addr( Instruction ) :
    pass

# mul-float/2addr vA, vB ( 4b, 4b )
class MulFloat2Addr( Instruction ) :
    pass

# div-float/2addr vA, vB ( 4b, 4b )
class DivFloat2Addr( Instruction ) :
    pass

# rem-float/2addr vA, vB ( 4b, 4b )
class RemFloat2Addr( Instruction ) :
    pass

# add-double/2addr vA, vB ( 4b, 4b )
class AddDouble2Addr( Instruction ) :
    pass

# sub-double/2addr vA, vB ( 4b, 4b )
class SubDouble2Addr( Instruction ) :
    pass

# mul-double/2addr vA, vB ( 4b, 4b )
class MulDouble2Addr( Instruction ) :
    pass

# div-double/2addr vA, vB ( 4b, 4b )
class DivDouble2Addr( Instruction ) :
    pass

# rem-double/2addr vA, vB ( 4b, 4b )
class RemDouble2Addr( Instruction ) :
    pass

# add-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AddIntLit16( Instruction ) :
    pass

# rsub-int vA, vB, #+CCCC ( 4b, 4b, 16b )
class RSubInt( Instruction ) :
    pass

# mul-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class MulIntLit16( Instruction ) :
    def __init__( self, args ) :
        print 'MulIntLit16 :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )
        self.const = int( args[2][1] )

    def emulate( self, memory ) :
        self.ins = '%s * %s' % ( memory[self.source].getContent( ).getValue( ),
        self.const )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# div-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class DivIntLit16( Instruction ) :
    pass

# rem-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class RemIntLit16( Instruction ) :
    pass

# and-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class AndIntLit16( Instruction ) :
    pass

# or-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class OrIntLit16( Instruction ) :
    pass

# xor-int/lit16 vA, vB, #+CCCC ( 4b, 4b, 16b )
class XorIntLit16( Instruction ) :
    pass

# add-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AddIntLit8( Instruction ) :
    pass

# rsub-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RSubIntLit8( Instruction ) :
    pass

# mul-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class MulIntLit8( Instruction ) :
    def __init__( self, args ) :
        print 'MulIntLit8 :', args
        Instruction.__init__( self, args )
        self.source = int( args[1][1] )
        self.const = int( args[2][1] )

    def emulate( self, memory ) :
        self.ins = '%s * %s' % ( memory[self.source].getContent( ).getValue( ),
        self.const )
        print 'Ins : %s' % self.ins

    def getValue( self ) :
        return self.ins

# div-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class DivIntLit8( Instruction ) :
    pass

# rem-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class RemIntLit8( Instruction ) :
    pass

# and-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class AndIntLit8( Instruction ) :
    pass

# or-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class OrIntLit8( Instruction ) :
    pass

# xor-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class XorIntLit8( Instruction ) :
    pass

# shl-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShlIntLit8( Instruction ) :
    pass

# shr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class ShrIntLit8( Instruction ) :
    pass

# ushr-int/lit8 vAA, vBB, #+CC ( 8b, 8b, 8b )
class UShrIntLit8( Instruction ) :
    pass

class This( ) :
    def __init__( self ) :
        pass

    def getContent( self ) :
        return self

    def getValue( self ) :
        return 'this'

class Param( ) :
    def __init__( self, name ) :
        self.name = name

    def getContent( self ) :
        return self

    def getValue( self ) :
        return self.name

INSTRUCTION_SET = {
    'nop'                     : Nop,
    'move'                    : Move,
    'move/from16'             : MoveFrom16,
    'move/16'                 : Move16,
    'move-wide'               : MoveWide,
    'move-wide/from16'        : MoveWideFrom16,
    'move-wide/16'            : MoveWide16,
    'move-object'             : MoveObject,
    'move-object/from16'      : MoveObjectFrom16,
    'move-object/16'          : MoveObject16,
    'move-result'             : MoveResult,
    'move-result-wide'        : MoveResultWide,
    'move-result-object'      : MoveResultObject,
    'move-exception'          : MoveException,
    'return-void'             : ReturnVoid,
    'return'                  : Return,
    'return-wide'             : ReturnWide,
    'return-object'           : ReturnObject,
    'const/4'                 : Const4,
    'const/16'                : Const16,
    'const'                   : Const,
    'const/high16'            : ConstHigh16,
    'const-wide/16'           : ConstWide16,
    'const-wide/32'           : ConstWide32,
    'const-wide'              : ConstWide,
    'const-wide/high16'       : ConstWideHigh16,
    'const-string'            : ConstString,
    'const-string/jumbo'      : ConstStringJumbo,
    'const-class'             : ConstClass,
    'monitor-enter'           : MonitorEnter,
    'monitor-exit'            : MonitorExit,
    'check-cast'              : CheckCast,
    'instance-of'             : InstanceOf,
    'array-length'            : ArrayLength,
    'new-instance'            : NewInstance,
    'new-array'               : NewArray,
    'filled-new-array'        : FilledNewArray,
    'filled-new-array/range'  : FilledNewArrayRange,
    'fill-array-data'         : FillArrayData,
    'throw'                   : Throw,
    'goto'                    : Goto,
    'goto/16'                 : Goto16,
    'goto/32'                 : Goto32,
    'packed-switch'           : PackedSwitch,
    'sparse-switch'           : SparseSwitch,
    'cmpl-float'              : CmplFloat,
    'cmpg-float'              : CmpgFloat,
    'cmpl-double'             : CmplDouble,
    'cmpg-double'             : CmpgDouble,
    'cmp-long'                : CmpLong,
    'if-eq'                   : IfEq,
    'if-ne'                   : IfNe,
    'if-lt'                   : IfLt,
    'if-ge'                   : IfGe,
    'if-gt'                   : IfGt,
    'if-le'                   : IfLe,
    'if-eqz'                  : IfEqz,
    'if-nez'                  : IfNez,
    'if-ltz'                  : IfLtz,
    'if-gez'                  : IfGez,
    'if-gtz'                  : IfGtz,
    'if-lez'                  : IfLez,
    'aget'                    : AGet,
    'aget-wide'               : AGetWide,
    'aget-object'             : AGetObject,
    'aget-boolean'            : AGetBoolean,
    'aget-byte'               : AGetByte,
    'aget-char'               : AGetChar,
    'aget-short'              : AGetShort,
    'aput'                    : APut,
    'aput-wide'               : APutWide,
    'aput-object'             : APutObject,
    'aput-boolean'            : APutBoolean,
    'aput-byte'               : APutByte,
    'aput-char'               : APutChar,
    'aput-short'              : APutShort,
    'iget'                    : IGet,
    'iget-wide'               : IGetWide,
    'iget-object'             : IGetObject,
    'iget-boolean'            : IGetBoolean,
    'iget-byte'               : IGetByte,
    'iget-char'               : IGetChar,
    'iget-short'              : IGetShort,
    'iput'                    : IPut,
    'iput-wide'               : IPutWide,
    'iput-object'             : IPutObject,
    'iput-boolean'            : IPutBoolean,
    'iput-byte'               : IPutByte,
    'iput-char'               : IPutChar,
    'iput-short'              : IPutShort,
    'sget'                    : SGet,
    'sget-wide'               : SGetWide,
    'sget-object'             : SGetObject,
    'sget-boolean'            : SGetBoolean,
    'sget-byte'               : SGetByte,
    'sget-char'               : SGetChar,
    'sget-short'              : SGetShort,
    'sput'                    : SPut,
    'sput-wide'               : SPutWide,
    'sput-object'             : SPutObject,
    'sput-boolean'            : SPutBoolean,
    'sput-byte'               : SPutByte,
    'sput-char'               : SPutChar,
    'sput-short'              : SPutShort,
    'invoke-virtual'          : InvokeVirtual,
    'invoke-super'            : InvokeSuper,
    'invoke-direct'           : InvokeDirect,
    'invoke-static'           : InvokeStatic,
    'invoke-interface'        : InvokeInterface,
    'invoke-virtual/range'    : InvokeVirtualRange,
    'invoke-super/range'      : InvokeSuperRange,
    'invoke-direct/range'     : InvokeDirectRange,
    'invoke-static/range'     : InvokeStaticRange,
    'invoke-interface/range'  : InvokeInterfaceRange,
    'neg-int'                 : NegInt,
    'not-int'                 : NotInt,
    'neg-long'                : NegLong,
    'not-long'                : NotLong,
    'neg-float'               : NegFloat,
    'neg-double'              : NegDouble,
    'int-to-long'             : IntToLong,
    'int-to-float'            : IntToFloat,
    'int-to-double'           : IntToDouble,
    'long-to-int'             : LongToInt,
    'long-to-float'           : LongToFloat,
    'long-to-double'          : LongToDouble,
    'float-to-int'            : FloatToInt,
    'float-to-long'           : FloatToLong,
    'float-to-double'         : FloatToDouble,
    'double-to-int'           : DoubleToInt,
    'double-to-long'          : DoubleToLong,
    'double-to-float'         : DoubleToFloat,
    'int-to-byte'             : IntToByte,
    'int-to-char'             : IntToChar,
    'int-to-short'            : IntToShort,
    'add-int'                 : AddInt,
    'sub-int'                 : SubInt,
    'mul-int'                 : MulInt,
    'div-int'                 : DivInt,
    'rem-int'                 : RemInt,
    'and-int'                 : AndInt,
    'or-int'                  : OrInt,
    'xor-int'                 : XorInt,
    'shl-int'                 : ShlInt,
    'shr-int'                 : ShrInt,
    'ushr-int'                : UShrInt,
    'add-long'                : AddLong,
    'sub-long'                : SubLong,
    'mul-long'                : MulLong,
    'div-long'                : DivLong,
    'rem-long'                : RemLong,
    'and-long'                : AndLong,
    'or-long'                 : OrLong,
    'xor-long'                : XorLong,
    'shl-long'                : ShlLong,
    'shr-long'                : ShrLong,
    'ushr-long'               : UShrLong,
    'add-float'               : AddFloat,
    'sub-float'               : SubFloat,
    'mul-float'               : MulFloat,
    'div-float'               : DivFloat,
    'rem-float'               : RemFloat,
    'add-double'              : AddDouble,
    'sub-double'              : SubDouble,
    'mul-double'              : MulDouble,
    'div-double'              : DivDouble,
    'rem-double'              : RemDouble,
    'add-int/2addr'           : AddInt2Addr,
    'sub-int/2addr'           : SubInt2Addr,
    'mul-int/2addr'           : MulInt2Addr,
    'div-int/2addr'           : DivInt2Addr,
    'rem-int/2addr'           : RemInt2Addr,
    'and-int/2addr'           : AndInt2Addr,
    'or-int/2addr'            : OrInt2Addr,
    'xor-int/2addr'           : XorInt2Addr,
    'shl-int/2addr'           : ShlInt2Addr,
    'shr-int/2addr'           : ShrInt2Addr,
    'ushr-int/2addr'          : UShrInt2Addr,
    'add-long/2addr'          : AddLong2Addr,
    'sub-long/2addr'          : SubLong2Addr,
    'mul-long/2addr'          : MulLong2Addr,
    'div-long/2addr'          : DivLong2Addr,
    'rem-long/2addr'          : RemLong2Addr,
    'and-long/2addr'          : AndLong2Addr,
    'or-long/2addr'           : OrLong2Addr,
    'xor-long/2addr'          : XorLong2Addr,
    'shl-long/2addr'          : ShlLong2Addr,
    'shr-long/2addr'          : ShrLong2Addr,
    'ushr-long/2addr'         : UShrLong2Addr,
    'add-float/2addr'         : AddFloat2Addr,
    'sub-float/2addr'         : SubFloat2Addr,
    'mul-float/2addr'         : MulFloat2Addr,
    'div-float/2addr'         : DivFloat2Addr,
    'rem-float/2addr'         : RemFloat2Addr,
    'add-double/2addr'        : AddDouble2Addr,
    'sub-double/2addr'        : SubDouble2Addr,
    'mul-double/2addr'        : MulDouble2Addr,
    'div-double/2addr'        : DivDouble2Addr,
    'rem-double/2addr'        : RemDouble2Addr,
    'add-int/lit16'           : AddIntLit16,
    'rsub-int'                : RSubInt,
    'mul-int/lit16'           : MulIntLit16,
    'div-int/lit16'           : DivIntLit16,
    'rem-int/lit16'           : RemIntLit16,
    'and-int/lit16'           : AndIntLit16,
    'or-int/lit16'            : OrIntLit16,
    'xor-int/lit16'           : XorIntLit16,
    'add-int/lit8'            : AddIntLit8,
    'rsub-int/lit8'           : RSubIntLit8,
    'mul-int/lit8'            : MulIntLit8,
    'div-int/lit8'            : DivIntLit8,
    'rem-int/lit8'            : RemIntLit8,
    'and-int/lit8'            : AndIntLit8,
    'or-int/lit8'             : OrIntLit8,
    'xor-int/lit8'            : XorIntLit8,
    'shl-int/lit8'            : ShlIntLit8,
    'shr-int/lit8'            : ShrIntLit8,
    'ushr-int/lit8'           : UShrIntLit8
}

TYPE_DESCRIPTOR = {
    'V' : 'void',
    'Z' : 'boolean',
    'B' : 'byte',
    'S' : 'short',
    'C' : 'char',
    'I' : 'int',
    'J' : 'long',
    'F' : 'float',
    'D' : 'double'
}

ACCESS_FLAGS_CLASSES = {
    0x1 : 'ACC_PUBLIC',
    0x2 : 'ACC_PRIVATE',
    0x4 : 'ACC_PROTECTED',
    0x8 : 'ACC_STATIC',
    0x10 : 'ACC_FINAL',
    0x200 : 'ACC_INTERFACE',
    0x400 : 'ACC_ABSTRACT',
    0x1000 : 'ACC_SYNTHETIC',
    0x2000 : 'ACC_ANNOTATION',
    0x4000 : 'ACC_ENUM'
}

ACCESS_FLAGS_FIELDS = {
    0x1 : 'ACC_PUBLIC',
    0x2 : 'ACC_PRIVATE',
    0x4 : 'ACC_PROTECTED',
    0x8 : 'ACC_STATIC',
    0x10 : 'ACC_FINAL',
    0x40 : 'ACC_VOLATILE',
    0x80 : 'ACC_TRANSIENT',
    0x1000 : 'ACC_SYNTHETIC',
    0x4000 : 'ACC_ENUM'
}

ACCESS_FLAGS_METHODS = {
    0x1 : 'ACC_PUBLIC',
    0x2 : 'ACC_PRIVATE',
    0x4 : 'ACC_PROTECTED',
    0x8 : 'ACC_STATIC',
    0x10 : 'ACC_FINAL',
    0x20 : 'ACC_SYNCHRONIZED',
    0x40 : 'ACC_BRIDGE',
    0x80 : 'ACC_VARARGS',
    0x100 : 'ACC_NATIVE',
    0x400 : 'ACC_ABSTRACT',
    0x800 : 'ACC_STRICT',
    0x1000 : 'ACC_SYNTHETIC',
    0x10000 : 'ACC_CONSTRUCTOR',
    0x20000 : 'ACC_DECLARED_SYNCHRONIZED'
}

def getType( type_ ) :
    res = TYPE_DESCRIPTOR.get( type_ )
    if res is None :
        if type_[0] == 'L' :
            res = type_[1:-1].replace( '/', '.' )
        elif type_[0] == '[' :
            res = getType( type_[1:] ) + '[]'
        else :
            print 'Unknown descriptor.'
            return None
    return res

class Register( ) :
    def __init__( self, content, num ) :
        self.content = content
        self.used = False
        self.num = num

    def modify( self, ins ) :
        if self.used :
            self.dump( ins )
        self.content = ins
        self.used = False

    def getContent( self ) :
        self.used = True
        return self.content

    def dump( self, ins ) :
        print 'Register #%d Dump :' % self.num
        print '---------------'
        print 'Old value :'
        print self.content
        print '->', self.content.getValue( )
        print '-------'
        print 'New value :'
        print ins
        print '->', ins.getValue( )
        print '---------------'

    def __str__( self ) :
        return str( self.content )

class Method( ) :
    def __init__( self, method ) :
        self.memory = { }
        self.method = method
        code = method.get_code( )
        access = method.get_access( )
        self.access = []
        for flag, acc in ACCESS_FLAGS_METHODS.iteritems( ) :
            if flag & access :
                self.access.append( acc )

        self.lins = code.get_bc( ).get( )
        
        self.nbregisters = code.registers_size.get_value( )
        self.nbparams = code.ins_size.get_value( )
        self.this = self.nbregisters - self.nbparams
        self.memory[ self.this ] = Register( This( ), self.this )
        # FIXME : prendre en compte le cas method static
        for i in xrange( 1, self.nbparams ) :
            self.memory[self.nbregisters - i] = Param( 'param%s' % i )

        self.ins = []
        self.cur = 0
        desc = method.get_descriptor( )
        self.type = getType( desc[-1] )
        params = desc[1:-2].split( )
        if params :
            self.paramsType = [ getType( param ) for param in params ]
        else :
            self.paramsType = None

    def getName( self ) :
        return self.method.get_name( )

    def process( self ) :
        while self.processNextIns( ) :
            print '========================'
        print
        self.debug( )

    def debug( self ) :
        print 'Dump of method :'
        for i, j in self.memory.iteritems( ) :
            if isinstance( j, This ) or isinstance( j, Param ) or i == 'heap' :
                print '%s : %s' % ( i, j )
            else :
                print '%s : %s, used : %s ' % ( i, j, j.used )
        print
        print 'Dump of ins :'
        acc = ''
        for i in self.access :
            acc += i[4:].lower( ) + ' '
        proto = acc + self.type + ' ' + self.method.get_name( ) + '('
        if self.paramsType :
            proto += ', '.join( [ '%s %s' % ( i, j ) for ( i, j ) in zip(
            self.paramsType, [self.memory[self.nbregisters - i].getValue( ) for
            i in xrange( 1, self.nbparams ) ] ) ] )
        proto += ') {'
        print proto
        for i in self.ins :
            print '%s;' % i
        print '}'
        
    def processNextIns( self ) :
        if self.cur < len( self.lins ) :
            heap = self.memory.get( 'heap' )
            ins = self.lins[self.cur]
            print 'Name :', ins.get_name( ), 'Operands :', ins.get_operands( )
            newIns = INSTRUCTION_SET.get( ins.get_name( ).lower( ) )
            if newIns is None :
                print 'Unknown instruction : %s.' % ins.get_name( ).lower( )
                return False
            newIns = newIns( ins.get_operands( )  )
            newIns.setDestDump( self.ins )
            newIns.emulate( self.memory )
            regnum = newIns.getReg( )
            if regnum is not None :
                register = self.memory.get( regnum )
                if register is None :
                    self.memory[newIns.getReg( )] = Register( newIns, regnum )
                else :
                    register.modify( newIns )
            print '----> newIns : %s, register : %s.' % ( ins.get_name( ), regnum )
            if heap and self.memory.get( 'heap' ) :
                print 'Append :', self.memory['heap'].getValue( )
                self.ins.append( self.memory['heap'].getValue( ) )
                self.memory['heap'] = None
            self.cur += 1
            return True
        return False

class DvMachine( ) :
    def __init__( self, vm ) :
        self.vm = vm.get_vm( )
        self.methods = {}
        for method in vm.get_methods( ) :
            self.methods[method.get_idx( )] = Method( method )
        print 'Methods added :'
        for name, meth in self.methods.iteritems( ) :
            print '%s ( %s )' % ( name, meth.getName( ) )

    def loadClass( self, cls = None ) :
        pass

    def selectMethod( self, name ) :
        for method in self.methods.values( ) :
            if method.getName( ) == name :
                break
        if method.getName( ) != name :
            print 'Method %s not found.' % name
            return
        method.process( )

    def __repr__( self ) :
        return repr( self.methods )

    def __str__( self ) :
        return str( self.methods )

if __name__ == '__main__' :

    TEST = 'examples/android/Test/bin/test.dex'
    #TEST = 'examples/android/Test/bin/classes.dex'
    #TEST = 'examples/java/Demo1/orig/DES.class'

    a = androguard.AndroguardS( TEST )
    #x = analysis.VM_BCA( a.get_vm( ) )

    machine = DvMachine( a )

    meth = 'go'
    print
    print 'Selection de la methode %s.' % meth
    print
    machine.selectMethod( meth )
