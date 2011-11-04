#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = [ './examples/java/test/orig/Test1.class', './examples/java/test/orig_main/Test.class' ]
TEST_OUTPUT = [ './examples/java/test/new/Test1.class', './examples/java/test/new_main/Test.class' ]

a = androguard.Androguard( TEST )

androguard.OBFU_Names( a, "Test1", "value", ".", androguard.OBFU_NAMES_FIELDS )
androguard.OBFU_Names( a, "Test1", ".", ".", androguard.OBFU_NAMES_METHODS )

i = 0
while i < len(TEST) :
    _a = a.get("file", TEST[i])

    fd = open( TEST_OUTPUT[i], "w" )
    fd.write( _a.save() )
    fd.close()

    i = i + 1
