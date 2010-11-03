#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

TEST  = 'examples/java/test/orig/Test1.class'


a = androguard.AndroguardS( TEST )

for i in a.get("method", "test_base") :
   x = analysis.JBCA( a, i )
   x.show()

