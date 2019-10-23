import sys
import re
import struct
import binascii
import time
from struct import pack, unpack, calcsize
import logging
import warnings
import zlib
import hashlib
from enum import IntEnum

from androguard.core import bytecode
from androguard.core.bytecodes.apk import APK
from androguard.core.androconf import CONF

from androguard.core import mutf8
from androguard.core.bytecodes.dvm_types import (
        TypeMapItem,
        ACCESS_FLAGS,
        TYPE_DESCRIPTOR,
        Kind,
        Operand,
        )



log = logging.getLogger("androguard.dvm")

# TODO: have some more generic magic...
DEX_FILE_MAGIC_35 = b'dex\n035\x00'
DEX_FILE_MAGIC_36 = b'dex\n036\x00'
DEX_FILE_MAGIC_37 = b'dex\n037\x00'
DEX_FILE_MAGIC_38 = b'dex\n038\x00'

ODEX_FILE_MAGIC_35 = b'dey\n035\x00'
ODEX_FILE_MAGIC_36 = b'dey\n036\x00'
ODEX_FILE_MAGIC_37 = b'dey\n037\x00'
ODEX_FILE_MAGIC_38 = b'dey\n038\x00'

# https://source.android.com/devices/tech/dalvik/dex-format#value-formats
VALUE_BYTE = 0x00  # (none; must be 0)      ubyte[1]         signed one-byte integer value
VALUE_SHORT = 0x02  # size - 1 (0..1)  ubyte[size]    signed two-byte integer value, sign-extended
VALUE_CHAR = 0x03  # size - 1 (0..1)  ubyte[size]    unsigned two-byte integer value, zero-extended
VALUE_INT = 0x04  # size - 1 (0..3)  ubyte[size]    signed four-byte integer value, sign-extended
VALUE_LONG = 0x06  # size - 1 (0..7)  ubyte[size]    signed eight-byte integer value, sign-extended
VALUE_FLOAT = 0x10  # size - 1 (0..3)  ubyte[size]    four-byte bit pattern, zero-extended to the right, and interpreted as an IEEE754 32-bit floating point value
VALUE_DOUBLE = 0x11  # size - 1 (0..7)  ubyte[size]    eight-byte bit pattern, zero-extended to the right, and interpreted as an IEEE754 64-bit floating point value
VALUE_STRING = 0x17  # size - 1 (0..3)  ubyte[size]    unsigned (zero-extended) four-byte integer value, interpreted as an index into the string_ids section and representing a string value
VALUE_TYPE = 0x18  # size - 1 (0..3)  ubyte[size]    unsigned (zero-extended) four-byte integer value, interpreted as an index into the type_ids section and representing a reflective type/class value
VALUE_FIELD = 0x19  # size - 1 (0..3)  ubyte[size]    unsigned (zero-extended) four-byte integer value, interpreted as an index into the field_ids section and representing a reflective field value
VALUE_METHOD = 0x1a  # size - 1 (0..3)  ubyte[size]    unsigned (zero-extended) four-byte integer value, interpreted as an index into the method_ids section and representing a reflective method value
VALUE_ENUM = 0x1b  # size - 1 (0..3)  ubyte[size]    unsigned (zero-extended) four-byte integer value, interpreted as an index into the field_ids section and representing the value of an enumerated type constant
VALUE_ARRAY = 0x1c  # (none; must be 0)      encoded_array  an array of values, in the format specified by "encoded_array Format" below. The size of the value is implicit in the encoding.
VALUE_ANNOTATION = 0x1d  # (none; must be 0)      encoded_annotation     a sub-annotation, in the format specified by "encoded_annotation Format" below. The size of the value is implicit in the encoding.
VALUE_NULL = 0x1e  # (none; must be 0)      (none)  null reference value
VALUE_BOOLEAN = 0x1f  # boolean (0..1) (none)  one-bit value; 0 for false and 1 for true. The bit is represented in the value_arg.

# https://source.android.com/devices/tech/dalvik/dex-format#debug-info-item
DBG_END_SEQUENCE = 0x00  # (none)  terminates a debug info sequence for a code_item
DBG_ADVANCE_PC = 0x01  # uleb128 addr_diff       addr_diff: amount to add to address register    advances the address register without emitting a positions entry
DBG_ADVANCE_LINE = 0x02  # sleb128 line_diff       line_diff: amount to change line register by    advances the line register without emitting a positions entry
DBG_START_LOCAL = 0x03  # uleb128 register_num
#    uleb128p1 name_idx
#    uleb128p1 type_idx
#         register_num: register that will contain local name_idx: string index of the name
#         type_idx: type index of the type  introduces a local variable at the current address. Either name_idx or type_idx may be NO_INDEX to indicate that that value is unknown.
DBG_START_LOCAL_EXTENDED = 0x04  # uleb128 register_num uleb128p1 name_idx uleb128p1 type_idx uleb128p1 sig_idx
#         register_num: register that will contain local
#         name_idx: string index of the name
#         type_idx: type index of the type
#         sig_idx: string index of the type signature
# introduces a local with a type signature at the current address. Any of name_idx, type_idx, or sig_idx may be NO_INDEX to indicate that that value is unknown. (
# If sig_idx is -1, though, the same data could be represented more efficiently using the opcode DBG_START_LOCAL.)
# Note: See the discussion under "dalvik.annotation.Signature" below for caveats about handling signatures.
DBG_END_LOCAL = 0x05  # uleb128 register_num
#           register_num: register that contained local
#           marks a currently-live local variable as out of scope at the current address
DBG_RESTART_LOCAL = 0x06  # uleb128 register_num
#           register_num: register to restart re-introduces a local variable at the current address.
#           The name and type are the same as the last local that was live in the specified register.
DBG_SET_PROLOGUE_END = 0x07  # (none)  sets the prologue_end state machine register, indicating that the next position entry that is added should be considered the end of a
#               method prologue (an appropriate place for a method breakpoint). The prologue_end register is cleared by any special (>= 0x0a) opcode.
DBG_SET_EPILOGUE_BEGIN = 0x08  # (none)  sets the epilogue_begin state machine register, indicating that the next position entry that is added should be considered the beginning
#               of a method epilogue (an appropriate place to suspend execution before method exit). The epilogue_begin register is cleared by any special (>= 0x0a) opcode.
DBG_SET_FILE = 0x09  # uleb128p1 name_idx
#           name_idx: string index of source file name; NO_INDEX if unknown indicates that all subsequent line number entries make reference to this source file name,
#           instead of the default name specified in code_item
DBG_Special_Opcodes_BEGIN = 0x0a  # (none)  advances the line and address registers, emits a position entry, and clears prologue_end and epilogue_begin. See below for description.
DBG_Special_Opcodes_END = 0xff
DBG_LINE_BASE = -4
DBG_LINE_RANGE = 15


class InvalidInstruction(Exception):
    pass


def read_null_terminated_string(f):
    """
    Read a null terminated string from a file-like object.
    :param f: file-like object
    :rtype: bytearray
    """
    x = []
    while True:
        z = f.read(128)
        if 0 in z:
            s = z.split(b'\x00',1)
            x.append(s[0])
            idx = f.get_idx()
            f.set_idx(idx - len(s[1]))
            break
        else:
            x.append(z)
    return b''.join(x)


def get_access_flags_string(value):
    """
    Transform an access flag field to the corresponding string

    :param value: the value of the access flags
    :type value: int

    :rtype: string
    """
    flags = []
    for k, v in ACCESS_FLAGS.items():
        if (k & value) == k:
            flags.append(v)

    return " ".join(flags)


def get_type(atype, size=None):
    """
    Retrieve the type of a descriptor (e.g : I)
    """
    if atype.startswith('java.lang'):
        atype = atype.replace('java.lang.', '')
    res = TYPE_DESCRIPTOR.get(atype.lstrip('java.lang'))
    if res is None:
        if atype[0] == 'L':
            res = atype[1:-1].replace('/', '.')
        elif atype[0] == '[':
            if size is None:
                res = '%s[]' % get_type(atype[1:])
            else:
                res = '{}[{}]'.format(get_type(atype[1:]), size)
        else:
            res = atype
    return res


MATH_DVM_OPCODES = {
    "add.": '+',
    "div.": '/',
    "mul.": '*',
    "or.": '|',
    "sub.": '-',
    "and.": '&',
    "xor.": '^',
    "shl.": "<<",
    "shr.": ">>",
}

FIELD_READ_DVM_OPCODES = [".get"]
FIELD_WRITE_DVM_OPCODES = [".put"]

BREAK_DVM_OPCODES = ["invoke.", "move.", ".put", "if."]

BRANCH_DVM_OPCODES = ["throw", "throw.", "if.", "goto", "goto.", "return",
                      "return.", "packed-switch$", "sparse-switch$"]


def clean_name_instruction(instruction):
    """USED IN ELSIM"""
    op_value = instruction.get_op_value()

    # goto range
    if 0x28 <= op_value <= 0x2a:
        return "goto"

    return instruction.get_name()


def static_operand_instruction(instruction):
    """USED IN ELSIM"""
    buff = ""

    if isinstance(instruction, Instruction):
        # get instructions without registers
        for val in instruction.get_literals():
            buff += "%s" % val

    op_value = instruction.get_op_value()
    if op_value == 0x1a or op_value == 0x1b:
        buff += instruction.get_string()

    return buff


def get_sbyte(cm, buff):
    return cm.packer["b"].unpack(buff.read(1))[0]


def get_byte(cm, buff):
    return cm.packer["B"].unpack(buff.read(1))[0]


def readuleb128(cm, buff):
    """
    Read an unsigned LEB128 at the current position of the buffer

    :param buff: a file like object
    :return: decoded unsigned LEB128
    """
    result = get_byte(cm, buff)
    if result > 0x7f:
        cur = get_byte(cm, buff)
        result = (result & 0x7f) | ((cur & 0x7f) << 7)
        if cur > 0x7f:
            cur = get_byte(cm, buff)
            result |= (cur & 0x7f) << 14
            if cur > 0x7f:
                cur = get_byte(cm, buff)
                result |= (cur & 0x7f) << 21
                if cur > 0x7f:
                    cur = get_byte(cm, buff)
                    if cur > 0x0f:
                        log.warning("possible error while decoding number")
                    result |= cur << 28

    return result


def readuleb128p1(cm, buff):
    """
    Read an unsigned LEB128p1 at the current position of the buffer.
    This format is the same as uLEB128 but has the ability to store the value -1.

    :param buff: a file like object
    :return: decoded uLEB128p1
    """
    return readuleb128(cm, buff) - 1


def readsleb128(cm, buff):
    """
    Read a signed LEB128 at the current position of the buffer.

    :param buff: a file like object
    :return: decoded sLEB128
    """
    result = 0
    shift = 0

    for x in range(0, 5):
        cur = get_byte(cm, buff)
        result |= (cur & 0x7f) << shift
        shift += 7

        if not cur & 0x80:
            bit_left = max(32 - shift, 0)
            result = result << bit_left
            if result > 0x7fffffff:
                result = (0x7fffffff & result) - 0x80000000
            result = result >> bit_left
            break

    return result


def writeuleb128(cm, value):
    """
    Convert an integer value to the corresponding unsigned LEB128.

    Raises a value error, if the given value is negative.

    :param value: non-negative integer
    :return: bytes
    """
    if value < 0:
        raise ValueError("value must be non-negative!")

    remaining = value >> 7

    buff = bytearray()
    while remaining > 0:
        buff += cm.packer["B"].pack(((value & 0x7f) | 0x80))

        value = remaining
        remaining >>= 7

    buff += cm.packer["B"].pack(value & 0x7f)
    return buff


def writesleb128(cm, value):
    """
    Convert an integer value to the corresponding signed LEB128

    :param value: integer value
    :return: bytes
    """
    remaining = value >> 7
    hasMore = True
    buff = bytearray()

    if (value & (-sys.maxsize - 1)) == 0:
        end = 0
    else:
        end = -1

    while hasMore:
        hasMore = (remaining != end) or ((remaining & 1) != ((value >> 6) & 1))
        tmp = 0
        if hasMore:
            tmp = 0x80

        buff += cm.packer["B"].pack((value & 0x7f) | tmp)
        value = remaining
        remaining >>= 7

    return buff


def determineNext(i, cur_idx, m):
    """
    Determine the next offsets inside the bytecode of an :class:`EncodedMethod`.
    The offsets are calculated in number of bytes from the start of the method.
    Note, that offsets inside the bytecode are denoted in 16bit units but this method returns actual bytes!

    Offsets inside the opcode are counted from the beginning of the opcode.

    The returned type is a list, as branching opcodes will have multiple paths.
    `if` and `switch` opcodes will return more than one item in the list, while
    `throw`, `return` and `goto` opcodes will always return a list with length one.

    An offset of -1 indicates that the method is exited, for example by `throw` or `return`.

    If the entered opcode is not branching or jumping, an empty list is returned.

    :param Instruction i: the current Instruction
    :param int cur_idx: Index of the instruction
    :param EncodedMethod m: the current method
    :return:
    :rtype: list
    """
    op_value = i.get_op_value()

    if (op_value == 0x27) or (0x0e <= op_value <= 0x11):
        # throw + return*
        return [-1]
    elif 0x28 <= op_value <= 0x2a:
        # all kind of 'goto'
        off = i.get_ref_off() * 2
        return [off + cur_idx]
    elif 0x32 <= op_value <= 0x3d:
        # all kind of 'if'
        off = i.get_ref_off() * 2
        return [cur_idx + i.get_length(), off + cur_idx]
    elif op_value in (0x2b, 0x2c):
        # packed/sparse switch
        # Code flow will continue after the switch command
        x = [cur_idx + i.get_length()]

        # The payload must be read at the offset position
        code = m.get_code().get_bc()
        off = i.get_ref_off() * 2

        # See DEX bytecode documentation:
        # "the instructions must be located on even-numbered bytecode offsets (that is, 4-byte aligned).
        # In order to meet this requirement, dex generation tools must
        # emit an extra nop instruction as a spacer if such an instruction would otherwise be unaligned."
        padding = (off + cur_idx) % 4
        if padding != 0:
            log.warning("Switch payload not aligned, assume stuff and add {} bytes...".format(padding))
        data = code.get_ins_off(off + cur_idx + padding)

        # TODO: some malware points to invalid code
        # Does Android ignores the nop and searches for the switch payload?
        # So we make sure that this is a switch payload
        if data and (isinstance(data, PackedSwitch) or isinstance(data, SparseSwitch)):
            for target in data.get_targets():
                x.append(target * 2 + cur_idx)
        else:
            log.warning("Could not determine payload of switch command at offset {} inside {}! "
                        "Possibly broken bytecode?".format(cur_idx, m))

        return x
    return []


def determineException(vm, m):
    """
    Returns try-catch handler inside the method.

    :param vm: a :class:`~DalvikVMFormat`
    :param m: a :class:`~EncodedMethod`
    :return:
    """
    # no exceptions !
    if m.get_code().get_tries_size() <= 0:
        return []

    h_off = {}

    handler_catch_list = m.get_code().get_handlers()

    for try_item in m.get_code().get_tries():
        offset_handler = try_item.get_handler_off(
        ) + handler_catch_list.get_off()
        if offset_handler in h_off:
            h_off[offset_handler].append([try_item])
        else:
            h_off[offset_handler] = []
            h_off[offset_handler].append([try_item])

    # print m.get_name(), "\t HANDLER_CATCH_LIST SIZE", handler_catch_list.size, handler_catch_list.get_offset()
    for handler_catch in handler_catch_list.get_list():
        if handler_catch.get_off() not in h_off:
            continue

        for i in h_off[handler_catch.get_off()]:
            i.append(handler_catch)

    exceptions = []
    # print m.get_name(), h_off
    for i in h_off:
        for value in h_off[i]:
            try_value = value[0]

            z = [try_value.get_start_addr() * 2,
                 (try_value.get_start_addr() * 2) +
                 (try_value.get_insn_count() * 2) - 1]

            handler_catch = value[1]

            for handler in handler_catch.get_handlers():
                z.append([vm.get_cm_type(handler.get_type_idx()),
                          handler.get_addr() * 2])

            if handler_catch.get_size() <= 0:
                z.append(["Ljava/lang/Throwable;",
                          handler_catch.get_catch_all_addr() * 2])

            exceptions.append(z)

    # print m.get_name(), exceptions
    return exceptions


class HeaderItem:
    """
    This class can parse an header_item of a dex file.
    Several checks are performed to detect if this is not an header_item.
    Also the Adler32 checksum of the file is calculated in order to detect file
    corruption.
    :param buff: a string which represents a Buff object of the header_item
    :type androguard.core.bytecode.BuffHandle buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, size, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        if self.offset != 0:
            log.warning("Unusual DEX file, does not have the header at offset 0")

        if len(buff) < self.get_length():
            raise ValueError("Not a DEX file, Header too small.")

        self.endian_tag, = unpack('<I', buff.read_at(40, 4))
        cm.packer = DalvikPacker(self.endian_tag)

        # Q is actually wrong, but we do not change it here and unpack our own
        # stuff...
        self.magic, \
        self.checksum, \
        self.signature, \
        self.file_size, \
        self.header_size, \
        endian_tag, \
        self.link_size, \
        self.link_off, \
        self.map_off, \
        self.string_ids_size, \
        self.string_ids_off, \
        self.type_ids_size, \
        self.type_ids_off, \
        self.proto_ids_size, \
        self.proto_ids_off, \
        self.field_ids_size, \
        self.field_ids_off, \
        self.method_ids_size, \
        self.method_ids_off, \
        self.class_defs_size, \
        self.class_defs_off, \
        self.data_size, \
        self.data_off = cm.packer['8sI20s20I'].unpack(buff.read(112))

        # possible dex or dey:
        if self.magic[:2] != b'de' or self.magic[2] not in [0x78, 0x79] or self.magic[3] != 0x0a or self.magic[7] != 0x00:
            raise ValueError("This is not a DEX file! Wrong magic: {}".format(repr(self.magic)))

        try:
            self.dex_version = int(self.magic[4:7].decode('ascii'), 10)
        except (UnicodeDecodeError, ValueError):
            log.warning("Wrong DEX version: {}, trying to parse anyways".format(repr(self.magic)))
            self.dex_version = 35  # assume a common version...

        if zlib.adler32(buff.readat(self.offset + 12)) != self.checksum:
            raise ValueError("Wrong Adler32 checksum for DEX file!")

        if self.file_size != buff.size():
            # Maybe raise an error here too...
            log.warning("DEX file size is different to the buffer. Trying to parse anyways.")

        if self.header_size != 0x70:
            raise ValueError("This is not a DEX file! Wrong header size: '{}'".format(self.header_size))

        if self.type_ids_size > 65535:
            raise ValueError("DEX file contains too many ({}) TYPE_IDs to be valid!".format(self.type_ids_size))

        if self.proto_ids_size > 65535:
            raise ValueError("DEX file contains too many ({}) PROTO_IDs to be valid!".format(self.proto_ids_size))

        if self.data_size % 4 != 0:
            log.warning("data_size is not a multiple of sizeof(uint32_t), but try to parse anyways.")

        self.map_off_obj = None
        self.string_off_obj = None
        self.type_off_obj = None
        self.proto_off_obj = None
        self.field_off_obj = None
        self.method_off_obj = None
        self.class_off_obj = None
        self.data_off_obj = None

    def get_obj(self):
        if self.map_off_obj is None:
            self.map_off_obj = self.CM.get_item_by_offset(self.map_off)

        if self.string_off_obj is None:
            self.string_off_obj = self.CM.get_item_by_offset(self.string_ids_off)

        if self.type_off_obj is None:
            self.type_off_obj = self.CM.get_item_by_offset(self.type_ids_off)

        if self.proto_off_obj is None:
            self.proto_off_obj = self.CM.get_item_by_offset(self.proto_ids_off)

        if self.field_off_obj is None:
            self.field_off_obj = self.CM.get_item_by_offset(self.field_ids_off)

        if self.method_off_obj is None:
            self.method_off_obj = self.CM.get_item_by_offset(
                self.method_ids_off)

        if self.class_off_obj is None:
            self.class_off_obj = self.CM.get_item_by_offset(self.class_defs_off)

        if self.data_off_obj is None:
            self.data_off_obj = self.CM.get_item_by_offset(self.data_off)

        # FIXME: has no object map_off_obj!
        self.map_off = self.map_off_obj.get_off()

        self.string_ids_size = len(self.string_off_obj)
        self.string_ids_off = self.string_off_obj[0].get_off()

        self.type_ids_size = len(self.type_off_obj.type)
        self.type_ids_off = self.type_off_obj.get_off()

        self.proto_ids_size = len(self.proto_off_obj.proto)
        self.proto_ids_off = self.proto_off_obj.get_off()

        self.field_ids_size = len(self.field_off_obj.elem)
        self.field_ids_off = self.field_off_obj.get_off()

        self.method_ids_size = len(self.method_off_obj.methods)
        self.method_ids_off = self.method_off_obj.get_off()

        self.class_defs_size = len(self.class_off_obj.class_def)
        self.class_defs_off = self.class_off_obj.get_off()

        # FIXME: data_off_obj has no map_item!!!
        self.data_size = len(self.data_off_obj.map_item)
        self.data_off = self.data_off_obj.get_off()

        return pack("<Q", self.magic) + \
               pack("<I", self.checksum) + \
               pack("<20s", self.signature) + \
               pack("<I", self.file_size) + \
               pack("<I", self.header_size) + \
               pack("<I", self.endian_tag) + \
               pack("<I", self.link_size) + \
               pack("<I", self.link_off) + \
               pack("<I", self.map_off) + \
               pack("<I", self.string_ids_size) + \
               pack("<I", self.string_ids_off) + \
               pack("<I", self.type_ids_size) + \
               pack("<I", self.type_ids_off) + \
               pack("<I", self.proto_ids_size) + \
               pack("<I", self.proto_ids_off) + \
               pack("<I", self.field_ids_size) + \
               pack("<I", self.field_ids_off) + \
               pack("<I", self.method_ids_size) + \
               pack("<I", self.method_ids_off) + \
               pack("<I", self.class_defs_size) + \
               pack("<I", self.class_defs_off) + \
               pack("<I", self.data_size) + \
               pack("<I", self.data_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return 112

    def show(self):
        bytecode._PrintSubBanner("Header Item")
        bytecode._PrintDefault("magic=%s, checksum=%s, signature=%s\n" %
                               (self.magic, self.checksum,
                                   binascii.hexlify(self.signature).decode("ASCII")))
        bytecode._PrintDefault("file_size=%x, header_size=%x, endian_tag=%x\n" %
                               (self.file_size, self.header_size,
                                self.endian_tag))
        bytecode._PrintDefault("link_size=%x, link_off=%x\n" %
                               (self.link_size, self.link_off))
        bytecode._PrintDefault("map_off=%x\n" % self.map_off)
        bytecode._PrintDefault("string_ids_size=%x, string_ids_off=%x\n" %
                               (self.string_ids_size, self.string_ids_off))
        bytecode._PrintDefault("type_ids_size=%x, type_ids_off=%x\n" %
                               (self.type_ids_size, self.type_ids_off))
        bytecode._PrintDefault("proto_ids_size=%x, proto_ids_off=%x\n" %
                               (self.proto_ids_size, self.proto_ids_off))
        bytecode._PrintDefault("field_ids_size=%x, field_ids_off=%x\n" %
                               (self.field_ids_size, self.field_ids_off))
        bytecode._PrintDefault("method_ids_size=%x, method_ids_off=%x\n" %
                               (self.method_ids_size, self.method_ids_off))
        bytecode._PrintDefault("class_defs_size=%x, class_defs_off=%x\n" %
                               (self.class_defs_size, self.class_defs_off))
        bytecode._PrintDefault("data_size=%x, data_off=%x\n" %
                               (self.data_size, self.data_off))

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset


class AnnotationOffItem:
    """
    This class can parse an annotation_off_item of a dex file

    :param buff: a string which represents a Buff object of the annotation_off_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.annotation_off, = cm.packer["I"].unpack(buff.read(4))

    def get_annotation_off(self):
        return self.annotation_off

    def show(self):
        bytecode._PrintSubBanner("Annotation Off Item")
        bytecode._PrintDefault("annotation_off=0x%x\n" % self.annotation_off)

    def get_obj(self):
        if self.annotation_off != 0:
            self.annotation_off = self.CM.get_obj_by_offset(
                self.annotation_off).get_off()

        return self.CM.packer["I"].pack(self.annotation_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())

    def get_annotation_item(self):
        return self.CM.get_annotation_item(self.get_annotation_off())


class AnnotationSetItem:
    """
    This class can parse an annotation_set_item of a dex file

    :param buff: a string which represents a Buff object of the annotation_set_item
    :type androguard.core.bytecode.BuffHandle buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.size, = cm.packer["I"].unpack(buff.read(4))
        self.annotation_off_item = [AnnotationOffItem(buff, cm) for _ in range(self.size)]

    def get_annotation_off_item(self):
        """
        Return the offset from the start of the file to an annotation

        :rtype: a list of :class:`AnnotationOffItem`
        """
        return self.annotation_off_item

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Annotation Set Item")
        for i in self.annotation_off_item:
            i.show()

    def get_obj(self):
        return self.CM.packer["I"].pack(self.size)

    def get_raw(self):
        return self.get_obj() + b''.join(i.get_raw()
                                         for i in self.annotation_off_item)

    def get_length(self):
        length = len(self.get_obj())

        for i in self.annotation_off_item:
            length += i.get_length()

        return length


class AnnotationSetRefItem:
    """
    This class can parse an annotation_set_ref_item of a dex file

    :param buff: a string which represents a Buff object of the annotation_set_ref_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.annotations_off, = cm.packer["I"].unpack(buff.read(4))

    def get_annotations_off(self):
        """
        Return the offset from the start of the file to the referenced annotation set or
        0 if there are no annotations for this element.

        :rtype: int
        """
        return self.annotations_off

    def show(self):
        bytecode._PrintSubBanner("Annotation Set Ref Item")
        bytecode._PrintDefault("annotation_off=0x%x\n" % self.annotations_off)

    def get_obj(self):
        if self.annotations_off != 0:
            self.annotations_off = self.CM.get_obj_by_offset(
                self.annotations_off).get_off()

        return self.CM.packer["I"].pack(self.annotations_off)

    def get_raw(self):
        return self.get_obj()


class AnnotationSetRefList:
    """
    This class can parse an annotation_set_ref_list_item of a dex file

    :param buff: a string which represents a Buff object of the annotation_set_ref_list_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.offset = buff.get_idx()

        self.CM = cm
        self.size, = cm.packer["I"].unpack(buff.read(4))

        self.list = [AnnotationSetRefItem(buff, cm) for _ in range(self.size)]

    def get_list(self):
        """
        Return elements of the list

        :rtype: :class:`AnnotationSetRefItem`
        """
        return self.list

    def get_off(self):
        return self.offset

    def set_off(self, off):
        self.offset = off

    def show(self):
        bytecode._PrintSubBanner("Annotation Set Ref List Item")
        for i in self.list:
            i.show()

    def get_obj(self):
        return [i for i in self.list]

    def get_raw(self):
        return self.CM.packer["I"].pack(self.size) + b''.join(i.get_raw() for i in self.list)

    def get_length(self):
        return len(self.get_raw())


class FieldAnnotation:
    """
    This class can parse a field_annotation of a dex file

    :param buff: a string which represents a Buff object of the field_annotation
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.offset = buff.get_idx()

        self.CM = cm
        self.field_idx, self.annotations_off = cm.packer["2I"].unpack(buff.read(8))

    def get_field_idx(self):
        """
        Return the index into the field_ids list for the identity of the field being annotated

        :rtype: int
        """
        return self.field_idx

    def get_annotations_off(self):
        """
        Return the offset from the start of the file to the list of annotations for the field

        :rtype: int
        """
        return self.annotations_off

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Field Annotation")
        bytecode._PrintDefault("field_idx=0x%x annotations_off=0x%x\n" %
                               (self.field_idx, self.annotations_off))

    def get_obj(self):
        if self.annotations_off != 0:
            self.annotations_off = self.CM.get_obj_by_offset(
                self.annotations_off).get_off()

        return self.CM.packer["2I"].pack(self.field_idx, self.annotations_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_raw())


