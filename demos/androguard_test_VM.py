#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = './examples/java/test/orig/Test1.class'
TEST_OUTPUT = './examples/java/test/new/Test1.class'

_a = androguard.AndroguardS( TEST )

#androguard.VM_int( _a, "test1", androguard.VM_INT_BASIC_MATH_FORMULA )
androguard.VM_int( _a, "test1", androguard.VM_INT_BASIC_PRNG )

print "CONSTANT_POOL_COUNT = %d" %_a.constant_pool_count.get_value()

fd = open( TEST_OUTPUT, "w" )
fd.write( _a.save() )
fd.close()
