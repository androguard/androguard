#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk

from xml.dom import minidom

def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected)),
    return (got == expected)

TESTS = [ "./examples/axml/AndroidManifest.xml",
          "./examples/axml/AndroidManifest-Chinese.xml",
  #        "./examples/axml/test.xml",
          "./examples/axml/test1.xml",
          "./examples/axml/test2.xml",
          "./examples/axml/test3.xml" ]

import codecs

for i in TESTS :
    in1 = open( i, mode="rb" )

    ap = apk.AXMLPrinter( in1.read() )
    minidom.parseString( ap.getBuff() )

    print "PASSED", i
    #out = codecs.open("res.xml", "w", "utf-8")
    #out.write( s )
    #out.close()
