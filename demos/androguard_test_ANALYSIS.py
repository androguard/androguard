#!/usr/bin/env python

import sys, hashlib

PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

OUTPUT = "./output/"
#TEST  = 'examples/java/test/orig/Test1.class'
#TEST  = 'examples/java/Demo1/orig/DES.class'
#TEST  = 'examples/java/Demo1/orig/Util.class'
TEST = 'examples/android/Test/bin/classes.dex'
#TEST = 'examples/android/Hello_Kitty/classes.dex'

a = androguard.AndroguardS( TEST )
x = analysis.VM_BCA( a.get_vm() )

#x.show()

for method in a.get_methods() :
   g = x.hmethods[ method ]
   
   g.basic_blocks.export_dot( OUTPUT + "%s-%s" % (method.get_name(), hashlib.md5( "%s-%s" % (method.get_class_name(), method.get_descriptor())).hexdigest()) + ".dot" )

   print method.get_class_name(), method.get_name(), method.get_descriptor()
   for i in g.basic_blocks.get() :
      print "\t %s %x %x" % (i.name, i.start, i.end), i.ins[-1].get_name(), '[ CHILDS = ', ', '.join( "%x-%x-%s" % (j[0], j[1], j[2].get_name()) for j in i.childs ), ']', '[ FATHERS = ', ', '.join( j[2].get_name() for j in i.fathers ), ']', i.free_blocks_offsets
