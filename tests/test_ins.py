#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of  
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

import sys, re

PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis


TESTS_CASES  = [ #'examples/android/TC/bin/classes.dex',
                 'examples/android/TestsAndroguard/bin/classes.dex',
               ]

VALUES = { 
            'examples/android/TestsAndroguard/bin/classes.dex' : {
                  "Ltests/androguard/TestInvoke; <init> ()V" : {
                     0x0 : ("invoke-direct" , [['v',1] , ['meth@', 3, 'Ljava/lang/Object;', '()', 'V', '<init>']]),
                     0xa : ("invoke-virtual", [['v',1], ['v',0] , ['meth@', 28, 'Ltests/androguard/TestInvoke;', '(I)', 'I', 'TestInvoke1']]),
                  },
               }, 
            #"Lorg/t0t0/androguard/TC/TCA; <init> ()V" : {
            #   0 : ("invoke-direct", [['v', 4], ['meth@', 5, 'Ljava/lang/Object;', '()', 'V', '<init>']]),
            #   6 : ("const/16", [['v', 0], ['#+', 30]]),
            #   10 : ("iput", [['v', 0], ['v', 4], ['field@', 4, 'Lorg/t0t0/androguard/TC/TCA;', 'I', 'TC1']]),
            #   78 : ("invoke-virtual", [['v', 0], ['v', 1], ['meth@', 3, 'Ljava/io/PrintStream;', '(Ljava/lang/String;)', 'V', 'println']]),
            #},

            #"Lorg/t0t0/androguard/TC/TCE; <init> ()V" : {
            #   316 : ("if-ge", [['v', 2], ['v', 1], ['+', 12]]),
            #   332 : ("add-int/2addr", [['v', 3], ['v', 4]]),
            #   334 : ("add-int/lit8", [['v', 2], ['v', 2], ['#+', 1]]),
            #   386 : ("add-int/lit8", [['v', 3], ['v', 3], ['#+', 2]]),
            #},
}

def test(got, expected):
   if got == expected:
      prefix = ' OK '
   else:
      prefix = '  X '

   print '\t%s got: %s expected: %s' % (prefix, repr(got), repr(expected))

def getVal(i) :
   op = i.get_operands()

   if isinstance(op, int) :
      return [ op ]
   elif i.get_name() == "lookupswitch" :
      x = []

      x.append( i.get_operands().default )
      for idx in range(0, i.get_operands().npairs) :
         off = getattr(i.get_operands(), "offset%d" % idx)
         x.append( off )
      return x
   
   return [-1]

def check(a, values) :
   for method in a.get_methods() :
      key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()
  
      if key not in values :
         continue

      print "CHECKING ...", method.get_class_name(), method.get_name(), method.get_descriptor()
      code = method.get_code()
      bc = code.get_bc()

      idx = 0
      for i in bc.get() :
         #print "\t", "%x(%d)" % (idx, idx), i.get_name(), i.get_operands()
         if idx in values[key] :
            elem = values[key][idx]
            
            val1 = i.get_name() + "%s" % i.get_operands()
            val2 = elem[0] + "%s" % elem[1]
            
            test(val1, val2)
            
            del values[key][idx]

         idx += i.get_length()


for i in TESTS_CASES :
   a = androguard.AndroguardS( i )
   check( a, VALUES[i] )
