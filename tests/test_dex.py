import unittest

import sys

from androguard.core.bytecodes import dvm


class DexTest(unittest.TestCase):
    def testDex(self):
        with open("examples/android/TestsAndroguard/bin/classes.dex", "rb") as fd:
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


    def testDexVersion(self):
        dexfiles = [
            'examples/dalvik/test/bin/classes_output.dex',
            'examples/dalvik/test/bin/classes.dex',
            'examples/obfu/classes_tc_diff_dasho.dex',
            'examples/obfu/classes_tc_dasho.dex',
            'examples/obfu/classes_tc_mark1.dex',
            'examples/obfu/classes_tc.dex',
            'examples/obfu/classes_tc_diff.dex',
            'examples/obfu/classes_tc_proguard.dex',
            'examples/android/TCDiff/bin/classes.dex',
            'examples/android/TestsAndroguard/bin/classes.dex',
            'examples/android/TC/bin/classes.dex',
            'examples/tests/Test.dex',
            'examples/tests/ExceptionHandling.dex',
            'examples/tests/InterfaceCls.dex',
            'examples/tests/FillArrays.dex',
            'examples/tests/StringTests.dex',
            'examples/tests/AnalysisTest.dex',
            'examples/tests/Switch.dex',
                ]

        for dexf in dexfiles:
            print(dexf)
            with open(dexf, 'rb') as fp:
                d = dvm.DalvikVMFormat(fp.read())

                self.assertEqual(d.version, 35)

                self.assertGreater(d.header.string_ids_size, 0)
                self.assertGreater(d.header.type_ids_size, 0)
                self.assertGreater(d.header.proto_ids_size, 0)
                self.assertGreater(d.header.method_ids_size, 0)
                self.assertGreater(d.header.class_defs_size, 0)
                self.assertGreater(d.header.data_size, 0)

                for i in range(d.header.string_ids_size):
                    self.assertIsInstance(d.strings[i], dvm.StringDataItem)


class MockClassManager():
    @property
    def packer(self):
        return dvm.DalvikPacker(0x12345678)


class InstructionTest(unittest.TestCase):
    def testNOP(self):
        instruction = dvm.Instruction10x(MockClassManager(), bytearray(b"\x00\x00"))
        self.assertEqual(instruction.get_name(), "nop")


if __name__ == '__main__':
    unittest.main()
