#!/usr/bin/env python

from __future__ import print_function
import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.session import Session

TEST = 'examples/android/TestsAndroguard/bin/classes.dex'

s = Session()
with open(TEST, "r") as fd:
    digest, d, dx = s.addDEX(TEST, fd.read())

for method in d.get_methods():
    print(method.get_class_name(), method.get_name(), method.get_descriptor())
    code = method.get_code()

    if code != None:
        bc = code.get_bc()
        idx = 0
        for i in bc.get_instructions():
            print("\t", "%x" % idx, i.get_name(), i.get_output())
            idx += i.get_length()

for method in d.get_methods():
    print(method.get_class_name(), method.get_name(), method.get_descriptor())
    idx = 0
    for i in method.get_instructions():
        print("\t", "%x" % idx, i.get_name(), i.get_output())
        idx += i.get_length()
