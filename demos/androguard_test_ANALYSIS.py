#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

OUTPUT = "./output/"
TEST  = 'examples/java/test/orig/Test1.class'
#TEST  = 'examples/java/Demo1/orig/DES.class'
#TEST  = 'examples/java/Demo1/orig/Util.class'

a = androguard.AndroguardS( TEST )
x = analysis.VM_BCA( a.get_vm() )

#x.show()

for method in a.get_methods() :
   g = x.hmethods[ method ]
   
   g.basic_blocks.export_dot( OUTPUT + method.get_name() + ".dot" )

   print method.get_name()
   for i in g.basic_blocks.get() :
      print "\t", i.name, i.start, i.end, '[ CHILDS = ', ', '.join( j[2].get_name() for j in i.childs ), ']', '[ FATHERS = ', ', '.join( j[2].get_name() for j in i.fathers ), ']', i.free_blocks_offsets
