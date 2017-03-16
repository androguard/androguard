#!/usr/bin/env python

from __future__ import print_function
import sys, hashlib

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.session import Session

TEST = 'examples/android/TestsAndroguard/bin/classes.dex'

s = Session()
with open(TEST, "r") as fd:
    digest, d, dx = s.addDEX(TEST, fd.read())

for method in d.get_methods():
    g = dx.get_method(method)

    if method.get_code() == None:
        continue

    idx = 0
    for i in g.basic_blocks.get():
        for ins in i.get_instructions():
            op_value = ins.get_op_value()

            # packed/sparse
            if op_value == 0x2b or op_value == 0x2c:
                special_ins = i.get_special_ins(idx)
                if special_ins != None:
                    print("\t %x" % idx, ins, special_ins, ins.get_name(
                    ), ins.get_output(), special_ins.get_values())
            # fill
            if op_value == 0x26:
                special_ins = i.get_special_ins(idx)
                if special_ins != None:
                    print("\t %x" % idx, ins, special_ins, ins.get_name(
                    ), ins.get_output(), repr(special_ins.get_data()))

            idx += ins.get_length()