class MethodAnnotation:
    """
    This class can parse a method_annotation of a dex file

    :param buff: a string which represents a Buff object of the method_annotation
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.offset = buff.get_idx()

        self.CM = cm
        self.method_idx, \
        self.annotations_off = cm.packer["2I"].unpack(buff.read(8))

    def get_method_idx(self):
        """
        Return the index into the method_ids list for the identity of the method being annotated

        :rtype: int
        """
        return self.method_idx

    def get_annotations_off(self):
        """
        Return the offset from the start of the file to the list of annotations for the method

        :rtype: int
        """
        return self.annotations_off

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Method Annotation")
        bytecode._PrintDefault("method_idx=0x%x annotations_off=0x%x\n" %
                               (self.method_idx, self.annotations_off))

    def get_obj(self):
        if self.annotations_off != 0:
            self.annotations_off = self.CM.get_obj_by_offset(
                self.annotations_off).get_off()

        return self.CM.packer["2I"].pack(self.method_idx, self.annotations_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_raw())


class ParameterAnnotation:
    """
    This class can parse a parameter_annotation of a dex file

    :param buff: a string which represents a Buff object of the parameter_annotation
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.offset = buff.get_idx()

        self.CM = cm
        self.method_idx, \
        self.annotations_off = cm.packer["2I"].unpack(buff.read(8))

    def get_method_idx(self):
        """
        Return the index into the method_ids list for the identity of the method whose parameters are being annotated

        :rtype: int
        """
        return self.get_method_idx

    def get_annotations_off(self):
        """
        Return the offset from the start of the file to the list of annotations for the method parameters

        :rtype: int
        """
        return self.annotations_off

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Parameter Annotation")
        bytecode._PrintDefault("method_idx=0x%x annotations_off=0x%x\n" %
                               (self.method_idx, self.annotations_off))

    def get_obj(self):
        if self.annotations_off != 0:
            self.annotations_off = self.CM.get_obj_by_offset(
                self.annotations_off).get_off()

        return self.CM.packer["2I"].pack(self.method_idx, self.annotations_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_raw())


class AnnotationsDirectoryItem:
    """
    This class can parse an annotations_directory_item of a dex file

    :param buff: a string which represents a Buff object of the annotations_directory_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.class_annotations_off, \
        self.annotated_fields_size, \
        self.annotated_methods_size, \
        self.annotated_parameters_size = cm.packer["4I"].unpack(buff.read(16))

        self.field_annotations = [FieldAnnotation(buff, cm) for i in range(0, self.annotated_fields_size)]

        self.method_annotations = [MethodAnnotation(buff, cm) for i in range(0, self.annotated_methods_size)]

        self.parameter_annotations = [ParameterAnnotation(buff, cm) for i in range(0, self.annotated_parameters_size)]

    def get_class_annotations_off(self):
        """
        Return the offset from the start of the file to the annotations made directly on the class,
        or 0 if the class has no direct annotations

        :rtype: int
        """
        return self.class_annotations_off

    def get_annotation_set_item(self):
        return self.CM.get_annotation_set_item(self.class_annotations_off)

    def get_annotated_fields_size(self):
        """
        Return the count of fields annotated by this item

        :rtype: int
        """
        return self.annotated_fields_size

    def get_annotated_methods_size(self):
        """
        Return the count of methods annotated by this item

        :rtype: int
        """
        return self.annotated_methods_size

    def get_annotated_parameters_size(self):
        """
        Return the count of method parameter lists annotated by this item

        :rtype: int
        """
        return self.annotated_parameters_size

    def get_field_annotations(self):
        """
        Return the list of associated field annotations

        :rtype: a list of :class:`FieldAnnotation`
        """
        return self.field_annotations

    def get_method_annotations(self):
        """
        Return the list of associated method annotations

        :rtype: a list of :class:`MethodAnnotation`
        """
        return self.method_annotations

    def get_parameter_annotations(self):
        """
        Return the list of associated method parameter annotations

        :rtype: a list of :class:`ParameterAnnotation`
        """
        return self.parameter_annotations

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Annotations Directory Item")
        bytecode._PrintDefault(
            "class_annotations_off=0x%x annotated_fields_size=%d annotated_methods_size=%d annotated_parameters_size=%d\n"
            % (self.class_annotations_off, self.annotated_fields_size,
               self.annotated_methods_size, self.annotated_parameters_size))

        for i in self.field_annotations:
            i.show()

        for i in self.method_annotations:
            i.show()

        for i in self.parameter_annotations:
            i.show()

    def get_obj(self):
        if self.class_annotations_off != 0:
            self.class_annotations_off = self.CM.get_obj_by_offset(
                self.class_annotations_off).get_off()

        return self.CM.packer["4I"].pack(self.class_annotations_off,
                    self.annotated_fields_size,
                    self.annotated_methods_size,
                    self.annotated_parameters_size)

    def get_raw(self):
        return self.get_obj() + \
               b''.join(i.get_raw() for i in self.field_annotations) + \
               b''.join(i.get_raw() for i in self.method_annotations) + \
               b''.join(i.get_raw() for i in self.parameter_annotations)

    def get_length(self):
        length = len(self.get_obj())
        for i in self.field_annotations:
            length += i.get_length()

        for i in self.method_annotations:
            length += i.get_length()

        for i in self.parameter_annotations:
            length += i.get_length()

        return length


class TypeItem:
    """
    This class can parse a type_item of a dex file

    :param buff: a string which represents a Buff object of the type_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.type_idx, = cm.packer["H"].unpack(buff.read(2))

    def get_type_idx(self):
        """
        Return the index into the type_ids list

        :rtype: int
        """
        return self.type_idx

    def get_string(self):
        """
        Return the type string

        :rtype: string
        """
        return self.CM.get_type(self.type_idx)

    def show(self):
        bytecode._PrintSubBanner("Type Item")
        bytecode._PrintDefault("type_idx=%d\n" % self.type_idx)

    def get_obj(self):
        return self.CM.packer["H"].pack(self.type_idx)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class TypeList:
    """
    This class can parse a type_list of a dex file

    :param buff: a string which represents a Buff object of the type_list
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()
        self.size, = cm.packer["I"].unpack(buff.read(4))

        self.list = [TypeItem(buff, cm) for _ in range(self.size)]

        self.pad = b""
        if self.size % 2 != 0:
            self.pad = buff.read(2)

        self.len_pad = len(self.pad)

    def get_pad(self):
        """
        Return the alignment string

        :rtype: string
        """
        return self.pad

    def get_type_list_off(self):
        """
        Return the offset of the item

        :rtype: int
        """
        return self.offset

    def get_string(self):
        """
        Return the concatenation of all strings

        :rtype: string
        """
        return ' '.join(i.get_string() for i in self.list)

    def get_size(self):
        """
        Return the size of the list, in entries

        :rtype: int
        """
        return self.size

    def get_list(self):
        """
        Return the list of TypeItem

        :rtype: a list of :class:`TypeItem` objects
        """
        return self.list

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset + self.len_pad

    def show(self):
        bytecode._PrintSubBanner("Type List")
        bytecode._PrintDefault("size=%d\n" % self.size)

        for i in self.list:
            i.show()

    def get_obj(self):
        return self.pad + self.CM.packer["I"].pack(self.size)

    def get_raw(self):
        return self.get_obj() + b''.join(i.get_raw() for i in self.list)

    def get_length(self):
        length = len(self.get_obj())

        for i in self.list:
            length += i.get_length()

        return length


class DBGBytecode:
    def __init__(self, cm, op_value):
        self.CM = cm
        self.op_value = op_value
        self.format = []

    def get_op_value(self):
        return self.op_value

    def add(self, value, ttype):
        self.format.append((value, ttype))

    def get_value(self):
        if self.get_op_value() == DBG_START_LOCAL:
            return self.CM.get_string(self.format[1][0])
        elif self.get_op_value() == DBG_START_LOCAL_EXTENDED:
            return self.CM.get_string(self.format[1][0])

        return None

    def show(self):
        bytecode._PrintSubBanner("DBGBytecode")
        bytecode._PrintDefault("op_value={:x} format={} value={}\n".format(
            self.op_value, str(self.format), self.get_value()))

    def get_obj(self):
        return []

    def get_raw(self):
        buff = self.op_value.get_value_buff()
        for i in self.format:
            if i[1] == "u":
                buff += writeuleb128(self.CM, i[0])
            elif i[1] == "s":
                buff += writesleb128(self.CM, i[0])
        return buff


class DebugInfoItem:
    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.line_start = readuleb128(cm, buff)
        self.parameters_size = readuleb128(cm, buff)

        # print "line", self.line_start, "params", self.parameters_size

        self.parameter_names = []
        for i in range(0, self.parameters_size):
            self.parameter_names.append(readuleb128p1(cm, buff))

        self.bytecodes = []
        bcode = DBGBytecode(self.CM, get_byte(cm, buff))
        self.bytecodes.append(bcode)

        while bcode.get_op_value() != DBG_END_SEQUENCE:
            bcode_value = bcode.get_op_value()

            if bcode_value == DBG_ADVANCE_PC:
                bcode.add(readuleb128(cm, buff), "u")
            elif bcode_value == DBG_ADVANCE_LINE:
                bcode.add(readsleb128(cm, buff), "s")
            elif bcode_value == DBG_START_LOCAL:
                bcode.add(readuleb128(cm, buff), "u")
                bcode.add(readuleb128p1(cm, buff), "u1")
                bcode.add(readuleb128p1(cm, buff), "u1")
            elif bcode_value == DBG_START_LOCAL_EXTENDED:
                bcode.add(readuleb128(cm, buff), "u")
                bcode.add(readuleb128p1(cm, buff), "u1")
                bcode.add(readuleb128p1(cm, buff), "u1")
                bcode.add(readuleb128p1(cm, buff), "u1")
            elif bcode_value == DBG_END_LOCAL:
                bcode.add(readuleb128(cm, buff), "u")
            elif bcode_value == DBG_RESTART_LOCAL:
                bcode.add(readuleb128(cm, buff), "u")
            elif bcode_value == DBG_SET_PROLOGUE_END:
                pass
            elif bcode_value == DBG_SET_EPILOGUE_BEGIN:
                pass
            elif bcode_value == DBG_SET_FILE:
                bcode.add(readuleb128p1(cm, buff), "u1")
            else:  # bcode_value >= DBG_Special_Opcodes_BEGIN and bcode_value <= DBG_Special_Opcodes_END:
                pass

            bcode = DBGBytecode(self.CM, get_byte(cm, buff))
            self.bytecodes.append(bcode)

    def get_parameters_size(self):
        return self.parameters_size

    def get_line_start(self):
        return self.line_start

    def get_parameter_names(self):
        return self.parameter_names

    def get_translated_parameter_names(self):
        l = []
        for i in self.parameter_names:
            if i == -1:
                l.append(None)
            else:
                l.append(self.CM.get_string(i))
        return l

    def get_bytecodes(self):
        return self.bytecodes

    def show(self):
        bytecode._PrintSubBanner("Debug Info Item")
        bytecode._PrintDefault("line_start=%d parameters_size=%d\n" %
                               (self.line_start, self.parameters_size))
        nb = 0
        for i in self.parameter_names:
            bytecode._PrintDefault("parameter_names[%d]=%s\n" %
                                   (nb, self.CM.get_string(i)))
            nb += 1

        for i in self.bytecodes:
            i.show()

    def get_raw(self):
        return [bytecode.Buff(self.__offset, writeuleb128(self.CM, self.line_start) + \
                              writeuleb128(self.CM, self.parameters_size) + \
                              b''.join(writeuleb128(self.CM, i) for i in self.parameter_names) + \
                              b''.join(i.get_raw() for i in self.bytecodes))]

    def get_off(self):
        return self.offset


class DebugInfoItemEmpty:
    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()
        self.__buff = buff
        self.__raw = ""

        self.reload()

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def reload(self):
        offset = self.offset

        n = self.CM.get_next_offset_item(offset)

        s_idx = self.__buff.get_idx()
        self.__buff.set_idx(offset)
        self.__raw = self.__buff.read(n - offset)
        self.__buff.set_idx(s_idx)

    def show(self):
        pass

    def get_obj(self):
        return []

    def get_raw(self):
        return self.__raw

    def get_length(self):
        return len(self.__raw)


class EncodedArray:
    """
    This class can parse an encoded_array of a dex file

    :param buff: a string which represents a Buff object of the encoded_array
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.size = readuleb128(cm, buff)

        self.values = [EncodedValue(buff, cm) for _ in range(self.size)]

    def get_size(self):
        """
        Return the number of elements in the array

        :rtype: int
        """
        return self.size

    def get_values(self):
        """
        Return a series of size encoded_value byte sequences in the format specified by this section,
        concatenated sequentially

        :rtype: a list of :class:`EncodedValue` objects
        """
        return self.values

    def show(self):
        bytecode._PrintSubBanner("Encoded Array")
        bytecode._PrintDefault("size=%d\n" % self.size)

        for i in self.values:
            i.show()

    def get_obj(self):
        return writeuleb128(self.CM, self.size)

    def get_raw(self):
        return self.get_obj() + b''.join(i.get_raw() for i in self.values)

    def get_length(self):
        length = len(self.get_obj())
        for i in self.values:
            length += i.get_length()

        return length


class EncodedValue:
    """
    This class can parse an encoded_value of a dex file

    :param buff: a string which represents a Buff object of the encoded_value
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm

        self.val = get_byte(cm, buff)
        self.value_arg = self.val >> 5
        self.value_type = self.val & 0x1f

        self.raw_value = None
        self.value = ""

        #  TODO: parse floats/doubles correctly
        if VALUE_SHORT <= self.value_type < VALUE_STRING:
            self.value, self.raw_value = self._getintvalue(buff.read(
                self.value_arg + 1))
        elif self.value_type == VALUE_STRING:
            id, self.raw_value = self._getintvalue(buff.read(self.value_arg +
                                                             1))
            self.value = cm.get_raw_string(id)
        elif self.value_type == VALUE_TYPE:
            id, self.raw_value = self._getintvalue(buff.read(self.value_arg +
                                                             1))
            self.value = cm.get_type(id)
        elif self.value_type == VALUE_FIELD:
            id, self.raw_value = self._getintvalue(buff.read(self.value_arg +
                                                             1))
            self.value = cm.get_field(id)
        elif self.value_type == VALUE_METHOD:
            id, self.raw_value = self._getintvalue(buff.read(self.value_arg +
                                                             1))
            self.value = cm.get_method(id)
        elif self.value_type == VALUE_ENUM:
            id, self.raw_value = self._getintvalue(buff.read(self.value_arg +
                                                             1))
            self.value = cm.get_field(id)
        elif self.value_type == VALUE_ARRAY:
            self.value = EncodedArray(buff, cm)
        elif self.value_type == VALUE_ANNOTATION:
            self.value = EncodedAnnotation(buff, cm)
        elif self.value_type == VALUE_BYTE:
            self.value = get_byte(cm, buff)
        elif self.value_type == VALUE_NULL:
            self.value = None
        elif self.value_type == VALUE_BOOLEAN:
            if self.value_arg:
                self.value = True
            else:
                self.value = False
        else:
            log.warning("Unknown value 0x%x" % self.value_type)

    def get_value(self):
        """
        Return the bytes representing the value, variable in length and interpreted differently for different value_type bytes,
        though always little-endian

        :rtype: an object representing the value
        """
        return self.value

    def get_value_type(self):
        return self.value_type

    def get_value_arg(self):
        return self.value_arg

    def _getintvalue(self, buf):
        ret = 0
        shift = 0
        for b in buf:
            ret |= b << shift
            shift += 8

        return ret, buf

    def show(self):
        bytecode._PrintSubBanner("Encoded Value")
        bytecode._PrintDefault("val=%x value_arg=%x value_type=%x\n" %
                               (self.val, self.value_arg, self.value_type))

    def get_obj(self):
        if not isinstance(self.value, str):
            return [self.value]
        return []

    def get_raw(self):
        if self.raw_value is None:
            return self.CM.packer["B"].pack(self.val) + bytecode.object_to_bytes(self.value)
        else:
            return self.CM.packer["B"].pack(self.val) + bytecode.object_to_bytes(self.raw_value)

    def get_length(self):
        return len(self.get_raw())


class AnnotationElement:
    """
    This class can parse an annotation_element of a dex file

    :param buff: a string which represents a Buff object of the annotation_element
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.name_idx = readuleb128(cm, buff)
        self.value = EncodedValue(buff, cm)

    def get_name_idx(self):
        """
        Return the element name, represented as an index into the string_ids section

        :rtype: int
        """
        return self.name_idx

    def get_value(self):
        """
        Return the element value (EncodedValue)

        :rtype: a :class:`EncodedValue` object
        """
        return self.value

    def show(self):
        bytecode._PrintSubBanner("Annotation Element")
        bytecode._PrintDefault("name_idx=%d\n" % self.name_idx)
        self.value.show()

    def get_obj(self):
        return writeuleb128(self.CM, self.name_idx)

    def get_raw(self):
        return self.get_obj() + self.value.get_raw()

    def get_length(self):
        return len(self.get_obj()) + self.value.get_length()


class EncodedAnnotation:
    """
    This class can parse an encoded_annotation of a dex file

    :param buff: a string which represents a Buff object of the encoded_annotation
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.type_idx = readuleb128(cm, buff)
        self.size = readuleb128(cm, buff)

        self.elements = [AnnotationElement(buff, cm) for _ in range(self.size)]

    def get_type_idx(self):
        """
        Return the type of the annotation. This must be a class (not array or primitive) type

        :rtype: int
        """
        return self.type_idx

    def get_size(self):
        """
        Return the number of name-value mappings in this annotation

        :rtype:int
        """
        return self.size

    def get_elements(self):
        """
        Return the elements of the annotation, represented directly in-line (not as offsets)

        :rtype: a list of :class:`AnnotationElement` objects
        """
        return self.elements

    def show(self):
        bytecode._PrintSubBanner("Encoded Annotation")
        bytecode._PrintDefault("type_idx=%d size=%d\n" %
                               (self.type_idx, self.size))

        for i in self.elements:
            i.show()

    def get_obj(self):
        return [i for i in self.elements]

    def get_raw(self):
        return writeuleb128(self.CM, self.type_idx) + writeuleb128(self.CM, self.size) + b''.join(
            i.get_raw() for i in self.elements)

    def get_length(self):
        length = len(writeuleb128(self.CM, self.type_idx) + writeuleb128(self.CM, self.size))

        for i in self.elements:
            length += i.get_length()

        return length


class AnnotationItem:
    """
    This class can parse an annotation_item of a dex file

    :param buff: a string which represents a Buff object of the annotation_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.visibility = get_byte(cm, buff)
        self.annotation = EncodedAnnotation(buff, cm)

    def get_visibility(self):
        """
        Return the intended visibility of this annotation

        :rtype: int
        """
        return self.visibility

    def get_annotation(self):
        """
        Return the encoded annotation contents

        :rtype: a :class:`EncodedAnnotation` object
        """
        return self.annotation

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Annotation Item")
        bytecode._PrintDefault("visibility=%d\n" % self.visibility)
        self.annotation.show()

    def get_obj(self):
        return [self.annotation]

    def get_raw(self):
        return self.CM.packer["B"].pack(self.visibility) + self.annotation.get_raw()

    def get_length(self):
        return len(self.get_raw())


class EncodedArrayItem:
    """
    This class can parse an encoded_array_item of a dex file

    :param buff: a string which represents a Buff object of the encoded_array_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()
        self.value = EncodedArray(buff, cm)

    def get_value(self):
        """
        Return the bytes representing the encoded array value

        :rtype: a :class:`EncodedArray` object
        """
        return self.value

    def set_off(self, off):
        self.offset = off

    def show(self):
        bytecode._PrintSubBanner("Encoded Array Item")
        self.value.show()

    def get_obj(self):
        return [self.value]

    def get_raw(self):
        return self.value.get_raw()

    def get_length(self):
        return self.value.get_length()

    def get_off(self):
        return self.offset


class StringDataItem:
    """
    This class can parse a string_data_item of a dex file

    Strings in Dalvik files might not be representable in python!
    This is due to the fact, that you can store any UTF-16 character inside
    a Dalvik file, but this string might not be decodeable in python as it can
    contain invalid surrogate-pairs.

    To circumvent this issue, this class has different methods how to access the
    string. There are also some fallbacks implemented to make a "invalid" string
    printable in python.
    Dalvik uses MUTF-8 as encoding for the strings. This encoding has the
    advantage to allow for null terminated strings in UTF-8 encoding, as the
    null character maps to something else.
    Therefore you can use :meth:`get_data` to retrieve the actual data of the
    string and can handle encoding yourself.
    Or you use :meth:`get_unicode` to return a decoded UTF-16 string, which
    might cause problems during printing or saving.
    If you want a representation of the string, which should be printable in
    python you ca use :meth:`get` which escapes invalid characters.

    :param buff: a string which represents a Buff object of the string_data_item
    :type buff: BuffHandle
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        # Content of string_data_item
        self.utf16_size = readuleb128(cm, buff)
        self.data = read_null_terminated_string(buff)

    def get_utf16_size(self):
        """
        Return the size of this string, in UTF-16 code units

        :rtype:int
        """
        return self.utf16_size

    def get_data(self):
        """
        Return a series of MUTF-8 code units (a.k.a. octets, a.k.a. bytes) followed by a byte of value 0

        :rtype: string
        """
        return self.data + b"\x00"

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def get(self):
        """
        Returns a MUTF8String object
        """
        return mutf8.MUTF8String(self.data)

    def show(self):
        bytecode._PrintSubBanner("String Data Item")
        bytecode._PrintDefault("utf16_size=%d data=%s\n" %
                               (self.utf16_size, repr(self.get())))

    def get_obj(self):
        return []

    def get_raw(self):
        """
        Returns the raw string including the ULEB128 coded length
        and null byte string terminator

        :return: bytes
        """
        return writeuleb128(self.CM, self.utf16_size) + self.data + b"\x00"

    def get_length(self):
        """
        Get the length of the raw string including the ULEB128 coded
        length and the null byte terminator

        :return: int
        """
        return len(writeuleb128(self.CM, self.utf16_size)) + len(self.data) + 1


