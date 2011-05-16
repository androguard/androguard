#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

import dvm, apk 

#TEST = "./examples/android/TC/bin/TC-debug.apk"
TEST = "./apks/iCalendar.apk"

a = apk.APK( TEST )
a.show()

j = dvm.DalvikVMFormat( a.get_dex() )

# SHOW CLASS (verbose)
#j.show()
