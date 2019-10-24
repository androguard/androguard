from enum import IntEnum
from collections import OrderedDict

# This file contains dictionaries used in the Dalvik Format.

# Used to identify different types of operands
class Kind(IntEnum):
    """
    This Enum is used to determine the kind of argument
    inside an Dalvik instruction.

    It is used to reference the actual item instead of the refernece index
    from the :class:`ClassManager` when disassembling the bytecode.
    """
    # Indicates a method reference
    METH = 0
    # Indicates that opcode argument is a string index
    STRING = 1
    # Indicates a field reference
    FIELD = 2
    # Indicates a type reference
    TYPE = 3
    # indicates a prototype reference
    PROTO = 9
    # indicates method reference and proto reference (invoke-polymorphic)
    METH_PROTO = 10
    # indicates call site item
    CALL_SITE = 11

    # TODO: not very well documented
    VARIES = 4
    # inline lined stuff
    INLINE_METHOD = 5
    # static linked stuff
    VTABLE_OFFSET = 6
    FIELD_OFFSET = 7
    RAW_STRING = 8


class Operand(IntEnum):
    """
    Enumeration used for the operand type of opcodes
    """
    REGISTER = 0
    LITERAL = 1
    RAW = 2
    OFFSET = 3
    # FIXME: KIND is used in combination with others, ie the Kind enum, therefore it is 0x100...
    # thus we could use an IntFlag here as well
    KIND = 0x100


