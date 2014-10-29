#!/usr/bin/env python

import sys, random, string

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

from androguard.util import read
import jvm

TEST = "./examples/java/test/orig/Test1.class"
TEST_REF = "./examples/java/Hello.class"
TEST_OUTPUT = "./examples/java/test/new/Test1.class"

j = jvm.JVMFormat( read(TEST, binary=False) )
j2 = jvm.JVMFormat( read(TEST_REF, binary=False) )

# Insert a method with java dependances methods/class
j.insert_direct_method( "toto2", j2.get_method("test5")[0] )

# SAVE CLASS
with open( TEST_OUTPUT, "w" ) as fd:
	fd.write( j.save() )
