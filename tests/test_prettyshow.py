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
import bytecode

TEST_CASE  = 'examples/android/TC/bin/classes.dex'

VALUES = [ "Lorg/t0t0/androguard/TC/TCA; <init> ()V",
           "Lorg/t0t0/androguard/TC/TCE; equal (I Ljava/lang/String;)Ljava/lang/String;" ]


def test(got, expected):
   if got == expected:
      prefix = ' OK '
   else:
      prefix = '  X '

   print '\t%s got: %s expected: %s' % (prefix, repr(got), repr(expected))

a = androguard.AndroguardS( TEST_CASE )
ax = analysis.VM_BCA( a.get_vm() )

for method in a.get_methods() :
   key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()
   
   if key not in VALUES :
      continue

   bytecode.set_pretty_show( 0 )
   method.pretty_show( ax )

   bytecode.set_pretty_show( 1 )
   method.pretty_show( ax )

   bytecode.method2dot( ax.get_method(method) )
   #bytecode.method2png( "test.png", ax.get_method( method ) )
