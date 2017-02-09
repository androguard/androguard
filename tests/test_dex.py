import unittest

import sys
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import dvm


class DexTest(unittest.TestCase):

    def testDex(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex",
                  "rb") as fd:
            d = dvm.DalvikVMFormat(fd.read())
            self.assertTrue(d)

            classes = d.get_classes()
            self.assertTrue(classes)
            self.assertEqual(len(classes), 340)

            methods = d.get_methods()
            self.assertTrue(methods)
            self.assertEqual(len(methods), 2600)

            fields = d.get_fields()
            self.assertTrue(fields)
            self.assertEqual(len(fields), 803)

    def testMultiDex(self):
        pass


class InstructionTest(unittest.TestCase):

    def testNOP(self):
        instruction = dvm.Instruction10x(None, bytearray(b"\x00\x00"))
        self.assertEqual(instruction.get_name(), "nop")


if __name__ == '__main__':
    unittest.main()
