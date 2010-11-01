#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

BASE_TEST = "./examples/java/Demo1/orig/"
BASE_TEST_OUTPUT = "./examples/java/Demo1/new"

BASE_MAIN_TEST = "./examples/java/Demo1/orig_main/"
BASE_MAIN_TEST_OUTPUT = "./examples/java/Demo1/new_main"

FILES = [ 
          ("BaseCipher.class", 0),
          ("DES.class", 0), 
          ("DES$Context.class", 0), 
          ("IBlockCipher.class", 0), 
          ("IBlockCipherSpi.class", 0), 
          ("Properties$1.class", 0), 
          ("Properties.class", 0), 
          ("Registry.class", 0), 
          ("Util.class", 0), 
          ("WeakKeyException.class", 0), 
          ("Demo1Main.class", 1)
        ]

TEST = []
for i in FILES :
   if i[1] == 0 :
      TEST.append( BASE_TEST + i[0] )
   else :
      TEST.append( BASE_MAIN_TEST + i[0] )

a = androguard.Androguard( TEST )

