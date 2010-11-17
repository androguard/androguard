#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = './examples/android/Test/bin/classes/org/t0t0/android/Test1.class'
TEST_STEAL = ''
TEST_ANDRO = './examples/android/Test/bin/classes.dex'

_a = androguard.AndroguardS( TEST )

wm = androguard.WM( _a, "org.t0t0.android.Test1", [ androguard.WM_L1 ], "./wm.xml" )

_b = androguard.AndroguardS( TEST_ANDRO )
androguard.WMCheck( _b, "./wm.xml" )
