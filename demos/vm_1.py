#!/usr/bin/env python                                                                                                                                                                                                             

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./core/vm")
sys.path.append(PATH_INSTALL + "./core/predicates")

from il_reil import VM_REIL, REIL_REGISTER, REIL_LITERAL, REIL_OFFSET, REIL_SUB, REIL_STRING

x = "HELLO WORLD"


var_j = REIL_REGISTER( "j", 4, 0 )
lit_1 = REIL_LITERAL( 50, 4 )

l = [ REIL_SUB( var_j, lit_1, var_j ) ]

v = VM_REIL()

v.execute( l )
v.show()

v.execute( REIL_STRING( x, 0x100 ) )
v.show()

#v.execute( ALGO )
