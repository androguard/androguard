#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

from androguard.util import read
import jvm

TEST = "./examples/java/test/orig/Test1.class"

j = jvm.JVMFormat( read(TEST, binary=False) )

# SHOW CLASS (verbose)
j.show()

# SHOW FIELDS
for i in j.get_fields() :
    print i.get_access(), i.get_name(), i.get_descriptor()

print

# SHOW METHODS
for i in j.get_methods() :
    print i.get_access(), i.get_name(), i.get_descriptor()
