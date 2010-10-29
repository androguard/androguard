#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = './examples/android/Demo1/bin/classes/org/t0t0/androguard/android/Demo1Math.class'
TEST_STEAL = './examples/android/Demo1/bin/classes/org/t0t0/androguard/android/Demo1Math.class'

_a = androguard.AndroguardS( TEST )
_b = androguard.AndroguardS( TEST_STEAL )

androguard.WM( _a, "org/t0t0/androguard/android/Demo1Math", "rc4", "([B)[B", androguard.WM_CREATE_R, "./androguard_rc4_wm.xml" )
androguard.WMCheck( _b, "./androguard_rc4_wm.xml" )
