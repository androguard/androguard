import binascii
import os
import random
import unittest

from androguard.core import dex
from androguard.misc import AnalyzeAPK

test_dir = os.path.dirname(os.path.abspath(__file__))


class MockClassManager:
    @property
    def packer(self):
        return dex.DalvikPacker(0x12345678)

    def get_odex_format(self):
        return False


class VMClassTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_apk_path = os.path.join(test_dir, 'data/APK/TestActivity.apk')
        cls.a, cls.d, cls.dx = AnalyzeAPK(test_apk_path)

    def testVMClass(self):
        """test number of ClassDefItems, StringDataItems, FieldIdItems, and MethodIdItems"""

        num_class_def_items = 0
        num_strings_data_items = 0
        num_field_id_items = 0
        num_method_id_items = 0

        # the below field exists in the fieldIds list, but
        # their class doesnt exist, this is bc its loaded at runtime
        # 19 [FieldIdItem]: class_idx=0x13 type_idx=0x242 name_idx=0x1099
        # classIdx = 0x13 = 19
        # typeIdx = 0x242 = 578
        # nameIdx = 0x1099 = 4249
        # className = Landroid/app/Notification;
        # typeName = [J
        # fieldName = vibrate

        # see DEX format spec https://source.android.com/docs/core/runtime/dex-format
        # https://reverseengineering.stackexchange.com/questions/21767/dex-file-referenced-type-is-not-defined-in-file
        # field ids, type ids, and method ids references
        # are not required to be defined in the dex since they can be resolved at runtime via shared library
        for vm in self.dx.vms:
            num_class_def_items += vm.get_len_classes()  # ClassDefItems
            num_strings_data_items += vm.get_len_strings()  # StringDataItems
            num_field_id_items += vm.get_len_fields()  # FieldIdItems
            num_method_id_items += vm.get_len_methods()  # MethodIdItems

        self.assertEqual(len(self.dx.vms), 1)
        self.assertEqual(num_class_def_items, 340)
        self.assertEqual(num_strings_data_items, 4329)
        self.assertEqual(num_field_id_items, 865)
        self.assertEqual(num_method_id_items, 3602)

    def testAccessflags(self):
        class_name_accessflag_map = {
            'Ltests/androguard/TestLoops;': {
                'access_flag': 0x1,  # public
                'methods': {
                    '<init>': 0x1 | 0x10000,  # public | constructor
                    'testBreak': 0x1,  # public
                    'testBreak2': 0x1,
                    'testBreak3': 0x1,
                    'testBreak4': 0x1,
                    'testBreakDoWhile': 0x1,
                    'testBreakMid': 0x1,
                    'testBreakbis': 0x1,
                    'testDiffWhileDoWhile': 0x1,
                    'testDoWhile': 0x1,
                    'testDoWhileTrue': 0x1,
                    'testFor': 0x1,
                    'testIrreducible': 0x1,
                    'testMultipleLoops': 0x1,
                    'testNestedLoops': 0x1,
                    'testReducible': 0x1,
                    'testWhile': 0x1,
                    'testWhile2': 0x1,
                    'testWhile3': 0x1,
                    'testWhile4': 0x1,
                    'testWhile5': 0x1,
                    'testWhileTrue': 0x1,
                },
                'fields': {},
            },
            'Ltests/androguard/TestLoops$Loop;': {
                'access_flag': 0x1,  # public
                'methods': {
                    '<init>': 0x4 | 0x10000  # protected | constructor
                },
                'fields': {
                    'i': 0x1 | 0x8,  # public | static
                    'j': 0x1 | 0x8,  # public | static
                },
            },
            'Ltests/androguard/TestIfs;': {
                'access_flag': 0x1,  # public
                'methods': {
                    '<init>': 0x1 | 0x10000,  # public | constructor
                    'testIF': 0x1 | 0x8,  # public | static
                    'testIF2': 0x1 | 0x8,
                    'testIF3': 0x1 | 0x8,
                    'testIF4': 0x1 | 0x8,
                    'testIF5': 0x1 | 0x8,
                    'testIfBool': 0x1 | 0x8,
                    'testShortCircuit': 0x1 | 0x8,
                    'testShortCircuit2': 0x1 | 0x8,
                    'testShortCircuit3': 0x1 | 0x8,
                    'testShortCircuit4': 0x1 | 0x8,
                    'testCFG': 0x1,  # public
                    'testCFG2': 0x1,
                },
                'fields': {'P': 0x2, 'Q': 0x2, 'R': 0x2, 'S': 0x2},  # private
            },
        }

        # ensure these classes exist in the Analysis
        for expected_class_name in class_name_accessflag_map.keys():
            self.assertTrue(self.dx.is_class_present(expected_class_name))

        # test access flags for classes
        for (
            expected_class_name,
            class_data,
        ) in class_name_accessflag_map.items():
            class_analysis = self.dx.get_class_analysis(expected_class_name)
            class_access_flags = (
                class_analysis.get_vm_class().get_access_flags()
            )
            self.assertEqual(class_access_flags, class_data['access_flag'])

            # test access flags for methods
            encoded_methods = class_analysis.get_vm_class().get_methods()
            for expected_method_name, expected_access_flags in class_data[
                'methods'
            ].items():
                # ensure this method is in the class
                self.assertIn(
                    expected_method_name,
                    [method.name for method in encoded_methods],
                )

                # ensure access flags match
                for method in encoded_methods:
                    if method.name == expected_method_name:
                        self.assertEqual(
                            method.get_access_flags(), expected_access_flags
                        )

            # test access flags for fields
            encoded_fields = class_analysis.get_vm_class().get_fields()
            for expected_field_name, expected_access_flags in class_data[
                'fields'
            ].items():
                # ensure this field is in the class
                self.assertIn(
                    expected_field_name,
                    [field.name for field in encoded_fields],
                )

                # ensure access flags match
                for field in encoded_fields:
                    if field.name == expected_field_name:
                        self.assertEqual(
                            field.get_access_flags(), expected_access_flags
                        )


