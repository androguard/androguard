#!/usr/bin/env python

import sys, hashlib

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)


from androguard.core.androgen import AndroguardS
from androguard.core.analysis import analysis

#TEST  = 'examples/java/test/orig/Test1.class'
#TEST  = 'examples/java/Demo1/orig/DES.class'
#TEST  = 'examples/java/Demo1/orig/Util.class'
#TEST = 'examples/android/Test/bin/classes.dex'
TEST = 'examples/android/TestsAndroguard/bin/classes.dex'
#TEST = 'examples/android/TC/bin/classes.dex'
#TEST = 'examples/android/Hello_Kitty/classes.dex'

a = AndroguardS( TEST )
x = analysis.VMAnalysis( a.get_vm() )


# CFG
for method in a.get_methods() :
    g = x.hmethods[ method ]

    print method.get_class_name(), method.get_name(), method.get_descriptor(), method.get_code().get_length(), method.get_code().registers_size.get_value()

    idx = 0
    for i in g.basic_blocks.get() :
        print "\t %s %x %x" % (i.name, i.start, i.end), i.ins[-1].get_name(), '[ CHILDS = ', ', '.join( "%x-%x-%s" % (j[0], j[1], j[2].get_name()) for j in i.childs ), ']', '[ FATHERS = ', ', '.join( j[2].get_name() for j in i.fathers ), ']', i.free_blocks_offsets

        for ins in i.get_ins() :
            print "\t\t %x" % idx, ins.get_name(), ins.get_operands()
            idx += ins.get_length()

        print ""
