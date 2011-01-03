#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/analysis")

import dvm, analysis

TEST = "./examples/android/Test/bin/classes.dex"

j = dvm.DalvikVMFormat( open(TEST).read() )
x = analysis.VM_BCA( j )

# SHOW CLASS (verbose) 
# j.show()

# SHOW METHODS
for i in j.get_methods() :
   i.pretty_show(  x.hmethods[ i ] )
