#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

#TEST  = 'examples/java/test/orig/Test1.class'
TEST = 'examples/android/TestsAndroguard/bin/classes.dex'

a = androguard.AndroguardS( TEST )
x = analysis.VMAnalysis( a.get_vm() )

for method in a.get_methods() :
    print method.get_class_name(), method.get_name(), method.get_descriptor()
    code = method.get_code()
    bc = code.get_bc()

    idx = 0
    for i in bc.get() :
        print "\t", "%x" % idx, i.get_name(), i.get_operands(), i.get_formatted_operands()

        idx += i.get_length()
