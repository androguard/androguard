#!/usr/bin/env python

import sys, random, string

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

from androguard.util import read
import jvm

TEST = "./examples/java/test/orig/Test1.class"
TEST_OUTPUT = "./examples/java/test/new/Test1.class"

j = jvm.JVMFormat( read(TEST, binary=False) )

# Modify the name of each field
for field in j.get_fields() :
    field.set_name( random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ] ) )

# Modify the name of each method (minus the constructor (<init>) and a extern called method (go))
for method in j.get_methods() :
    if method.get_name() != "go" and method.get_name() != "<init>" :
        method.set_name( random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ] ) )

# SAVE CLASS
with open( TEST_OUTPUT, "w" ) as fd:
	fd.write( j.save() )

