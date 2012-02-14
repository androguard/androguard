#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk


from xml.dom import minidom

ap = apk.AXMLPrinter( open("examples/axml/AndroidManifest.xml", "r").read() )

print minidom.parseString( ap.getBuff() ).toxml()
