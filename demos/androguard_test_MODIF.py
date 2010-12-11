#!/usr/bin/env python

import random, string

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = './examples/java/test/orig/Test1.class'
TEST_OUTPUT = './examples/java/test/new/Test1.class'

TEST2 = './examples/java/Hello.class'

_a = androguard.AndroguardS( TEST )
_b = androguard.AndroguardS( TEST2 )

_a.show()

#nb = 0
#for field in _a.gets( "fields" ) :
#   field.set_name( random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ] ) )
#   nb += 1

#for string in _a.gets( "strings" ) :
#   print string

#for method in _a.get("method", "rc4") :
#   if method.with_descriptor( "([B)[B" ) :
#      code = method.get_code()
#      code.show()

#      code.remplace_at( 19, [ "sipush", 254 ] )

#      code.insert_at( 21, [ "sipush", 254 ] )
#      code.insert_at( 22, [ "iand" ] )
#      code.remove_at( 19 )
#      code.remove_at( 19 )

#      code.show()

#      code.remove_at( 19 )
#      code.insert_at( 19, [ "sipush", 254 ] )

_a.insert_string( "BLAAAA" )
#_a.insert_craft_method( "toto", [ "ACC_PUBLIC", "[B", "[B" ], [ [ "aconst_null" ], [ "areturn" ] ] ) #( "sipush", 254 ) ] )

#_a.insert_direct_method( "toto2", _b.get("method", "test3")[0] )
_a.insert_direct_method( "toto2", _b.get("method", "test5")[0] )

for method in _a.get("method", "test_base") :
   if method.with_descriptor( "(I)I" ) :
      code = method.get_code()

      code.removes_at( [ 13, 14 ] ) 

      code.insert_at( 13, [ "aload_0" ] )

      method_toto2 = _a.get("method", "toto2")[0]
      code.insert_at( 14, [ "invokevirtual", "Test1", "toto2", method_toto2.get_descriptor() ] )
 
      method.show()

#for method in _a.get("method", "test1") :
#   code = method.get_code()

#   code.remove_at( 0 )
#   code.insert_at( 0, [ "aload_0" ] )

#   method_toto2 = _a.get("method", "toto2")[0]
#   code.insert_at( 1, [ "invokevirtual", "toto2", method_toto2.get_descriptor() ] )

#   method.show()

fd = open( TEST_OUTPUT, "w" )
fd.write( _a.save() )
fd.close()