class StringIdItem:
    """
    This class can parse a string_id_item of a dex file

    :param buff: a string which represents a Buff object of the string_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.string_data_off, = cm.packer["I"].unpack(buff.read(4))

    def get_string_data_off(self):
        """
        Return the offset from the start of the file to the string data for this item

        :rtype: int
        """
        return self.string_data_off

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("String Id Item")
        bytecode._PrintDefault("string_data_off=%x\n" % self.string_data_off)

    def get_obj(self):
        if self.string_data_off != 0:
            self.string_data_off = self.CM.get_string_by_offset(
                self.string_data_off).get_off()

        return self.CM.packer["I"].pack(self.string_data_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class TypeIdItem:
    """
    This class can parse a type_id_item of a dex file

    :param buff: a string which represents a Buff object of the type_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.descriptor_idx, = cm.packer["I"].unpack(buff.read(4))
        self.descriptor_idx_value = self.CM.get_string(self.descriptor_idx)

    def get_descriptor_idx(self):
        """
        Return the index into the string_ids list for the descriptor string of this type

        :rtype: int
        """
        return self.descriptor_idx

    def get_descriptor_idx_value(self):
        """
        Return the string associated to the descriptor

        :rtype: string
        """
        return self.descriptor_idx_value

    def show(self):
        bytecode._PrintSubBanner("Type Id Item")
        bytecode._PrintDefault("descriptor_idx=%d descriptor_idx_value=%s\n" %
                               (self.descriptor_idx, self.descriptor_idx_value))

    def get_obj(self):
        return self.CM.packer["I"].pack(self.descriptor_idx)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class TypeHIdItem:
    """
    This class can parse a list of type_id_item of a dex file

    :param buff: a string which represents a Buff object of the list of type_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, size, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.type = [TypeIdItem(buff, cm) for i in range(0,size)]

    def get_type(self):
        """
        Return the list of type_id_item

        :rtype: a list of :class:`TypeIdItem` objects
        """
        return self.type

    def get(self, idx):
        try:
            return self.type[idx].get_descriptor_idx()
        except IndexError:
            return -1

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def show(self):
        bytecode._PrintSubBanner("Type List Item")
        for i in self.type:
            i.show()

    def get_obj(self):
        return [i for i in self.type]

    def get_raw(self):
        return b''.join(i.get_raw() for i in self.type)

    def get_length(self):
        length = 0
        for i in self.type:
            length += i.get_length()
        return length


class ProtoIdItem:
    """
    This class can parse a proto_id_item of a dex file

    :param buff: a string which represents a Buff object of the proto_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.shorty_idx, \
        self.return_type_idx, \
        self.parameters_off = cm.packer["3I"].unpack(buff.read(12))

        self.shorty_idx_value = self.CM.get_string(self.shorty_idx)
        self.return_type_idx_value = self.CM.get_type(self.return_type_idx)
        self.parameters_off_value = None

    def get_shorty_idx(self):
        """
        Return the index into the string_ids list for the short-form descriptor string of this prototype

        :rtype: int
        """
        return self.shorty_idx

    def get_return_type_idx(self):
        """
        Return the index into the type_ids list for the return type of this prototype

        :rtype: int
        """
        return self.return_type_idx

    def get_parameters_off(self):
        """
        Return the offset from the start of the file to the list of parameter types for this prototype, or 0 if this prototype has no parameters

        :rtype: int
        """
        return self.parameters_off

    def get_shorty_idx_value(self):
        """
        Return the string associated to the shorty_idx

        :rtype: string
        """
        if self.shorty_idx_value is None:
            self.shorty_idx_value = self.CM.get_string(self.shorty_idx)
        return self.shorty_idx_value

    def get_return_type_idx_value(self):
        """
        Return the string associated to the return_type_idx

        :rtype: string
        """
        if self.return_type_idx_value is None:
            self.return_type_idx_value = self.CM.get_type(self.return_type_idx)

        return self.return_type_idx_value

    def get_parameters_off_value(self):
        """
        Return the string associated to the parameters_off

        :rtype: MUTF8String
        """
        if self.parameters_off_value is None:
            params = self.CM.get_type_list(self.parameters_off)
            self.parameters_off_value = mutf8.MUTF8String(b'(' + b' '.join(params) + b')')
        return self.parameters_off_value

    def show(self):
        bytecode._PrintSubBanner("Proto Item")
        bytecode._PrintDefault(
            "shorty_idx=%d return_type_idx=%d parameters_off=%d\n" %
            (self.shorty_idx, self.return_type_idx, self.parameters_off))
        bytecode._PrintDefault(
            "shorty_idx_value=%s return_type_idx_value=%s parameters_off_value=%s\n"
            % (self.shorty_idx_value, self.return_type_idx_value,
               self.parameters_off_value))

    def get_obj(self):
        if self.parameters_off != 0:
            self.parameters_off = self.CM.get_obj_by_offset(
                self.parameters_off).get_off()

        return self.CM.packer["3I"].pack(self.shorty_idx,
                    self.return_type_idx,
                    self.parameters_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class ProtoHIdItem:
    """
    This class can parse a list of proto_id_item of a dex file

    :param buff: a string which represents a Buff object of the list of proto_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, size, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.proto = [ProtoIdItem(buff, cm) for i in range(0, size)]

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def get(self, idx):
        try:
            return self.proto[idx]
        except IndexError:
            return ProtoIdItemInvalid()

    def show(self):
        bytecode._PrintSubBanner("Proto List Item")
        for i in self.proto:
            i.show()

    def get_obj(self):
        return [i for i in self.proto]

    def get_raw(self):
        return b''.join(i.get_raw() for i in self.proto)

    def get_length(self):
        length = 0
        for i in self.proto:
            length += i.get_length()
        return length


class FieldIdItem:
    """
    This class can parse a field_id_item of a dex file

    :param buff: a string which represents a Buff object of the field_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.class_idx, \
        self.type_idx, \
        self.name_idx = cm.packer["2HI"].unpack(buff.read(8))

        self.reload()

    def reload(self):
        self.class_idx_value = self.CM.get_type(self.class_idx)
        self.type_idx_value = self.CM.get_type(self.type_idx)
        self.name_idx_value = self.CM.get_string(self.name_idx)

    def get_class_idx(self):
        """
        Return the index into the type_ids list for the definer of this field

        :rtype: int
        """
        return self.class_idx

    def get_type_idx(self):
        """
        Return the index into the type_ids list for the type of this field

        :rtype: int
        """
        return self.type_idx

    def get_name_idx(self):
        """
        Return the index into the string_ids list for the name of this field

        :rtype: int
        """
        return self.name_idx

    def get_class_name(self):
        """
        Return the class name of the field

        :rtype: string
        """
        if self.class_idx_value is None:
            self.class_idx_value = self.CM.get_type(self.class_idx)

        return self.class_idx_value

    def get_type(self):
        """
        Return the type of the field

        :rtype: string
        """
        if self.type_idx_value is None:
            self.type_idx_value = self.CM.get_type(self.type_idx)

        return self.type_idx_value

    def get_descriptor(self):
        """
        Return the descriptor of the field

        :rtype: string
        """
        if self.type_idx_value is None:
            self.type_idx_value = self.CM.get_type(self.type_idx)

        return self.type_idx_value

    def get_name(self):
        """
        Return the name of the field

        :rtype: string
        """
        if self.name_idx_value is None:
            self.name_idx_value = self.CM.get_string(self.name_idx)

        return self.name_idx_value

    def get_list(self):
        return [self.get_class_name(), self.get_type(), self.get_name()]

    def show(self):
        bytecode._PrintSubBanner("Field Id Item")
        bytecode._PrintDefault("class_idx=%d type_idx=%d name_idx=%d\n" %
                               (self.class_idx, self.type_idx, self.name_idx))
        bytecode._PrintDefault(
            "class_idx_value=%s type_idx_value=%s name_idx_value=%s\n" %
            (self.class_idx_value, self.type_idx_value, self.name_idx_value))

    def get_obj(self):
        return self.CM.packer["2HI"].pack(self.class_idx,
                    self.type_idx,
                    self.name_idx)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class FieldHIdItem:
    """
    This class can parse a list of field_id_item of a dex file

    :param buff: a string which represents a Buff object of the list of field_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, size, buff, cm):
        self.offset = buff.get_idx()

        self.elem = [FieldIdItem(buff, cm) for i in range(0, size)]

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def gets(self):
        return self.elem

    def get(self, idx):
        try:
            return self.elem[idx]
        except IndexError:
            return FieldIdItemInvalid()

    def show(self):
        nb = 0
        for i in self.elem:
            print(nb, end=' ')
            i.show()
            nb = nb + 1

    def get_obj(self):
        return [i for i in self.elem]

    def get_raw(self):
        return b''.join(i.get_raw() for i in self.elem)

    def get_length(self):
        length = 0
        for i in self.elem:
            length += i.get_length()
        return length


class MethodIdItem:
    """
    This class can parse a method_id_item of a dex file

    :param buff: a string which represents a Buff object of the method_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.class_idx, \
        self.proto_idx, \
        self.name_idx = cm.packer["2HI"].unpack(buff.read(8))

        self.reload()

    def reload(self):
        self.class_idx_value = self.CM.get_type(self.class_idx)
        self.proto_idx_value = self.CM.get_proto(self.proto_idx)
        self.name_idx_value = self.CM.get_string(self.name_idx)

    def get_class_idx(self):
        """
        Return the index into the type_ids list for the definer of this method

        :rtype: int
        """
        return self.class_idx

    def get_proto_idx(self):
        """
        Return the index into the proto_ids list for the prototype of this method

        :rtype: int
        """
        return self.proto_idx

    def get_name_idx(self):
        """
        Return the index into the string_ids list for the name of this method

        :rtype: int
        """
        return self.name_idx

    def get_class_name(self):
        """
        Return the class name of the method

        :rtype: string
        """
        if self.class_idx_value is None:
            self.class_idx_value = self.CM.get_type(self.class_idx)

        return self.class_idx_value

    def get_proto(self):
        """
        Return the prototype of the method

        :rtype: string
        """
        if self.proto_idx_value is None:
            self.proto_idx_value = self.CM.get_proto(self.proto_idx)

        return self.proto_idx_value

    def get_descriptor(self):
        """
        Return the descriptor

        :rtype: string
        """
        proto = self.get_proto()
        return proto[0] + proto[1]

    def get_real_descriptor(self):
        """
        Return the real descriptor (i.e. without extra spaces)

        :rtype: string
        """
        proto = self.get_proto()
        return proto[0].replace(' ', '') + proto[1]

    def get_name(self):
        """
        Return the name of the method

        :rtype: string
        """
        if self.name_idx_value is None:
            self.name_idx_value = self.CM.get_string(self.name_idx)

        return self.name_idx_value

    def get_list(self):
        return [self.get_class_name(), self.get_name(), self.get_proto()]

    def get_triple(self):
        return self.get_class_name()[1:-1], self.get_name(
        ), self.get_real_descriptor()

    def show(self):
        bytecode._PrintSubBanner("Method Id Item")
        bytecode._PrintDefault("class_idx=%d proto_idx=%d name_idx=%d\n" %
                               (self.class_idx, self.proto_idx, self.name_idx))
        bytecode._PrintDefault(
            "class_idx_value=%s proto_idx_value=%s name_idx_value=%s\n" %
            (self.class_idx_value, self.proto_idx_value, self.name_idx_value))

    def get_obj(self):
        return self.CM.packer["2HI"].pack(self.class_idx,
                    self.proto_idx,
                    self.name_idx)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class MethodHIdItem:
    """
    This class can parse a list of method_id_item of a dex file

    :param buff: a string which represents a Buff object of the list of method_id_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, size, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.methods = [MethodIdItem(buff, cm) for i in range(0, size)]

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def get(self, idx):
        try:
            return self.methods[idx]
        except IndexError:
            return MethodIdItemInvalid()

    def reload(self):
        for i in self.methods:
            i.reload()

    def show(self):
        print("METHOD_ID_ITEM")
        nb = 0
        for i in self.methods:
            print(nb, end=' ')
            i.show()
            nb = nb + 1

    def get_obj(self):
        return [i for i in self.methods]

    def get_raw(self):
        return b''.join(i.get_raw() for i in self.methods)

    def get_length(self):
        length = 0
        for i in self.methods:
            length += i.get_length()
        return length


class ProtoIdItemInvalid:
    def get_params(self):
        return "AG:IPI:invalid_params;"

    def get_shorty(self):
        return "(AG:IPI:invalid_shorty)"

    def get_return_type(self):
        return "(AG:IPI:invalid_return_type)"

    def show(self):
        print("AG:IPI:invalid_proto_item", self.get_shorty(
        ), self.get_return_type(), self.get_params())


class FieldIdItemInvalid:
    def get_class_name(self):
        return "AG:IFI:invalid_class_name;"

    def get_type(self):
        return "(AG:IFI:invalid_type)"

    def get_descriptor(self):
        return "(AG:IFI:invalid_descriptor)"

    def get_name(self):
        return "AG:IFI:invalid_name"

    def get_list(self):
        return [self.get_class_name(), self.get_type(), self.get_name()]

    def show(self):
        print("AG:IFI:invalid_field_item")


class MethodIdItemInvalid:
    def get_class_name(self):
        return "AG:IMI:invalid_class_name;"

    def get_descriptor(self):
        return "(AG:IMI:invalid_descriptor)"

    def get_proto(self):
        return "()AG:IMI:invalid_proto"

    def get_name(self):
        return "AG:IMI:invalid_name"

    def get_list(self):
        return [self.get_class_name(), self.get_name(), self.get_proto()]

    def show(self):
        print("AG:IMI:invalid_method_item")


class EncodedField:
    """
    This class can parse an encoded_field of a dex file

    :param buff: a string which represents a Buff object of the encoded field
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.field_idx_diff = readuleb128(cm, buff)
        self.access_flags = readuleb128(cm, buff)

        self.field_idx = 0

        self.name = None
        self.proto = None
        self.class_name = None

        self.init_value = None
        self.access_flags_string = None
        self.loaded = False

    def load(self):
        if self.loaded:
            return
        self.reload()
        self.loaded = True

    def reload(self):
        name = self.CM.get_field(self.field_idx)
        self.class_name = name[0]
        self.name = name[2]
        self.proto = name[1]

    def set_init_value(self, value):
        """
        Setup the init value object of the field

        :param value: the init value
        :type value: :class:`EncodedValue`
        """
        self.init_value = value

    def get_init_value(self):
        """
        Return the init value object of the field

        :rtype: :class:`EncodedValue`
        """
        return self.init_value

    def adjust_idx(self, val):
        self.field_idx = self.field_idx_diff + val

    def get_field_idx_diff(self):
        """
        Return the index into the field_ids list for the identity of this field (includes the name and descriptor),
        represented as a difference from the index of previous element in the list

        :rtype: int
        """
        return self.field_idx_diff

    def get_field_idx(self):
        """
        Return the real index of the method

        :rtype: int
        """
        return self.field_idx

    def get_access_flags(self):
        """
        Return the access flags of the field

        :rtype: int
        """
        return self.access_flags

    def get_class_name(self):
        """
        Return the class name of the field

        :rtype: string
        """
        if not self.loaded:
            self.load()
        return self.class_name

    def get_descriptor(self):
        """
        Return the descriptor of the field

        The descriptor of a field is the type of the field.

        :rtype: string
        """
        if not self.loaded:
            self.load()
        return self.proto

    def get_name(self):
        """
        Return the name of the field

        :rtype: string
        """
        if not self.loaded:
            self.load()
        return self.name

    def get_access_flags_string(self):
        """
        Return the access flags string of the field

        :rtype: string
        """
        if self.access_flags_string is None:
            if self.get_access_flags() == 0:
                # No access flags, i.e. Java defaults apply
                self.access_flags_string = ""
                return self.access_flags_string

            # Try to parse the string
            self.access_flags_string = get_access_flags_string(self.get_access_flags())

            # Fallback for unknown strings
            if self.access_flags_string == "":
                self.access_flags_string = "0x{:06x}".format(self.get_access_flags())
        return self.access_flags_string

    def set_name(self, value):
        self.CM.set_hook_field_name(self, value)
        self.reload()

    def get_obj(self):
        return []

    def get_raw(self):
        return writeuleb128(self.CM, self.field_idx_diff) + writeuleb128(self.CM, 
            self.access_flags)

    def get_size(self):
        return len(self.get_raw())

    def show(self):
        """
        Display the information (with a pretty print) about the field
        """
        bytecode._PrintSubBanner("Field Information")
        bytecode._PrintDefault("{}->{} {} [access_flags={}]\n".format(
            self.get_class_name(), self.get_name(), self.get_descriptor(),
            self.get_access_flags_string()))

        init_value = self.get_init_value()
        if init_value is not None:
            bytecode._PrintDefault("\tinit value: %s\n" %
                                   str(init_value.get_value()))

    def __str__(self):
        return "{}->{} {} [access_flags={}]\n".format(
            self.get_class_name(), self.get_name(), self.get_descriptor(),
            self.get_access_flags_string())


class EncodedMethod:
    """
    This class can parse an encoded_method of a dex file

    :param buff: a string which represents a Buff object of the encoded_method
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.method_idx_diff = readuleb128(cm, buff)  #: method index diff in the corresponding section
        self.access_flags = readuleb128(cm, buff)  #: access flags of the method
        self.code_off = readuleb128(cm, buff)  #: offset of the code section

        self.method_idx = 0

        self.name = None
        self.proto = None
        self.class_name = None

        self.code = None

        self.access_flags_string = None

        self.notes = []
        self.loaded = False

    def adjust_idx(self, val):
        self.method_idx = self.method_idx_diff + val

    def get_method_idx(self):
        """
        Return the real index of the method

        :rtype: int
        """
        return self.method_idx

    def get_method_idx_diff(self):
        """
        Return index into the method_ids list for the identity of this method (includes the name and descriptor),
        represented as a difference from the index of previous element in the lis

        :rtype: int
        """
        return self.method_idx_diff

    def get_access_flags(self):
        """
        Return the access flags of the method

        :rtype: int
        """
        return self.access_flags

    def get_code_off(self):
        """
        Return the offset from the start of the file to the code structure for this method,
        or 0 if this method is either abstract or native

        :rtype: int
        """
        return self.code_off

    def get_address(self):
        """
        Return the offset from the start of the file to the code structure for this method,
        or 0 if this method is either abstract or native

        :rtype: int
        """
        return self.code_off + 0x10

    def get_access_flags_string(self):
        """
        Return the access flags string of the method

        A description of all access flags can be found here:
        https://source.android.com/devices/tech/dalvik/dex-format#access-flags

        :rtype: string
        """
        if self.access_flags_string is None:
            self.access_flags_string = get_access_flags_string(self.get_access_flags())

            if self.access_flags_string == "" and self.get_access_flags() != 0x0:
                self.access_flags_string = "0x%x" % self.get_access_flags()
        return self.access_flags_string

    def load(self):
        if self.loaded:
            return
        self.reload()
        self.loaded = True

    def reload(self):
        v = self.CM.get_method(self.method_idx)
        # TODO this can probably be more elegant:
        # get_method returns an array with the already resolved types.
        # But for example to count the number of parameters, we need to split the string now.
        # This is quite tedious and could be avoided if we would return the type IDs
        # instead and resolve them here.
        if v and len(v) >= 3:
            self.class_name = v[0]
            self.name = v[1]
            self.proto = mutf8.MUTF8String.join(i for i in v[2])
        else:
            self.class_name = 'CLASS_NAME_ERROR'
            self.name = 'NAME_ERROR'
            self.proto = 'PROTO_ERROR'

        self.code = self.CM.get_code(self.code_off)

    def get_locals(self):
        """
        Get the number of local registers used by the method

        This number is equal to the number of registers minus the number of parameters minus 1.

        :return: number of local registers
        :rtype: int
        """
        ret = self.proto.split(')')
        params = ret[0][1:].split()

        return self.code.get_registers_size() - len(params) - 1

    def get_information(self):
        """
        Get brief information about the method's register use,
        parameters and return type.

        The resulting dictionary has the form:

        .. code-block:: none

            {
                registers: (start, end),
                params: [(reg_1, type_1), (reg_2, type_2), ..., (reg_n, type_n)],
                return: type
            )

        The end register is not the last register used, but the last register
        used not for parameters. Hence, they represent the local registers.
        The start register is always zero.
        The register numbers for the parameters can be found in the tuples
        for each parameter.

        :return: a dictionary with the basic information about the method
        :rtype: dict
        """
        info = dict()
        if self.code:
            nb = self.code.get_registers_size()
            proto = self.get_descriptor()

            ret = proto.split(')')
            params = ret[0][1:].split()

            info["return"] = get_type(ret[1])

            if params:
                info["registers"] = (0, nb - len(params) - 1)
                j = 0
                info["params"] = []
                for i in range(nb - len(params), nb):
                    info["params"].append((i, get_type(params[j])))
                    j += 1
            else:
                info["registers"] = (0, nb - 1)

        return info

    def each_params_by_register(self, nb, proto):
        """
        From the Dalvik Bytecode documentation:

        > The N arguments to a method land in the last N registers
        > of the method's invocation frame, in order.
        > Wide arguments consume two registers.
        > Instance methods are passed a this reference as their first argument.

        This method will print a description of the register usage to stdout.

        :param nb: number of registers
        :param proto: descriptor of method
        """
        bytecode._PrintSubBanner("Params")

        ret = proto.split(')')
        params = ret[0][1:].split()
        if params:
            bytecode._PrintDefault("- local registers: v%d...v%d\n" %
                                   (0, nb - len(params) - 1))
            j = 0
            for i in range(nb - len(params), nb):
                bytecode._PrintDefault("- v%d: %s\n" % (i, get_type(params[j])))
                j += 1
        else:
            bytecode._PrintDefault("local registers: v%d...v%d\n" % (0, nb - 1))

        bytecode._PrintDefault("- return: %s\n" % get_type(ret[1]))
        bytecode._PrintSubBanner()

    def __str__(self):
        return "{}->{}{} [access_flags={}] @ 0x{:x}".format(
            self.get_class_name(), self.get_name(), self.get_descriptor(),
            self.get_access_flags_string(), self.get_code_off())

    @property
    def full_name(self):
        """Return class_name + name + descriptor, separated by spaces (no access flags"""
        return mutf8.MUTF8String.join([self.class_name, self.name, self.get_descriptor()], spacing=b' ')

    @property
    def descriptor(self):
        """Get the descriptor of the method"""
        return self.get_descriptor()

    def get_short_string(self):
        """
        Return a shorter formatted String which encodes this method.
        The returned name has the form:
        <classname> <methodname> ([arguments ...])<returntype>

        * All Class names are condensed to the actual name (no package).
        * Access flags are not returned.
        * <init> and <clinit> are NOT replaced by the classname!

        This name might not be unique!

        :return: str
        """
        def _fmt_classname(cls):
            arr = ""
            # Test for arrays
            while cls.startswith("["):
                arr += "["
                cls = cls[1:]

            # is a object type
            if cls.startswith("L"):
                cls = cls[1:-1]
            # only return last element
            if "/" in cls:
                cls = cls.rsplit("/", 1)[1]
            return arr + cls

        clsname = _fmt_classname(str(self.get_class_name()))

        param, ret = str(self.get_descriptor())[1:].split(")")
        params = map(_fmt_classname, param.split(" "))
        desc = "({}){}".format(''.join(params), _fmt_classname(ret))
        return "{cls} {meth} {desc}".format(cls=clsname, meth=self.get_name(), desc=desc)

    def show_info(self):
        """
        Display the basic information about the method
        """
        bytecode._PrintSubBanner("Method Information")
        bytecode._PrintDefault("{}->{}{} [access_flags={}]\n".format(
            self.get_class_name(), self.get_name(), self.get_descriptor(),
            self.get_access_flags_string()))

    def show(self):
        """
        Display the information (with a pretty print) about the method
        """
        self.show_info()
        self.show_notes()
        if self.code:
            self.each_params_by_register(self.code.get_registers_size(), self.get_descriptor())
            self.code.show()

    def show_notes(self):
        """
        Display the notes about the method
        """
        if self.notes:
            bytecode._PrintSubBanner("Notes")
            for i in self.notes:
                bytecode._PrintNote(i)
            bytecode._PrintSubBanner()

    def source(self):
        """
        Return the source code of this method

        :rtype: string
        """
        self.CM.decompiler_ob.display_source(self)

    def get_source(self):
        return self.CM.decompiler_ob.get_source_method(self)

    def get_length(self):
        """
        Return the length of the associated code of the method

        :rtype: int
        """
        if self.code is not None:
            return self.code.get_length()
        return 0

    def get_code(self):
        """
        Return the code object associated to the method


        :rtype: :class:`DalvikCode` object or None if no Code
        """
        if not self.loaded:
            self.load()
        return self.code

    def is_cached_instructions(self):
        if self.code is None:
            return False

        return self.code.get_bc().is_cached_instructions()

    def get_instructions(self):
        """
        Get the instructions

        :rtype: a generator of each :class:`Instruction` (or a cached list of instructions if you have setup instructions)
        """
        if self.get_code() is None:
            return []
        return self.get_code().get_bc().get_instructions()

    def get_instructions_idx(self):
        """
        Iterate over all instructions of the method, but also return the current index.
        This is the same as using :meth:`get_instructions` and adding the instruction length
        to a variable each time.

        :return:
        :rtype: Iterator[(int, Instruction)]
        """
        if self.get_code() is None:
            return []
        idx = 0
        for ins in self.get_code().get_bc().get_instructions():
            yield idx, ins
            idx += ins.get_length()

    def set_instructions(self, instructions):
        """
        Set the instructions

        :param instructions: the list of instructions
        :type instructions: a list of :class:`Instruction`
        """
        if self.code is None:
            return []
        return self.code.get_bc().set_instructions(instructions)

    def get_instruction(self, idx, off=None):
        """
        Get a particular instruction by using (default) the index of the address if specified

        :param idx: index of the instruction (the position in the list of the instruction)
        :type idx: int
        :param off: address of the instruction
        :type off: int

        :rtype: an :class:`Instruction` object
        """
        if self.get_code() is not None:
            return self.get_code().get_bc().get_instruction(idx, off)
        return None

    def get_debug(self):
        """
        Return the debug object associated to this method

        :rtype: :class:`DebugInfoItem`
        """
        if self.get_code() is None:
            return None
        return self.get_code().get_debug()

    def get_descriptor(self):
        """
        Return the descriptor of the method
        A method descriptor will have the form (A A A ...)R
        Where A are the arguments to the method and R is the return type.
        Basic types will have the short form, i.e. I for integer, V for void
        and class types will be named like a classname, e.g. Ljava/lang/String;.

        Typical descriptors will look like this:
        ```
        (I)I   // one integer argument, integer return
        (C)Z   // one char argument, boolean as return
        (Ljava/lang/CharSequence; I)I   // CharSequence and integer as
        argyument, integer as return
        (C)Ljava/lang/String;  // char as argument, String as return.
        ```

        More information about type descriptors are found here:
        https://source.android.com/devices/tech/dalvik/dex-format#typedescriptor

        :rtype: string
        """
        if not self.loaded:
            self.load()
        return self.proto

    def get_class_name(self):
        """
        Return the class name of the method

        :rtype: string
        """
        if not self.loaded:
            self.load()
        return self.class_name

    def get_name(self):
        """
        Return the name of the method

        :rtype: string
        """
        if not self.loaded:
            self.load()
        return self.name

    def get_triple(self):
        return self.CM.get_method_ref(self.method_idx).get_triple()

    def add_inote(self, msg, idx, off=None):
        """
        Add a message to a specific instruction by using (default) the index of the address if specified

        :param msg: the message
        :type msg: string
        :param idx: index of the instruction (the position in the list of the instruction)
        :type idx: int
        :param off: address of the instruction
        :type off: int
        """
        if self.code is not None:
            self.code.add_inote(msg, idx, off)

    def add_note(self, msg):
        """
        Add a message to this method

        :param msg: the message
        :type msg: string
        """
        self.notes.append(msg)

    def set_code_idx(self, idx):
        """
        Set the start address of the buffer to disassemble

        :param idx: the index
        :type idx: int
        """
        if self.code is not None:
            self.code.set_idx(idx)

    def set_name(self, value):
        self.CM.set_hook_method_name(self, value)
        self.reload()

    def get_raw(self):
        if self.code is not None:
            self.code_off = self.code.get_off()

        return writeuleb128(self.CM, self.method_idx_diff) + writeuleb128(self.CM, 
            self.access_flags) + writeuleb128(self.CM, self.code_off)

    def get_size(self):
        return len(self.get_raw())


class ClassDataItem:
    """
    This class can parse a class_data_item of a dex file

    :param buff: a string which represents a Buff object of the class_data_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.static_fields_size = readuleb128(cm, buff)
        self.instance_fields_size = readuleb128(cm, buff)
        self.direct_methods_size = readuleb128(cm, buff)
        self.virtual_methods_size = readuleb128(cm, buff)

        self.static_fields = []
        self.instance_fields = []
        self.direct_methods = []
        self.virtual_methods = []

        self._load_elements(self.static_fields_size, self.static_fields,
                            EncodedField, buff, cm)
        self._load_elements(self.instance_fields_size, self.instance_fields,
                            EncodedField, buff, cm)
        self._load_elements(self.direct_methods_size, self.direct_methods,
                            EncodedMethod, buff, cm)
        self._load_elements(self.virtual_methods_size, self.virtual_methods,
                            EncodedMethod, buff, cm)

    def get_static_fields_size(self):
        """
        Return the number of static fields defined in this item

        :rtype: int
        """
        return self.static_fields_size

    def get_instance_fields_size(self):
        """
        Return the number of instance fields defined in this item

        :rtype: int
        """
        return self.instance_fields_size

    def get_direct_methods_size(self):
        """
        Return the number of direct methods defined in this item

        :rtype: int
        """
        return self.direct_methods_size

    def get_virtual_methods_size(self):
        """
        Return the number of virtual methods defined in this item

        :rtype: int
        """
        return self.virtual_methods_size

    def get_static_fields(self):
        """
        Return the defined static fields, represented as a sequence of encoded elements

        :rtype: a list of :class:`EncodedField` objects
        """
        return self.static_fields

    def get_instance_fields(self):
        """
        Return the defined instance fields, represented as a sequence of encoded elements

        :rtype: a list of :class:`EncodedField` objects
        """
        return self.instance_fields

    def get_direct_methods(self):
        """
        Return the defined direct (any of static, private, or constructor) methods, represented as a sequence of encoded elements

        :rtype: a list of :class:`EncodedMethod` objects
        """
        return self.direct_methods

    def get_virtual_methods(self):
        """
        Return the defined virtual (none of static, private, or constructor) methods, represented as a sequence of encoded elements

        :rtype: a list of :class:`EncodedMethod` objects

        """

        return self.virtual_methods

    def get_methods(self):
        """
        Return direct and virtual methods

        :rtype: a list of :class:`EncodedMethod` objects
        """
        return [x
                for x in self.direct_methods] + [x
                                                 for x in self.virtual_methods]

    def get_fields(self):
        """
        Return static and instance fields

        :rtype: a list of :class:`EncodedField` objects
        """
        return [x for x in self.static_fields] + [x
                                                  for x in self.instance_fields]

    def set_off(self, off):
        self.offset = off

    def set_static_fields(self, value):
        if value is not None:
            values = value.get_values()
            if len(values) <= len(self.static_fields):
                for i in range(0, len(values)):
                    self.static_fields[i].set_init_value(values[i])

    def _load_elements(self, size, l, Type, buff, cm):
        prev = 0
        for i in range(0, size):
            el = Type(buff, cm)
            el.adjust_idx(prev)

            if isinstance(el, EncodedField):
                prev = el.get_field_idx()
            else:
                prev = el.get_method_idx()

            l.append(el)

    def show(self):
        bytecode._PrintSubBanner("Class Data Item")
        bytecode._PrintDefault(
            "static_fields_size=%d instance_fields_size=%d direct_methods_size=%d virtual_methods_size=%d\n" % \
            (self.static_fields_size, self.instance_fields_size, self.direct_methods_size, self.virtual_methods_size))

        bytecode._PrintSubBanner("Static Fields")
        for i in self.static_fields:
            i.show()

        bytecode._PrintSubBanner("Instance Fields")
        for i in self.instance_fields:
            i.show()

        bytecode._PrintSubBanner("Direct Methods")
        for i in self.direct_methods:
            i.show()

        bytecode._PrintSubBanner("Virtual Methods")
        for i in self.virtual_methods:
            i.show()

    def get_obj(self):
        return [i for i in self.static_fields] + \
               [i for i in self.instance_fields] + \
               [i for i in self.direct_methods] + \
               [i for i in self.virtual_methods]

    def get_raw(self):
        buff = writeuleb128(self.CM, self.static_fields_size) + \
               writeuleb128(self.CM, self.instance_fields_size) + \
               writeuleb128(self.CM, self.direct_methods_size) + \
               writeuleb128(self.CM, self.virtual_methods_size) + \
               b''.join(i.get_raw() for i in self.static_fields) + \
               b''.join(i.get_raw() for i in self.instance_fields) + \
               b''.join(i.get_raw() for i in self.direct_methods) + \
               b''.join(i.get_raw() for i in self.virtual_methods)

        return buff

    def get_length(self):
        length = len(writeuleb128(self.CM, self.static_fields_size)) + \
                 len(writeuleb128(self.CM, self.instance_fields_size)) + \
                 len(writeuleb128(self.CM, self.direct_methods_size)) + \
                 len(writeuleb128(self.CM, self.virtual_methods_size))

        for i in self.static_fields:
            length += i.get_size()

        for i in self.instance_fields:
            length += i.get_size()

        for i in self.direct_methods:
            length += i.get_size()

        for i in self.virtual_methods:
            length += i.get_size()

        return length

    def get_off(self):
        return self.offset


class ClassDefItem:
    """
    This class can parse a class_def_item of a dex file

    :param buff: a string which represents a Buff object of the class_def_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.class_idx, \
        self.access_flags, \
        self.superclass_idx, \
        self.interfaces_off, \
        self.source_file_idx, \
        self.annotations_off, \
        self.class_data_off, \
        self.static_values_off = cm.packer["8I"].unpack(buff.read(32))

        self.interfaces = []
        self.class_data_item = None
        self.static_values = None
        self.annotations_directory_item = None

        self.name = None
        self.sname = None
        self.access_flags_string = None

        self.reload()

    def reload(self):
        self.name = self.CM.get_type(self.class_idx)
        self.sname = self.CM.get_type(self.superclass_idx)
        self.interfaces = self.CM.get_type_list(self.interfaces_off)

        if self.class_data_off != 0:
            self.class_data_item = self.CM.get_class_data_item(self.class_data_off)

        if self.annotations_off != 0:
            self.annotations_directory_item = self.CM.get_annotations_directory_item(self.annotations_off)

        if self.static_values_off != 0:
            self.static_values = self.CM.get_encoded_array_item(self.static_values_off)

            if self.class_data_item:
                self.class_data_item.set_static_fields(self.static_values.get_value())

    def __str__(self):
        return "{}->{}".format(self.get_superclassname(), self.get_name())

    def __repr__(self):
        return "<dvm.ClassDefItem {}>".format(self.__str__())

    def get_methods(self):
        """
        Return all methods of this class

        :rtype: a list of :class:`EncodedMethod` objects
        """
        if self.class_data_item is not None:
            return self.class_data_item.get_methods()
        return []

    def get_fields(self):
        """
        Return all fields of this class

        :rtype: a list of :class:`EncodedField` objects
        """
        if self.class_data_item is not None:
            return self.class_data_item.get_fields()
        return []

    def _get_annotation_type_ids(self):
        """
        Get the EncodedAnnotations from this class

        :rtype: Iterator[EncodedAnnotation]
        """
        if self.annotations_directory_item is None:
            return []
        annotation_set_item = self.annotations_directory_item.get_annotation_set_item()
        if annotation_set_item is None:
            return []
        
        annotation_off_item = annotation_set_item.get_annotation_off_item()

        if annotation_off_item is None:
            return []
        
        return [annotation.get_annotation_item().annotation for annotation in annotation_off_item]

    def get_annotations(self):
        """
        Returns the class names of the annotations of this class.

        For example, if the class is marked as :code:`@Deprecated`, this will return
        :code:`['Ljava/lang/Deprecated;']`.

        :rtype: Iterator[mutf8.MUTF8String]
        """
        return [self.CM.get_type(x.get_type_idx()) for x in self._get_annotation_type_ids()]

    def get_class_idx(self):
        """
        Return the index into the type_ids list for this class

        :rtype: int
        """
        return self.class_idx

    def get_access_flags(self):
        """
        Return the access flags for the class (public, final, etc.)

        :rtype: int
        """
        return self.access_flags

    def get_superclass_idx(self):
        """
        Return the index into the type_ids list for the superclass

        :rtype: int
        """
        return self.superclass_idx

    def get_interfaces_off(self):
        """
        Return the offset from the start of the file to the list of interfaces, or 0 if there are none

        :rtype: int
        """
        return self.interfaces_off

    def get_source_file_idx(self):
        """
        Return the index into the string_ids list for the name of the file containing the original
        source for (at least most of) this class, or the special value NO_INDEX to represent a lack of this information

        :rtype: int
        """
        return self.source_file_idx

    def get_annotations_off(self):
        """
        Return the offset from the start of the file to the annotations structure for this class,
        or 0 if there are no annotations on this class.

        :rtype: int
        """
        return self.annotations_off

    def get_class_data_off(self):
        """
        Return the offset from the start of the file to the associated class data for this item,
        or 0 if there is no class data for this class

        :rtype: int
        """
        return self.class_data_off

    def get_static_values_off(self):
        """
        Return the offset from the start of the file to the list of initial values for static fields,
        or 0 if there are none (and all static fields are to be initialized with 0 or null)

        :rtype: int
        """
        return self.static_values_off

    def get_class_data(self):
        """
        Return the associated class_data_item

        :rtype: a :class:`ClassDataItem` object
        """
        return self.class_data_item

    def get_name(self):
        """
        Return the name of this class

        :rtype: MUTF8String
        """
        return self.name

    def get_superclassname(self):
        """
        Return the name of the super class

        :rtype: MUTF8String
        """
        return self.sname

    def get_interfaces(self):
        """
        Return the names of the interfaces

        :rtype: List[MUTF8String]
        """
        return self.interfaces

    def get_access_flags_string(self):
        """
        Return the access flags string of the class

        :rtype: str
        """
        if self.access_flags_string is None:
            self.access_flags_string = get_access_flags_string(
                self.get_access_flags())

            if self.access_flags_string == "":
                self.access_flags_string = "0x%x" % self.get_access_flags()
        return self.access_flags_string

    def show(self):
        bytecode._PrintSubBanner("Class Def Item")
        bytecode._PrintDefault(
            "name=%s, sname=%s, interfaces=%s, access_flags=%s\n" %
            (self.name, self.sname, self.interfaces,
             self.get_access_flags_string()))
        bytecode._PrintDefault(
            "class_idx=%d, superclass_idx=%d, interfaces_off=%x, source_file_idx=%d, annotations_off=%x, class_data_off=%x, static_values_off=%x\n"
            % (self.class_idx, self.superclass_idx, self.interfaces_off,
               self.source_file_idx, self.annotations_off, self.class_data_off,
               self.static_values_off))

        for method in self.get_methods():
            method.show()

    def source(self):
        """
        Return the source code of the entire class

        :rtype: string
        """
        self.CM.decompiler_ob.display_all(self)

    def get_source(self):
        return self.CM.decompiler_ob.get_source_class(self)

    def get_source_ext(self):
        return self.CM.decompiler_ob.get_source_class_ext(self)

    def get_ast(self):
        return self.CM.decompiler_ob.get_ast_class(self)

    def set_name(self, value):
        self.CM.set_hook_class_name(self, value)

    def get_obj(self):
        if self.interfaces_off != 0:
            self.interfaces_off = self.CM.get_obj_by_offset(
                self.interfaces_off).get_off()

        if self.annotations_off != 0:
            self.annotations_off = self.CM.get_obj_by_offset(
                self.annotations_off).get_off()

        if self.class_data_off != 0:
            self.class_data_off = self.CM.get_obj_by_offset(
                self.class_data_off).get_off()

        if self.static_values_off != 0:
            self.static_values_off = self.CM.get_obj_by_offset(
                self.static_values_off).get_off()

        return self.CM.packer["8I"].pack(self.class_idx,
                    self.access_flags,
                    self.superclass_idx,
                    self.interfaces_off,
                    self.source_file_idx,
                    self.annotations_off,
                    self.class_data_off,
                    self.static_values_off)

    def get_raw(self):
        return self.get_obj()

    def get_length(self):
        return len(self.get_obj())


class ClassHDefItem:
    """
    This class can parse a list of class_def_item of a dex file

    :param buff: a string which represents a Buff object of the list of class_def_item
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, size, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.class_def = []

        for i in range(0, size):
            idx = buff.get_idx()

            class_def = ClassDefItem(buff, cm)
            self.class_def.append(class_def)

            buff.set_idx(idx + calcsize("8I"))

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def get_class_idx(self, idx):
        for i in self.class_def:
            if i.get_class_idx() == idx:
                return i
        return None

    def get_method(self, name_class, name_method):
        l = []

        for i in self.class_def:
            if i.get_name() == name_class:
                for j in i.get_methods():
                    if j.get_name() == name_method:
                        l.append(j)

        return l

    def get_names(self):
        return [x.get_name() for x in self.class_def]

    def show(self):
        for i in self.class_def:
            i.show()

    def get_obj(self):
        return [i for i in self.class_def]

    def get_raw(self):
        return b''.join(i.get_raw() for i in self.class_def)

    def get_length(self):
        length = 0
        for i in self.class_def:
            length += i.get_length()
        return length


class EncodedTypeAddrPair:
    """
    This class can parse an encoded_type_addr_pair of a dex file

    :param buff: a string which represents a Buff object of the encoded_type_addr_pair
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, cm, buff):
        self.CM = cm
        self.type_idx = readuleb128(cm, buff)
        self.addr = readuleb128(cm, buff)

    def get_type_idx(self):
        """
        Return the index into the type_ids list for the type of the exception to catch

        :rtype: int
        """
        return self.type_idx

    def get_addr(self):
        """
        Return the bytecode address of the associated exception handler

        :rtype: int
        """
        return self.addr

    def get_obj(self):
        return []

    def show(self):
        bytecode._PrintSubBanner("Encoded Type Addr Pair")
        bytecode._PrintDefault("type_idx=%d addr=%x\n" %
                               (self.type_idx, self.addr))

    def get_raw(self):
        return writeuleb128(self.CM, self.type_idx) + writeuleb128(self.CM, self.addr)

    def get_length(self):
        return len(self.get_raw())


class EncodedCatchHandler:
    """
    This class can parse an encoded_catch_handler of a dex file

    :param buff: a string which represents a Buff object of the encoded_catch_handler
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.size = readsleb128(cm, buff)

        self.handlers = []

        for i in range(0, abs(self.size)):
            self.handlers.append(EncodedTypeAddrPair(cm, buff))

        if self.size <= 0:
            self.catch_all_addr = readuleb128(cm, buff)

    def get_size(self):
        """
        Return the number of catch types in this list

        :rtype: int
        """
        return self.size

    def get_handlers(self):
        """
        Return the stream of abs(size) encoded items, one for each caught type, in the order that the types should be tested.

        :rtype: a list of :class:`EncodedTypeAddrPair` objects
        """
        return self.handlers

    def get_catch_all_addr(self):
        """
        Return the bytecode address of the catch-all handler. This element is only present if size is non-positive.

        :rtype: int
        """
        return self.catch_all_addr

    def get_off(self):
        return self.offset

    def set_off(self, off):
        self.offset = off

    def show(self):
        bytecode._PrintSubBanner("Encoded Catch Handler")
        bytecode._PrintDefault("size=%d\n" % self.size)

        for i in self.handlers:
            i.show()

        if self.size <= 0:
            bytecode._PrintDefault("catch_all_addr=%x\n" % self.catch_all_addr)

    def get_raw(self):
        """
        :rtype: bytearray
        """
        buff = bytearray()
        buff += writesleb128(self.CM, self.size)
        for i in self.handlers:
            buff += i.get_raw()

        if self.size <= 0:
            buff += writeuleb128(self.CM, self.catch_all_addr)

        return buff

    def get_length(self):
        length = len(writesleb128(self.CM, self.size))

        for i in self.handlers:
            length += i.get_length()

        if self.size <= 0:
            length += len(writeuleb128(self.CM, self.catch_all_addr))

        return length


class EncodedCatchHandlerList:
    """
    This class can parse an encoded_catch_handler_list of a dex file

    :param buff: a string which represents a Buff object of the encoded_catch_handler_list
    :type buff: Buff object
    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.size = readuleb128(cm, buff)
        self.list = [EncodedCatchHandler(buff, cm) for _ in range(self.size)]

    def get_size(self):
        """
        Return the size of this list, in entries

        :rtype: int
        """
        return self.size

    def get_list(self):
        """
        Return the actual list of handler lists, represented directly (not as offsets), and concatenated sequentially

        :rtype: a list of :class:`EncodedCatchHandler` objects
        """
        return self.list

    def show(self):
        bytecode._PrintSubBanner("Encoded Catch Handler List")
        bytecode._PrintDefault("size=%d\n" % self.size)

        for i in self.list:
            i.show()

    def get_off(self):
        return self.offset

    def set_off(self, off):
        self.offset = off

    def get_obj(self):
        return writeuleb128(self.CM, self.size)

    def get_raw(self):
        """
        :rtype: bytearray
        """
        buff = bytearray()
        buff += self.get_obj()
        for i in self.list:
            buff += i.get_raw()
        return buff

    def get_length(self):
        length = len(self.get_obj())

        for i in self.list:
            length += i.get_length()
        return length


def get_kind(cm, kind, value):
    """
    Return the value of the 'kind' argument

    :param cm: a ClassManager object
    :type cm: :class:`ClassManager`
    :param kind: the type of the 'kind' argument
    :type kind: int
    :param value: the value of the 'kind' argument
    :type value: int

    :rtype: string
    """
    if kind == Kind.METH:
        method = cm.get_method_ref(value)
        class_name = method.get_class_name()
        name = method.get_name()
        descriptor = method.get_descriptor()

        return "{}->{}{}".format(class_name, name, descriptor)

    elif kind == Kind.STRING:
        return repr(cm.get_string(value))

    # TODO: unused?
    elif kind == Kind.RAW_STRING:
        return cm.get_string(value)

    elif kind == Kind.FIELD:
        class_name, proto, field_name = cm.get_field(value)
        return "{}->{} {}".format(class_name, field_name, proto)

    elif kind == Kind.TYPE:
        return cm.get_type(value)

    elif kind == Kind.VTABLE_OFFSET:
        return "vtable[0x%x]" % value

    elif kind == Kind.FIELD_OFFSET:
        return "field[0x%x]" % value

    elif kind == Kind.INLINE_METHOD:
        buff = "inline[0x%x]" % value

        # FIXME: depends of the android version ...
        if len(INLINE_METHODS) > value:
            elem = INLINE_METHODS[value]
            buff += " {}->{}{}".format(elem[0], elem[1], elem[2])

        return buff

    return None


class Instruction:
    """
    This class represents a Dalvik instruction

    It can both handle normal instructions as well as optimized instructions.

    .. warning::
        There is not much documentation about the optimized opcodes!
        Hence, it relies on reverese engineered specification!

    More information about the instruction format can be found in the official documentation:
    https://source.android.com/devices/tech/dalvik/instruction-formats.html

    .. warning::
        Values stored in the instructions are already interpreted at this stage.

    The Dalvik VM has a eight opcodes to create constant integer values.
    There are four variants for 32bit values and four for 64bit.
    If floating point numbers are required, you have to use the conversion opcodes
    like :code:`int-to-float`, :code:`int-to-double` or the variants using :code:`long`.

    Androguard will always show the values as they are used in the opcode and also extend signs
    and shift values!
    As an example: The opcode :code:`const/high16` can be used to create constant values
    where the lower 16 bits are all zero.
    In this case, androguard will process bytecode :code:`15 00 CD AB` as beeing
    :code:`const/high16 v0, 0xABCD0000`.
    For the sign-extension, nothing is really done here, as it only affects the bit represenation
    in the virtual machine. As androguard parses the values and uses python types internally,
    we are not bound to specific size.
    """
    length = 0
    OP = 0

    def get_kind(self):
        """
        Return the 'kind' argument of the instruction

        This is the type of the argument, i.e. in which kind of table you have
        to look up the argument in the ClassManager

        :rtype: int
        """
        if self.OP >= 0xf2ff:
            return DALVIK_OPCODES_OPTIMIZED[self.OP][1][1]
        return DALVIK_OPCODES_FORMAT[self.OP][1][1]

    def get_name(self):
        """
        Return the mnemonic of the instruction

        :rtype: string
        """
        if self.OP >= 0xf2ff:
            return DALVIK_OPCODES_OPTIMIZED[self.OP][1][0]
        return DALVIK_OPCODES_FORMAT[self.OP][1][0]

    def get_op_value(self):
        """
        Return the numerical value of the opcode

        :rtype: int
        """
        return self.OP

    def get_literals(self):
        """
        Return the associated literals

        :rtype: list of int
        """
        return []

    def show(self, idx):
        """
        Print the instruction

        No Line ending is printed.
        """
        print(self.get_name() + " " + self.get_output(idx), end=' ')

    def show_buff(self, idx):
        """
        Return the display of the instruction

        :rtype: string
        """
        return self.get_output(idx)

    def get_translated_kind(self):
        """
        Return the translated value of the 'kind' argument

        :rtype: string
        """
        return get_kind(self.cm, self.get_kind(), self.get_ref_kind())

    def get_output(self, idx=-1):
        """
        Return an additional output of the instruction

        :rtype: string
        """
        return ""

    def get_operands(self, idx=-1):
        """
        Return all operands

        This will return a list of tuples, containing the Enum :class:`Operand`
        at the first position and the objects afterwards.

        :rtype: List[Tuple(Operand, object, ...)]
        """
        return []

    def get_length(self):
        """
        Return the length of the instruction in bytes

        :rtype: int
        """
        return self.length

    def get_raw(self):
        """
        Return the object in a raw format

        :rtype: string
        """
        raise Exception("not implemented")

    def get_ref_kind(self):
        """
        Return the value of the 'kind' argument

        :rtype: value
        """
        raise Exception("not implemented")

    def get_formatted_operands(self):
        """
        Returns the formatted operands, if any.
        This is a list with the parsed and interpreted operands
        of the opcode.

        Returns None if no operands, otherwise a List

        .. deprecated:: 3.4.0
            Will be removed! This method always returns None
        """
        warnings.warn("deprecated, this class will be removed!", DeprecationWarning)
        return None

    def get_hex(self):
        """
        Returns a HEX String, separated by spaces every byte

        The hex string contains the raw bytes of the instruction,
        including the opcode and all arguments.

        :rtype: str
        """
        s = binascii.hexlify(self.get_raw()).decode('ascii')
        return " ".join(s[i:i + 2] for i in range(0, len(s), 2))

    def __str__(self):
        return "{} {}".format(self.get_name(), self.get_output())

    # FIXME Better name
    def disasm(self):
        """Some small line for disassembly view"""
        s = binascii.hexlify(self.get_raw()).decode('ascii')
        byteview = " ".join(s[i:i + 4] for i in range(0, len(s), 4))
        return '{:24s}  {:24s} {}'.format(byteview, self.get_name(), self.get_output())


class FillArrayData:
    """
    This class can parse a FillArrayData instruction

    :param buff: a Buff object which represents a buffer where the instruction is stored
    """

    # FIXME: why is this not a subclass of Instruction?
    def __init__(self, cm, buff):
        self.OP = 0x0
        self.notes = []
        self.CM = cm

        self.format_general_size = calcsize("2HI")
        self.ident, \
        self.element_width, \
        self.size = cm.packer["2HI"].unpack(buff[0:8])

        buf_len = self.size * self.element_width
        if buf_len % 2:
            buf_len += 1

        self.data = buff[self.format_general_size:self.format_general_size + buf_len]

    def add_note(self, msg):
        """
        Add a note to this instruction

        :param msg: the message
        :type msg: objects (string)
        """
        self.notes.append(msg)

    def get_notes(self):
        """
        Get all notes from this instruction

        :rtype: a list of objects
        """
        return self.notes

    def get_op_value(self):
        """
        Get the value of the opcode

        :rtype: int
        """
        return self.ident

    def get_data(self):
        """
        Return the data of this instruction (the payload)

        :rtype: bytes
        """
        return self.data

    def get_output(self, idx=-1):
        """
        Return an additional output of the instruction

        :rtype: string
        """
        buff = ""

        data = self.get_data()

        buff += repr(data) + " | "
        for i in range(0, len(data)):
            buff += "\\x{:02x}".format(data[i])

        return buff

    def get_operands(self, idx=-1):
        # FIXME: not sure of binascii is the right choise here,
        # but before it was repr(), which lead to weird outputs of bytearrays
        if isinstance(self.get_data(), bytearray):
            return [(Operand.RAW, binascii.hexlify(self.get_data()).decode('ascii'))]
        else:
            return [(Operand.RAW, repr(self.get_data()))]

    def get_formatted_operands(self):
        return None

    def get_name(self):
        """
        Return the name of the instruction

        :rtype: string
        """
        return "fill-array-data-payload"

    def show_buff(self, pos):
        """
        Return the display of the instruction

        :rtype: string
        """
        buff = self.get_name() + " "

        for i in range(0, len(self.data)):
            buff += "\\x%02x" % self.data[i]
        return buff

    def show(self, pos):
        """
        Print the instruction
        """
        print(self.show_buff(pos), end=' ')

    def get_length(self):
        """
        Return the length of the instruction

        :rtype: int
        """
        return ((self.size * self.element_width + 1) // 2 + 4) * 2

    def get_raw(self):
        return self.CM.packer["2HI"].pack(self.ident, self.element_width, self.size) + self.data

    def get_hex(self):
        """
        Returns a HEX String, separated by spaces every byte
        """
        s = binascii.hexlify(self.get_raw()).decode("ascii")
        return " ".join(s[i:i + 2] for i in range(0, len(s), 2))

    def disasm(self):
        # FIXME:
        return self.show_buff(None)


class SparseSwitch:
    """
    This class can parse a SparseSwitch instruction

    :param buff: a Buff object which represents a buffer where the instruction is stored
    """

    # FIXME: why is this not a subclass of Instruction?
    def __init__(self, cm, buff):
        self.OP = 0x0
        self.notes = []
        self.CM = cm

        self.format_general_size = calcsize("2H")
        self.ident, \
        self.size = cm.packer["2H"].unpack(buff[0:4])

        self.keys = []
        self.targets = []

        idx = self.format_general_size
        for i in range(0, self.size):
            self.keys.append(cm.packer["l"].unpack(buff[idx:idx + 4])[0])
            idx += 4

        for i in range(0, self.size):
            self.targets.append(cm.packer["l"].unpack(buff[idx:idx + 4])[0])
            idx += 4

    def add_note(self, msg):
        """
        Add a note to this instruction

        :param msg: the message
        :type msg: objects (string)
        """
        self.notes.append(msg)

    def get_notes(self):
        """
        Get all notes from this instruction

        :rtype: a list of objects
        """
        return self.notes

    def get_op_value(self):
        """
        Get the value of the opcode

        :rtype: int
        """
        return self.ident

    def get_keys(self):
        """
        Return the keys of the instruction

        :rtype: a list of long
        """
        return self.keys

    def get_values(self):
        return self.get_keys()

    def get_targets(self):
        """
        Return the targets (address) of the instruction

        :rtype: a list of long
        """
        return self.targets

    def get_output(self, idx=-1):
        """
        Return an additional output of the instruction

        :rtype: string
        """
        return " ".join("%x" % i for i in self.keys)

    def get_operands(self, idx=-1):
        """
        Return an additional output of the instruction

        :rtype: string
        """
        return []

    def get_formatted_operands(self):
        return None

    def get_name(self):
        """
        Return the name of the instruction

        :rtype: string
        """
        return "sparse-switch-payload"

    def show_buff(self, pos):
        """
        Return the display of the instruction

        :rtype: string
        """
        buff = self.get_name() + " "
        for i in range(0, len(self.keys)):
            buff += "{:x}:{:x} ".format(self.keys[i], self.targets[i])

        return buff

    def show(self, pos):
        """
        Print the instruction
        """
        print(self.show_buff(pos), end=' ')

    def get_length(self):
        return self.format_general_size + (self.size * calcsize('<L')) * 2

    def get_raw(self):
        return self.CM.packer["2H"].pack(self.ident, self.size) + b''.join(self.CM.packer["l"].pack(i) for i in self.keys) + b''.join(self.CM.packer["l"].pack(i) for i in self.targets)

    def get_hex(self):
        """
        Returns a HEX String, separated by spaces every byte
        """
        s = binascii.hexlify(self.get_raw()).decode('ascii')
        return " ".join(s[i:i + 2] for i in range(0, len(s), 2))

    def disasm(self):
        # FIXME:
        return self.show_buff(None)


class PackedSwitch:
    """
    This class can parse a PackedSwitch instruction

    :param buff: a Buff object which represents a buffer where the instruction is stored
    """

    # FIXME: why is this not a subclass of Instruction?
    def __init__(self, cm, buff):
        self.OP = 0x0
        self.notes = []
        self.CM = cm

        self.format_general_size = calcsize("2HI")

        self.ident, \
        self.size, \
        self.first_key = cm.packer["2Hi"].unpack(buff[0:8])

        self.targets = []

        idx = self.format_general_size

        max_size = self.size
        if (max_size * 4) > len(buff):
            max_size = len(buff) - idx - 8

        for i in range(0, max_size):
            self.targets.append(cm.packer["l"].unpack(buff[idx:idx + 4])[0])
            idx += 4

    def add_note(self, msg):
        """
        Add a note to this instruction

        :param msg: the message
        :type msg: objects (string)
        """
        self.notes.append(msg)

    def get_notes(self):
        """
        Get all notes from this instruction

        :rtype: a list of objects
        """
        return self.notes

    def get_op_value(self):
        """
        Get the value of the opcode

        :rtype: int
        """
        return self.ident

    def get_keys(self):
        """
        Return the keys of the instruction

        :rtype: a list of long
        """
        return [(self.first_key + i) for i in range(0, len(self.targets))]

    def get_values(self):
        return self.get_keys()

    def get_targets(self):
        """
        Return the targets (address) of the instruction

        :rtype: a list of long
        """
        return self.targets

    def get_output(self, idx=-1):
        """
      Return an additional output of the instruction

        :rtype: string

        """
        return " ".join("%x" % (self.first_key + i)
                        for i in range(0, len(self.targets)))

    def get_operands(self, idx=-1):
        """
        Return an additional output of the instruction

        :rtype: string
        """
        return []

    def get_formatted_operands(self):
        return None

    def get_name(self):
        """
        Return the name of the instruction

        :rtype: string
        """
        return "packed-switch-payload"

    def show_buff(self, pos):
        """
        Return the display of the instruction

        :rtype: string
        """
        buff = self.get_name() + " "
        buff += "%x:" % self.first_key

        for i in self.targets:
            buff += " %x" % i

        return buff

    def show(self, pos):
        """
        Print the instruction
        """
        print(self.show_buff(pos), end=' ')

    def get_length(self):
        return self.format_general_size + (self.size * calcsize('<L'))

    def get_raw(self):
        return self.CM.packer["2Hi"].pack(self.ident, self.size, self.first_key) + b''.join(self.CM.packer["l"].pack(i) for i in self.targets)

    def get_hex(self):
        """
        Returns a HEX String, separated by spaces every byte
        """
        s = binascii.hexlify(self.get_raw()).decode('ascii')
        return " ".join(s[i:i + 2] for i in range(0, len(s), 2))

    def disasm(self):
        # FIXME:
        return self.show_buff(None)


class Instruction35c(Instruction):
    """
    This class represents all instructions which have the 35c format
    """
    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16a, self.BBBB, i16b = cm.packer["3H"].unpack(buff[:self.length])
        self.OP = i16a & 0xff
        self.G = (i16a >> 8) & 0xf
        self.A = (i16a >> 12) & 0xf

        self.C = i16b & 0xf
        self.D = (i16b >> 4) & 0xf
        self.E = (i16b >> 8) & 0xf
        self.F = (i16b >> 12) & 0xf

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.A == 0:
            return "%s" % kind
        elif self.A == 1:
            return "v%d, %s" % (self.C, kind)
        elif self.A == 2:
            return "v%d, v%d, %s" % (self.C, self.D, kind)
        elif self.A == 3:
            return "v%d, v%d, v%d, %s" % (self.C, self.D, self.E, kind)
        elif self.A == 4:
            return "v%d, v%d, v%d, v%d, %s" % (self.C, self.D, self.E, self.F,
                                               kind)
        elif self.A == 5:
            return "v%d, v%d, v%d, v%d, v%d, %s" % (self.C, self.D, self.E,
                                                    self.F, self.G, kind)

        return ''

    def get_operands(self, idx=-1):
        l = []
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.A == 0:
            l.append((self.get_kind() + Operand.KIND, self.BBBB, kind))
        elif self.A == 1:
            l.extend([(Operand.REGISTER, self.C), (self.get_kind(
            ) + Operand.KIND, self.BBBB, kind)])
        elif self.A == 2:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                self.get_kind() + Operand.KIND, self.BBBB, kind)])
        elif self.A == 3:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (self.get_kind() + Operand.KIND,
                                            self.BBBB, kind)])
        elif self.A == 4:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (Operand.REGISTER, self.F), (
                          self.get_kind() + Operand.KIND, self.BBBB, kind)])
        elif self.A == 5:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (Operand.REGISTER, self.F), (
                          Operand.REGISTER, self.G), (self.get_kind() + Operand.KIND,
                                                      self.BBBB, kind)])

        return l

    def get_ref_kind(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["3H"].pack((self.A << 12) | (self.G << 8) | self.OP, self.BBBB,
                    (self.F << 12) | (self.E << 8) | (self.D << 4) | self.C)


class Instruction10x(Instruction):
    """
    This class represents all instructions which have the 10x format
    """

    length = 2

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, padding = cm.packer["BB"].unpack(buff[:self.length])
        if padding != 0:
            raise InvalidInstruction('High byte of opcode with format 10x must be zero!')

    def get_raw(self):
        return self.cm.packer["H"].pack(self.OP)


class Instruction21h(Instruction):
    """
    This class represents all instructions which have the 21h format
    """
    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.__BBBB = cm.packer["BBh"].unpack(buff[:self.length])

        if self.OP == 0x15:
            # OP 0x15: int16_t -> int32_t
            self.BBBB = self.__BBBB << 16
        elif self.OP == 0x19:
            # OP 0x19: int16_t -> int64_t
            self.BBBB = self.__BBBB << 48
        else:
            # Unknown opcode?
            self.BBBB = self.__BBBB

    def get_output(self, idx=-1):
        return "v{}, {}".format(self.AA, self.BBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.LITERAL, self.BBBB)]

    def get_literals(self):
        return [self.BBBB]

    def get_raw(self):
        return self.cm.packer["Hh"].pack((self.AA << 8) | self.OP, self.__BBBB)


class Instruction11n(Instruction):
    """
    This class represents all instructions which have the 11n format
    """
    length = 2

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, i8 = cm.packer["Bb"].unpack(buff[:self.length])
        self.A = i8 & 0xf
        # Sign extension not required
        self.B = i8 >> 4

    def get_output(self, idx=-1):
        return "v{}, {}".format(self.A, self.B)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.A), (Operand.LITERAL, self.B)]

    def get_literals(self):
        return [self.B]

    def get_raw(self):
        return self.cm.packer["h"].pack((self.B << 12) | (self.A << 8) | self.OP)


class Instruction21c(Instruction):
    """
    This class represents all instructions which have the 21c format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm
        self.OP, self.AA, self.BBBB = cm.packer["BBH"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)
        if self.get_kind() == Kind.STRING:
            kind = '"{}"'.format(kind)
        return "v{}, {}".format(self.AA, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)
        return [(Operand.REGISTER, self.AA),
                (self.get_kind() + Operand.KIND, self.BBBB, kind)]

    def get_ref_kind(self):
        return self.BBBB

    def get_string(self):
        return get_kind(self.cm, self.get_kind(), self.BBBB)

    def get_raw_string(self):
        return get_kind(self.cm, Kind.RAW_STRING, self.BBBB)

    def get_raw(self):
        return self.cm.packer["2H"].pack((self.AA << 8) | self.OP, self.BBBB)


class Instruction21s(Instruction):
    """
    This class represents all instructions which have the 21s format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        # BBBB is a signed int (16bit)
        self.OP, self.AA, self.BBBB = self.cm.packer["BBh"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, {}".format(self.AA, self.BBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.LITERAL, self.BBBB)]

    def get_literals(self):
        return [self.BBBB]

    def get_raw(self):
        return self.cm.packer["BBh"].pack(self.OP, self.AA, self.BBBB)


class Instruction22c(Instruction):
    """
    This class represents all instructions which have the 22c format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16, self.CCCC = cm.packer["2H"].unpack(buff[:self.length])
        self.OP = i16 & 0xff
        self.A = (i16 >> 8) & 0xf
        self.B = (i16 >> 12) & 0xf

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.CCCC)
        return "v{}, v{}, {}".format(self.A, self.B, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.CCCC)
        return [(Operand.REGISTER, self.A), (Operand.REGISTER, self.B),
                (self.get_kind() + Operand.KIND, self.CCCC, kind)]

    def get_ref_kind(self):
        return self.CCCC

    def get_raw(self):
        return self.cm.packer["2H"].pack((self.B << 12) | (self.A << 8) | self.OP, self.CCCC)


class Instruction22cs(Instruction):
    """
    This class represents all instructions which have the 22cs format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16, self.CCCC = cm.packer["2H"].unpack(buff[:self.length])
        self.OP = i16 & 0xff
        self.A = (i16 >> 8) & 0xf
        self.B = (i16 >> 12) & 0xf

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.CCCC)
        return "v{}, v{}, {}".format(self.A, self.B, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.CCCC)
        return [(Operand.REGISTER, self.A), (Operand.REGISTER, self.B),
                (self.get_kind() + Operand.KIND, self.CCCC, kind)]

    def get_ref_kind(self):
        return self.CCCC

    def get_raw(self):
        return self.cm.packer["2H"].pack((self.B << 12) | (self.A << 8) | self.OP, self.CCCC)


class Instruction31t(Instruction):
    """
    This class represents all instructions which have the 31t format
    """
    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBBBBBB = cm.packer["BBi"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, {:+08x}h".format(self.AA, self.BBBBBBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.OFFSET, self.BBBBBBBB)]

    def get_ref_off(self):
        return self.BBBBBBBB

    def get_raw(self):
        return self.cm.packer["Hi"].pack((self.AA << 8) | self.OP, self.BBBBBBBB)


class Instruction31c(Instruction):
    """
    This class represents all instructions which have the 31c format
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm
        self.OP, self.AA, self.BBBBBBBB = cm.packer["BBi"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)
        return "v{}, {}".format(self.AA, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)
        return [(Operand.REGISTER, self.AA),
                (self.get_kind() + Operand.KIND, self.BBBBBBBB, kind)]

    def get_ref_kind(self):
        return self.BBBBBBBB

    def get_string(self):
        """
        Return the string associated to the 'kind' argument

        :rtype: string
        """
        return get_kind(self.cm, self.get_kind(), self.BBBBBBBB)

    def get_raw_string(self):
        return get_kind(self.cm, Kind.RAW_STRING, self.BBBBBBBB)

    def get_raw(self):
        return self.cm.packer["HI"].pack((self.AA << 8) | self.OP, self.BBBBBBBB)


class Instruction12x(Instruction):
    """
    This class represents all instructions which have the 12x format
    """

    length = 2

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16, = cm.packer["h"].unpack(buff[:self.length])
        self.OP = i16 & 0xff
        self.A = (i16 >> 8) & 0xf
        self.B = (i16 >> 12) & 0xf

    def get_output(self, idx=-1):
        return "v{}, v{}".format(self.A, self.B)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.A), (Operand.REGISTER, self.B)]

    def get_raw(self):
        return self.cm.packer["H"].pack((self.B << 12) | (self.A << 8) | self.OP)


