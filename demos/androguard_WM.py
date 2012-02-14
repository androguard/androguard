#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

from androguard.core.androgen import AndroguardS, WM, WM_L2

#TEST_ORIG = './examples/android/Test/bin/classes/org/t0t0/android/Test1.class'
TEST_ORIG = './examples/java/test/orig/Test1.class'
TEST_MODIF_OUTPUT = './examples/java/test/new/'

TEST_JAVA_STEAL = './examples/java/test/orig/Test1.class'
TEST_ANDRO_STEAL = './examples/android/Test/bin/classes.dex'

_a = AndroguardS( TEST_ORIG )

#wm = androguard.WM( _a, "Test1", TEST_MODIF_OUTPUT, [ androguard.WM_L5 ], "./wm.xml" )
wm = WM( _a, "Test1", TEST_MODIF_OUTPUT, [ WM_L2 ], "./wm.xml")

#_b = androguard.AndroguardS( TEST_JAVA_STEAL )
#androguard.WMCheck( _b, "org.t0t0.android.Test1", "./wm.xml" )
