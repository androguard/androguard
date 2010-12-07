#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

#TEST  = 'examples/java/test/orig/Test1.class'
TEST  = 'examples/java/Demo1/orig/DES.class'
#TEST  = 'examples/java/Demo1/orig/Util.class'

a = androguard.AndroguardS( TEST )
x = analysis.VMBCA( a.get_vm() )

#x.show()

#g = x.hmethods[ a.get_method("test_base")[0] ]

for method in a.get_methods() :
   g = x.hmethods[ method ]
   
   print method.get_name()
   for i in g.basic_blocks.get() :
      print "\t", i.name, i.start, i.end, i.free_blocks_offsets