class Instruction11x(Instruction):
    """
    This class represents all instructions which have the 11x format
    """

    length = 2

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA = cm.packer["BB"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}".format(self.AA)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA)]

    def get_raw(self):
        return self.cm.packer["H"].pack((self.AA << 8) | self.OP)


class Instruction51l(Instruction):
    """
    This class represents all instructions which have the 51l format
    """

    length = 10

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        # arbitrary double-width (64-bit) constant
        self.OP, self.AA, self.BBBBBBBBBBBBBBBB = cm.packer["BBq"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, {}".format(self.AA, self.BBBBBBBBBBBBBBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.LITERAL, self.BBBBBBBBBBBBBBBB)]

    def get_literals(self):
        return [self.BBBBBBBBBBBBBBBB]

    def get_raw(self):
        return self.cm.packer["BBq"].pack(self.OP, self.AA, self.BBBBBBBBBBBBBBBB)


class Instruction31i(Instruction):
    """
    This class represents all instructions which have the 31i format
    """
    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBBBBBB = cm.packer["BBi"].unpack(buff[:self.length])

        # 0x14 // const vAA, #+BBBBBBBB: arbitrary 32-bit constant
        # 0x17 // const-wide/32 vAA, #+BBBBBBBB: signed int (32 bits)

    def get_output(self, idx=-1):
        #FIXME: on const-wide/32: it is actually a register pair vAA:vAA+1!
        return "v{}, {}".format(self.AA, self.BBBBBBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.LITERAL, self.BBBBBBBB)]

    def get_literals(self):
        return [self.BBBBBBBB]

    def get_raw(self):
        return self.cm.packer["BBi"].pack(self.OP, self.AA, self.BBBBBBBB)


