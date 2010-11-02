#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = './examples/java/Demo1/orig/DES.class'
TEST_STEAL = ''
TEST_ANDRO = './examples/android/Demo1/bin/classes.dex'

_a = androguard.AndroguardS( TEST )
_b = androguard.AndroguardS( TEST_ANDRO )

wm = androguard.WM( _a, "DES", "desFunc" )

androguard.WMCheck( _b, wm.get_output() )
