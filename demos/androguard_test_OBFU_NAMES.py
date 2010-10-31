#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard

TEST = [ './examples/java/test/orig/Test1.class', './examples/java/test/orig_main/Test.class' ]
TEST_OUTPUT = [ './examples/java/test/new/Test1.class', './examples/java/test/new_main/Test.class' ]

a = androguard.Androguard( TEST )

androguard.OBFU_Names( )


fd = open( TEST_OUTPUT, "w" )
fd.write( a.save() )
fd.close()
