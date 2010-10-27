#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

TEST = './examples/watermarks/Demo1/bin/classes/org/t0t0/androguard/watermarks/Demo1Math.class'


a = androguard.AndroguardS( TEST )

for i in a.get_method("RC4") :
   analysis.JBCA( a, i )