# https://source.android.com/devices/tech/dalvik/dex-format#type-codes
class TypeMapItem(IntEnum):
    HEADER_ITEM = 0x0
    STRING_ID_ITEM = 0x1
    TYPE_ID_ITEM = 0x2
    PROTO_ID_ITEM = 0x3
    FIELD_ID_ITEM = 0x4
    METHOD_ID_ITEM = 0x5
    CLASS_DEF_ITEM = 0x6
    CALL_SITE_ITEM = 0x7  # New in DEX038
    METHOD_HANDLE_ITEM = 0x8  # New in DEX038
    MAP_LIST = 0x1000
    TYPE_LIST = 0x1001
    ANNOTATION_SET_REF_LIST = 0x1002
    ANNOTATION_SET_ITEM = 0x1003
    CLASS_DATA_ITEM = 0x2000
    CODE_ITEM = 0x2001
    STRING_DATA_ITEM = 0x2002
    DEBUG_INFO_ITEM = 0x2003
    ANNOTATION_ITEM = 0x2004
    ENCODED_ARRAY_ITEM = 0x2005
    ANNOTATIONS_DIRECTORY_ITEM = 0x2006

    @staticmethod
    def _get_dependencies():
        return OrderedDict([
            (TypeMapItem.HEADER_ITEM, set()),
            (TypeMapItem.STRING_ID_ITEM, {TypeMapItem.STRING_DATA_ITEM}),
            (TypeMapItem.TYPE_ID_ITEM, {TypeMapItem.STRING_ID_ITEM}),
            (TypeMapItem.PROTO_ID_ITEM, {TypeMapItem.STRING_ID_ITEM, TypeMapItem.TYPE_ID_ITEM, TypeMapItem.TYPE_LIST}),
            (TypeMapItem.FIELD_ID_ITEM, {TypeMapItem.STRING_ID_ITEM, TypeMapItem.TYPE_ID_ITEM}),
            (TypeMapItem.METHOD_ID_ITEM,
             {TypeMapItem.STRING_ID_ITEM, TypeMapItem.TYPE_ID_ITEM, TypeMapItem.PROTO_ID_ITEM}),
            (TypeMapItem.CLASS_DEF_ITEM,
             {TypeMapItem.TYPE_ID_ITEM, TypeMapItem.TYPE_LIST, TypeMapItem.STRING_ID_ITEM, TypeMapItem.DEBUG_INFO_ITEM,
              TypeMapItem.ANNOTATIONS_DIRECTORY_ITEM, TypeMapItem.CLASS_DATA_ITEM, TypeMapItem.ENCODED_ARRAY_ITEM}),
            (TypeMapItem.CALL_SITE_ITEM,
             {TypeMapItem.METHOD_HANDLE_ITEM, TypeMapItem.STRING_ID_ITEM, TypeMapItem.METHOD_ID_ITEM}),
            # TODO: check if this is correct
            (TypeMapItem.METHOD_HANDLE_ITEM, {TypeMapItem.FIELD_ID_ITEM, TypeMapItem.METHOD_ID_ITEM}),
            # TODO: check if this is correct
            (TypeMapItem.MAP_LIST, set()),
            (TypeMapItem.TYPE_LIST, {TypeMapItem.TYPE_ID_ITEM}),
            (TypeMapItem.ANNOTATION_SET_REF_LIST, {TypeMapItem.ANNOTATION_SET_ITEM}),
            (TypeMapItem.ANNOTATION_SET_ITEM, {TypeMapItem.ANNOTATION_ITEM}),
            (TypeMapItem.CLASS_DATA_ITEM, {TypeMapItem.FIELD_ID_ITEM, TypeMapItem.METHOD_ID_ITEM}),
            (TypeMapItem.CODE_ITEM, {TypeMapItem.DEBUG_INFO_ITEM, TypeMapItem.TYPE_ID_ITEM}),
            (TypeMapItem.STRING_DATA_ITEM, set()),
            (TypeMapItem.DEBUG_INFO_ITEM, {TypeMapItem.STRING_ID_ITEM, TypeMapItem.TYPE_ID_ITEM}),
            (TypeMapItem.ANNOTATION_ITEM,
             {TypeMapItem.PROTO_ID_ITEM, TypeMapItem.STRING_ID_ITEM, TypeMapItem.TYPE_ID_ITEM,
              TypeMapItem.FIELD_ID_ITEM, TypeMapItem.METHOD_ID_ITEM}),
            (TypeMapItem.ENCODED_ARRAY_ITEM,
             {TypeMapItem.PROTO_ID_ITEM, TypeMapItem.STRING_ID_ITEM, TypeMapItem.TYPE_ID_ITEM,
              TypeMapItem.FIELD_ID_ITEM, TypeMapItem.METHOD_ID_ITEM}),
            (TypeMapItem.ANNOTATIONS_DIRECTORY_ITEM,
             {TypeMapItem.FIELD_ID_ITEM, TypeMapItem.METHOD_ID_ITEM, TypeMapItem.ANNOTATION_SET_ITEM})
        ])

    @staticmethod
    def determine_load_order():
        dependencies = TypeMapItem._get_dependencies()
        ordered = dict()
        while dependencies:
            found_next = False
            for type_name, unloaded in dependencies.items():
                if not unloaded:
                    ordered[type_name] = len(ordered)
                    found_next = True
                    break
            if found_next is False:
                raise Exception('recursive loading dependency')
            dependencies.pop(type_name)
            for unloaded in dependencies.values():
                unloaded.discard(type_name)
        return ordered

# https://source.android.com/devices/tech/dalvik/dex-format#access-flags
ACCESS_FLAGS = {
    0x1: 'public',
    0x2: 'private',
    0x4: 'protected',
    0x8: 'static',
    0x10: 'final',
    0x20: 'synchronized',
    0x40: 'bridge',
    0x80: 'varargs',
    0x100: 'native',
    0x200: 'interface',
    0x400: 'abstract',
    0x800: 'strictfp',
    0x1000: 'synthetic',
    0x4000: 'enum',
    0x8000: 'unused',
    0x10000: 'constructor',
    0x20000: 'synchronized',
}

# https://source.android.com/devices/tech/dalvik/dex-format#typedescriptor
TYPE_DESCRIPTOR = {
    'V': 'void',
    'Z': 'boolean',
    'B': 'byte',
    'S': 'short',
    'C': 'char',
    'I': 'int',
    'J': 'long',
    'F': 'float',
    'D': 'double',
}

