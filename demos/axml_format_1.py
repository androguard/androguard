#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")

from xml.dom import minidom
import apk 

ap = apk.AXMLPrinter( open("examples/axml/AndroidManifest.xml", "r").read() )

print minidom.parseString( ap.getBuff() ).toxml()
