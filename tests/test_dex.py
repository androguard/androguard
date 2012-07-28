#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import apk
from androguard.core.bytecodes import dvm

def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected)),
    return (got == expected)

def test_dex_save() :
  pass

def test_dex_
TESTS = [ "" ]

for i in TESTS :
    in1 = open( i, mode="rb" )

    ap = apk.AXMLPrinter( in1.read() )
    minidom.parseString( ap.getBuff() )

    print "PASSED", i
    #out = codecs.open("res.xml", "w", "utf-8")
    #out.write( s )
    #out.close()
