#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = [ './examples/java/Hello.class' ]
#TEST = [ './examples/java/test/orig/Test1.class' ]
#TEST = [ './examples/java/test/Test.class' ]
#TEST = [ './VM.class' ]

_a = androguard.AndroguardS( TEST[0] )
_a.show()

#nb = 0
#for i in _a.gets("constant_pool") :
#   print nb, 
#   i.show()
#   nb += 1

#for method in _a.get("method", "rc4") :
#   method.show()
