#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
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

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis
from analysis import *

#TEST_CASE  = 'examples/android/TC/bin/classes.dex'
TEST_CASE  = 'apks/DroidDream/tmp/classes.dex'

GRAMMAR_TYPE_ANONYMOUS = 0

VALUES = { "Lorg/t0t0/androguard/TC/R$attr; <init> ()V" : {
               GRAMMAR_TYPE_ANONYMOUS : "BPMR",
           },

           "Lorg/t0t0/androguard/TC/R$drawable; <init> ()V" : {
              GRAMMAR_TYPE_ANONYMOUS : "BPMR",
           },

           "Lorg/t0t0/androguard/TC/R$layout; <init> ()V" : {
              GRAMMAR_TYPE_ANONYMOUS : "BPMR",
           },

           "Lorg/t0t0/androguard/TC/R$string; <init> ()V" : {
              GRAMMAR_TYPE_ANONYMOUS : "BPMR",
           },

           "Lorg/t0t0/androguard/TC/TCMod1; T1 ()V" : {
              GRAMMAR_TYPE_ANONYMOUS : "BBBFRIFWBFRGPCPMSPMFRSPMPMPMPMFRPCPMSPMSPMPMPMPMBBIBFRGPCPMSPMSPMPMPMPMFRFWFRPCPMSPMFRSPMPMPMPMBBIBBFRIFWBGBFRGPCPMSPMFRSPMPMPMPMFRPCPMSPMSPMPMPMPMFRPCPMSPMSPMPMPMPMBFRFWBFRIPCPMSPMFRSPMPMPMPMBR",
           }
}

def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected))


a = androguard.AndroguardS( TEST_CASE )
x = analysis.VMAnalysis( a.get_vm(), code_analysis=True )

for method in a.get_methods() :
    key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()

    #if key not in VALUES :
    #   continue

    print method.get_class_name(), method.get_name(), method.get_descriptor()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_0).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_1).get_string()
    print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_2).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_3).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_4).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_5).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_0_L1).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_0_L2).get_string()
    #print "-> : \t", x.get_method_signature(method, predef_sign = SIGNATURE_L0_0_L3).get_string()

    print

#   if key in VALUES :
#      for i in VALUES[ key ] :
#         test( VALUES[ key ][i], x.get_method_signature(method, i) )
