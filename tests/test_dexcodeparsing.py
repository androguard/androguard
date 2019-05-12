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
            self.assertEqual(parsed.methods[m.get_method_idx()],
                             code,
                             "incorrect code for "
                             "[{}]: {} --> {}:\n"
                             "{}\ntries_size: {}, insns_size: {}\nSHOULD BE {}\n{}\n{}".format(m.get_method_idx(),
                                         m.get_class_name(),
                                         m.get_name(),
                                         "".join(dif.compare(parsed.methods[m.get_method_idx()],
                                         code)),
                                         m.get_code().tries_size,
                                         m.get_code().insns_size,
                                         hexlify(m.get_code().get_raw()),
                                         parsed.methods[m.get_method_idx()],
                                         hexlify(m.get_code().code.get_raw())))

    def testClassManager(self):
        """Test if the classmanager has the same items"""

        from androguard.core.mutf8 import decode

        fname = "examples/android/TestsAndroguard/bin/classes.dex"

        parsed = parse_dex.read_dex(fname)

        with open(fname, "rb") as f:
            d = DalvikVMFormat(f.read())

        cm = d.get_class_manager()

        self.assertFalse(cm.get_odex_format())

        ERR_STR = 'AG:IS: invalid string'

        ## Testing Strings...
        for idx in range(parsed.string_ids_size):
            self.assertNotEqual(cm.get_string(idx), ERR_STR)
            self.assertNotEqual(cm.get_raw_string(idx), ERR_STR)
            self.assertEqual(cm.get_raw_string(idx), decode(parsed.str_raw[idx]))

        self.assertEqual(cm.get_string(parsed.string_ids_size), ERR_STR)
        self.assertEqual(cm.get_raw_string(parsed.string_ids_size), ERR_STR)

        self.assertEqual(cm.get_string(parsed.string_ids_size + 100), ERR_STR)
        self.assertEqual(cm.get_raw_string(parsed.string_ids_size + 100), ERR_STR)



if __name__ == '__main__':
    unittest.main()
