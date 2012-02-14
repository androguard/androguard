#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

from androguard.core.androgen import AndroguardS, VM_int, VM_INT_BASIC_MATH_FORMULA

TEST = './examples/java/test/orig/Test1.class'
TEST_OUTPUT = './examples/java/test/new/Test1.class'

_a = AndroguardS( TEST )
vm = _a.get_vm()

VM_int( _a, "Test1", "test1", "(I)I", VM_INT_BASIC_MATH_FORMULA )
#VM_int( _a, "Test1", "test1", "(I)I", VM_INT_BASIC_PRNG )

print "CONSTANT_POOL_COUNT = %d" % vm.constant_pool_count.get_value()

fd = open( TEST_OUTPUT, "w" )
fd.write( _a.save() )
fd.close()
