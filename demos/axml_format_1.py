#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

import dvm

TEST = "./examples/android/Test/bin/Test-debug.apk"
#TEST = "examples/android/Hello_Kitty/Hello_Kitty_Wallpapers_3.0.0.apk"

#ap = dvm.AXMLPrinter( open("/tmp/AndroidManifest.xml", "r").read() )
ap = dvm.AXMLPrinter( open("apks/tmp/AndroidManifest.xml", "r").read() )

fd = open("TotoManifest.xml", "w")
fd.write( ap.getBuff() )
fd.close()