class Instruction22x(Instruction):
    """
    This class represents all instructions which have the 22x format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB = cm.packer["BBH"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, v{}".format(self.AA, self.BBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.REGISTER, self.BBBB)]

    def get_raw(self):
        return self.cm.packer["2H"].pack((self.AA << 8) | self.OP, self.BBBB)


class Instruction23x(Instruction):
    """
    This class represents all instructions which have the 23x format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BB, self.CC = cm.packer["BBBB"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, v{}, v{}".format(self.AA, self.BB, self.CC)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA),
                (Operand.REGISTER, self.BB),
                (Operand.REGISTER, self.CC)]

    def get_raw(self):
        return self.cm.packer["2H"].pack((self.AA << 8) | self.OP, (self.CC << 8) | self.BB)


class Instruction20t(Instruction):
    """
    This class represents all instructions which have the 20t format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, padding, self.AAAA = cm.packer["BBh"].unpack(buff[:self.length])
        if padding != 0:
            raise InvalidInstruction('High byte of opcode with format 20t must be zero!')

    def get_output(self, idx=-1):
        # Offset is in 16bit units
        return "{:+04x}h".format(self.AAAA)

    def get_operands(self, idx=-1):
        return [(Operand.OFFSET, self.AAAA)]

    def get_ref_off(self):
        return self.AAAA

    def get_raw(self):
        return self.cm.packer["Hh"].pack(self.OP, self.AAAA)


class Instruction21t(Instruction):
    """
    This class represents all instructions which have the 21t format
    """
    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB = cm.packer["BBh"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, {:+04x}h".format(self.AA, self.BBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.OFFSET, self.BBBB)]

    def get_ref_off(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["Hh"].pack((self.AA << 8) | self.OP, self.BBBB)


class Instruction10t(Instruction):
    """
    This class represents all instructions which have the 10t format
    """

    length = 2

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA = cm.packer["Bb"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        # Offset is given in 16bit units
        return "{:+02x}h".format(self.AA)

    def get_operands(self, idx=-1):
        return [(Operand.OFFSET, self.AA)]

    def get_ref_off(self):
        return self.AA

    def get_raw(self):
        return self.cm.packer["Bb"].pack(self.OP, self.AA)


class Instruction22t(Instruction):
    """
    This class represents all instructions which have the 22t format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16, self.CCCC = cm.packer["Hh"].unpack(buff[:self.length])
        self.OP = i16 & 0xff
        self.A = (i16 >> 8) & 0xf
        self.B = (i16 >> 12) & 0xf

    def get_output(self, idx=-1):
        return "v{}, v{}, {:+04x}h".format(self.A, self.B, self.CCCC)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.A), (Operand.REGISTER, self.B),
                (Operand.OFFSET, self.CCCC)]

    def get_ref_off(self):
        return self.CCCC

    def get_raw(self):
        return self.cm.packer["Hh"].pack((self.B << 12) | (self.A << 8) | self.OP, self.CCCC)


class Instruction22s(Instruction):
    """
    This class represents all instructions which have the 22s format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16, self.CCCC = cm.packer["Hh"].unpack(buff[:self.length])
        self.OP = i16 & 0xff
        self.A = (i16 >> 8) & 0xf
        self.B = (i16 >> 12) & 0xf

    def get_output(self, idx=-1):
        return "v{}, v{}, {}".format(self.A, self.B, self.CCCC)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.A), (Operand.REGISTER, self.B),
                (Operand.LITERAL, self.CCCC)]

    def get_literals(self):
        return [self.CCCC]

    def get_raw(self):
        return self.cm.packer["Hh"].pack((self.B << 12) | (self.A << 8) | self.OP, self.CCCC)


class Instruction22b(Instruction):
    """
    This class represents all instructions which have the 22b format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BB, self.CC = cm.packer["BBBb"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "v{}, v{}, {}".format(self.AA, self.BB, self.CC)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AA), (Operand.REGISTER, self.BB),
                (Operand.LITERAL, self.CC)]

    def get_literals(self):
        return [self.CC]

    def get_raw(self):
        return self.cm.packer["Hh"].pack((self.AA << 8) | self.OP, (self.CC << 8) | self.BB)


