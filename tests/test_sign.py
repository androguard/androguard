#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

#TEST_CASE  = 'examples/android/TC/bin/classes.dex'
TEST_CASE = "apks/wat1.3.7.apk"

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
x = analysis.VM_BCA( a.get_vm(), code_analysis=True )

for method in a.get_methods() :
    key = method.get_class_name() + " " + method.get_name() + " " + method.get_descriptor()

    #if key not in VALUES :
    #   continue

    print method.get_class_name(), method.get_name(), method.get_descriptor()
    print "1 : \t", x.get_method_signature(method, 0)
    print "2 : \t", x.get_method_signature(method, 1)
    print "3 : \t", x.get_method_signature(method, 2, ["Landroid"])
    print "4 : \t", x.get_method_signature(method, 2, ["Ljava"])
    print "5 : \t", x.get_method_signature(method, 3, ["Landroid"])

#   if key in VALUES :
#      for i in VALUES[ key ] :
#         test( VALUES[ key ][i], x.get_method_signature(method, i) )
