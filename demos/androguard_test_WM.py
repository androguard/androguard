#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST_ORIG = './examples/android/Test/bin/classes/org/t0t0/android/Test1.class'
TEST_JAVA_STEAL = './examples/java/test/orig/Test1.class'
TEST_ANDRO_STEAL = './examples/android/Test/bin/classes.dex'

_a = androguard.AndroguardS( TEST_ORIG )

wm = androguard.WM( _a, "org.t0t0.android.Test1", [ androguard.WM_L2, androguard.WM_L1, androguard.WM_L4 ], "./wm.xml" )

#_b = androguard.AndroguardS( TEST_JAVA_STEAL )
#androguard.WMCheck( _b, "org.t0t0.android.Test1", "./wm.xml" )