class Instruction30t(Instruction):
    """
    This class represents all instructions which have the 30t format
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, padding, self.AAAAAAAA = cm.packer["BBi"].unpack(buff[:self.length])
        if padding != 0:
            raise InvalidInstruction('High byte of opcode with format 30t must be zero!')

    def get_output(self, idx=-1):
        return "{:+08x}h".format(self.AAAAAAAA)

    def get_operands(self, idx=-1):
        return [(Operand.OFFSET, self.AAAAAAAA)]

    def get_ref_off(self):
        return self.AAAAAAAA

    def get_raw(self):
        return self.cm.packer["Hi"].pack(self.OP, self.AAAAAAAA)


class Instruction3rc(Instruction):
    """
    This class represents all instructions which have the 3rc format
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB, self.CCCC = cm.packer["BBHH"].unpack(buff[:self.length])

        self.NNNN = self.CCCC + self.AA - 1

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.CCCC == self.NNNN:
            return "v{}, {}".format(self.CCCC, kind)
        else:
            return "v{} ... v{}, {}".format(self.CCCC, self.NNNN, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        return [(Operand.REGISTER, i) for i in range(self.CCCC, self.NNNN + 1)] + \
               [(self.get_kind() + Operand.KIND, self.BBBB, kind)]

    def get_ref_kind(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["3H"].pack((self.AA << 8) | self.OP, self.BBBB, self.CCCC)


class Instruction32x(Instruction):
    """
    This class represents all instructions which have the 32x format
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, padding, self.AAAA, self.BBBB = cm.packer["BBHH"].unpack(buff[:self.length])
        if padding != 0:
            raise InvalidInstruction('High byte of opcode with format 32x must be zero!')

    def get_output(self, idx=-1):
        return "v{}, v{}".format(self.AAAA, self.BBBB)

    def get_operands(self, idx=-1):
        return [(Operand.REGISTER, self.AAAA), (Operand.REGISTER, self.BBBB)]

    def get_raw(self):
        return self.cm.packer["3H"].pack(self.OP, self.AAAA, self.BBBB)


class Instruction20bc(Instruction):
    """
    This class represents all instructions which have the 20bc format
    """

    length = 4

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB = cm.packer["BBH"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        return "{}, {}".format(self.AA, self.BBBB)

    def get_operands(self, idx=-1):
        return [(Operand.LITERAL, self.AA), (Operand.LITERAL, self.BBBB)]

    def get_raw(self):
        return self.cm.packer["2H"].pack((self.AA << 8) | self.OP, self.BBBB)


class Instruction35mi(Instruction):
    """
    This class represents all instructions which have the 35mi format
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16a, \
        self.BBBB, \
        i16b = cm.packer["3H"].unpack(buff[:self.length])
        self.OP = i16a & 0xff
        self.G = (i16a >> 8) & 0xf
        self.A = (i16a >> 12) & 0xf
        self.C = i16b & 0xf
        self.D = (i16b >> 4) & 0xf
        self.E = (i16b >> 8) & 0xf
        self.F = (i16b >> 12) & 0xf

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.A == 1:
            return "v%d, %s" % (self.C, kind)
        elif self.A == 2:
            return "v%d, v%d, %s" % (self.C, self.D, kind)
        elif self.A == 3:
            return "v%d, v%d, v%d, %s" % (self.C, self.D, self.E, kind)
        elif self.A == 4:
            return "v%d, v%d, v%d, v%d, %s" % (self.C, self.D, self.E, self.F,
                                                kind)
        elif self.A == 5:
            return "v%d, v%d, v%d, v%d, v%d, %s" % (self.C, self.D, self.E,
                                                     self.F, self.G, kind)

    def get_operands(self, idx=-1):
        l = []
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.A == 1:
            l.extend([(Operand.REGISTER, self.C), (self.get_kind(
            ) + Operand.KIND, self.BBBB, kind)])
        elif self.A == 2:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                self.get_kind() + Operand.KIND, self.BBBB, kind)])
        elif self.A == 3:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (self.get_kind() + Operand.KIND,
                                            self.BBBB, kind)])
        elif self.A == 4:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (Operand.REGISTER, self.F), (
                          self.get_kind() + Operand.KIND, self.BBBB, kind)])
        elif self.A == 5:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (Operand.REGISTER, self.F), (
                          Operand.REGISTER, self.G), (self.get_kind() + Operand.KIND,
                                                      self.BBBB, kind)])

        return l

    def get_ref_kind(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["3H"].pack((self.A << 12) | (self.G << 8) | self.OP, self.BBBB,
                    (self.F << 12) | (self.E << 8) | (self.D << 4) | self.C)


class Instruction35ms(Instruction):
    """
    This class represents all instructions which have the 35ms format
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        i16a, \
        self.BBBB, \
        i16b = cm.packer["3H"].unpack(buff[:self.length])
        self.OP = i16a & 0xff
        self.G = (i16a >> 8) & 0xf
        self.A = (i16a >> 12) & 0xf
        self.C = i16b & 0xf
        self.D = (i16b >> 4) & 0xf
        self.E = (i16b >> 8) & 0xf
        self.F = (i16b >> 12) & 0xf

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.A == 1:
            return "v%d, %s" % (self.C, kind)
        elif self.A == 2:
            return "v%d, v%d, %s" % (self.C, self.D, kind)
        elif self.A == 3:
            return "v%d, v%d, v%d, %s" % (self.C, self.D, self.E, kind)
        elif self.A == 4:
            return "v%d, v%d, v%d, v%d, %s" % (self.C, self.D, self.E, self.F,
                                               kind)
        elif self.A == 5:
            return "v%d, v%d, v%d, v%d, v%d, %s" % (self.C, self.D, self.E,
                                                    self.F, self.G, kind)

    def get_operands(self, idx=-1):
        l = []
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.A == 1:
            l.extend([(Operand.REGISTER, self.C), (self.get_kind(
            ) + Operand.KIND, self.BBBB, kind)])
        elif self.A == 2:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                self.get_kind() + Operand.KIND, self.BBBB, kind)])
        elif self.A == 3:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (self.get_kind() + Operand.KIND,
                                            self.BBBB, kind)])
        elif self.A == 4:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (Operand.REGISTER, self.F), (
                          self.get_kind() + Operand.KIND, self.BBBB, kind)])
        elif self.A == 5:
            l.extend([(Operand.REGISTER, self.C), (Operand.REGISTER, self.D), (
                Operand.REGISTER, self.E), (Operand.REGISTER, self.F), (
                          Operand.REGISTER, self.G), (self.get_kind() + Operand.KIND,
                                                      self.BBBB, kind)])

        return l

    def get_ref_kind(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["3H"].pack((self.A << 12) | (self.G << 8) | self.OP, self.BBBB,
                                         (self.F << 12) | (self.E << 8) | (self.D << 4) | self.C)


class Instruction3rmi(Instruction):
    """
    This class represents all instructions which have the 3rmi format

    Note, this instruction is similar to 3rc but holds an inline
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB, self.CCCC = cm.packer["BBHH"].unpack(buff[:self.length])

        self.NNNN = self.CCCC + self.AA - 1

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.CCCC == self.NNNN:
            return "v{}, {}".format(self.CCCC, kind)
        else:
            return "v{} ... v{}, {}".format(self.CCCC, self.NNNN, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.CCCC == self.NNNN:
            return [(Operand.REGISTER, self.CCCC),
                    (self.get_kind() + Operand.KIND, self.BBBB, kind)]
        else:
            l = []
            for i in range(self.CCCC, self.NNNN):
                l.append((Operand.REGISTER, i))

            l.append((self.get_kind() + Operand.KIND, self.BBBB, kind))
            return l

    def get_ref_kind(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["3H"].pack((self.AA << 8) | self.OP, self.BBBB, self.CCCC)


class Instruction3rms(Instruction):
    """
    This class represents all instructions which have the 3rms format

    Note, this instruction is similar to 3rc but holds a vtaboff
    """

    length = 6

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB, self.CCCC = cm.packer["BBHH"].unpack(buff[:self.length])

        self.NNNN = self.CCCC + self.AA - 1

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.CCCC == self.NNNN:
            return "v{}, {}".format(self.CCCC, kind)
        else:
            return "v{} ... v{}, {}".format(self.CCCC, self.NNNN, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBB)

        if self.CCCC == self.NNNN:
            return [(Operand.REGISTER, self.CCCC),
                    (self.get_kind() + Operand.KIND, self.BBBB, kind)]
        else:
            l = []
            for i in range(self.CCCC, self.NNNN):
                l.append((Operand.REGISTER, i))

            l.append((self.get_kind() + Operand.KIND, self.BBBB, kind))
            return l

    def get_ref_kind(self):
        return self.BBBB

    def get_raw(self):
        return self.cm.packer["3H"].pack((self.AA << 8) | self.OP, self.BBBB, self.CCCC)


class Instruction41c(Instruction):
    """
    This class represents all instructions which have the 41c format

    This instruction is only used in ODEX
    """

    length = 8

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, \
        self.BBBBBBBB, \
        self.AAAA = cm.packer["HIH"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)
        return "v{}, {}".format(self.AAAA, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)
        return [(Operand.REGISTER, self.AAAA),
                (self.get_kind() + Operand.KIND, self.BBBBBBBB, kind)]

    def get_ref_kind(self):
        return self.BBBBBBBB

    def get_raw(self):
        return self.cm.packer["HIH"].pack(self.OP, self.BBBBBBBB, self.AAAA)


class Instruction40sc(Instruction):
    """
    This class represents all instructions which have the 40sc format

    This instruction is only used in ODEX
    """

    length = 8

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, \
        self.BBBBBBBB, \
        self.AAAA = cm.packer["HIH"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)
        return "{}, {}".format(self.AAAA, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)
        return [(Operand.LITERAL, self.AAAA),
                (self.get_kind() + Operand.KIND, self.BBBBBBBB, kind)]

    def get_ref_kind(self):
        return self.BBBBBBBB

    def get_raw(self):
        return self.cm.packer["HIH"].pack(self.OP, self.BBBBBBBB, self.AAAA)


class Instruction52c(Instruction):
    """
    This class represents all instructions which have the 52c format

    This instruction is only used in ODEX
    """

    length = 10

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        # FIXME: Not in the documentation!
        # Using 16bit for opcode, but its ODEX, so...
        self.OP, \
        self.CCCCCCCC, \
        self.AAAA, \
        self.BBBB = cm.packer["HI2H"].unpack(buff[:self.length])

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.CCCCCCCC)
        return "v{}, v{}, {}".format(self.AAAA, self.BBBB, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.CCCCCCCC)
        return [(Operand.LITERAL, self.AAAA), (Operand.LITERAL, self.BBBB),
                (self.get_kind() + Operand.KIND, self.CCCCCCCC, kind)]

    def get_ref_kind(self):
        return self.CCCCCCCC

    def get_raw(self):
        return self.cm.packer["HI2H"].pack(self.OP, self.CCCCCCCC, self.AAAA, self.BBBB)


class Instruction5rc(Instruction):
    """
    This class represents all instructions which have the 5rc format

    This instruction is only used in ODEX
    """

    length = 10

    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, \
        self.BBBBBBBB, \
        self.AAAA, \
        self.CCCC = cm.packer["HI2H"].unpack(buff[:self.length])

        self.NNNN = self.CCCC + self.AAAA - 1

    def get_output(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)

        if self.CCCC == self.NNNN:
            return "v{}, {}".format(self.CCCC, kind)
        else:
            return "v{} ... v{}, {}".format(self.CCCC, self.NNNN, kind)

    def get_operands(self, idx=-1):
        kind = get_kind(self.cm, self.get_kind(), self.BBBBBBBB)

        if self.CCCC == self.NNNN:
            return [(Operand.REGISTER, self.CCCC),
                    (self.get_kind() + Operand.KIND, self.BBBBBBBB, kind)]
        else:
            l = []
            for i in range(self.CCCC, self.NNNN):
                l.append((Operand.REGISTER, i))

            l.append((self.get_kind() + Operand.KIND, self.BBBBBBBB, kind))
            return l

    def get_ref_kind(self):
        return self.BBBBBBBB

    def get_raw(self):
        return self.cm.packer["HI2H"].pack(self.OP, self.BBBBBBBB, self.AAAA, self.CCCC)


class Instruction45cc(Instruction):
    length = 8

    # FIXME!!!
    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        # Note: the documentation says A|G|op|BBBB ... but we need to parse op|A|G because of LE
        self.OP, reg1, self.BBBB, reg2, self.HHHH = self.cm.packer["BBHHH"].unpack(buff[:self.get_length()])
        # TODO need to check if registers are correct
        self.A = (reg1 & 0xF0) >> 4
        if self.A > 5:
            raise InvalidInstruction("A is greater than 5 (it is {}) which should never happen!".format(self.A))
        self.G = (reg1 & 0x0F)

        self.D = (reg2 & 0xF0) >> 4
        self.C = (reg2 & 0x0F)

        self.F = (reg2 & 0xF000) >> 12
        self.E = (reg2 & 0x0F00) >> 8

    def get_raw(self):
        return self.cm.packer["BBHHH"].pack(
                    self.OP,
                    self.A << 4 | self.G,
                    self.BBBB,
                    self.F << 12 | self.E << 8 | self.D << 4 | self.C,
                    self.HHHH)

    def get_output(self, idx=-1):
        # FIXME get_kind of BBBB (method) and HHHH (proto)
        if self.A == 1:
            return 'v{}, {}, {}'.format(self.C, self.BBBB, self.HHHH)
        if self.A == 2:
            return 'v{}, v{}, {}, {}'.format(self.C, self.D, self.BBBB, self.HHHH)
        if self.A == 3:
            return 'v{}, v{}, v{}, {}, {}'.format(self.C, self.D, self.E, self.BBBB, self.HHHH)
        if self.A == 4:
            return 'v{}, v{}, v{}, v{}, {}, {}'.format(self.C, self.D, self.E, self.F, self.BBBB, self.HHHH)
        if self.A == 5:
            return 'v{}, v{}, v{}, v{}, v{}, {}, {}'.format(self.C, self.D, self.E, self.F, self.G, self.BBBB, self.HHHH)

    def get_operands(self):
        # FIXME
        # THis one gets especially nasty, as all other opcodes assume that there
        # is only a single kind type! But this opcode has two...
        pass


class Instruction4rcc(Instruction):
    length = 8

    # FIXME!!!
    def __init__(self, cm, buff):
        super().__init__()
        self.cm = cm

        self.OP, self.AA, self.BBBB, self.CCCC, self.HHHH = self.cm.packer['BBHHH'].unpack(buff[:self.get_length()])
        self.NNNN = self.AA + self.CCCC - 1

    def get_raw(self):
        return self.cm.packer['BBHHH'].pack(self.OP, self.AA, self.BBBB, self.CCCC, self.HHHH)

    def get_output(self, idx=-1):
        # FIXME get_kind of BBBB (meth) and HHHH (proto)
        return 'v{} .. v{} {} {}'.format(self.CCCC, self.NNNN, self.BBBB, self.HHHH)

    def get_operands(self):
        # FIXME
        pass


class Instruction00x(Instruction):
    """A class for unused instructions, has zero length and raises an error on initialization"""
    length = 0

    def __init__(self, cm, buff):
        raise InvalidInstruction("Instruction with opcode '0x{:02x}' is unused! This looks like invalid bytecode.".format(buff[0]))


DALVIK_OPCODES_FORMAT = {
    # From the Dalvik documentation:
    #
    # > Most format IDs consist of three characters, two digits followed by a letter.
    # > The first digit indicates the number of 16-bit code units in the format.
    # > The second digit indicates the maximum number of registers that the
    # > format contains (maximum, since some formats can accommodate a variable number of registers),
    # > with the special designation "r" indicating that a range of registers is encoded.
    # > The final letter semi-mnemonically indicates the type of any extra data encoded by the format.
    # > For example, format "21t" is of length two, contains one register reference,
    # > and additionally contains a branch target.
    #
    # This dict contains the Instruction type as a python class, the instruction
    # name and if the instruction contains typed arguments also the Kind
    # descriptor.

    0x00: [Instruction10x, ["nop"]],
    0x01: [Instruction12x, ["move"]],
    0x02: [Instruction22x, ["move/from16"]],
    0x03: [Instruction32x, ["move/16"]],
    0x04: [Instruction12x, ["move-wide"]],
    0x05: [Instruction22x, ["move-wide/from16"]],
    0x06: [Instruction32x, ["move-wide/16"]],
    0x07: [Instruction12x, ["move-object"]],
    0x08: [Instruction22x, ["move-object/from16"]],
    0x09: [Instruction32x, ["move-object/16"]],
    0x0a: [Instruction11x, ["move-result"]],
    0x0b: [Instruction11x, ["move-result-wide"]],
    0x0c: [Instruction11x, ["move-result-object"]],
    0x0d: [Instruction11x, ["move-exception"]],
    0x0e: [Instruction10x, ["return-void"]],
    0x0f: [Instruction11x, ["return"]],
    0x10: [Instruction11x, ["return-wide"]],
    0x11: [Instruction11x, ["return-object"]],
    0x12: [Instruction11n, ["const/4"]],
    0x13: [Instruction21s, ["const/16"]],
    0x14: [Instruction31i, ["const"]],
    0x15: [Instruction21h, ["const/high16"]],
    0x16: [Instruction21s, ["const-wide/16"]],
    0x17: [Instruction31i, ["const-wide/32"]],
    0x18: [Instruction51l, ["const-wide"]],
    0x19: [Instruction21h, ["const-wide/high16"]],
    0x1a: [Instruction21c, ["const-string", Kind.STRING]],
    0x1b: [Instruction31c, ["const-string/jumbo", Kind.STRING]],
    0x1c: [Instruction21c, ["const-class", Kind.TYPE]],
    0x1d: [Instruction11x, ["monitor-enter"]],
    0x1e: [Instruction11x, ["monitor-exit"]],
    0x1f: [Instruction21c, ["check-cast", Kind.TYPE]],
    0x20: [Instruction22c, ["instance-of", Kind.TYPE]],
    0x21: [Instruction12x, ["array-length"]],
    0x22: [Instruction21c, ["new-instance", Kind.TYPE]],
    0x23: [Instruction22c, ["new-array", Kind.TYPE]],
    0x24: [Instruction35c, ["filled-new-array", Kind.TYPE]],
    0x25: [Instruction3rc, ["filled-new-array/range", Kind.TYPE]],
    0x26: [Instruction31t, ["fill-array-data"]],
    0x27: [Instruction11x, ["throw"]],
    0x28: [Instruction10t, ["goto"]],
    0x29: [Instruction20t, ["goto/16"]],
    0x2a: [Instruction30t, ["goto/32"]],
    0x2b: [Instruction31t, ["packed-switch"]],
    0x2c: [Instruction31t, ["sparse-switch"]],
    0x2d: [Instruction23x, ["cmpl-float"]],
    0x2e: [Instruction23x, ["cmpg-float"]],
    0x2f: [Instruction23x, ["cmpl-double"]],
    0x30: [Instruction23x, ["cmpg-double"]],
    0x31: [Instruction23x, ["cmp-long"]],
    0x32: [Instruction22t, ["if-eq"]],
    0x33: [Instruction22t, ["if-ne"]],
    0x34: [Instruction22t, ["if-lt"]],
    0x35: [Instruction22t, ["if-ge"]],
    0x36: [Instruction22t, ["if-gt"]],
    0x37: [Instruction22t, ["if-le"]],
    0x38: [Instruction21t, ["if-eqz"]],
    0x39: [Instruction21t, ["if-nez"]],
    0x3a: [Instruction21t, ["if-ltz"]],
    0x3b: [Instruction21t, ["if-gez"]],
    0x3c: [Instruction21t, ["if-gtz"]],
    0x3d: [Instruction21t, ["if-lez"]],
    # unused
    0x3e: [Instruction00x, ["unused"]],
    0x3f: [Instruction00x, ["unused"]],
    0x40: [Instruction00x, ["unused"]],
    0x41: [Instruction00x, ["unused"]],
    0x42: [Instruction00x, ["unused"]],
    0x43: [Instruction00x, ["unused"]],

    0x44: [Instruction23x, ["aget"]],
    0x45: [Instruction23x, ["aget-wide"]],
    0x46: [Instruction23x, ["aget-object"]],
    0x47: [Instruction23x, ["aget-boolean"]],
    0x48: [Instruction23x, ["aget-byte"]],
    0x49: [Instruction23x, ["aget-char"]],
    0x4a: [Instruction23x, ["aget-short"]],
    0x4b: [Instruction23x, ["aput"]],
    0x4c: [Instruction23x, ["aput-wide"]],
    0x4d: [Instruction23x, ["aput-object"]],
    0x4e: [Instruction23x, ["aput-boolean"]],
    0x4f: [Instruction23x, ["aput-byte"]],
    0x50: [Instruction23x, ["aput-char"]],
    0x51: [Instruction23x, ["aput-short"]],
    0x52: [Instruction22c, ["iget", Kind.FIELD]],
    0x53: [Instruction22c, ["iget-wide", Kind.FIELD]],
    0x54: [Instruction22c, ["iget-object", Kind.FIELD]],
    0x55: [Instruction22c, ["iget-boolean", Kind.FIELD]],
    0x56: [Instruction22c, ["iget-byte", Kind.FIELD]],
    0x57: [Instruction22c, ["iget-char", Kind.FIELD]],
    0x58: [Instruction22c, ["iget-short", Kind.FIELD]],
    0x59: [Instruction22c, ["iput", Kind.FIELD]],
    0x5a: [Instruction22c, ["iput-wide", Kind.FIELD]],
    0x5b: [Instruction22c, ["iput-object", Kind.FIELD]],
    0x5c: [Instruction22c, ["iput-boolean", Kind.FIELD]],
    0x5d: [Instruction22c, ["iput-byte", Kind.FIELD]],
    0x5e: [Instruction22c, ["iput-char", Kind.FIELD]],
    0x5f: [Instruction22c, ["iput-short", Kind.FIELD]],
    0x60: [Instruction21c, ["sget", Kind.FIELD]],
    0x61: [Instruction21c, ["sget-wide", Kind.FIELD]],
    0x62: [Instruction21c, ["sget-object", Kind.FIELD]],
    0x63: [Instruction21c, ["sget-boolean", Kind.FIELD]],
    0x64: [Instruction21c, ["sget-byte", Kind.FIELD]],
    0x65: [Instruction21c, ["sget-char", Kind.FIELD]],
    0x66: [Instruction21c, ["sget-short", Kind.FIELD]],
    0x67: [Instruction21c, ["sput", Kind.FIELD]],
    0x68: [Instruction21c, ["sput-wide", Kind.FIELD]],
    0x69: [Instruction21c, ["sput-object", Kind.FIELD]],
    0x6a: [Instruction21c, ["sput-boolean", Kind.FIELD]],
    0x6b: [Instruction21c, ["sput-byte", Kind.FIELD]],
    0x6c: [Instruction21c, ["sput-char", Kind.FIELD]],
    0x6d: [Instruction21c, ["sput-short", Kind.FIELD]],
    0x6e: [Instruction35c, ["invoke-virtual", Kind.METH]],
    0x6f: [Instruction35c, ["invoke-super", Kind.METH]],
    0x70: [Instruction35c, ["invoke-direct", Kind.METH]],
    0x71: [Instruction35c, ["invoke-static", Kind.METH]],
    0x72: [Instruction35c, ["invoke-interface", Kind.METH]],
    # unused
    0x73: [Instruction00x, ["unused"]],

    0x74: [Instruction3rc, ["invoke-virtual/range", Kind.METH]],
    0x75: [Instruction3rc, ["invoke-super/range", Kind.METH]],
    0x76: [Instruction3rc, ["invoke-direct/range", Kind.METH]],
    0x77: [Instruction3rc, ["invoke-static/range", Kind.METH]],
    0x78: [Instruction3rc, ["invoke-interface/range", Kind.METH]],
    # unused
    0x79: [Instruction00x, ["unused"]],
    0x7a: [Instruction00x, ["unused"]],

    0x7b: [Instruction12x, ["neg-int"]],
    0x7c: [Instruction12x, ["not-int"]],
    0x7d: [Instruction12x, ["neg-long"]],
    0x7e: [Instruction12x, ["not-long"]],
    0x7f: [Instruction12x, ["neg-float"]],
    0x80: [Instruction12x, ["neg-double"]],
    0x81: [Instruction12x, ["int-to-long"]],
    0x82: [Instruction12x, ["int-to-float"]],
    0x83: [Instruction12x, ["int-to-double"]],
    0x84: [Instruction12x, ["long-to-int"]],
    0x85: [Instruction12x, ["long-to-float"]],
    0x86: [Instruction12x, ["long-to-double"]],
    0x87: [Instruction12x, ["float-to-int"]],
    0x88: [Instruction12x, ["float-to-long"]],
    0x89: [Instruction12x, ["float-to-double"]],
    0x8a: [Instruction12x, ["double-to-int"]],
    0x8b: [Instruction12x, ["double-to-long"]],
    0x8c: [Instruction12x, ["double-to-float"]],
    0x8d: [Instruction12x, ["int-to-byte"]],
    0x8e: [Instruction12x, ["int-to-char"]],
    0x8f: [Instruction12x, ["int-to-short"]],
    0x90: [Instruction23x, ["add-int"]],
    0x91: [Instruction23x, ["sub-int"]],
    0x92: [Instruction23x, ["mul-int"]],
    0x93: [Instruction23x, ["div-int"]],
    0x94: [Instruction23x, ["rem-int"]],
    0x95: [Instruction23x, ["and-int"]],
    0x96: [Instruction23x, ["or-int"]],
    0x97: [Instruction23x, ["xor-int"]],
    0x98: [Instruction23x, ["shl-int"]],
    0x99: [Instruction23x, ["shr-int"]],
    0x9a: [Instruction23x, ["ushr-int"]],
    0x9b: [Instruction23x, ["add-long"]],
    0x9c: [Instruction23x, ["sub-long"]],
    0x9d: [Instruction23x, ["mul-long"]],
    0x9e: [Instruction23x, ["div-long"]],
    0x9f: [Instruction23x, ["rem-long"]],
    0xa0: [Instruction23x, ["and-long"]],
    0xa1: [Instruction23x, ["or-long"]],
    0xa2: [Instruction23x, ["xor-long"]],
    0xa3: [Instruction23x, ["shl-long"]],
    0xa4: [Instruction23x, ["shr-long"]],
    0xa5: [Instruction23x, ["ushr-long"]],
    0xa6: [Instruction23x, ["add-float"]],
    0xa7: [Instruction23x, ["sub-float"]],
    0xa8: [Instruction23x, ["mul-float"]],
    0xa9: [Instruction23x, ["div-float"]],
    0xaa: [Instruction23x, ["rem-float"]],
    0xab: [Instruction23x, ["add-double"]],
    0xac: [Instruction23x, ["sub-double"]],
    0xad: [Instruction23x, ["mul-double"]],
    0xae: [Instruction23x, ["div-double"]],
    0xaf: [Instruction23x, ["rem-double"]],
    0xb0: [Instruction12x, ["add-int/2addr"]],
    0xb1: [Instruction12x, ["sub-int/2addr"]],
    0xb2: [Instruction12x, ["mul-int/2addr"]],
    0xb3: [Instruction12x, ["div-int/2addr"]],
    0xb4: [Instruction12x, ["rem-int/2addr"]],
    0xb5: [Instruction12x, ["and-int/2addr"]],
    0xb6: [Instruction12x, ["or-int/2addr"]],
    0xb7: [Instruction12x, ["xor-int/2addr"]],
    0xb8: [Instruction12x, ["shl-int/2addr"]],
    0xb9: [Instruction12x, ["shr-int/2addr"]],
    0xba: [Instruction12x, ["ushr-int/2addr"]],
    0xbb: [Instruction12x, ["add-long/2addr"]],
    0xbc: [Instruction12x, ["sub-long/2addr"]],
    0xbd: [Instruction12x, ["mul-long/2addr"]],
    0xbe: [Instruction12x, ["div-long/2addr"]],
    0xbf: [Instruction12x, ["rem-long/2addr"]],
    0xc0: [Instruction12x, ["and-long/2addr"]],
    0xc1: [Instruction12x, ["or-long/2addr"]],
    0xc2: [Instruction12x, ["xor-long/2addr"]],
    0xc3: [Instruction12x, ["shl-long/2addr"]],
    0xc4: [Instruction12x, ["shr-long/2addr"]],
    0xc5: [Instruction12x, ["ushr-long/2addr"]],
    0xc6: [Instruction12x, ["add-float/2addr"]],
    0xc7: [Instruction12x, ["sub-float/2addr"]],
    0xc8: [Instruction12x, ["mul-float/2addr"]],
    0xc9: [Instruction12x, ["div-float/2addr"]],
    0xca: [Instruction12x, ["rem-float/2addr"]],
    0xcb: [Instruction12x, ["add-double/2addr"]],
    0xcc: [Instruction12x, ["sub-double/2addr"]],
    0xcd: [Instruction12x, ["mul-double/2addr"]],
    0xce: [Instruction12x, ["div-double/2addr"]],
    0xcf: [Instruction12x, ["rem-double/2addr"]],
    0xd0: [Instruction22s, ["add-int/lit16"]],
    0xd1: [Instruction22s, ["rsub-int"]],
    0xd2: [Instruction22s, ["mul-int/lit16"]],
    0xd3: [Instruction22s, ["div-int/lit16"]],
    0xd4: [Instruction22s, ["rem-int/lit16"]],
    0xd5: [Instruction22s, ["and-int/lit16"]],
    0xd6: [Instruction22s, ["or-int/lit16"]],
    0xd7: [Instruction22s, ["xor-int/lit16"]],
    0xd8: [Instruction22b, ["add-int/lit8"]],
    0xd9: [Instruction22b, ["rsub-int/lit8"]],
    0xda: [Instruction22b, ["mul-int/lit8"]],
    0xdb: [Instruction22b, ["div-int/lit8"]],
    0xdc: [Instruction22b, ["rem-int/lit8"]],
    0xdd: [Instruction22b, ["and-int/lit8"]],
    0xde: [Instruction22b, ["or-int/lit8"]],
    0xdf: [Instruction22b, ["xor-int/lit8"]],
    0xe0: [Instruction22b, ["shl-int/lit8"]],
    0xe1: [Instruction22b, ["shr-int/lit8"]],
    0xe2: [Instruction22b, ["ushr-int/lit8"]],
    # unused
    0xe3: [Instruction00x, ["unused"]],
    0xe4: [Instruction00x, ["unused"]],
    0xe5: [Instruction00x, ["unused"]],
    0xe6: [Instruction00x, ["unused"]],
    0xe7: [Instruction00x, ["unused"]],
    0xe8: [Instruction00x, ["unused"]],
    0xe9: [Instruction00x, ["unused"]],
    0xea: [Instruction00x, ["unused"]],
    0xeb: [Instruction00x, ["unused"]],
    0xec: [Instruction00x, ["unused"]],
    0xed: [Instruction00x, ["unused"]],
    0xee: [Instruction00x, ["unused"]],
    0xef: [Instruction00x, ["unused"]],
    0xf0: [Instruction00x, ["unused"]],
    0xf1: [Instruction00x, ["unused"]],
    0xf2: [Instruction00x, ["unused"]],
    0xf3: [Instruction00x, ["unused"]],
    0xf4: [Instruction00x, ["unused"]],
    0xf5: [Instruction00x, ["unused"]],
    0xf6: [Instruction00x, ["unused"]],
    0xf7: [Instruction00x, ["unused"]],
    0xf8: [Instruction00x, ["unused"]],
    0xf9: [Instruction00x, ["unused"]],

    # FIXME: what is with the Kinds? Need to implement in get_kinds and opcodes too
    0xfa: [Instruction45cc, ["invoke-polymorphic", Kind.METH_PROTO]],  # Dalvik 038
    0xfb: [Instruction4rcc, ["invoke-polymorphic/range", Kind.METH_PROTO]],  # Dalvik 038
    0xfc: [Instruction35c, ["invoke-custom", Kind.CALL_SITE]],  # Dalvik 038
    0xfd: [Instruction3rc, ["invoke-custom/range", Kind.CALL_SITE]],  # Dalvik 038
    0xfe: [Instruction21c, ["const-method-handle", Kind.METH]],  # Dalvik 039
    0xff: [Instruction21c, ['const-method-type', Kind.PROTO]],  # Dalvik 039
}

# Pseudo instructions used for payload
DALVIK_OPCODES_PAYLOAD = {
    0x0100: [PackedSwitch],
    0x0200: [SparseSwitch],
    0x0300: [FillArrayData],
}

# TODO: is this even used? Examples?
INLINE_METHODS = [
    ["Lorg/apache/harmony/dalvik/NativeTestTarget;", "emptyInlineMethod", "()V"
     ],
    ["Ljava/lang/String;", "charAt", "(I)C"],
    ["Ljava/lang/String;", "compareTo", "(Ljava/lang/String;)I"],
    ["Ljava/lang/String;", "equals", "(Ljava/lang/Object;)Z"],
    ["Ljava/lang/String;", "fastIndexOf", "(II)I"],
    ["Ljava/lang/String;", "isEmpty", "()Z"],
    ["Ljava/lang/String;", "length", "()I"],
    ["Ljava/lang/Math;", "abs", "(I)I"],
    ["Ljava/lang/Math;", "abs", "(J)J"],
    ["Ljava/lang/Math;", "abs", "(F)F"],
    ["Ljava/lang/Math;", "abs", "(D)D"],
    ["Ljava/lang/Math;", "min", "(II)I"],
    ["Ljava/lang/Math;", "max", "(II)I"],
    ["Ljava/lang/Math;", "sqrt", "(D)D"],
    ["Ljava/lang/Math;", "cos", "(D)D"],
    ["Ljava/lang/Math;", "sin", "(D)D"],
    ["Ljava/lang/Float;", "floatToIntBits", "(F)I"],
    ["Ljava/lang/Float;", "floatToRawIntBits", "(F)I"],
    ["Ljava/lang/Float;", "intBitsToFloat", "(I)F"],
    ["Ljava/lang/Double;", "doubleToLongBits", "(D)J"],
    ["Ljava/lang/Double;", "doubleToRawLongBits", "(D)J"],
    ["Ljava/lang/Double;", "longBitsToDouble", "(J)D"],
]

DALVIK_OPCODES_OPTIMIZED = {
    0xf2ff: [Instruction5rc, ["invoke-object-init/jumbo", Kind.METH]],
    0xf3ff: [Instruction52c, ["iget-volatile/jumbo", Kind.FIELD]],
    0xf4ff: [Instruction52c, ["iget-wide-volatile/jumbo", Kind.FIELD]],
    0xf5ff: [Instruction52c, ["iget-object-volatile/jumbo ", Kind.FIELD]],
    0xf6ff: [Instruction52c, ["iput-volatile/jumbo", Kind.FIELD]],
    0xf7ff: [Instruction52c, ["iput-wide-volatile/jumbo", Kind.FIELD]],
    0xf8ff: [Instruction52c, ["iput-object-volatile/jumbo", Kind.FIELD]],
    0xf9ff: [Instruction41c, ["sget-volatile/jumbo", Kind.FIELD]],
    0xfaff: [Instruction41c, ["sget-wide-volatile/jumbo", Kind.FIELD]],
    0xfbff: [Instruction41c, ["sget-object-volatile/jumbo", Kind.FIELD]],
    0xfcff: [Instruction41c, ["sput-volatile/jumbo", Kind.FIELD]],
    0xfdff: [Instruction41c, ["sput-wide-volatile/jumbo", Kind.FIELD]],
    0xfeff: [Instruction41c, ["sput-object-volatile/jumbo", Kind.FIELD]],
    0xffff: [Instruction40sc, ["throw-verification-error/jumbo", Kind.VARIES]],
}


def get_instruction(cm, op_value, buff):
    """
    Return the :class:`Instruction` for the given opcode

    :param ClassManager cm: ClassManager to propagate to Instruction
    :param int op_value: integer value of the instruction
    :param bytearray buff: Bytecode starting with the instruction
    :return: the parsed Instruction
    :rtype: Instruction
    """
    try:
        return DALVIK_OPCODES_FORMAT[op_value][0](cm, buff)
    except struct.error:
        # FIXME: there are other possible errors too...
        raise InvalidInstruction("Invalid Instruction for '0x{:02x}': {}".format(op_value, repr(buff)))


def get_optimized_instruction(cm, op_value, buff):
    try:
        return DALVIK_OPCODES_OPTIMIZED[op_value][0](cm, buff)
    except struct.error:
        # FIXME: there are other possible errors too...
        raise InvalidInstruction("Invalid Instruction for '0x{:04x}': {}".format(op_value, repr(buff)))


def get_instruction_payload(op_value, cm, buff):
    try:
        return DALVIK_OPCODES_PAYLOAD[op_value][0](cm, buff)
    except struct.error:
        # FIXME: there are other possible errors too...
        raise InvalidInstruction("Invalid Instruction for '0x{:04x}': {}".format(op_value, repr(buff)))


class LinearSweepAlgorithm:
    """
    This class is used to disassemble a method. The algorithm used by this class is linear sweep.
    """

    @staticmethod
    def get_instructions(cm, size, insn, idx):
        """
        Yields all instructions for the given bytecode sequence.
        If unknown/corrupt/unused instructions are encountered,
        the loop will stop and an error is written to the log.

        That means that the bytecode read might be corrupt
        or was crafted in this way, to break parsers.

        :param ClassManager cm: a ClassManager object
        :param int size: the total size of the buffer in 16-bit units
        :param bytearray insn: a raw buffer where are the instructions
        :param int idx: a start address in the buffer
        :param bool raise_errors: True to raise errors instead of simply logging them

        :rtype: Iterator[Instruction]
        """
        is_odex = cm.get_odex_format()

        max_idx = size * calcsize('H')
        if max_idx > len(insn):
            log.warning("Declared size of instructions is larger than the bytecode!")
            max_idx = len(insn)

        # Get instructions
        # TODO sometimes there are padding bytes after the last instruction, to ensure 16bit alignment.
        while idx < max_idx:
            # Get one 16bit unit
            # TODO: possible optimization; instead of reading the first 16 bits twice,
            #       just push this into the Instruction's constructor
            op_value, = cm.packer['H'].unpack(insn[idx:idx + 2])

            try:
                if op_value > 0xff and (op_value & 0xff) in (0x00, 0xff):
                    # FIXME: in theory, it could happen that this is a normal opcode? I.e. a 0xff opcode with AA being non zero
                    if op_value in DALVIK_OPCODES_PAYLOAD:
                        # payload instructions, i.e. for arrays or switch
                        obj = get_instruction_payload(op_value, cm, insn[idx:])
                    elif is_odex and (op_value in DALVIK_OPCODES_OPTIMIZED):
                        # optimized instructions, only of ODEX file
                        obj = get_optimized_instruction(cm, op_value, insn[idx:])
                    else:
                        raise InvalidInstruction("Unknown Instruction '0x{:04x}'".format(op_value))
                else:
                    obj = get_instruction(cm, op_value & 0xff, insn[idx:])
            except InvalidInstruction as e:
                # TODO somehow it would be nice to know that the parsing failed at the level of EncodedMethod or for the decompiler
                log.error("Invalid instruction encountered! Stop parsing bytecode at idx %s. Message: %s", idx, e)
                return
            # emit instruction
            yield obj
            idx += obj.get_length()


class DCode:
    """
    This class represents the instructions of a method

    :param class_manager: the ClassManager
    :type class_manager: :class:`ClassManager` object
    :param offset: the offset of the buffer
    :type offset: int
    :param size: the total size of the buffer
    :type size: int
    :param buff: a raw buffer where are the instructions
    :type buff: string
    """

    def __init__(self, class_manager, offset, size, buff):
        self.CM = class_manager
        self.insn = buff
        self.offset = offset
        self.size = size

        self.notes = {}
        self.cached_instructions = None

        self.idx = 0

    def get_insn(self):
        """
        Get the insn buffer

        :rtype: bytes
        """
        return self.insn

    def set_insn(self, insn):
        """
        Set a new raw buffer to disassemble

        :param insn: the buffer
        :type insn: bytes
        """
        self.insn = insn
        self.size = len(self.insn)

    def set_idx(self, idx):
        """
        Set the start address of the buffer

        :param idx: the index
        :type idx: int
        """
        self.idx = idx

    def is_cached_instructions(self):
        if self.cached_instructions is not None:
            return True
        return False

    def set_instructions(self, instructions):
        """
        Set the instructions

        :param instructions: the list of instructions
        :type instructions: a list of :class:`Instruction`
        """
        self.cached_instructions = instructions

    def get_instructions(self):
        """
        Get the instructions

        :rtype: a generator of each :class:`Instruction` (or a cached list of instructions if you have setup instructions)
        """
        # it is possible to a cache for instructions (avoid a new disasm)
        if self.cached_instructions is None:
            ins = LinearSweepAlgorithm.get_instructions(self.CM, self.size, self.insn, self.idx)
            self.cached_instructions = list(ins)

        for i in self.cached_instructions:
            yield i

    def add_inote(self, msg, idx, off=None):
        """
        Add a message to a specific instruction by using (default) the index of the address if specified

        :param msg: the message
        :type msg: string
        :param idx: index of the instruction (the position in the list of the instruction)
        :type idx: int
        :param off: address of the instruction
        :type off: int
        """
        if off is not None:
            idx = self.off_to_pos(off)

        if idx not in self.notes:
            self.notes[idx] = []

        self.notes[idx].append(msg)

    def get_instruction(self, idx, off=None):
        """
        Get a particular instruction by using (default) the index of the address if specified

        :param idx: index of the instruction (the position in the list of the instruction)
        :type idx: int
        :param off: address of the instruction
        :type off: int

        :rtype: an :class:`Instruction` object
        """
        if off is not None:
            idx = self.off_to_pos(off)
        if self.cached_instructions is None:
            self.get_instructions()
        return self.cached_instructions[idx]

    def off_to_pos(self, off):
        """
        Get the position of an instruction by using the address

        :param off: address of the instruction
        :type off: int

        :rtype: int
        """
        idx = 0
        nb = 0
        for i in self.get_instructions():
            if idx == off:
                return nb
            nb += 1
            idx += i.get_length()
        return -1

    def get_ins_off(self, off):
        """
        Get a particular instruction by using the address

        :param off: address of the instruction
        :type off: int

        :rtype: an :class:`Instruction` object
        """
        idx = 0
        for i in self.get_instructions():
            if idx == off:
                return i
            idx += i.get_length()
        return None

    def show(self):
        """
        Display (with a pretty print) this object
        """
        off = 0
        for n, i in enumerate(self.get_instructions()):
            print("{:8d} (0x{:08x}) {:04x} {:30} {}".format(n, off, i.get_op_value(), i.get_name(), i.get_output(self.idx)))
            off += i.get_length()

    def get_raw(self):
        """
        Return the raw buffer of this object

        :rtype: bytearray
        """
        buff = bytearray()
        for i in self.get_instructions():
            buff += i.get_raw()
        return buff

    def get_length(self):
        """
        Return the length of this object

        :rtype: int
        """
        return len(self.get_raw())


class TryItem:
    """
    This class represents the try_item format

    :param buff: a raw buffer where are the try_item format
    :type buff: BuffHandle
    :param cm: the ClassManager
    :type cm: ClassManager
    """

    def __init__(self, buff, cm):
        self.offset = buff.get_idx()

        self.CM = cm

        self.start_addr, \
        self.insn_count, \
        self.handler_off = cm.packer["I2H"].unpack(buff.read(8))

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def get_start_addr(self):
        """
        Get the start address of the block of code covered by this entry. The address is a count of 16-bit code units to the start of the first covered instruction.

        :rtype: int
        """
        return self.start_addr

    def get_insn_count(self):
        """
        Get the number of 16-bit code units covered by this entry

        :rtype: int
        """
        return self.insn_count

    def get_handler_off(self):
        """
        Get the offset in bytes from the start of the associated :class:`EncodedCatchHandlerList` to the :class:`EncodedCatchHandler` for this entry.

        :rtype: int
        """
        return self.handler_off

    def get_raw(self):
        return self.CM.packer["I2H"].pack(self.start_addr,
                    self.insn_count,
                    self.handler_off)

    def get_length(self):
        return len(self.get_raw())


class DalvikCode:
    """
    This class represents the instructions of a method

    :param buff: a raw buffer where are the instructions
    :type buff: BuffHandle
    :param cm: the ClassManager
    :type cm: :class:`ClassManager` object
    """

    def __init__(self, buff, cm):
        self.CM = cm
        self.offset = buff.get_idx()

        self.registers_size, \
        self.ins_size, \
        self.outs_size, \
        self.tries_size, \
        self.debug_info_off, \
        self.insns_size = cm.packer["4H2I"].unpack(buff.read(16))

        ushort = calcsize('H')

        self.code = DCode(self.CM, buff.get_idx(), self.insns_size, buff.read(self.insns_size * ushort))

        if self.insns_size % 2 == 1 and self.tries_size > 0:
            self.padding, = cm.packer["H"].unpack(buff.read(2))

        self.tries = []
        self.handlers = None
        if self.tries_size > 0:
            for i in range(0, self.tries_size):
                self.tries.append(TryItem(buff, self.CM))

            self.handlers = EncodedCatchHandlerList(buff, self.CM)

    def get_registers_size(self):
        """
        Get the number of registers used by this code

        :rtype: int
        """
        return self.registers_size

    def get_ins_size(self):
        """
        Get the number of words of incoming arguments to the method that this code is for

        :rtype: int
        """
        return self.ins_size

    def get_outs_size(self):
        """
        Get the number of words of outgoing argument space required by this code for method invocation

        :rtype: int
        """
        return self.outs_size

    def get_tries_size(self):
        """
        Get the number of :class:`TryItem` for this instance

        :rtype: int
        """
        return self.tries_size

    def get_debug_info_off(self):
        """
        Get the offset from the start of the file to the debug info (line numbers + local variable info) sequence for this code, or 0 if there simply is no information

        :rtype: int
        """
        return self.debug_info_off

    def get_insns_size(self):
        """
        Get the size of the instructions list, in 16-bit code units

        :rtype: int
        """
        return self.insns_size

    def get_handlers(self):
        """
        Get the bytes representing a list of lists of catch types and associated handler addresses.

        :rtype: :class:`EncodedCatchHandlerList`
        """
        return self.handlers

    def get_tries(self):
        """
        Get the array indicating where in the code exceptions are caught and how to handle them

        :rtype: a list of :class:`TryItem` objects
        """
        return self.tries

    def get_debug(self):
        """
        Return the associated debug object

        :rtype: :class:`DebugInfoItem`
        """
        return self.CM.get_debug_off(self.debug_info_off)

    def get_bc(self):
        """
        Return the associated code object

        :rtype: :class:`DCode`
        """
        return self.code

    def set_idx(self, idx):
        self.code.set_idx(idx)

    def get_length(self):
        return self.insns_size

    def _begin_show(self):
        log.debug("registers_size: %d" % self.registers_size)
        log.debug("ins_size: %d" % self.ins_size)
        log.debug("outs_size: %d" % self.outs_size)
        log.debug("tries_size: %d" % self.tries_size)
        log.debug("debug_info_off: %d" % self.debug_info_off)
        log.debug("insns_size: %d" % self.insns_size)

        bytecode._PrintBanner()

    def show(self):
        self._begin_show()
        self.code.show()
        self._end_show()

    def _end_show(self):
        bytecode._PrintBanner()

    def get_obj(self):
        return [self.code, self.tries, self.handlers]

    def get_raw(self):
        """
        Get the reconstructed code as bytearray

        :rtype: bytearray
        """
        code_raw = self.code.get_raw()
        self.insns_size = (len(code_raw) // 2) + (len(code_raw) % 2)

        buff = bytearray()
        buff += self.CM.packer["4H2I"].pack(self.registers_size,
                    self.ins_size,
                    self.outs_size,
                    self.tries_size,
                    self.debug_info_off,
                    self.insns_size) + code_raw

        if self.tries_size > 0:
            if (self.insns_size % 2 == 1):
                buff += self.CM.packer["H"].pack(self.padding)

            for i in self.tries:
                buff += i.get_raw()
            buff += self.handlers.get_raw()

        return buff

    def add_inote(self, msg, idx, off=None):
        """
        Add a message to a specific instruction by using (default) the index of the address if specified

        :param msg: the message
        :type msg: string
        :param idx: index of the instruction (the position in the list of the instruction)
        :type idx: int
        :param off: address of the instruction
        :type off: int
        """
        if self.code:
            return self.code.add_inote(msg, idx, off)

    def get_instruction(self, idx, off=None):
        if self.code:
            return self.code.get_instruction(idx, off)

    def get_size(self):
        return len(self.get_raw())

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset


class CodeItem:
    def __init__(self, size, buff, cm):
        self.CM = cm

        self.offset = buff.get_idx()

        self.code = []
        self.__code_off = {}

        for i in range(0, size):
            # As we read the DalvikCode items from the map, there might be
            # padding bytes in between.
            # We know, that the alignment is 4 bytes.
            off = buff.get_idx()
            if off % 4 != 0:
                buff.set_idx(off + (4 - (off % 4)))

            x = DalvikCode(buff, cm)
            self.code.append(x)
            self.__code_off[x.get_off()] = x

    def set_off(self, off):
        self.offset = off

    def get_off(self):
        return self.offset

    def get_code(self, off):
        try:
            return self.__code_off[off]
        except KeyError:
            return None

    def show(self):
        # FIXME workaround for showing the MAP_ITEMS
        # if m_a is none, we use get_raw.
        # Otherwise the real code is printed...
        bytecode._PrintDefault("CODE_ITEM\n")
        bytecode._PrintDefault(binascii.hexlify(self.get_raw()).decode("ASCII"))
        bytecode._PrintDefault("\n")

    def get_obj(self):
        return [i for i in self.code]

    def get_raw(self):
        buff = bytearray()
        for c in self.code:
            buff += c.get_raw()
        return buff

    def get_length(self):
        length = 0
        for i in self.code:
            length += i.get_size()
        return length


class MapItem:
    def __init__(self, buff, cm):
        """
        Implementation of a map_item, which occours in a map_list

        https://source.android.com/devices/tech/dalvik/dex-format#map-item
        """
        self.CM = cm
        self.buff = buff

        self.off = buff.get_idx()

        self.type = TypeMapItem(cm.packer["H"].unpack(buff.read(2))[0])
        self.unused, \
        self.size, \
        self.offset = cm.packer["H2I"].unpack(buff.read(10))

        self.item = None

    def get_off(self):
        """Gets the offset of the map item itself inside the DEX file"""
        return self.off

    def get_offset(self):
        """Gets the offset of the item of the map item"""
        return self.offset

    def get_type(self):
        return self.type

    def get_size(self):
        """
        Returns the number of items found at the location indicated by
        :meth:`get_offset`.
        """
        return self.size

    def parse(self):
        log.debug("Starting parsing map_item '{}'".format(self.type.name))
        started_at = time.time()

        # Not all items are aligned in the same way. Most are aligned by four bytes,
        # but there are a few which are not!
        # Hence, we need to check the alignment for each item.

        buff = self.buff
        cm = self.CM

        if TypeMapItem.STRING_ID_ITEM == self.type:
            # Byte aligned
            buff.set_idx(self.offset)
            self.item = [StringIdItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.CODE_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = CodeItem(self.size, buff, cm)

        elif TypeMapItem.TYPE_ID_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = TypeHIdItem(self.size, buff, cm)

        elif TypeMapItem.PROTO_ID_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = ProtoHIdItem(self.size, buff, cm)

        elif TypeMapItem.FIELD_ID_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = FieldHIdItem(self.size, buff, cm)

        elif TypeMapItem.METHOD_ID_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = MethodHIdItem(self.size, buff, cm)

        elif TypeMapItem.CLASS_DEF_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = ClassHDefItem(self.size, buff, cm)

        elif TypeMapItem.HEADER_ITEM == self.type:
            # FIXME probably not necessary to parse again here...
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = HeaderItem(self.size, buff, cm)

        elif TypeMapItem.ANNOTATION_ITEM == self.type:
            # Byte aligned
            buff.set_idx(self.offset)
            self.item = [AnnotationItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.ANNOTATION_SET_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = [AnnotationSetItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.ANNOTATIONS_DIRECTORY_ITEM == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = [AnnotationsDirectoryItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.ANNOTATION_SET_REF_LIST == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = [AnnotationSetRefList(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.TYPE_LIST == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            self.item = [TypeList(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.STRING_DATA_ITEM == self.type:
            # Byte aligned
            buff.set_idx(self.offset)
            self.item = [StringDataItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.DEBUG_INFO_ITEM == self.type:
            # Byte aligned
            buff.set_idx(self.offset)
            self.item = DebugInfoItemEmpty(buff, cm)

        elif TypeMapItem.ENCODED_ARRAY_ITEM == self.type:
            # Byte aligned
            buff.set_idx(self.offset)
            self.item = [EncodedArrayItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.CLASS_DATA_ITEM == self.type:
            # Byte aligned
            buff.set_idx(self.offset)
            self.item = [ClassDataItem(buff, cm) for _ in range(self.size)]

        elif TypeMapItem.MAP_LIST == self.type:
            # 4-byte aligned
            buff.set_idx(self.offset + (self.offset % 4))
            pass  # It's me I think !!! No need to parse again

        else:
            log.warning("Map item with id '{type}' offset: 0x{off:x} ({off}) "
                        "size: {size} is unknown. "
                        "Is this a newer DEX format?".format(type=self.type, off=buff.get_idx(), size=self.size))

        diff = time.time() - started_at
        minutes, seconds = diff // 60, diff % 60
        log.debug("End of parsing map_item '{}'. Required time {:.0f}:{:07.4f}".format(self.type.name, minutes, seconds))

    def show(self):
        bytecode._Print("\tMAP_TYPE_ITEM", self.type.name)

        if self.item is not None:
            if isinstance(self.item, list):
                for i in self.item:
                    i.show()
            else:
                self.item.show()

    def get_obj(self):
        """
        Return the associated item itself.
        Might return None, if :meth:`parse` was not called yet.

        This method is the same as :meth:`get_item`.
        """
        return self.item

    # alias
    get_item = get_obj

    def get_raw(self):
        # FIXME why is it necessary to get the offset here agin? We have this
        # stored?!
        if isinstance(self.item, list):
            self.offset = self.item[0].get_off()
        else:
            self.offset = self.item.get_off()

        return self.CM.packer["2H2I"].pack(self.type,
                    self.unused,
                    self.size,
                    self.offset)

    def get_length(self):
        return calcsize("HHII")

    def set_item(self, item):
        self.item = item


class OffObj:
    def __init__(self, o):
        """
        .. deprecated:: 3.3.5
            Will be removed!
        """
        warnings.warn("deprecated, this class will be removed!", DeprecationWarning)
        self.off = o


class ClassManager:
    """
    This class is used to access to all elements (strings, type, proto ...) of the dex format
    based on their offset or index.
    """

    def __init__(self, vm):
        """
        :param DalvikVMFormat vm: the VM to create a ClassManager for
        """
        self.vm = vm
        self.buff = vm

        self.decompiler_ob = None

        self.__packer = None

        self.__manage_item = {}
        self.__manage_item_off = []

        self.__strings_off = {}
        self.__typelists_off = {}
        self.__classdata_off = {}

        self.__obj_offset = {}
        self.__item_offset = {}

        self.__cached_proto = {}

        self.hook_strings = {}

        if self.vm:
            self.odex_format = self.vm.get_format_type() == "ODEX"
        else:
            self.odex_format = False

    @property
    def packer(self):
        return self.__packer

    @packer.setter
    def packer(self, p):
        self.__packer = p

    def get_ascii_string(self, s):
        # TODO Remove method
        try:
            return s.decode("ascii")
        except UnicodeDecodeError:
            d = ""
            for i in s:
                if i < 128:
                    d += i
                else:
                    d += "%x" % i
            return d

    def get_odex_format(self):
        """Returns True if the underlying VM is ODEX"""
        return self.odex_format

    def get_obj_by_offset(self, offset):
        """
        Returnes a object from as given offset inside the DEX file
        """
        return self.__obj_offset[offset]

    def get_item_by_offset(self, offset):
        return self.__item_offset[offset]

    def get_string_by_offset(self, offset):
        return self.__strings_off[offset]

    def get_lazy_analysis(self):
        """
        .. deprecated:: 3.3.5
            do not use this function anymore!
        """
        warnings.warn("deprecated, this method always returns False!", DeprecationWarning)
        return False

    def set_decompiler(self, decompiler):
        self.decompiler_ob = decompiler

    def get_engine(self):
        """
        .. deprecated:: 3.3.5
            do not use this function anymore!
        """
        warnings.warn("deprecated, this method always returns None!", DeprecationWarning)
        return None

    def get_all_engine(self):
        """
        .. deprecated:: 3.3.5
            do not use this function anymore!
        """
        warnings.warn("deprecated, this method always returns None!", DeprecationWarning)
        return None

    def add_type_item(self, type_item, c_item, item):
        self.__manage_item[type_item] = item

        self.__obj_offset[c_item.get_off()] = c_item
        self.__item_offset[c_item.get_offset()] = item

        if item is None:
            pass
        elif isinstance(item, list):
            for i in item:
                goff = i.offset
                self.__manage_item_off.append(goff)

                self.__obj_offset[i.get_off()] = i

                if type_item == TypeMapItem.STRING_DATA_ITEM:
                    self.__strings_off[goff] = i
                elif type_item == TypeMapItem.TYPE_LIST:
                    self.__typelists_off[goff] = i
                elif type_item == TypeMapItem.CLASS_DATA_ITEM:
                    self.__classdata_off[goff] = i
        else:
            self.__manage_item_off.append(c_item.get_offset())

    def get_code(self, idx):
        try:
            return self.__manage_item[TypeMapItem.CODE_ITEM].get_code(idx)
        except KeyError:
            return None

    def get_class_data_item(self, off):
        i = self.__classdata_off.get(off)
        if i is None:
            log.warning("unknown class data item @ 0x%x" % off)

        return i

    def get_encoded_array_item(self, off):
        for i in self.__manage_item[TypeMapItem.ENCODED_ARRAY_ITEM]:
            if i.get_off() == off:
                return i

    def get_annotations_directory_item(self, off):
        for i in self.__manage_item[TypeMapItem.ANNOTATIONS_DIRECTORY_ITEM]:
            if i.get_off() == off:
                return i

    def get_annotation_set_item(self, off):
        for i in self.__manage_item[TypeMapItem.ANNOTATION_SET_ITEM]:
            if i.get_off() == off:
                return i

    def get_annotation_off_item(self, off):
        for i in self.__manage_item[TypeMapItem.ANNOTATION_OFF_ITEM]:
            if i.get_off() == off:
                return i
    
    def get_annotation_item(self, off):
        for i in self.__manage_item[TypeMapItem.ANNOTATION_ITEM]:
            if i.get_off() == off:
                return i

    def get_string(self, idx):
        """
        Return a string from the string table at index `idx`

        If string is hooked, the hooked string is returned.

        :param int idx: index in the string section
        """
        if idx in self.hook_strings:
            return self.hook_strings[idx]

        return self.get_raw_string(idx)

    def get_raw_string(self, idx):
        """
        Return the (unprocessed) string from the string table at index `idx`.

        :param int idx: the index in the string section
        """
        try:
            off = self.__manage_item[TypeMapItem.STRING_ID_ITEM][idx].get_string_data_off()
        except IndexError:
            log.warning("unknown string item @ %d" % idx)
            return "AG:IS: invalid string"

        try:
            return self.__strings_off[off].get()
        except KeyError:
            log.warning("unknown string item @ 0x%x(%d)" % (off, idx))
            return "AG:IS: invalid string"

    def get_type_list(self, off):
        if off == 0:
            return []

        i = self.__typelists_off[off]
        return [type_.get_string() for type_ in i.get_list()]

    def get_type(self, idx):
        """
        Return the resolved type name based on the index

        This returns the string associated with the type.

        :param int idx:
        :return: the type name
        :rtype: str
        """
        _type = self.get_type_ref(idx)
        if _type == -1:
            return "AG:ITI: invalid type"
        return self.get_string(_type)

    def get_type_ref(self, idx):
        """
        Returns the string reference ID for a given type ID.

        This method is similar to :meth:`get_type` but does not resolve
        the string but returns the ID into the string section.

        If the type IDX is not found, -1 is returned.
        """
        return self.__manage_item[TypeMapItem.TYPE_ID_ITEM].get(idx)

    def get_proto(self, idx):
        proto = self.__cached_proto.get(idx)
        if not proto:
            proto = self.__manage_item[TypeMapItem.PROTO_ID_ITEM].get(idx)
            self.__cached_proto[idx] = proto

        return [proto.get_parameters_off_value(),
                proto.get_return_type_idx_value()]

    def get_field(self, idx):
        field = self.get_field_ref(idx)
        return [field.get_class_name(), field.get_type(), field.get_name()]

    def get_field_ref(self, idx):
        return self.__manage_item[TypeMapItem.FIELD_ID_ITEM].get(idx)

    def get_method(self, idx):
        return self.get_method_ref(idx).get_list()

    def get_method_ref(self, idx):
        return self.__manage_item[TypeMapItem.METHOD_ID_ITEM].get(idx)

    def set_hook_class_name(self, class_def, value):
        python_export = True
        _type = self.__manage_item[TypeMapItem.TYPE_ID_ITEM].get(
            class_def.get_class_idx())
        self.set_hook_string(_type, value)

        try:
            self.vm._delete_python_export_class(class_def)
        except AttributeError:
            python_export = False

        class_def.reload()

        # FIXME
        self.__manage_item[TypeMapItem.METHOD_ID_ITEM].reload()

        for i in class_def.get_methods():
            i.reload()

        for i in class_def.get_fields():
            i.reload()

        if python_export:
            self.vm._create_python_export_class(class_def)

    def set_hook_method_name(self, encoded_method, value):
        python_export = True

        method = self.__manage_item[TypeMapItem.METHOD_ID_ITEM].get(
            encoded_method.get_method_idx())
        self.set_hook_string(method.get_name_idx(), value)

        class_def = self.__manage_item[TypeMapItem.CLASS_DEF_ITEM].get_class_idx(
            method.get_class_idx())
        if class_def is not None:
            try:
                name = bytecode.FormatNameToPython(encoded_method.get_name())
            except AttributeError:
                name += "_" + bytecode.FormatDescriptorToPython(
                    encoded_method.get_descriptor())

            log.debug("try deleting old name in python...")
            try:
                delattr(class_def.M, name)
                log.debug("success with regular name")
            except AttributeError:
                log.debug("WARNING: fail with regular name")
                # python_export = False

                try:
                    name = bytecode.FormatNameToPython(encoded_method.get_name(
                    ) + '_' + encoded_method.proto.replace(' ', '').replace(
                        '(', '').replace('[', '').replace(')', '').replace(
                        '/', '_').replace(';', ''))
                except AttributeError:
                    name += "_" + bytecode.FormatDescriptorToPython(
                        encoded_method.get_descriptor())

                try:
                    delattr(class_def.M, name)
                    log.debug("success with name containing prototype")
                except AttributeError:
                    log.debug("WARNING: fail with name containing prototype")
                    python_export = False

            if python_export:
                name = bytecode.FormatNameToPython(value)
                setattr(class_def.M, name, encoded_method)
                log.debug("new name in python: created: %s." % name)
            else:
                log.debug("skipping creating new name in python")

        method.reload()

    def set_hook_field_name(self, encoded_field, value):
        python_export = True

        field = self.__manage_item[TypeMapItem.FIELD_ID_ITEM].get(
            encoded_field.get_field_idx())
        self.set_hook_string(field.get_name_idx(), value)

        class_def = self.__manage_item[TypeMapItem.CLASS_DEF_ITEM].get_class_idx(
            field.get_class_idx())
        if class_def is not None:
            try:
                name = bytecode.FormatNameToPython(encoded_field.get_name())
            except AttributeError:
                name += "_" + bytecode.FormatDescriptorToPython(
                    encoded_field.get_descriptor())

            try:
                delattr(class_def.F, name)
            except AttributeError:
                python_export = False

            if python_export:
                name = bytecode.FormatNameToPython(value)
                setattr(class_def.F, name, encoded_field)

        field.reload()

    def set_hook_string(self, idx, value):
        self.hook_strings[idx] = value

    def get_next_offset_item(self, idx):
        for i in self.__manage_item_off:
            if i > idx:
                return i
        return idx

    def get_debug_off(self, off):
        self.buff.set_idx(off)

        return DebugInfoItem(self.buff, self)


class MapList:
    """
    This class can parse the "map_list" of the dex format

    https://source.android.com/devices/tech/dalvik/dex-format#map-list
    """

    def __init__(self, cm, off, buff):
        self.CM = cm

        buff.set_idx(off)

        self.offset = off

        self.size, = cm.packer["I"].unpack(buff.read(4))

        self.map_item = []
        for _ in range(0, self.size):
            idx = buff.get_idx()

            mi = MapItem(buff, self.CM)
            self.map_item.append(mi)

            buff.set_idx(idx + mi.get_length())

        load_order = TypeMapItem.determine_load_order()
        ordered = sorted(self.map_item, key=lambda mi: load_order[mi.get_type()])

        for mi in ordered:
            mi.parse()

            c_item = mi.get_item()
            if c_item is None:
                mi.set_item(self)
                c_item = mi.get_item()

            self.CM.add_type_item(mi.get_type(), mi, c_item)

    def get_off(self):
        return self.offset

    def set_off(self, off):
        self.offset = off

    def get_item_type(self, ttype):
        """
        Get a particular item type

        :param ttype: a string which represents the desired type

        :rtype: None or the item object
        """
        for i in self.map_item:
            if i.get_type() == ttype:
                return i.get_item()
        return None

    def show(self):
        """
        Print with a pretty display the MapList object
        """
        bytecode._Print("MAP_LIST SIZE", self.size)
        for i in self.map_item:
            if i.item != self:
                # FIXME this does not work for CodeItems!
                # as we do not have the method analysis here...
                i.show()

    def get_obj(self):
        return [x.get_obj() for x in self.map_item]

    def get_raw(self):
        return self.CM.packer["I"].pack(self.size) + b''.join(x.get_raw() for x in self.map_item)

    def get_class_manager(self):
        return self.CM

    def get_length(self):
        return len(self.get_raw())


class DalvikPacker:
    """
    Generic Packer class to unpack bytes based on different endianness
    """
    def __init__(self, endian_tag):
        if endian_tag == 0x78563412:
            log.error("DEX file with byte swapped endian tag is not supported!")
            raise NotImplementedError("Byte swapped endian tag encountered!")
        elif endian_tag == 0x12345678:
            self.endian_tag = '<'
        else:
            raise ValueError("This is not a DEX file! Wrong endian tag: '0x{:08x}'".format(endian_tag))
        self.__structs = {}

    def __getitem__(self, item):
        try:
            return self.__structs[item]
        except KeyError:
            self.__structs[item] = struct.Struct(self.endian_tag + item)
        return self.__structs[item]

    def __getstate__(self):
        return self.endian_tag

    def __setstate__(self, state):
        self.endian_tag = state
        self.__structs = {}


class DalvikVMFormat(bytecode.BuffHandle):
    """
    This class can parse a classes.dex file of an Android application (APK).

    :param buff: a string which represents the classes.dex file
    :param decompiler: associate a decompiler object to display the java source code
    :type buff: bytes
    :type decompiler: object

    example::

        d = DalvikVMFormat( read("classes.dex") )
    """

    def __init__(self, buff, decompiler=None, config=None, using_api=None):
        # to allow to pass apk object ==> we do not need to pass additionally target version
        if isinstance(buff, APK):
            self.api_version = buff.get_target_sdk_version()
            buff = buff.get_dex()  # getting dex from APK file
        elif using_api:
            self.api_version = using_api
        else:
            self.api_version = CONF["DEFAULT_API"]

        super().__init__(buff)
        self._flush()

        self.CM = ClassManager(self)
        self.CM.set_decompiler(decompiler)

        self._preload(buff)
        self._load(buff)

    def _preload(self, buff):
        pass

    def _load(self, buff):
        self.header = HeaderItem(0, self, self.CM)

        if self.header.map_off == 0:
            # TODO check if the header specifies items but does not have a map
            log.warning("no map list! This DEX file is probably empty.")
        else:
            self.map_list = MapList(self.CM, self.header.map_off, self)

            self.classes = self.map_list.get_item_type(TypeMapItem.CLASS_DEF_ITEM)
            self.methods = self.map_list.get_item_type(TypeMapItem.METHOD_ID_ITEM)
            self.fields = self.map_list.get_item_type(TypeMapItem.FIELD_ID_ITEM)
            self.codes = self.map_list.get_item_type(TypeMapItem.CODE_ITEM)
            self.strings = self.map_list.get_item_type(TypeMapItem.STRING_DATA_ITEM)
            self.debug = self.map_list.get_item_type(TypeMapItem.DEBUG_INFO_ITEM)

        self._flush()

    def _flush(self):
        """
        Flush all caches
        Might be used after classes, methods or fields are added.
        """
        self.classes_names = None
        self.__cache_methods = None
        self.__cached_methods_idx = None
        self.__cache_fields = None

        # cache methods and fields as well, otherwise the decompiler is quite slow
        self.__cache_all_methods = None
        self.__cache_all_fields = None

    @property
    def version(self):
        """
        Returns the version number of the DEX Format
        """
        return self.header.dex_version

    def get_vmanalysis(self):
        """
        .. deprecated:: 3.1.0
            The :class:`~androguard.core.analysis.analysis.Analysis` is not
            loaded anymore into :class:`DalvikVMFormat` in order to avoid
            cyclic dependencies.
            :class:`~androguard.core.analysis.analysis.Analysis` extends now
            :class:`DalvikVMFormat`.
            This Method does nothing anymore!

        The Analysis Object should contain all the information required,
        inclduing the DalvikVMFormats.
        """
        warnings.warn("deprecated, this method does nothing!", DeprecationWarning)

    def set_vmanalysis(self, analysis):
        """
        .. deprecated:: 3.1.0
            The :class:`~androguard.core.analysis.analysis.Analysis` is not
            loaded anymore into :class:`DalvikVMFormat` in order to avoid
            cyclic dependencies.
            :class:`~androguard.core.analysis.analysis.Analysis` extends now
            :class:`DalvikVMFormat`.
            This Method does nothing anymore!

        The Analysis Object should contain all the information required,
        inclduing the DalvikVMFormats.
        """
        warnings.warn("deprecated, this method does nothing!", DeprecationWarning)

    def get_api_version(self):
        """
        This method returns api version that should be used for loading api
        specific resources.

        :rtype: int
        """
        return self.api_version

    def get_classes_def_item(self):
        """
        This function returns the class def item

        :rtype: :class:`ClassHDefItem` object
        """
        return self.classes

    def get_methods_id_item(self):
        """
        This function returns the method id item

        :rtype: :class:`MethodHIdItem` object
        """
        return self.methods

    def get_fields_id_item(self):
        """
        This function returns the field id item

        :rtype: :class:`FieldHIdItem` object
        """
        return self.fields

    def get_codes_item(self):
        """
        This function returns the code item

        :rtype: :class:`CodeItem` object
        """
        return self.codes

    def get_string_data_item(self):
        """
        This function returns the string data item

        :rtype: :class:`StringDataItem` object
        """
        return self.strings

    def get_debug_info_item(self):
        """
        This function returns the debug info item

        :rtype: :class:`DebugInfoItem` object
        """
        return self.debug

    def get_header_item(self):
        """
        This function returns the header item

        :rtype: :class:`HeaderItem` object
        """
        return self.header

    def get_class_manager(self):
        """
        This function returns a ClassManager object which allow you to get
        access to all index references (strings, methods, fields, ....)

        :rtype: :class:`ClassManager` object
        """
        return self.CM

    def show(self):
        """
        Show the all information in the object
        """
        self.map_list.show()

    def save(self):
        """
        Return the dex (with the modifications) into raw format (fix checksums)
        (beta: do not use !)

        :rtype: string
        """
        l = []
        h = {}
        s = {}
        h_r = {}

        idx = 0
        for i in self.map_list.get_obj():
            length = 0

            if isinstance(i, list):
                for j in i:
                    if isinstance(j, AnnotationsDirectoryItem):
                        if idx % 4 != 0:
                            idx = idx + (4 - (idx % 4))

                    l.append(j)

                    c_length = j.get_length()
                    if isinstance(j, StringDataItem):
                        c_length += 1
                    h[j] = idx + length
                    h_r[idx + length] = j
                    s[idx + length] = c_length

                    length += c_length
                    # log.debug("SAVE" + str(j) + " @ 0x%x" % (idx+length))

                log.debug("SAVE " + str(i[0]) + " @0x{:x} ({:x})".format(idx, length))

            else:
                if isinstance(i, MapList):
                    if idx % 4 != 0:
                        idx = idx + (4 - (idx % 4))

                l.append(i)
                h[i] = idx
                h_r[idx] = i

                length = i.get_length()

                s[idx] = length

                log.debug("SAVE " + str(i) + " @0x{:x} ({:x})".format(idx, length))

            idx += length

        self.header.file_size = idx

        for i in l:
            idx = h[i]
            i.set_off(idx)
            if isinstance(i, CodeItem):
                last_idx = idx
                for j in i.get_obj():
                    j.set_off(last_idx)
                    # j.set_debug_info_off(0)
                    last_idx += j.get_size()

        last_idx = 0
        buff = bytearray()
        for i in l:
            idx = h[i]

            if idx != last_idx:
                log.debug("Adjust alignment @{:x} with 00 {:x}".format(idx, idx - last_idx))
                buff += bytearray([0] * (idx - last_idx))

            buff += i.get_raw()
            if isinstance(i, StringDataItem):
                buff += b"\x00"
            last_idx = idx + s[idx]

        log.debug("GLOBAL SIZE %d" % len(buff))

        return self.fix_checksums(buff)

    def fix_checksums(self, buff):
        """
          Fix a dex format buffer by setting all checksums

          :rtype: string
        """

        signature = hashlib.sha1(buff[32:]).digest()

        buff = buff[:12] + signature + buff[32:]
        checksum = zlib.adler32(buff[12:])
        buff = buff[:8] + self.CM.packer["I"].pack(checksum) + buff[12:]

        log.debug("NEW SIGNATURE %s" % repr(signature))
        log.debug("NEW CHECKSUM %x" % checksum)

        return buff

    def get_cm_field(self, idx):
        """
        Get a specific field by using an index

        :param idx: index of the field
        :type idx: int
        """
        return self.CM.get_field(idx)

    def get_cm_method(self, idx):
        """
        Get a specific method by using an index

        :param idx: index of the method
        :type idx: int
        """
        return self.CM.get_method(idx)

    def get_cm_string(self, idx):
        """
        Get a specific string by using an index

        :param idx: index of the string
        :type idx: int
        """
        return self.CM.get_raw_string(idx)

    def get_cm_type(self, idx):
        """
        Get a specific type by using an index

        :param idx: index of the type
        :type idx: int
        """
        return self.CM.get_type(idx)

    def get_classes_names(self, update=False):
        """
        Return the names of classes

        :param update: True indicates to recompute the list.
                       Maybe needed after using a MyClass.set_name().
        :rtype: a list of string
        """
        if self.classes_names is None or update:
            self.classes_names = [i.get_name() for i in self.get_classes()]
        return self.classes_names

    def get_classes(self):
        """
        Return all classes

        :rtype: a list of :class:`ClassDefItem` objects
        """
        if self.classes:
            return self.classes.class_def
        else:
            # There is a rare case that the DEX has no classes
            return []

    def get_class(self, name):
        """
        Return a specific class

        :param name: the name of the class

        :rtype: a :class:`ClassDefItem` object
        """
        for i in self.get_classes():
            if i.get_name() == name:
                return i
        return None

    def get_method(self, name):
        """
        Return a list all methods which corresponds to the regexp

        :param name: the name of the method (a python regexp)

        :rtype: a list with all :class:`EncodedMethod` objects
        """
        # TODO could use a generator here
        name = bytes(mutf8.MUTF8String.from_str(name))
        prog = re.compile(name)
        l = []
        for i in self.get_classes():
            for j in i.get_methods():
                if prog.match(j.get_name()):
                    l.append(j)
        return l

    def get_field(self, name):
        """
        Return a list all fields which corresponds to the regexp

        :param name: the name of the field (a python regexp)

        :rtype: a list with all :class:`EncodedField` objects
        """
        # TODO could use a generator here
        name = bytes(mutf8.MUTF8String.from_str(name))
        prog = re.compile(name)
        l = []
        for i in self.get_classes():
            for j in i.get_fields():
                if prog.match(j.get_name()):
                    l.append(j)
        return l

    def get_all_fields(self):
        """
        Return a list of field items

        :rtype: a list of :class:`FieldIdItem` objects
        """
        try:
            return self.fields.gets()
        except AttributeError:
            return []

    def get_fields(self):
        """
        Return all field objects

        :rtype: a list of :class:`EncodedField` objects
        """
        if self.__cache_all_fields is None:
            self.__cache_all_fields = []
            for i in self.get_classes():
                for j in i.get_fields():
                    self.__cache_all_fields.append(j)
        return self.__cache_all_fields

    def get_methods(self):
        """
        Return all method objects

        :rtype: a list of :class:`EncodedMethod` objects
        """
        if self.__cache_all_methods is None:
            self.__cache_all_methods = []
            for i in self.get_classes():
                for j in i.get_methods():
                    self.__cache_all_methods.append(j)
        return self.__cache_all_methods

    def get_len_methods(self):
        """
        Return the number of methods

        :rtype: int
        """
        return len(self.get_methods())

    def get_method_by_idx(self, idx):
        """
        Return a specific method by using an index
        :param idx: the index of the method
        :type idx: int

        :rtype: None or an :class:`EncodedMethod` object
        """
        if self.__cached_methods_idx is None:
            self.__cached_methods_idx = {}
            for i in self.get_classes():
                for j in i.get_methods():
                    self.__cached_methods_idx[j.get_method_idx()] = j

        try:
            return self.__cached_methods_idx[idx]
        except KeyError:
            return None

    def get_method_descriptor(self, class_name, method_name, descriptor):
        """
        Return the specific method

        :param class_name: the class name of the method
        :type class_name: string
        :param method_name: the name of the method
        :type method_name: string
        :param descriptor: the descriptor of the method
        :type descriptor: string

        :rtype: None or a :class:`EncodedMethod` object
        """
        key = class_name + method_name + descriptor

        if self.__cache_methods is None:
            self.__cache_methods = {}
            for i in self.get_classes():
                for j in i.get_methods():
                    self.__cache_methods[j.get_class_name() + j.get_name() +
                                         j.get_descriptor()] = j

        return self.__cache_methods.get(key)

    def get_methods_descriptor(self, class_name, method_name):
        """
        Return the specific methods of the class

        :param class_name: the class name of the method
        :type class_name: string
        :param method_name: the name of the method
        :type method_name: string

        :rtype: None or a :class:`EncodedMethod` object
        """
        l = []
        for i in self.get_classes():
            if i.get_name() == class_name:
                for j in i.get_methods():
                    if j.get_name() == method_name:
                        l.append(j)

        return l

    def get_methods_class(self, class_name):
        """
        Return all methods of a specific class

        :param class_name: the class name
        :type class_name: string

        :rtype: a list with :class:`EncodedMethod` objects
        """
        l = []
        for i in self.get_classes():
            for j in i.get_methods():
                if class_name == j.get_class_name():
                    l.append(j)

        return l

    def get_fields_class(self, class_name):
        """
        Return all fields of a specific class

        :param class_name: the class name
        :type class_name: string

        :rtype: a list with :class:`EncodedField` objects
        """
        l = []
        for i in self.get_classes():
            for j in i.get_fields():
                if class_name == j.get_class_name():
                    l.append(j)

        return l

    def get_field_descriptor(self, class_name, field_name, descriptor):
        """
        Return the specific field

        :param class_name: the class name of the field
        :type class_name: string
        :param field_name: the name of the field
        :type field_name: string
        :param descriptor: the descriptor of the field
        :type descriptor: string

        :rtype: None or a :class:`EncodedField` object
        """

        key = class_name + field_name + descriptor

        if self.__cache_fields is None:
            self.__cache_fields = {}
            for i in self.get_classes():
                for j in i.get_fields():
                    self.__cache_fields[j.get_class_name() + j.get_name() +
                                        j.get_descriptor()] = j

        return self.__cache_fields.get(key)

    def get_strings(self):
        """
        Return all strings

        The strings will have escaped surrogates, if only a single high or low surrogate is found.
        Complete surrogates are put together into the representing 32bit character.

        :rtype: a list with all strings used in the format (types, names ...)
        """
        return [i.get() for i in self.strings]

    def get_regex_strings(self, regular_expressions):
        """
        Return all target strings matched the regex

        :param regular_expressions: the python regex
        :type regular_expressions: string

        :rtype: a list of strings matching the regex expression
        """
        str_list = []
        if regular_expressions.count is None:
            return None
        for i in self.get_strings():
            if re.match(regular_expressions, i):
                str_list.append(i)
        return str_list

    def get_format_type(self):
        """
        Return the type

        :rtype: a string
        """
        return "DEX"

    def create_python_export(self):
        """
        Export classes/methods/fields' names in the python namespace
        """
        setattr(self, "C", ExportObject())

        for _class in self.get_classes():
            self._create_python_export_class(_class)

    def _delete_python_export_class(self, _class):
        self._create_python_export_class(_class, True)

    def _create_python_export_class(self, _class, delete=False):
        if _class is not None:
            ### Class
            name = str(bytecode.FormatClassToPython(_class.get_name()))
            if delete:
                delattr(self.C, name)
                return
            else:
                setattr(self.C, name, _class)
                setattr(_class, "M", ExportObject())
                setattr(_class, "F", ExportObject())

            self._create_python_export_methods(_class, delete)
            self._create_python_export_fields(_class, delete)

    def _create_python_export_methods(self, _class, delete):
        m = {}
        for method in _class.get_methods():
            if method.get_name() not in m:
                m[method.get_name()] = []
            m[method.get_name()].append(method)
            setattr(method, "XF", ExportObject())
            setattr(method, "XT", ExportObject())

        for i in m:
            if len(m[i]) == 1:
                j = m[i][0]
                name = str(bytecode.FormatNameToPython(j.get_name()))
                setattr(_class.M, name, j)
            else:
                for j in m[i]:
                    name = (
                        str(bytecode.FormatNameToPython(j.get_name())) + "_" +
                        str(bytecode.FormatDescriptorToPython(j.get_descriptor())))
                    setattr(_class.M, name, j)

    def _create_python_export_fields(self, _class, delete):
        f = {}
        for field in _class.get_fields():
            if field.get_name() not in f:
                f[field.get_name()] = []
            f[field.get_name()].append(field)
            setattr(field, "XR", ExportObject())
            setattr(field, "XW", ExportObject())

        for i in f:
            if len(f[i]) == 1:
                j = f[i][0]
                name = str(bytecode.FormatNameToPython(j.get_name()))
                setattr(_class.F, name, j)
            else:
                for j in f[i]:
                    name = str(bytecode.FormatNameToPython(j.get_name(
                    ))) + "_" + str(bytecode.FormatDescriptorToPython(
                        j.get_descriptor()))
                    setattr(_class.F, name, j)

    def get_BRANCH_DVM_OPCODES(self):
        """
        .. deprecated:: 3.4.0
            Will be removed!
        """
        warnings.warn("deprecated, this method will be removed!", DeprecationWarning)
        return BRANCH_DVM_OPCODES

    def get_determineNext(self):
        """
        .. deprecated:: 3.4.0
            Will be removed!
        """
        warnings.warn("deprecated, this method will be removed!", DeprecationWarning)
        return determineNext

    def get_determineException(self):
        """
        .. deprecated:: 3.4.0
            Will be removed!
        """
        warnings.warn("deprecated, this method will be removed!", DeprecationWarning)
        return determineException

    def set_decompiler(self, decompiler):
        self.CM.set_decompiler(decompiler)

    def disassemble(self, offset, size):
        """
        Disassembles a given offset in the DEX file

        :param offset: offset to disassemble in the file (from the beginning of the file)
        :type offset: int
        :param size:
        :type size:
        """
        for i in DCode(
                self.CM, offset, size,
                self.get_buff()[offset:offset + size]).get_instructions():
            yield i

    def _get_class_hierarchy(self):
        """
        Constructs a tree out of all the classes.
        The classes are added to this tree by their superclass.

        :return:
        :rtype: androguard.core.bytecode.Node
        """
        # Contains the class names as well as their running number
        ids = dict()
        present = dict()
        r_ids = dict()
        to_add = dict()
        els = []

        for current_class in self.get_classes():
            s_name = current_class.get_superclassname()[1:-1]
            c_name = current_class.get_name()[1:-1]

            if s_name not in ids:
                ids[s_name] = len(ids) + 1
                r_ids[ids[s_name]] = s_name

            if c_name not in ids:
                ids[c_name] = len(ids) + 1

            els.append([ids[c_name], ids[s_name], c_name])
            present[ids[c_name]] = True

        for i in els:
            if i[1] not in present:
                to_add[i[1]] = r_ids[i[1]]

        for i in to_add:
            els.append([i, 0, to_add[i]])

        treeMap = dict()
        Root = bytecode.Node(0, "Root")
        treeMap[Root.id] = Root
        for element in els:
            nodeId, parentId, title = element
            if not nodeId in treeMap:
                treeMap[nodeId] = bytecode.Node(nodeId, title)
            else:
                treeMap[nodeId].id = nodeId
                treeMap[nodeId].title = title

            if not parentId in treeMap:
                treeMap[parentId] = bytecode.Node(0, '')
            treeMap[parentId].children.append(treeMap[nodeId])

        return Root

    def print_classes_hierarchy(self):
        """
        .. deprecated:: 3.4.0
            Will be removed!
        """
        warnings.warn("deprecated, this method will be removed!", DeprecationWarning)

        def print_map(node, l, lvl=0):
            for n in node.children:
                if lvl == 0:
                    l.append("%s" % n.title)
                else:
                    l.append("{} {}".format('\t' * lvl, n.title))
                if len(n.children) > 0:
                    print_map(n, l, lvl + 1)

        l = []
        print_map(self._get_class_hierarchy(), l)
        return l

    def list_classes_hierarchy(self):
        """
        Get a tree structure of the classes.
        The parent is always the superclass.

        You can use pprint.pprint to print the
        dictionary in a pretty way.

        :return: a dict with all the classnames
        :rtype: dict
        """

        def print_map(node, l):
            if node.title not in l:
                l[node.title] = []

            for n in node.children:
                if len(n.children) > 0:
                    w = {n.title: []}
                    l[node.title].append(w)

                    print_map(n, w)
                else:
                    l[node.title].append(n.title)

        l = {}
        print_map(self._get_class_hierarchy(), l)

        return l

    def get_format(self):
        """
        .. deprecated:: 3.4.0
            Will be removed!
        """
        warnings.warn("deprecated, this method will be removed!", DeprecationWarning)
        objs = self.map_list.get_obj()

        h = {}
        index = {}
        self._get_objs(h, index, objs)

        return h, index

    def _get_objs(self, h, index, objs):
        """
        .. deprecated:: 3.4.0
            Will be removed!
        """
        warnings.warn("deprecated, this method will be removed!", DeprecationWarning)
        for i in objs:
            if isinstance(i, list):
                self._get_objs(h, index, i)
            else:
                try:
                    if i is not None:
                        h[i] = {}
                        index[i] = i.offset
                except AttributeError:
                    pass

                try:
                    if not isinstance(i, MapList):
                        next_objs = i.get_obj()
                        if isinstance(next_objs, list):
                            self._get_objs(h[i], index, next_objs)
                except AttributeError:
                    pass


class OdexHeaderItem:
    """
    This class can parse the odex header

    :param buff: a Buff object string which represents the odex dependencies
    """

    def __init__(self, buff):
        buff.set_idx(8)

        self.dex_offset = unpack("=I", buff.read(4))[0]
        self.dex_length = unpack("=I", buff.read(4))[0]
        self.deps_offset = unpack("=I", buff.read(4))[0]
        self.deps_length = unpack("=I", buff.read(4))[0]
        self.aux_offset = unpack("=I", buff.read(4))[0]
        self.aux_length = unpack("=I", buff.read(4))[0]
        self.flags = unpack("=I", buff.read(4))[0]
        self.padding = unpack("=I", buff.read(4))[0]

    def show(self):
        print("dex_offset:{:x} dex_length:{:x} deps_offset:{:x} deps_length:{:x} aux_offset:{:x} aux_length:{:x} flags:{:x}".format(
            self.dex_offset, self.dex_length, self.deps_offset,
            self.deps_length, self.aux_offset, self.aux_length, self.flags))

    def get_raw(self):
        return pack("=I", self.dex_offset) + \
               pack("=I", self.dex_length) + \
               pack("=I", self.deps_offset) + \
               pack("=I", self.deps_length) + \
               pack("=I", self.aux_offset) + \
               pack("=I", self.aux_length) + \
               pack("=I", self.flags) + \
               pack("=I", self.padding)


class OdexDependencies:
    """
    This class can parse the odex dependencies

    :param buff: a Buff object string which represents the odex dependencies
    """

    def __init__(self, buff):
        self.modification_time = unpack("=I", buff.read(4))[0]
        self.crc = unpack("=I", buff.read(4))[0]
        self.dalvik_build = unpack("=I", buff.read(4))[0]
        self.dependency_count = unpack("=I", buff.read(4))[0]
        self.dependencies = []
        self.dependency_checksums = []

        for i in range(0, self.dependency_count):
            string_length = unpack("=I", buff.read(4))[0]
            name_dependency = buff.read(string_length)
            self.dependencies.append(name_dependency)
            self.dependency_checksums.append(buff.read(20))

    def get_dependencies(self):
        """
            Return the list of dependencies

            :rtype: a list of strings
        """
        return self.dependencies

    def get_raw(self):
        dependencies = b""

        for idx, value in enumerate(self.dependencies):
            dependencies += pack("=I", len(value)) + \
                            pack("=%ds" % len(value), value) + \
                            pack("=20s", self.dependency_checksums[idx])

        return pack("=I", self.modification_time) + \
               pack("=I", self.crc) + \
               pack("=I", self.dalvik_build) + \
               pack("=I", self.dependency_count) + \
               dependencies


class DalvikOdexVMFormat(DalvikVMFormat):
    """
        This class can parse an odex file

        :param buff: a string which represents the odex file
        :param decompiler: associate a decompiler object to display the java source code
        :type buff: string
        :type decompiler: object

        :Example:
          DalvikOdexVMFormat( read("classes.odex") )
    """

    def _preload(self, buff):
        self.orig_buff = buff
        self.magic = buff[:8]
        if self.magic in (ODEX_FILE_MAGIC_35, ODEX_FILE_MAGIC_36, ODEX_FILE_MAGIC_37):
            self.odex_header = OdexHeaderItem(self)

            self.set_idx(self.odex_header.deps_offset)
            self.dependencies = OdexDependencies(self)

            self.padding = buff[self.odex_header.deps_offset +
                                self.odex_header.deps_length:]

            self.set_idx(self.odex_header.dex_offset)
            self.set_buff(self.read(self.odex_header.dex_length))
            self.set_idx(0)

    def save(self):
        """
          Do not use !
        """
        dex_raw = super().save()
        return self.magic + self.odex_header.get_raw(
        ) + dex_raw + self.dependencies.get_raw() + self.padding

    def get_buff(self):
        return self.magic + self.odex_header.get_raw() + super().get_buff() + self.dependencies.get_raw() + self.padding

    def get_dependencies(self):
        """
            Return the odex dependencies object

            :rtype: an OdexDependencies object
        """
        return self.dependencies

    def get_format_type(self):
        """
            Return the type

            :rtype: a string
        """
        return "ODEX"


def get_params_info(nb, proto):
    i_buffer = "# Parameters:\n"

    ret = proto.split(')')
    params = ret[0][1:].split()
    if params:
        i_buffer += "# - local registers: v%d...v%d\n" % (0,
                                                          nb - len(params) - 1)
        j = 0
        for i in range(nb - len(params), nb):
            i_buffer += "# - v%d:%s\n" % (i, get_type(params[j]))
            j += 1
    else:
        i_buffer += "# local registers: v%d...v%d\n" % (0, nb - 1)

    i_buffer += "#\n# - return:%s\n\n" % get_type(ret[1])

    return i_buffer


def get_bytecodes_method(dex_object, ana_object, method):
    mx = ana_object.get_method(method)
    return get_bytecodes_methodx(method, mx)


def get_bytecodes_methodx(method, mx):
    basic_blocks = mx.basic_blocks.gets()
    i_buffer = ""

    idx = 0
    nb = 0

    i_buffer += "# {}->{}{} [access_flags={}]\n#\n".format(
        method.get_class_name(), method.get_name(), method.get_descriptor(),
        method.get_access_flags_string())
    if method.code is not None:
        i_buffer += get_params_info(method.code.get_registers_size(),
                                    method.get_descriptor())

        for i in basic_blocks:
            bb_buffer = ""
            ins_buffer = ""

            bb_buffer += "%s : " % i.name

            # TODO using the generator object as a list again is not ideal...
            instructions = list(i.get_instructions())
            for ins in instructions:
                ins_buffer += "\t%-8d(%08x) " % (nb, idx)
                ins_buffer += "{:<20} {}".format(ins.get_name(), ins.get_output(idx))

                op_value = ins.get_op_value()
                if ins == instructions[-1] and i.childs != []:
                    # packed/sparse-switch
                    if (op_value == 0x2b or op_value == 0x2c) and len(i.childs) > 1:
                        values = i.get_special_ins(idx).get_values()
                        bb_buffer += "[ D:%s " % i.childs[0][2].name
                        bb_buffer += ' '.join(
                            "%d:%s" % (values[j], i.childs[j + 1][2].name)
                            for j in range(0, len(i.childs) - 1)) + " ]"
                    else:
                        # if len(i.childs) == 2:
                        #    i_buffer += "%s[ %s%s " % (branch_false_color, i.childs[0][2].name, branch_true_color))
                        #    print_fct(' '.join("%s" % c[2].name for c in i.childs[1:]) + " ]%s" % normal_color)
                        # else:
                        bb_buffer += "[ " + ' '.join("%s" % c[2].name for c in i.childs) + " ]"

                idx += ins.get_length()
                nb += 1

                ins_buffer += "\n"

            if i.get_exception_analysis() is not None:
                ins_buffer += "\t%s\n" % (i.exception_analysis.show_buff())

            i_buffer += bb_buffer + "\n" + ins_buffer + "\n"

    return i_buffer


class ExportObject:
    """
    Wrapper object for ipython exports
    """
    pass
