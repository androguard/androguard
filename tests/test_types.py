#!/usr/bin/env python

import sys

PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

TEST_CASE  = 'examples/android/TestCase/bin/classes.dex'

VALUES = { "Lorg/t0t0/android/TestCase1; <init> ()V" : [
                  42,
                  -42,
                  0,

                  42,
                  -42,
                  0,

                  42.0,
                  -42.0,
                  0.0,

                  42.0,
                  -42.0,
                  0.0,
            ],
}

def test(got, expected):
   if got == expected:
      prefix = ' OK '
   else:
      prefix = '  X '
   print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected))


a = androguard.AndroguardS( TEST_CASE )

for method in a.get_methods() :
   key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()

   if key not in VALUES :
      continue

   print method.get_class_name(), method.get_name(), method.get_descriptor()
   code = method.get_code()
   bc = code.get_bc()

   idx = 0
   for i in bc.get() :
   #   print "\t", "%x" % idx, i.get_name(), i.get_operands()
      if "const" in i.get_name() :
         formatted_operands = i.get_formatted_operands()
         for f in formatted_operands :
            test( f[1], VALUES[ key ].pop(0) )

      idx += i.get_length()
