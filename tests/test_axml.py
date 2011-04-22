#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./core/")
sys.path.append(PATH_INSTALL + "./core/bytecodes/")

import dvm

from xml.dom import minidom

def test(got, expected):
   if got == expected:
      prefix = ' OK '
   else:
      prefix = '  X '
   print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected)),
   return (got == expected)

def hexdump(src, length=8, off=0):
   result = []   
   digits = 4 if isinstance(src, unicode) else 2
   for i in xrange(0, len(src), length):   
      s = src[i:i+length]
      hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])      
      text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
      result.append( b"%04X   %-*s   %s" % (i+off, length*(digits + 1), hexa, text) )      
   return b'\n'.join(result)

TESTS = [ "./examples/axml/AndroidManifest.xml",
          "./examples/axml/AndroidManifest-Chinese.xml" ]

for i in TESTS :
   ap = dvm.AXMLPrinter( open( i, "r").read() )
   buff = minidom.parseString( ap.getBuff() ).toprettyxml()

