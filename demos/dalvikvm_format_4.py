#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/analysis")
sys.path.append(PATH_INSTALL + "/decompiler")

import dvm, analysis, decompiler

#TEST = "examples/android/TestsAndroguard/bin/classes.dex"
TEST = "apks/malwares/DroidDream/tmp/classes.dex"

j = dvm.DalvikVMFormat( open(TEST).read() )
d = decompiler.DecompilerDex2Jad( j )
#d = decompiler.DecompilerDed( j )
j.set_decompiler( d )

# SHOW METHODS
for i in j.get_methods() :
    if i.get_name() == "onCreate" :
        print i.get_class_name(), i.get_name()
        i.source()

#    if i.get_name() == "testWhileTrue" :
#        i.source()
