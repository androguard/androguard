from __future__ import print_function
from androguard.core.bytecodes.dvm import DalvikVMFormat
from binascii import hexlify
import parse_dex
import unittest
from difflib import Differ


class TestDexCodeParsing(unittest.TestCase):

    def testcode(self):
        skipped_methods = []

        fname = "examples/android/TestsAndroguard/bin/classes.dex"

        parsed = parse_dex.read_dex(fname)

        with open(fname, "rb") as f:
            d = DalvikVMFormat(f.read())

            dif = Differ()

            for m in d.get_methods():
                if not m.get_code():
                    continue

                if m.get_method_idx() in skipped_methods:
                    continue

                code = hexlify(m.get_code().get_raw())
                self.assertEqual(parsed[m.get_method_idx()],
                                 code,
                                 "incorrect code for "
                                 "[{}]: {} --> {}:\n"
                                 "{}\ntries_size: {}, insns_size: {}\nSHOULD BE {}\n{}\n{}".format(m.get_method_idx(),
                                             m.get_class_name(),
                                             m.get_name(),
                                             "".join(dif.compare(parsed[m.get_method_idx()],
                                             code)),
                                             m.get_code().tries_size,
                                             m.get_code().insns_size,
                                             hexlify(m.get_code().get_raw()),
                                             parsed[m.get_method_idx()],
                                             hexlify(m.get_code().code.get_raw())))


if __name__ == '__main__':
    unittest.main()
