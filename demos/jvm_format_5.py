#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/analysis")

from androguard.util import read
import jvm, analysis

TEST = "./examples/java/test/orig/Test1.class"

j = jvm.JVMFormat( read(TEST, binary=False) )
x = analysis.VMAnalysis( j )

# SHOW CLASS (verbose and pretty)
#j.pretty_show( x )

# SHOW METHODS
for i in j.get_methods() :
    print i
    i.pretty_show( x )
