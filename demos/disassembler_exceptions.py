#!/usr/bin/env python

import sys, hashlib

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.androgen import AndroguardS
from androguard.core.analysis import analysis
from androguard.core.bytecodes import dvm

#TEST  = 'examples/java/test/orig/Test1.class'
#TEST  = 'examples/java/Demo1/orig/DES.class'
#TEST  = 'examples/java/Demo1/orig/Util.class'
TEST = 'examples/android/TestsAndroguard/bin/classes.dex'
TEST = 'apks/crash/reusing-catch-testcase/br.gov.infraero_1496895122692848224.apk'

a = AndroguardS( TEST )
x = analysis.VMAnalysis( a.get_vm() )


# CFG
for method in a.get_methods() :
    g = x.get_method( method )

    # Display only methods with exceptions
    if method.get_code() == None :
      continue

    if method.get_code().tries_size <= 0 :
      continue

    if (method.get_name() != "replyFromServer") or (method.get_class_name() != "Lcom/db4o/cs/internal/messages/MReadObject;") : 
      continue

    print method.get_class_name(), method.get_name(), method.get_descriptor(), method.get_code().get_length(), method.get_code().registers_size

    idx = 0
    for i in g.basic_blocks.get() :
        print "\t %s %x %x" % (i.name, i.start, i.end), '[ CHILDS = ', ', '.join( "%x-%x-%s" % (j[0], j[1], j[2].get_name()) for j in i.childs ), ']', '[ FATHERS = ', ', '.join( j[2].get_name() for j in i.fathers ), ']'

        for ins in i.get_instructions() :
            print "\t\t %x" % idx, ins.get_name(), ins.get_output()
            idx += ins.get_length()

        print ""

    for i in g.exceptions.gets() :
        print '%x %x %s' % (i.start, i.end, i.exceptions)

    print dvm.determineException(a.get_vm(), method)

