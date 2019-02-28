from enum import IntEnum

# This file contains dictionaries used in the Dalvik Format.

# https://source.android.com/devices/tech/dalvik/dex-format#type-codes
class TypeMapItem(IntEnum):
    HEADER_ITEM = 0x0
    STRING_ID_ITEM = 0x1
    TYPE_ID_ITEM = 0x2
    PROTO_ID_ITEM = 0x3
    FIELD_ID_ITEM = 0x4
    METHOD_ID_ITEM = 0x5
    CLASS_DEF_ITEM = 0x6
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

