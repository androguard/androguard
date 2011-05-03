#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

import dvm

TEST = "./examples/android/Test/bin/Test-debug.apk"
#TEST = "examples/android/Hello_Kitty/Hello_Kitty_Wallpapers_3.0.0.apk"
#TEST = "apks/TAT-LWP-Mod-Dandelion.apk"
#TEST = "apks/com.swampy.sexpos.apk-GEINIMI-INFECTED.apk"

a = dvm.APK( TEST )
a.show()

j = dvm.DalvikVMFormat( a.get_dex() )

# SHOW CLASS (verbose)
#j.show()
