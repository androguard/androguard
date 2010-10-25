#!/usr/bin/env python

import sys, os

PATH_INSTALL = "./"

import androguard

TEST_RC4 = ['./examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/R.class', './examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/RC4.class', './examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/RC4Activity.class', './examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/R$attr.class', './examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/R$layout.class', './examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/R$string.class']

TEST_RC4 = ['./examples/android/test_rc4_app/bin/classes/org/t0t0/testrc4/RC4.class']

def get_classes(path) :
   g_files = []
   for root, dirs, files in os.walk( path ) :
      if files != [] :
         for file in files :
            if ".class" in file :
               g_files.append(root + "/" + file)

   return g_files

def __main__() :
#   if len( sys.argv ) > 1 :
#      files = get_classes( sys.argv[1] )
#      a = Androguard( files )

   a = androguard.Androguard( TEST_RC4 )

__main__()
