import unittest

import sys
import binascii

from androguard.core.bytecodes import dvm


class FakeClassManager:
    def get_odex_format(self):
        return False


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

                for m in d.get_methods():
                    l = 0
                    i = -1
                    for i, ins in enumerate(m.get_instructions()):
                        l += ins.get_length()
                        if ins.get_op_value() <= 0xFF:
                            self.assertIsInstance(ins, dvm.Instruction)
                        else:
                            self.assertIn(ins.get_name(), ('fill-array-data-payload',
                                                           'packed-switch-payload',
                                                           'sparse-switch-payload'))
                    if m.get_code() is not None:
                        # Make sure all instructions are parsed
                        self.assertGreaterEqual(i + 1, 1)
                        self.assertEqual(l % 2, 0)
                        self.assertEqual(l, m.get_code().insns_size * 2)


class InstructionTest(unittest.TestCase):
    def testInstructions(self):
        """Tests if all instructions are at least covered"""
        for op_value in range(0, 256):
            ins = dvm.DALVIK_OPCODES_FORMAT[op_value][0]
            self.assertEqual(issubclass(ins, dvm.Instruction), True)

            # The Name should code for the length of the opcode
            length = int(ins.__name__[11]) * 2
            self.assertEqual(ins.length, length)

    def testNOP(self):
        """test if NOP instructions are parsed"""
        instruction = dvm.Instruction10x(FakeClassManager(), bytearray(b"\x00\x00"))
        self.assertEqual(instruction.get_name(), "nop")

    def testLinearSweep(self):
        bytecode = bytearray(b"\x00\x00\x00\x00\x00\x00\x0e\x00")

        instructions = ['nop', 'nop', 'nop', 'return-void']
        l = 0

        for ins in dvm.LinearSweepAlgorithm.get_instructions(FakeClassManager(), 4, bytecode, 0):
            self.assertIsInstance(ins, dvm.Instruction10x)
            self.assertEqual(ins.get_length(), 2)
            self.assertEqual(ins.get_name(), instructions.pop(0))
            l += ins.get_length()

        self.assertEqual(instructions, [])
        self.assertEqual(len(bytecode), l)

    def testLinearSweepStrings(self):
        # very basic function, strings and invokes
        bytecode = bytearray(binascii.unhexlify('1A000F001A0100001A0214001A0311001A0415001A0413001A0508001A061200'
                                                '1A0716001A081000620900006E2002000900620000006E200200100062000000'
                                                '6E2002002000620000006E2002003000620000006E2002003000620000006E20'
                                                '02004000620000006E2002005000620000006E2002006000620000006E200200'
                                                '7000620000006E20020080000E00'))
        instructions = [
            'const-string', 'const-string',
            'const-string', 'const-string',
            'const-string', 'const-string',
            'const-string', 'const-string',
            'const-string', 'const-string',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'sget-object', 'invoke-virtual',
            'return-void',
        ]
        l = 0

        for ins in dvm.LinearSweepAlgorithm.get_instructions(FakeClassManager(), 71, bytecode, 0):
            self.assertIsInstance(ins, dvm.Instruction)
            self.assertEqual(ins.get_name(), instructions.pop(0))
            l += ins.get_length()
        # check if all instructions were consumed
        self.assertEqual(instructions, [])
        # Check if all bytes are read
        self.assertEqual(len(bytecode), l)
        
    def testLinearSweepSwitch(self):
        """test if switch payloads are unpacked correctly"""
        bytecode = bytearray(binascii.unhexlify('2B02140000001300110038030400130063000F001300170028F913002A0028F6'
                                                '1300480028F3000000010300010000000A0000000D00000010000000'))

        instructions = [
            'packed-switch',
            'const/16',
            'if-eqz',
            'const/16',
            'return',
            'const/16',
            'goto',
            'const/16',
            'goto',
            'const/16',
            'goto',
            'nop',
            'packed-switch-payload',
        ]
        l = 0

        for ins in dvm.LinearSweepAlgorithm.get_instructions(FakeClassManager(), 30, bytecode, 0):
            if len(instructions) > 1:
                self.assertIsInstance(ins, dvm.Instruction)
            else:
                self.assertIsInstance(ins, dvm.PackedSwitch)
            self.assertEqual(ins.get_name(), instructions.pop(0))
            l += ins.get_length()
        # check if all instructions were consumed
        self.assertEqual(instructions, [])
        self.assertEqual(len(bytecode), l)

    def testLSAArrays(self):
        """Test if fill-array-data-payload is parsed"""
        bytecode = bytearray(binascii.unhexlify('12412310030026002D0000005B30000012702300050026002B0000005B300300'
                                                '1250230004002600350000005B300100231007002600380000005B3002001220'
                                                '2300060012011A020D004D02000112111A0211004D0200015B3004000E000000'
                                                '0003010004000000141E28320003040007000000010000000200000003000000'
                                                '0400000005000000E70300000A899D0000030200050000006100620078007A00'
                                                '63000000000302000400000005000A000F001400'))

        instructions = [
            'const/4', 'new-array', 'fill-array-data', 'iput-object',
            'const/4', 'new-array', 'fill-array-data', 'iput-object',
            'const/4', 'new-array', 'fill-array-data', 'iput-object',
            'new-array', 'fill-array-data', 'iput-object',
            'const/4', 'new-array',
            'const/4', 'const-string', 'aput-object',
            'const/4', 'const-string', 'aput-object',
            'iput-object',
            'return-void',
            'nop',  # alignment
            'fill-array-data-payload',
            'fill-array-data-payload',
            'fill-array-data-payload',
            'nop',  # alignment
            'fill-array-data-payload',
        ]
        l = 0

        # array information: (element_width, size)
        arrays = [(1, 4), (4, 7), (2, 5), (2, 4)]

        for ins in dvm.LinearSweepAlgorithm.get_instructions(FakeClassManager(), 90, bytecode, 0):
            self.assertEqual(ins.get_name(), instructions.pop(0))
            if ins.get_name() != 'fill-array-data-payload':
                self.assertIsInstance(ins, dvm.Instruction)
            else:
                self.assertIsInstance(ins, dvm.FillArrayData)
                elem_size, size = arrays.pop(0)
                self.assertEqual(ins.element_width, elem_size)
                self.assertEqual(ins.size, size)
            l += ins.get_length()

        # check if all instructions were consumed
        self.assertEqual(instructions, [])
        self.assertEqual(arrays, [])
        self.assertEqual(len(bytecode), l)

    def testWrongInstructions(self):
        """Test if unknown instructions throws an error"""
        with self.assertRaises(dvm.InvalidInstruction):
            for _ in dvm.LinearSweepAlgorithm.get_instructions(FakeClassManager(), 1, bytearray(b"\xff\xab"), 0):
                pass

    def testIncompleteInstruction(self):
        """Test if incomplete bytecode throws an error"""
        # Test if instruction can be parsed
        self.assertIsInstance(dvm.Instruction51l(FakeClassManager(),
                                                 bytearray(b'\x18\x01\x23\x23\x00\xff\x99\x11\x22\x22')), dvm.Instruction51l)

        with self.assertRaises(dvm.InvalidInstruction):
            # const-wide should be 10 bytes long
            for _ in dvm.LinearSweepAlgorithm.get_instructions(FakeClassManager(), 5, bytearray(b"\x18\x01\xff\xff"), 0):
                pass


if __name__ == '__main__':
    unittest.main()
