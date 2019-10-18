import unittest

import sys
import random
import binascii
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

    def testBrokenDex(self):
        """Test various broken DEX headers"""
        # really not a dex file
        with self.assertRaises(ValueError) as cnx:
            dvm.DalvikVMFormat(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertIn('Header too small', str(cnx.exception))

        # Adler32 will not match, zeroed out file
        dex = binascii.unhexlify('6465780A303335001F6C4D5A6ACF889AF588F3237FC9F20B41F56A2408749D1B'
                                 'C81E000070000000785634120000000000000000341E00009400000070000000'
                                 '2E000000C0020000310000007803000011000000C4050000590000004C060000'
                                 '090000001409000094140000340A0000' + ('00' * (7880 - 0x70)))

        with self.assertRaises(ValueError) as cnx:
            dvm.DalvikVMFormat(dex)
        self.assertIn("Adler32", str(cnx.exception))

        # A very very basic dex file (without a map)
        # But should parse...
        dex = binascii.unhexlify('6465780A30333500460A4882696E76616C6964696E76616C6964696E76616C69'
                                 '7000000070000000785634120000000000000000000000000000000000000000'
                                 '0000000000000000000000000000000000000000000000000000000000000000'
                                 '00000000000000000000000000000000')
        with self.assertLogs(logger='androguard.dvm', level=logging.WARNING) as cnx:
            self.assertIsNotNone(dvm.DalvikVMFormat(dex))
        self.assertEqual(cnx.output, ["WARNING:androguard.dvm:no map list! This DEX file is probably empty."])

        # Wrong header size
        dex = binascii.unhexlify('6465780A30333500480A2C8D696E76616C6964696E76616C6964696E76616C69'
                                 '7100000071000000785634120000000000000000000000000000000000000000'
                                 '0000000000000000000000000000000000000000000000000000000000000000'
                                 '0000000000000000000000000000000000')
        with self.assertRaises(ValueError) as cnx:
            dvm.DalvikVMFormat(dex)
        self.assertIn("Wrong header size", str(cnx.exception))

        # Non integer version
        dex = binascii.unhexlify('6465780AFF00AB00460A4882696E76616C6964696E76616C6964696E76616C69'
                                 '7000000070000000785634120000000000000000000000000000000000000000'
                                 '0000000000000000000000000000000000000000000000000000000000000000'
                                 '00000000000000000000000000000000')
        with self.assertLogs(logger='androguard.dvm', level=logging.WARNING) as cnx:
            dvm.DalvikVMFormat(dex)
        self.assertEqual(cnx.output, ["WARNING:androguard.dvm:Wrong DEX version: b'dex\\n\\xff\\x00\\xab\\x00', trying to parse anyways",
                                      "WARNING:androguard.dvm:no map list! This DEX file is probably empty."])

        # Big Endian file
        dex = binascii.unhexlify('6465780A30333500460AF480696E76616C6964696E76616C6964696E76616C69'
                                 '7000000070000000123456780000000000000000000000000000000000000000'
                                 '0000000000000000000000000000000000000000000000000000000000000000'
                                 '00000000000000000000000000000000')
        with self.assertRaises(NotImplementedError) as cnx:
            dvm.DalvikVMFormat(dex)
        self.assertIn("swapped endian tag", str(cnx.exception))

        # Weird endian file
        dex = binascii.unhexlify('6465780A30333500AB0BC3E4696E76616C6964696E76616C6964696E76616C69'
                                 '7000000070000000ABCDEF120000000000000000000000000000000000000000'
                                 '0000000000000000000000000000000000000000000000000000000000000000'
                                 '00000000000000000000000000000000')
        with self.assertRaises(ValueError) as cnx:
            dvm.DalvikVMFormat(dex)
        self.assertIn("Wrong endian tag", str(cnx.exception))

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
            # Dalvik 036
            ('examples/tests/2992e3a94a774ddfe2b50c6e8667d925a5684d71.36.dex', 36),
            ('examples/tests/921d74ac9568121d0ea1453922a369cb66739c68.36.dex', 36),
            # Dalvik 037
            ('examples/tests/dc4b1bb9d58daa82f29e60f79d5662f731a3351f.37.dex', 37),
            ('examples/tests/fdroid/com.example.trigger_130.dex', 37),
            ('examples/tests/fdroid/net.eneiluj.nextcloud.phonetrack_2.dex', 37),
            ('examples/tests/fdroid/org.andstatus.app_254.dex', 37),
            # Dalvik 038 / Requires a minimal API level of 26
            ('examples/tests/fdroid/cat.mvmike.minimalcalendarwidget_17.dex', 38),
            ('examples/tests/okhttp.d8.038.dex', 38),
            ('examples/tests/okhttp.dx.038.dex', 38),  # contains invoke-custom opcode
            # Dalvik 039 / Requires a minimal API level of 28
            ('examples/tests/okhttp.d8.039.dex', 39),
            ('examples/tests/okhttp.dx.039.dex', 39),  # contains invoke-custom opcode
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


class MockClassManager():
    @property
    def packer(self):
        return dvm.DalvikPacker(0x12345678)

    def get_odex_format(self):
        return False


class InstructionTest(unittest.TestCase):
    def testInstructions(self):
        """Tests if all instructions are at least covered"""
        # Set the seed here, so we have reproduceable results later
        random.seed(1337)

        for op_value in range(0, 256):
            ins = dvm.DALVIK_OPCODES_FORMAT[op_value][0]
            name = dvm.DALVIK_OPCODES_FORMAT[op_value][1]
            self.assertEqual(issubclass(ins, dvm.Instruction), True)

            # The Name should code for the length of the opcode
            length = int(ins.__name__[11]) * 2
            self.assertEqual(ins.length, length)

            if name[0] == 'unused':
                # unused instructions should raise an error on invocation
                with self.assertRaises(dvm.InvalidInstruction):
                    ins(MockClassManager(), bytearray([op_value, 0]))
                # therefore, we can not test much else here...
                continue

            # Test if instruction can be parsed
            bytecode = bytearray([op_value] + [0] * (length - 1))
            instruction = ins(MockClassManager(), bytecode)
            self.assertIsInstance(instruction, dvm.Instruction)
            self.assertEqual(instruction.get_op_value(), op_value)

            # And packed again
            self.assertEqual(instruction.get_raw(), bytecode)

            # Test with some pseudorandom stuff
            if ins.__name__ in ['Instruction10x', 'Instruction20t', 'Instruction30t', 'Instruction32x', 'Instruction45cc']:
                # note this only works for certain opcode (which are not forced to 0 in certain places)
                # Thus we need to make sure these places are zero.
                # Instruction45cc: Has constrained regarding the parameter AA
                bytecode = bytearray([op_value, 0] + [random.randint(0x00, 0xff) for _ in range(length - 2)])
            else:
                bytecode = bytearray([op_value] + [random.randint(0x00, 0xff) for _ in range(length - 1)])
            instruction = ins(MockClassManager(), bytecode)
            self.assertIsInstance(instruction, dvm.Instruction)
            self.assertEqual(instruction.get_op_value(), op_value)
            self.assertEqual(instruction.get_raw(), bytecode)

    def testNOP(self):
        """test if NOP instructions are parsed"""
        instruction = dvm.Instruction10x(MockClassManager(), bytearray(b"\x00\x00"))
        self.assertEqual(instruction.get_name(), "nop")

    def testLinearSweep(self):
        bytecode = bytearray(b"\x00\x00\x00\x00\x00\x00\x0e\x00")

        instructions = ['nop', 'nop', 'nop', 'return-void']
        l = 0

        for ins in dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 4, bytecode, 0):
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

        for ins in dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 71, bytecode, 0):
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

        for ins in dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 30, bytecode, 0):
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

        for ins in dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 90, bytecode, 0):
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
        """Test if unknown instructions log an error"""
        with self.assertLogs(logger='androguard.dvm', level=logging.ERROR) as cnx:
            ins = list(dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 1, bytearray(b"\xff\xab"), 0))
        self.assertEqual(cnx.output, ["ERROR:androguard.dvm:Invalid instruction encountered! "
                                      "Stop parsing bytecode at idx 0. Message: Unknown Instruction '0xabff'"])
        self.assertEqual(len(ins), 0)  # No instruction should be parsed

        with self.assertLogs(logger='androguard.dvm', level=logging.ERROR) as cnx:
            ins = list(dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 2, bytearray(b"\x00\x00"
                                                                                                  b"\xff\xab"), 0))
        self.assertEqual(cnx.output, ["ERROR:androguard.dvm:Invalid instruction encountered! "
                                      "Stop parsing bytecode at idx 2. Message: Unknown Instruction '0xabff'"])
        self.assertEqual(len(ins), 1)  # One instruction should be parsed

    def testIncompleteInstruction(self):
        """Test if incomplete bytecode log an error"""
        # Test if instruction can be parsed
        self.assertIsInstance(dvm.Instruction51l(MockClassManager(),
                                                 bytearray(b'\x18\x01\x23\x23\x00\xff\x99\x11\x22\x22')), dvm.Instruction51l)

        ins = list(dvm.LinearSweepAlgorithm.get_instructions(MockClassManager(), 5, bytearray(b"\x18\x01\xff\xff"), 0))
        self.assertEqual(len(ins), 0)

    def testInstruction21h(self):
        """Test function of Instruction 21h used for const{,-wide}/high16"""
        ins = dvm.Instruction21h(MockClassManager(), bytearray([0x15, 0x00, 0x42, 0x11]))
        self.assertEqual(ins.get_op_value(), 0x15)
        self.assertEqual(ins.get_literals(), [0x11420000])
        self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, 0x00), (dvm.Operand.LITERAL, 0x11420000)])
        self.assertEqual(ins.get_name(), 'const/high16')
        self.assertEqual(ins.get_output(), 'v0, 289538048')
        self.assertEqual(ins.get_raw(), bytearray([0x15, 0x00, 0x42, 0x11]))

        ins = dvm.Instruction21h(MockClassManager(), bytearray([0x19, 0x00, 0x42, 0x11]))
        self.assertEqual(ins.get_op_value(), 0x19)
        self.assertEqual(ins.get_literals(), [0x1142000000000000])
        self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, 0x00), (dvm.Operand.LITERAL, 0x1142000000000000)])
        self.assertEqual(ins.get_name(), 'const-wide/high16')
        self.assertEqual(ins.get_output(), 'v0, 1243556447107678208')
        self.assertEqual(ins.get_raw(), bytearray([0x19, 0x00, 0x42, 0x11]))

        ins = dvm.Instruction21h(MockClassManager(), bytearray([0x19, 0x00, 0xbe, 0xff]))
        self.assertEqual(ins.get_op_value(), 0x19)
        self.assertEqual(ins.get_literals(), [-18577348462903296])
        self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, 0x00), (dvm.Operand.LITERAL, -18577348462903296)])
        self.assertEqual(ins.get_name(), 'const-wide/high16')
        self.assertEqual(ins.get_output(), 'v0, -18577348462903296')
        self.assertEqual(ins.get_raw(), bytearray([0x19, 0x00, 0xbe, 0xff]))

    def testInstruction51l(self):
        """test the functionality of const-wide"""
        ins = dvm.Instruction51l(MockClassManager(), bytearray([0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
        self.assertEqual(ins.get_op_value(), 0x18)
        self.assertEqual(ins.get_literals(), [0])
        self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, 0x00), (dvm.Operand.LITERAL, 0)])
        self.assertEqual(ins.get_name(), 'const-wide')
        self.assertEqual(ins.get_output(), 'v0, 0')
        self.assertEqual(ins.get_raw(), bytearray([0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

        bytecode = bytearray([0x18, 0x00, 0x12, 0x34, 0x56, 0x78, 0x90, 0x12, 0x34, 0x70])
        ins = dvm.Instruction51l(MockClassManager(), bytecode)
        self.assertEqual(ins.get_op_value(), 0x18)
        self.assertEqual(ins.get_literals(), [0x7034129078563412])
        self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, 0x00), (dvm.Operand.LITERAL, 0x7034129078563412)])
        self.assertEqual(ins.get_name(), 'const-wide')
        self.assertEqual(ins.get_output(), 'v0, 8085107642740388882')
        self.assertEqual(ins.get_raw(), bytecode)

        bytecode = bytearray([0x18, 0x00, 0xee, 0xcb, 0xa9, 0x87, 0x6f, 0xed, 0xcb, 0x8f])
        ins = dvm.Instruction51l(MockClassManager(), bytecode)
        self.assertEqual(ins.get_op_value(), 0x18)
        self.assertEqual(ins.get_literals(), [-8085107642740388882])
        self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, 0x00), (dvm.Operand.LITERAL, -8085107642740388882)])
        self.assertEqual(ins.get_name(), 'const-wide')
        self.assertEqual(ins.get_output(), 'v0, -8085107642740388882')
        self.assertEqual(ins.get_raw(), bytecode)

    def testInstruction11n(self):
        """Test the functionality for Instruction 11n (only used for const/4)"""
        tests = [
            (0x00, 0, 0),
            (0x13, 3, 1),
            (0x10, 0, 1),
            (0x11, 1, 1),
            (0x71, 1, 7),
            (0xF0, 0, -1),
            (0x61, 1, 6),
            (0xE6, 6, -2),
            (0x86, 6, -8),
        ]
        for args, reg, lit in tests:
            ins = dvm.Instruction11n(MockClassManager(), bytearray([0x12, args]))
            self.assertEqual(ins.get_name(), 'const/4')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytearray([0x12, args]))
            self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, reg), (dvm.Operand.LITERAL, lit)])
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

    def testInstruction21s(self):
        """Test functionality of Instruction 21s (const/16, const-wide/16)"""

        # Both instructions have the same format, the difference is that they either write into 32bit or 64bit registers
        # But this does not matter for us...
        tests = [
            ([0x01, 0x0E, 0x00], 1, 0x0E),
            ([0x02, 0x10, 0x00], 2, 0x10),
            ([0x02, 0x0B, 0x00], 2, 0x0B),
            ([0x00, 0x02, 0x20], 0, 0x2002),
            ([0x00, 0x00, 0x10], 0, 0x1000),
            ([0x02, 0x18, 0xFC], 2, -0x3E8),
            ([0x00, 0x00, 0x80], 0, -0x8000),
            ([0x00, 0xFF, 0x7F], 0, 0x7FFF),
            ([0x00, 0x80, 0xFF], 0, -0x80),
        ]
        for args, reg, lit in tests:
            # const/16
            bytecode = bytearray([0x13] + args)
            ins = dvm.Instruction21s(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const/16')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, reg), (dvm.Operand.LITERAL, lit)])
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

            # const-wide/16
            bytecode = bytearray([0x16] + args)
            ins = dvm.Instruction21s(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const-wide/16')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, reg), (dvm.Operand.LITERAL, lit)])
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

    def testInstruction31i(self):
        """Test functionaltiy of Instruction31i (const, const-wide/32)"""

        # const is often used to load resources...
        tests = [
            ([0x00, 0xFF, 0xFF, 0xFF, 0x1F], 0, 0x1FFFFFFF),
            ([0x00, 0x62, 0x00, 0x07, 0x7F], 0, 0x7F070062),
            ([0x00, 0x74, 0x00, 0x07, 0x7F], 0, 0x7F070074),
            # FIXME: test negative numbers
        ]
        for args, reg, lit in tests:
            # const
            bytecode = bytearray([0x14] + args)
            ins = dvm.Instruction31i(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, reg), (dvm.Operand.LITERAL, lit)])
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

            # const-wide/32
            bytecode = bytearray([0x17] + args)
            ins = dvm.Instruction31i(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const-wide/32')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(ins.get_operands(), [(dvm.Operand.REGISTER, reg), (dvm.Operand.LITERAL, lit)])
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))


if __name__ == '__main__':
    unittest.main()
