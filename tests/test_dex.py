import unittest

import sys

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

    def testDexWrapper(self):
        from androguard.misc import AnalyzeDex
        from androguard.core.bytecodes.dvm import DalvikVMFormat
        from androguard.core.analysis.analysis import Analysis
        h, d, dx = AnalyzeDex("examples/android/TestsAndroguard/bin/classes.dex")
        self.assertEqual(h, '2f24538b3064f1f88d3eb29ee7fbd2146779a4c9144aefa766d18965be8775c7')
        self.assertIsInstance(d, DalvikVMFormat)
        self.assertIsInstance(dx, Analysis)

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
