#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

from androguard.core.androgen import Androguard, OBFU_Names, OBFU_NAMES_FIELDS, OBFU_NAMES_METHODS

TEST = [ './examples/java/test/orig/Test1.class', './examples/java/test/orig_main/Test.class' ]
TEST_OUTPUT = [ './examples/java/test/new/Test1.class', './examples/java/test/new_main/Test.class' ]

a = Androguard( TEST )

OBFU_Names( a, "Test1", "value", ".", OBFU_NAMES_FIELDS )
OBFU_Names( a, "Test1", ".", ".", OBFU_NAMES_METHODS )

i = 0
while i < len(TEST) :
    _a = a.get("file", TEST[i])

    fd = open( TEST_OUTPUT[i], "w" )
    fd.write( _a.save() )
    fd.close()

    i = i + 1
