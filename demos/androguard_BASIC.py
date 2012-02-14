#!/usr/bin/env python

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

from androguard.core.androgen import AndroguardS

TEST = [ './examples/java/Hello.class' ]

_a = AndroguardS( TEST[0] )
_a.show()


for field in _a.gets("fields") :
    print field.get_name(), field.get_descriptor()

for method in _a.get("method", "test") :
    print method.get_name(), method.get_descriptor()

method, _ =_a.get_method_descriptor("Hello", "test", "([B)[B")
print method.get_name()

for method in _a.gets("methods") :
    print method.get_name()
