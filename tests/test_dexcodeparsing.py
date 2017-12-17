from __future__ import print_function
from androguard.core.bytecodes.dvm import DalvikVMFormat
from binascii import hexlify
import parse_dex
import unittest
from difflib import Differ


class TestDexCodeParsing(unittest.TestCase):

    def testcode(self):
        # FIXME these methods do not produce the same output.
        # But we are not sure if the parse_dex is broken or androguard...
        skipped_methods = [1185, 1186, 1187, 1188, 1190, 1325, 1360, 1363, 1364,
                1365, 1366, 1367, 1368, 1369, 1370, 1372, 1374, 1375, 1376,
                1404, 1405, 3494, 3586, 611, 633, 634, 635, 640, 674, 824, 825,
                836, 1073, 1074]

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
                                 "{}".format(m.get_method_idx(),
                                             m.get_class_name(),
                                             m.get_name(),
                                             "".join(dif.compare(parsed[m.get_method_idx()],
                                             code))))


if __name__ == '__main__':
    unittest.main()
