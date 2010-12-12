#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

import dvm

TEST = "./examples/android/Test/bin/Test-debug.apk"
TEST = "examples/android/Hello_Kitty/Hello_Kitty_Wallpapers_3.0.0.apk"

a = dvm.APK( TEST )
a.show()

j = dvm.DalvikVMFormat( a.get_dex() )

# SHOW CLASS (verbose) 
j.show()

# SHOW FIELDS
for i in j.get_fields() :
   print i.get_access(), i.get_name(), i.get_descriptor()

print

# SHOW METHODS
for i in j.get_methods() :
   print i.get_access(), i.get_name(), i.get_descriptor()

