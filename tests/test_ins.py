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


TEST_CASE  = 'examples/android/TC/bin/classes.dex'

VALUES = { "Lorg/t0t0/androguard/TC/TCA; <init> ()V" : [
                  ("return", [-1]),
            ],
}

###############################################
MODIF = { "TCE <init> ()V" : [
            ("remove_at", 28),
       ]
}
###############################################

###############################################
MODIF2 = { "TCE <init> ()V" : [
            ("insert_at", 28, [ "aload_0"]),
         ]
}
###############################################

###############################################
MODIF3 = { "TCE <init> ()V" : [
            ("remove_at", 88),
         ]
}

VALUES3 = { "TCE <init> ()V" : [
                  ("if_icmpge", [113]),
                  ("if_icmpge", [16]),
                  ("goto", [-15]),
                  ("lookupswitch", [22, 19]),
                  ("lookupswitch", [47, 40, 34, 37]),
                  ("goto", [-120]),
                  ("return", [-1]),
            ],
}
###############################################

###############################################
MODIF4 = { "TCE <init> ()V" : [
            ("insert_at", 88, [ "sipush", 400 ]),
         ]
}
###############################################

###############################################
MODIF4 = { "TCE <init> ()V" : [
            ("insert_at", 88, [ "sipush", 400 ]),
         ]
}
###############################################


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

def check(a, values, branch) :
   b = []
   for i in branch : 
      b.append( re.compile( i ) )

   for method in a.get_methods() :
      key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()
   
      if key not in values :
         continue

      print "CHECKING ...", method.get_class_name(), method.get_name(), method.get_descriptor()
      code = method.get_code()
      bc = code.get_bc()

      idx = 0
      v = 0
      for i in bc.get() :
#         print "\t", "%x(%d)" % (idx, idx), i.get_name(), i.get_operands()
         for j in b :
            if j.match(i.get_name()) != None :
               elem = values[key][v]
               test("%s %s" % (elem[0], elem[1]), "%s %s" % (i.get_name(), getVal(i)))

               v += 1
               break

         idx += i.get_length()

def modify(a, modif) :
   for method in a.get_methods() :
      key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()

      if key not in modif :
         continue

      print "MODIFYING ...", method.get_class_name(), method.get_name(), method.get_descriptor()
      code = method.get_code()

      for i in modif[key] :
         getattr( code, i[0] )( *i[1:] )

a = androguard.AndroguardS( TEST_CASE )

### INIT CHECK ###
check( a, VALUES, BRANCH2_JVM_OPCODES )
### APPLY MODIFICATION ###
modify( a, MODIF )
### CHECK IF MODIFICATION IS OK ###
check( a, VALUES, BRANCH2_JVM_OPCODES )

modify( a, MODIF2 )
check( a, VALUES, BRANCH2_JVM_OPCODES )

modify( a, MODIF3 )
check( a, VALUES3, BRANCH2_JVM_OPCODES )

modify( a, MODIF4 )
check( a, VALUES, BRANCH2_JVM_OPCODES )
