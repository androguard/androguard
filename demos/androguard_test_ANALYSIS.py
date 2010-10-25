#!/usr/bin/env python

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = [ './examples/java/test/orig/Test1.class' ]

a = androguard.Androguard( TEST )

a.analysis("test1")

