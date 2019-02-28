import unittest

import sys
import logging

from androguard.core.bytecodes import dvm


log = logging.getLogger("androguard.tests")

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
            ('examples/dalvik/test/bin/classes_output.dex', 35),
            ('examples/dalvik/test/bin/classes.dex', 35),
            ('examples/obfu/classes_tc_diff_dasho.dex', 35),
            ('examples/obfu/classes_tc_dasho.dex', 35),
            ('examples/obfu/classes_tc_mark1.dex', 35),
            ('examples/obfu/classes_tc.dex', 35),
            ('examples/obfu/classes_tc_diff.dex', 35),
            ('examples/obfu/classes_tc_proguard.dex', 35),
            ('examples/android/TCDiff/bin/classes.dex', 35),
            ('examples/android/TestsAndroguard/bin/classes.dex', 35),
            ('examples/android/TC/bin/classes.dex', 35),
            ('examples/tests/Test.dex', 35),
            ('examples/tests/ExceptionHandling.dex', 35),
            ('examples/tests/InterfaceCls.dex', 35),
            ('examples/tests/FillArrays.dex', 35),
            ('examples/tests/StringTests.dex', 35),
            ('examples/tests/AnalysisTest.dex', 35),
            ('examples/tests/Switch.dex', 35),
                ]

        for dexf, dexver in dexfiles:
            log.info("Testing {} -> Version {}".format(dexf, dexver))
            with open(dexf, 'rb') as fp:
                d = dvm.DalvikVMFormat(fp.read())

                self.assertEqual(d.version, dexver)

                self.assertGreater(d.header.string_ids_size, 0)
                self.assertGreater(d.header.type_ids_size, 0)
                self.assertGreater(d.header.proto_ids_size, 0)
                self.assertGreater(d.header.method_ids_size, 0)
                self.assertGreater(d.header.class_defs_size, 0)
                self.assertGreater(d.header.data_size, 0)

                for i in range(d.header.string_ids_size):
                    self.assertIsInstance(d.strings[i], dvm.StringDataItem)

                for m in d.get_methods():
                    log.debug("%s -> %s", m, m.get_code_off())
                    ins_length = 0
                    for ins in m.get_instructions():
                        self.assertNotIsInstance(ins, dvm.InstructionInvalid)
                        self.assertNotIsInstance(ins, dvm.Unresolved)

                        ins_length += ins.get_length()
                    if m.get_code_off() != 0:
                        # Test if all opcodes have been consumed
                        # insns_size is number of 16bit units, but instruction
                        # returns len in bytes
                        self.assertEqual(ins_length % 2, 0)
                        self.assertEqual(m.get_code().insns_size * 2, ins_length)


class InstructionTest(unittest.TestCase):
    def testNOP(self):
        instruction = dvm.Instruction10x(None, bytearray(b"\x00\x00"))
        self.assertEqual(instruction.get_name(), "nop")


if __name__ == '__main__':
    unittest.main()