class InstructionTest(unittest.TestCase):
    def testInstructions(self):
        """Tests if all instructions are at least covered"""
        # Set the seed here, so we have reproduceable results later
        random.seed(1337)

        for op_value in range(0, 256):
            ins = dex.DALVIK_OPCODES_FORMAT[op_value][0]
            name = dex.DALVIK_OPCODES_FORMAT[op_value][1]
            self.assertEqual(issubclass(ins, dex.Instruction), True)

            # The Name should code for the length of the opcode
            length = int(ins.__name__[11]) * 2
            self.assertEqual(ins.length, length)

            if name[0] == 'unused':
                # unused instructions should raise an error on invocation
                with self.assertRaises(dex.InvalidInstruction):
                    ins(MockClassManager(), bytearray([op_value, 0]))
                # therefore, we can not test much else here...
                continue

            # Test if instruction can be parsed
            bytecode = bytearray([op_value] + [0] * (length - 1))
            instruction = ins(MockClassManager(), bytecode)
            self.assertIsInstance(instruction, dex.Instruction)
            self.assertEqual(instruction.get_op_value(), op_value)

            # And packed again
            self.assertEqual(instruction.get_raw(), bytecode)

            # Test with some pseudorandom stuff
            if ins.__name__ in [
                'Instruction10x',
                'Instruction20t',
                'Instruction30t',
                'Instruction32x',
                'Instruction45cc',
            ]:
                # note this only works for certain opcode (which are not forced to 0 in certain places)
                # Thus we need to make sure these places are zero.
                # Instruction45cc: Has constrained regarding the parameter AA
                bytecode = bytearray(
                    [op_value, 0]
                    + [random.randint(0x00, 0xFF) for _ in range(length - 2)]
                )
            else:
                bytecode = bytearray(
                    [op_value]
                    + [random.randint(0x00, 0xFF) for _ in range(length - 1)]
                )
            instruction = ins(MockClassManager(), bytecode)
            self.assertIsInstance(instruction, dex.Instruction)
            self.assertEqual(instruction.get_op_value(), op_value)
            self.assertEqual(instruction.get_raw(), bytecode)

    def testNOP(self):
        """test if NOP instructions are parsed"""
        instruction = dex.Instruction10x(
            MockClassManager(), bytearray(b"\x00\x00")
        )
        self.assertEqual(instruction.get_name(), "nop")

    def testLinearSweep(self):
        bytecode = bytearray(b"\x00\x00\x00\x00\x00\x00\x0e\x00")

        instructions = ['nop', 'nop', 'nop', 'return-void']
        l = 0

        for ins in dex.LinearSweepAlgorithm.get_instructions(
            MockClassManager(), 4, bytecode, 0
        ):
            self.assertIsInstance(ins, dex.Instruction10x)
            self.assertEqual(ins.get_length(), 2)
            self.assertEqual(ins.get_name(), instructions.pop(0))
            l += ins.get_length()

        self.assertEqual(instructions, [])
        self.assertEqual(len(bytecode), l)

    def testLinearSweepStrings(self):
        # very basic function, strings and invokes
        bytecode = bytearray(
            binascii.unhexlify(
                '1A000F001A0100001A0214001A0311001A0415001A0413001A0508001A061200'
                '1A0716001A081000620900006E2002000900620000006E200200100062000000'
                '6E2002002000620000006E2002003000620000006E2002003000620000006E20'
                '02004000620000006E2002005000620000006E2002006000620000006E200200'
                '7000620000006E20020080000E00'
            )
        )
        instructions = [
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'const-string',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'sget-object',
            'invoke-virtual',
            'return-void',
        ]
        l = 0

        for ins in dex.LinearSweepAlgorithm.get_instructions(
            MockClassManager(), 71, bytecode, 0
        ):
            self.assertIsInstance(ins, dex.Instruction)
            self.assertEqual(ins.get_name(), instructions.pop(0))
            l += ins.get_length()
        # check if all instructions were consumed
        self.assertEqual(instructions, [])
        # Check if all bytes are read
        self.assertEqual(len(bytecode), l)

    def testLinearSweepSwitch(self):
        """test if switch payloads are unpacked correctly"""
        bytecode = bytearray(
            binascii.unhexlify(
                '2B02140000001300110038030400130063000F001300170028F913002A0028F6'
                '1300480028F3000000010300010000000A0000000D00000010000000'
            )
        )

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

        for ins in dex.LinearSweepAlgorithm.get_instructions(
            MockClassManager(), 30, bytecode, 0
        ):
            if len(instructions) > 1:
                self.assertIsInstance(ins, dex.Instruction)
            else:
                self.assertIsInstance(ins, dex.PackedSwitch)
            self.assertEqual(ins.get_name(), instructions.pop(0))
            l += ins.get_length()
        # check if all instructions were consumed
        self.assertEqual(instructions, [])
        self.assertEqual(len(bytecode), l)

    def testLSAArrays(self):
        """Test if fill-array-data-payload is parsed"""
        bytecode = bytearray(
            binascii.unhexlify(
                '12412310030026002D0000005B30000012702300050026002B0000005B300300'
                '1250230004002600350000005B300100231007002600380000005B3002001220'
                '2300060012011A020D004D02000112111A0211004D0200015B3004000E000000'
                '0003010004000000141E28320003040007000000010000000200000003000000'
                '0400000005000000E70300000A899D0000030200050000006100620078007A00'
                '63000000000302000400000005000A000F001400'
            )
        )

        instructions = [
            'const/4',
            'new-array',
            'fill-array-data',
            'iput-object',
            'const/4',
            'new-array',
            'fill-array-data',
            'iput-object',
            'const/4',
            'new-array',
            'fill-array-data',
            'iput-object',
            'new-array',
            'fill-array-data',
            'iput-object',
            'const/4',
            'new-array',
            'const/4',
            'const-string',
            'aput-object',
            'const/4',
            'const-string',
            'aput-object',
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

        for ins in dex.LinearSweepAlgorithm.get_instructions(
            MockClassManager(), 90, bytecode, 0
        ):
            self.assertEqual(ins.get_name(), instructions.pop(0))
            if ins.get_name() != 'fill-array-data-payload':
                self.assertIsInstance(ins, dex.Instruction)
            else:
                self.assertIsInstance(ins, dex.FillArrayData)
                elem_size, size = arrays.pop(0)
                self.assertEqual(ins.element_width, elem_size)
                self.assertEqual(ins.size, size)
            l += ins.get_length()

        # check if all instructions were consumed
        self.assertEqual(instructions, [])
        self.assertEqual(arrays, [])
        self.assertEqual(len(bytecode), l)

    def testWrongInstructions(self):
        """Test if unknown instructions raise an InvalidInstruction error"""
        with self.assertRaises(dex.InvalidInstruction):
            ins = list(
                dex.LinearSweepAlgorithm.get_instructions(
                    MockClassManager(), 1, bytearray(b"\xff\xab"), 0
                )
            )

        with self.assertRaises(dex.InvalidInstruction):
            ins = list(
                dex.LinearSweepAlgorithm.get_instructions(
                    MockClassManager(),
                    2,
                    bytearray(b"\x00\x00" b"\xff\xab"),
                    0,
                )
            )

    def testIncompleteInstruction(self):
        """Test if incomplete bytecode log an error"""
        # Test if instruction can be parsed
        self.assertIsInstance(
            dex.Instruction51l(
                MockClassManager(),
                bytearray(b'\x18\x01\x23\x23\x00\xff\x99\x11\x22\x22'),
            ),
            dex.Instruction51l,
        )

        with self.assertRaises(dex.InvalidInstruction):
            ins = list(
                dex.LinearSweepAlgorithm.get_instructions(
                    MockClassManager(), 5, bytearray(b"\x18\x01\xff\xff"), 0
                )
            )

    def testInstruction21h(self):
        """Test function of Instruction 21h used for const{,-wide}/high16"""
        ins = dex.Instruction21h(
            MockClassManager(), bytearray([0x15, 0x00, 0x42, 0x11])
        )
        self.assertEqual(ins.get_op_value(), 0x15)
        self.assertEqual(ins.get_literals(), [0x11420000])
        self.assertEqual(
            ins.get_operands(),
            [(dex.Operand.REGISTER, 0x00), (dex.Operand.LITERAL, 0x11420000)],
        )
        self.assertEqual(ins.get_name(), 'const/high16')
        self.assertEqual(ins.get_output(), 'v0, 289538048')
        self.assertEqual(ins.get_raw(), bytearray([0x15, 0x00, 0x42, 0x11]))

        ins = dex.Instruction21h(
            MockClassManager(), bytearray([0x19, 0x00, 0x42, 0x11])
        )
        self.assertEqual(ins.get_op_value(), 0x19)
        self.assertEqual(ins.get_literals(), [0x1142000000000000])
        self.assertEqual(
            ins.get_operands(),
            [
                (dex.Operand.REGISTER, 0x00),
                (dex.Operand.LITERAL, 0x1142000000000000),
            ],
        )
        self.assertEqual(ins.get_name(), 'const-wide/high16')
        self.assertEqual(ins.get_output(), 'v0, 1243556447107678208')
        self.assertEqual(ins.get_raw(), bytearray([0x19, 0x00, 0x42, 0x11]))

        ins = dex.Instruction21h(
            MockClassManager(), bytearray([0x19, 0x00, 0xBE, 0xFF])
        )
        self.assertEqual(ins.get_op_value(), 0x19)
        self.assertEqual(ins.get_literals(), [-18577348462903296])
        self.assertEqual(
            ins.get_operands(),
            [
                (dex.Operand.REGISTER, 0x00),
                (dex.Operand.LITERAL, -18577348462903296),
            ],
        )
        self.assertEqual(ins.get_name(), 'const-wide/high16')
        self.assertEqual(ins.get_output(), 'v0, -18577348462903296')
        self.assertEqual(ins.get_raw(), bytearray([0x19, 0x00, 0xBE, 0xFF]))

    def testInstruction51l(self):
        """test the functionality of const-wide"""
        ins = dex.Instruction51l(
            MockClassManager(),
            bytearray(
                [0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            ),
        )
        self.assertEqual(ins.get_op_value(), 0x18)
        self.assertEqual(ins.get_literals(), [0])
        self.assertEqual(
            ins.get_operands(),
            [(dex.Operand.REGISTER, 0x00), (dex.Operand.LITERAL, 0)],
        )
        self.assertEqual(ins.get_name(), 'const-wide')
        self.assertEqual(ins.get_output(), 'v0, 0')
        self.assertEqual(
            ins.get_raw(),
            bytearray(
                [0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            ),
        )

        bytecode = bytearray(
            [0x18, 0x00, 0x12, 0x34, 0x56, 0x78, 0x90, 0x12, 0x34, 0x70]
        )
        ins = dex.Instruction51l(MockClassManager(), bytecode)
        self.assertEqual(ins.get_op_value(), 0x18)
        self.assertEqual(ins.get_literals(), [0x7034129078563412])
        self.assertEqual(
            ins.get_operands(),
            [
                (dex.Operand.REGISTER, 0x00),
                (dex.Operand.LITERAL, 0x7034129078563412),
            ],
        )
        self.assertEqual(ins.get_name(), 'const-wide')
        self.assertEqual(ins.get_output(), 'v0, 8085107642740388882')
        self.assertEqual(ins.get_raw(), bytecode)

        bytecode = bytearray(
            [0x18, 0x00, 0xEE, 0xCB, 0xA9, 0x87, 0x6F, 0xED, 0xCB, 0x8F]
        )
        ins = dex.Instruction51l(MockClassManager(), bytecode)
        self.assertEqual(ins.get_op_value(), 0x18)
        self.assertEqual(ins.get_literals(), [-8085107642740388882])
        self.assertEqual(
            ins.get_operands(),
            [
                (dex.Operand.REGISTER, 0x00),
                (dex.Operand.LITERAL, -8085107642740388882),
            ],
        )
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
            ins = dex.Instruction11n(
                MockClassManager(), bytearray([0x12, args])
            )
            self.assertEqual(ins.get_name(), 'const/4')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytearray([0x12, args]))
            self.assertEqual(
                ins.get_operands(),
                [(dex.Operand.REGISTER, reg), (dex.Operand.LITERAL, lit)],
            )
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
            ins = dex.Instruction21s(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const/16')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(
                ins.get_operands(),
                [(dex.Operand.REGISTER, reg), (dex.Operand.LITERAL, lit)],
            )
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

            # const-wide/16
            bytecode = bytearray([0x16] + args)
            ins = dex.Instruction21s(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const-wide/16')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(
                ins.get_operands(),
                [(dex.Operand.REGISTER, reg), (dex.Operand.LITERAL, lit)],
            )
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

    def testInstruction31i(self):
        """Test functionality of Instruction31i (const, const-wide/32)"""

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
            ins = dex.Instruction31i(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(
                ins.get_operands(),
                [(dex.Operand.REGISTER, reg), (dex.Operand.LITERAL, lit)],
            )
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

            # const-wide/32
            bytecode = bytearray([0x17] + args)
            ins = dex.Instruction31i(MockClassManager(), bytecode)
            self.assertEqual(ins.get_name(), 'const-wide/32')
            self.assertEqual(ins.get_literals(), [lit])
            self.assertEqual(ins.get_raw(), bytecode)
            self.assertEqual(
                ins.get_operands(),
                [(dex.Operand.REGISTER, reg), (dex.Operand.LITERAL, lit)],
            )
            self.assertEqual(ins.get_output(), 'v{}, {}'.format(reg, lit))

    def testBrokenDex(self):
        """Test various broken DEX headers"""
        # really not a dex file
        with self.assertRaises(ValueError) as cnx:
            dex.DEX(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertIn('Header too small', str(cnx.exception))

        # Adler32 will not match, zeroed out file
        data_dex = binascii.unhexlify(
            '6465780A303335001F6C4D5A6ACF889AF588F3237FC9F20B41F56A2408749D1B'
            'C81E000070000000785634120000000000000000341E00009400000070000000'
            '2E000000C0020000310000007803000011000000C4050000590000004C060000'
            '090000001409000094140000340A0000' + ('00' * (7880 - 0x70))
        )

        with self.assertRaises(ValueError) as cnx:
            dex.DEX(data_dex)
        self.assertIn("Adler32", str(cnx.exception))

        # A very very basic dex file (without a map)
        # But should parse...
        data_dex = binascii.unhexlify(
            '6465780A30333500460A4882696E76616C6964696E76616C6964696E76616C69'
            '7000000070000000785634120000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '00000000000000000000000000000000'
        )
        self.assertIsNotNone(dex.DEX(data_dex))

        # Wrong header size
        data_dex = binascii.unhexlify(
            '6465780A30333500480A2C8D696E76616C6964696E76616C6964696E76616C69'
            '7100000071000000785634120000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000'
        )
        with self.assertRaises(ValueError) as cnx:
            dex.DEX(data_dex)
        self.assertIn("Wrong header size", str(cnx.exception))

        # Non integer version, but parse it
        data_dex = binascii.unhexlify(
            '6465780AFF00AB00460A4882696E76616C6964696E76616C6964696E76616C69'
            '7000000070000000785634120000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '00000000000000000000000000000000'
        )
        self.assertIsNotNone(dex.DEX(data_dex))

        # Big Endian file
        data_dex = binascii.unhexlify(
            '6465780A30333500460AF480696E76616C6964696E76616C6964696E76616C69'
            '7000000070000000123456780000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '00000000000000000000000000000000'
        )
        with self.assertRaises(NotImplementedError) as cnx:
            dex.DEX(data_dex)
        self.assertIn("swapped endian tag", str(cnx.exception))

        # Weird endian file
        data_dex = binascii.unhexlify(
            '6465780A30333500AB0BC3E4696E76616C6964696E76616C6964696E76616C69'
            '7000000070000000ABCDEF120000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000000000'
            '00000000000000000000000000000000'
        )
        with self.assertRaises(ValueError) as cnx:
            dex.DEX(data_dex)
        self.assertIn("Wrong endian tag", str(cnx.exception))


if __name__ == '__main__':
    unittest.main()
