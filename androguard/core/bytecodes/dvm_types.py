# This file contains dictionaries used in the Dalvik Format.

# https://source.android.com/devices/tech/dalvik/dex-format#type-codes
TYPE_MAP_ITEM = {
    0x0: "TYPE_HEADER_ITEM",
    0x1: "TYPE_STRING_ID_ITEM",
    0x2: "TYPE_TYPE_ID_ITEM",
    0x3: "TYPE_PROTO_ID_ITEM",
    0x4: "TYPE_FIELD_ID_ITEM",
    0x5: "TYPE_METHOD_ID_ITEM",
    0x6: "TYPE_CLASS_DEF_ITEM",
    0x1000: "TYPE_MAP_LIST",
    0x1001: "TYPE_TYPE_LIST",
    0x1002: "TYPE_ANNOTATION_SET_REF_LIST",
    0x1003: "TYPE_ANNOTATION_SET_ITEM",
    0x2000: "TYPE_CLASS_DATA_ITEM",
    0x2001: "TYPE_CODE_ITEM",
    0x2002: "TYPE_STRING_DATA_ITEM",
    0x2003: "TYPE_DEBUG_INFO_ITEM",
    0x2004: "TYPE_ANNOTATION_ITEM",
    0x2005: "TYPE_ENCODED_ARRAY_ITEM",
    0x2006: "TYPE_ANNOTATIONS_DIRECTORY_ITEM",
}

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

