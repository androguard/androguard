from __future__ import division
from __future__ import print_function

from builtins import chr
from builtins import range
from builtins import object
from androguard.core import bytecode

from androguard.core.resources import public

from struct import pack, unpack
from xml.sax.saxutils import escape
import collections
from collections import defaultdict

import lxml.sax
from lxml import etree
import logging

log = logging.getLogger("androguard.axml")


################################## AXML FORMAT ########################################
# Translated from
# http://code.google.com/p/android4me/source/browse/src/android/content/res/AXmlResourceParser.java

# Flags in the STRING Section
SORTED_FLAG = 1 << 0
UTF8_FLAG = 1 << 8


class StringBlock(object):
    """
    StringBlock is a CHUNK inside an AXML File
    It contains all strings, which are used by referecing to ID's

    TODO might migrate this block into the ARSCParser, as it it not a "special" block but a normal tag.
    """
    def __init__(self, buff, header):
        self._cache = {}
        self.header = header
        # We already read the header (which was chunk_type and chunk_size
        # Now, we read the string_count:
        self.stringCount = unpack('<i', buff.read(4))[0]
        # style_count
        self.styleOffsetCount = unpack('<i', buff.read(4))[0]

        # flags
        self.flags = unpack('<i', buff.read(4))[0]
        self.m_isUTF8 = ((self.flags & UTF8_FLAG) != 0)

        # string_pool_offset
        # The string offset is counted from the beginning of the string section
        self.stringsOffset = unpack('<i', buff.read(4))[0]
        # style_pool_offset
        # The styles offset is counted as well from the beginning of the string section
        self.stylesOffset = unpack('<i', buff.read(4))[0]

        # Check if they supplied a stylesOffset even if the count is 0:
        if self.styleOffsetCount == 0 and self.stylesOffset > 0:
            log.warning("Styles Offset given, but styleCount is zero.")

        self.m_stringOffsets = []
        self.m_styleOffsets = []
        self.m_charbuff = ""
        self.m_styles = []

        # Next, there is a list of string following
        # This is only a list of offsets (4 byte each)
        for i in range(0, self.stringCount):
            self.m_stringOffsets.append(unpack('<i', buff.read(4))[0])

        # And a list of styles
        # again, a list of offsets
        for i in range(0, self.styleOffsetCount):
            self.m_styleOffsets.append(unpack('<i', buff.read(4))[0])


        # FIXME it is probably better to parse n strings and not calculate the size
        size = self.header.size - self.stringsOffset

        # if there are styles as well, we do not want to read them too.
        # Only read them, if no
        if self.stylesOffset != 0 and self.styleOffsetCount != 0:
            size = self.stylesOffset - self.stringsOffset

        # FIXME unaligned
        if (size % 4) != 0:
            log.warning("Size of strings is not aligned by four bytes.")

        self.m_charbuff = buff.read(size)

        if self.stylesOffset != 0 and self.styleOffsetCount != 0:
            size = self.header.size - self.stylesOffset

            # FIXME unaligned
            if (size % 4) != 0:
                log.warning("Size of styles is not aligned by four bytes.")

            for i in range(0, size // 4):
                self.m_styles.append(unpack('<i', buff.read(4))[0])

    def getString(self, idx):
        if idx in self._cache:
            return self._cache[idx]

        if idx < 0 or not self.m_stringOffsets or idx >= len(
                self.m_stringOffsets):
            return ""

        offset = self.m_stringOffsets[idx]

        if self.m_isUTF8:
            self._cache[idx] = self.decode8(offset)
        else:
            self._cache[idx] = self.decode16(offset)

        return self._cache[idx]

    def getStyle(self, idx):
        # FIXME
        return self.m_styles[idx]

    def decode8(self, offset):
        str_len, skip = self.decodeLength(offset, 1)
        offset += skip

        encoded_bytes, skip = self.decodeLength(offset, 1)
        offset += skip

        data = self.m_charbuff[offset: offset + encoded_bytes]

        return self.decode_bytes(data, 'utf-8', str_len)

    def decode16(self, offset):
        str_len, skip = self.decodeLength(offset, 2)
        offset += skip

        encoded_bytes = str_len * 2

        data = self.m_charbuff[offset: offset + encoded_bytes]

        return self.decode_bytes(data, 'utf-16', str_len)

    def decode_bytes(self, data, encoding, str_len):
        string = data.decode(encoding, 'replace')
        if len(string) != str_len:
            log.warning("invalid decoded string length")
        return string

    def decodeLength(self, offset, sizeof_char):
        length = self.m_charbuff[offset]

        sizeof_2chars = sizeof_char << 1
        fmt_chr = 'B' if sizeof_char == 1 else 'H'
        fmt = "<2" + fmt_chr

        length1, length2 = unpack(fmt, self.m_charbuff[offset:(offset + sizeof_2chars)])

        highbit = 0x80 << (8 * (sizeof_char - 1))

        if (length & highbit) != 0:
            return ((length1 & ~highbit) << (8 * sizeof_char)) | length2, sizeof_2chars
        else:
            return length1, sizeof_char

    def show(self):
        print("StringBlock(%x, %x, %x, %x, %x, %x" % (
            self.start,
            self.header,
            self.header_size,
            self.chunkSize,
            self.stringsOffset,
            self.flags))
        for i in range(0, len(self.m_stringOffsets)):
            print(i, repr(self.getString(i)))


# Position of the fields inside an attribute
ATTRIBUTE_IX_NAMESPACE_URI = 0
ATTRIBUTE_IX_NAME = 1
ATTRIBUTE_IX_VALUE_STRING = 2
ATTRIBUTE_IX_VALUE_TYPE = 3
ATTRIBUTE_IX_VALUE_DATA = 4
ATTRIBUTE_LENGHT = 5

# Chunk Headers
CHUNK_AXML_FILE = 0x00080003
CHUNK_STRING = 0x001C0001
CHUNK_RESOURCEIDS = 0x00080180
CHUNK_XML_FIRST = 0x00100100
CHUNK_XML_START_NAMESPACE = 0x00100100
CHUNK_XML_END_NAMESPACE = 0x00100101
CHUNK_XML_START_TAG = 0x00100102
CHUNK_XML_END_TAG = 0x00100103
CHUNK_XML_TEXT = 0x00100104
CHUNK_XML_LAST = 0x00100104

START_DOCUMENT = 0
END_DOCUMENT = 1
START_TAG = 2
END_TAG = 3
TEXT = 4


class AXMLParser(object):
    def __init__(self, raw_buff):
        self.reset()

        self.valid_axml = True
        self.axml_tampered = False
        self.packerwarning = False
        self.buff = bytecode.BuffHandle(raw_buff)

        axml_file, = unpack('<L', self.buff.read(4))

        if axml_file != CHUNK_AXML_FILE:
            # It looks like the header is wrong.
            # need some other checks.
            # We noted, that a some of files start with 0x0008NNNN, where NNNN is some random number
            if axml_file >> 16 == 0x0008:
                self.axml_tampered = True
                log.warning("AXML file has an unusual header, most malwares like doing such stuff to anti androguard! But we try to parse it anyways. Header: 0x{:08x}".format(axml_file))
            else:
                self.valid_axml = False
                log.error("Not a valid AXML file. Header 0x{:08x}".format(axml_file))
                return

        # Next is the filesize
        self.filesize, = unpack('<L', self.buff.read(4))
        assert self.filesize <= self.buff.size(), "Declared filesize does not match real size: {} vs {}".format(self.filesize, self.buff.size())

        # Now we parse the STRING POOL
        header = ARSCHeader(self.buff) # read 8 byte = String header + chunk_size
        assert header.type == RES_STRING_POOL_TYPE, "Expected String Pool header, got %x" % header.type

        self.sb = StringBlock(self.buff, header)

        self.m_resourceIDs = []
        self.m_prefixuri = {}
        self.m_uriprefix = defaultdict(list)
        # Contains a list of current prefix/uri pairs
        self.m_prefixuriL = []
        # Store which namespaces are already printed
        self.visited_ns = []

    def is_valid(self):
        return self.valid_axml

    def reset(self):
        self.m_event = -1
        self.m_lineNumber = -1
        self.m_name = -1
        self.m_namespaceUri = -1
        self.m_attributes = []
        self.m_idAttribute = -1
        self.m_classAttribute = -1
        self.m_styleAttribute = -1

    def __next__(self):
        self.doNext()
        return self.m_event

    def doNext(self):
        if self.m_event == END_DOCUMENT:
            return

        event = self.m_event

        self.reset()
        while True:
            chunkType = -1
            # General notes:
            # * chunkSize is from start of chunk, including the tag type

            # Fake END_DOCUMENT event.
            if event == END_TAG:
                pass

            # START_DOCUMENT
            if event == START_DOCUMENT:
                chunkType = CHUNK_XML_START_TAG
            else:
                # Stop at the declared filesize or at the end of the file
                if self.buff.end() or self.buff.get_idx() == self.filesize:
                    self.m_event = END_DOCUMENT
                    break
                chunkType = unpack('<L', self.buff.read(4))[0]

            # Parse ResourceIDs. This chunk is after the String section
            if chunkType == CHUNK_RESOURCEIDS:
                chunkSize = unpack('<L', self.buff.read(4))[0]

                # Check size: < 8 bytes mean that the chunk is not complete
                # Should be aligned to 4 bytes.
                if chunkSize < 8 or chunkSize % 4 != 0:
                    log.warning("Invalid chunk size in chunk RESOURCEIDS")

                for i in range(0, (chunkSize // 4) - 2):
                    self.m_resourceIDs.append(unpack('<L', self.buff.read(4))[0])

                continue

            # FIXME, unknown chunk types might cause problems
            if chunkType < CHUNK_XML_FIRST or chunkType > CHUNK_XML_LAST:
                log.warning("invalid chunk type 0x{:08x}".format(chunkType))

            # Fake START_DOCUMENT event.
            if chunkType == CHUNK_XML_START_TAG and event == -1:
                self.m_event = START_DOCUMENT
                break

            # After the chunk_type, there are always 3 fields for the remaining tags we need to parse:
            # Chunk Size (we do not need it)
            # TODO for sanity checks, we should use it and check if the chunks are correct in size
            self.buff.read(4)
            # Line Number
            self.m_lineNumber = unpack('<L', self.buff.read(4))[0]
            # Comment_Index (usually 0xFFFFFFFF, we do not need it)
            self.buff.read(4)

            # Now start to parse the field

            # There are five (maybe more) types of Chunks:
            # * START_NAMESPACE
            # * END_NAMESPACE
            # * START_TAG
            # * END_TAG
            # * TEXT
            if chunkType == CHUNK_XML_START_NAMESPACE or chunkType == CHUNK_XML_END_NAMESPACE:
                if chunkType == CHUNK_XML_START_NAMESPACE:
                    prefix = unpack('<L', self.buff.read(4))[0]
                    uri = unpack('<L', self.buff.read(4))[0]

                    # FIXME We will get a problem here, if the same uri is used with different prefixes!
                    # prefix --> uri is a 1:1 mapping
                    self.m_prefixuri[prefix] = uri
                    # but uri --> prefix is a 1:n mapping!
                    self.m_uriprefix[uri].append(prefix)
                    self.m_prefixuriL.append((prefix, uri))
                    self.ns = uri

                    # Workaround for closing tags
                    if (uri, prefix) in self.visited_ns:
                        self.visited_ns.remove((uri, prefix))
                else:
                    self.ns = -1
                    # END_PREFIX contains again prefix and uri field
                    prefix, = unpack('<L', self.buff.read(4))
                    uri, = unpack('<L', self.buff.read(4))

                    # We can then remove those from the prefixuriL
                    if (prefix, uri) in self.m_prefixuriL:
                        self.m_prefixuriL.remove((prefix, uri))

                    # We also remove the entry from prefixuri and uriprefix:
                    if prefix in self.m_prefixuri:
                        del self.m_prefixuri[prefix]
                    if uri in self.m_uriprefix:
                        self.m_uriprefix[uri].remove(prefix)
                    # Need to remove them from visisted namespaces as well, as it might pop up later
                    # FIXME we need to remove it also if we leave a tag which closes it namespace
                    # Workaround for now: remove it on a START_NAMESPACE tag
                    if (uri, prefix) in self.visited_ns:
                        self.visited_ns.remove((uri, prefix))

                    else:
                        log.warning("Reached a NAMESPACE_END without having the namespace stored before? Prefix ID: {}, URI ID: {}".format(prefix, uri))

                continue

            # START_TAG is the start of a new tag.
            if chunkType == CHUNK_XML_START_TAG:
                # The TAG consists of some fields:
                # * (chunk_size, line_number, comment_index - we read before)
                # * namespace_uri
                # * name
                # * flags
                # * attribute_count
                # * class_attribute
                # After that, there are two lists of attributes, 20 bytes each

                self.m_namespaceUri = unpack('<L', self.buff.read(4))[0]
                self.m_name = unpack('<L', self.buff.read(4))[0]

                # FIXME
                self.buff.read(4)  # flags

                attributeCount = unpack('<L', self.buff.read(4))[0]
                self.m_idAttribute = (attributeCount >> 16) - 1
                attributeCount = attributeCount & 0xFFFF
                self.m_classAttribute = unpack('<L', self.buff.read(4))[0]
                self.m_styleAttribute = (self.m_classAttribute >> 16) - 1

                self.m_classAttribute = (self.m_classAttribute & 0xFFFF) - 1

                # Now, we parse the attributes.
                # Each attribute has 5 fields of 4 byte
                for i in range(0, attributeCount * ATTRIBUTE_LENGHT):
                    # Each field is linearly parsed into the array
                    self.m_attributes.append(unpack('<L', self.buff.read(4))[0])

                # Then there are class_attributes
                for i in range(ATTRIBUTE_IX_VALUE_TYPE, len(self.m_attributes),
                               ATTRIBUTE_LENGHT):
                    self.m_attributes[i] = self.m_attributes[i] >> 24

                self.m_event = START_TAG
                break

            if chunkType == CHUNK_XML_END_TAG:
                self.m_namespaceUri = unpack('<L', self.buff.read(4))[0]
                self.m_name = unpack('<L', self.buff.read(4))[0]
                self.m_event = END_TAG
                break

            if chunkType == CHUNK_XML_TEXT:
                # TODO we do not know what the TEXT field does...
                self.m_name = unpack('<L', self.buff.read(4))[0]

                # FIXME
                # Raw_value
                self.buff.read(4)
                # typed_value, is an enum
                self.buff.read(4)

                self.m_event = TEXT
                break

    def getPrefixByUri(self, uri):
        # As uri --> prefix is 1:n mapping,
        # We will just return the first one we match.
        if uri not in self.m_uriprefix:
            return -1
        else:
            if len(self.m_uriprefix[uri]) == 0:
                return -1
            return self.m_uriprefix[uri][0]

    def getPrefix(self):
        # The default is, that the namespaceUri is 0xFFFFFFFF
        # Then we know, there is none
        if self.m_namespaceUri == 0xFFFFFFFF:
            return u''

        # FIXME this could be problematic. Need to find the correct namespace prefix
        if self.m_namespaceUri in self.m_uriprefix:
            candidate = self.m_uriprefix[self.m_namespaceUri][0]
            try:
                return self.sb.getString(candidate)
            except KeyError:
                return u''
        else:
            return u''

    def getName(self):
        if self.m_name == -1 or (self.m_event != START_TAG and
                                         self.m_event != END_TAG):
            return u''

        return self.sb.getString(self.m_name)

    def getText(self):
        if self.m_name == -1 or self.m_event != TEXT:
            return u''

        return self.sb.getString(self.m_name)

    def getNamespacePrefix(self, pos):
        prefix = self.m_prefixuriL[pos][0]
        return self.sb.getString(prefix)

    def getNamespaceUri(self, pos):
        uri = self.m_prefixuriL[pos][1]
        return self.sb.getString(uri)

    def getXMLNS(self):
        buff = ""
        for prefix, uri in self.m_prefixuri.items():
            if (uri, prefix) not in self.visited_ns:
                prefix_str = self.sb.getString(prefix)
                prefix_uri = self.sb.getString(self.m_prefixuri[prefix])
                # FIXME Packers like Liapp use empty uri to fool XML Parser
                # FIXME they also mess around with the Manifest, thus it can not be parsed easily
                if prefix_uri == '':
                    log.warning("Empty Namespace URI for Namespace {}.".format(prefix_str))
                    self.packerwarning = True

                # if prefix is (null), which is indicated by an empty str, then do not print :
                if prefix_str != '':
                    prefix_str = ":" + prefix_str
                buff += 'xmlns{}="{}"\n'.format(prefix_str, prefix_uri)
                self.visited_ns.append((uri, prefix))
        return buff

    def getNamespaceCount(self, pos):
        pass

    def getAttributeOffset(self, index):
        # FIXME
        if self.m_event != START_TAG:
            log.warning("Current event is not START_TAG.")

        offset = index * 5
        # FIXME
        if offset >= len(self.m_attributes):
            log.warning("Invalid attribute index")

        return offset

    def getAttributeCount(self):
        if self.m_event != START_TAG:
            return -1

        return len(self.m_attributes) // ATTRIBUTE_LENGHT

    def getAttributePrefix(self, index):
        offset = self.getAttributeOffset(index)
        uri = self.m_attributes[offset + ATTRIBUTE_IX_NAMESPACE_URI]

        prefix = self.getPrefixByUri(uri)

        if prefix == -1:
            return ""

        return self.sb.getString(prefix)

    def getAttributeName(self, index):
        offset = self.getAttributeOffset(index)
        name = self.m_attributes[offset + ATTRIBUTE_IX_NAME]

        if name == -1:
            return ""

        res = self.sb.getString(name)
        # If the result is a (null) string, we need to look it up.
        if not res:
            attr = self.m_resourceIDs[name]
            if attr in public.SYSTEM_RESOURCES['attributes']['inverse']:
                res = 'android:' + public.SYSTEM_RESOURCES['attributes']['inverse'][
                    attr
                ]
            else:
                # Attach the HEX Number, so for multiple missing attributes we do not run
                # into problems.
                res = 'android:UNKNOWN_SYSTEM_ATTRIBUTE_{:08x}'.format(attr)

        return res

    def getAttributeValueType(self, index):
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset + ATTRIBUTE_IX_VALUE_TYPE]

    def getAttributeValueData(self, index):
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset + ATTRIBUTE_IX_VALUE_DATA]

    def getAttributeValue(self, index):
        """
        This function is only used to look up strings
        All other work is made by format_value
        # FIXME should unite those functions
        :param index:
        :return:
        """
        offset = self.getAttributeOffset(index)
        valueType = self.m_attributes[offset + ATTRIBUTE_IX_VALUE_TYPE]
        if valueType == TYPE_STRING:
            valueString = self.m_attributes[offset + ATTRIBUTE_IX_VALUE_STRING]
            return self.sb.getString(valueString)
        return ""


# FIXME there are duplicates and missing values...
TYPE_NULL = 0
TYPE_REFERENCE = 1
TYPE_ATTRIBUTE = 2
TYPE_STRING = 3
TYPE_FLOAT = 4
TYPE_DIMENSION = 5
TYPE_FRACTION = 6
TYPE_FIRST_INT = 16
TYPE_INT_DEC = 16
TYPE_INT_HEX = 17
TYPE_INT_BOOLEAN = 18
TYPE_FIRST_COLOR_INT = 28
TYPE_INT_COLOR_ARGB8 = 28
TYPE_INT_COLOR_RGB8 = 29
TYPE_INT_COLOR_ARGB4 = 30
TYPE_INT_COLOR_RGB4 = 31
TYPE_LAST_COLOR_INT = 31
TYPE_LAST_INT = 31

TYPE_TABLE = {
    TYPE_ATTRIBUTE: "attribute",
    TYPE_DIMENSION: "dimension",
    TYPE_FLOAT: "float",
    TYPE_FRACTION: "fraction",
    TYPE_INT_BOOLEAN: "int_boolean",
    TYPE_INT_COLOR_ARGB4: "int_color_argb4",
    TYPE_INT_COLOR_ARGB8: "int_color_argb8",
    TYPE_INT_COLOR_RGB4: "int_color_rgb4",
    TYPE_INT_COLOR_RGB8: "int_color_rgb8",
    TYPE_INT_DEC: "int_dec",
    TYPE_INT_HEX: "int_hex",
    TYPE_NULL: "null",
    TYPE_REFERENCE: "reference",
    TYPE_STRING: "string",
}

RADIX_MULTS = [0.00390625, 3.051758E-005, 1.192093E-007, 4.656613E-010]
DIMENSION_UNITS = ["px", "dip", "sp", "pt", "in", "mm"]
FRACTION_UNITS = ["%", "%p"]

COMPLEX_UNIT_MASK = 15


def complexToFloat(xcomplex):
    return float(xcomplex & 0xFFFFFF00) * RADIX_MULTS[(xcomplex >> 4) & 3]


def long2int(l):
    if l > 0x7fffffff:
        l = (0x7fffffff & l) - 0x80000000
    return l


def long2str(l):
    """Convert an integer to a string."""
    if type(l) not in (types.IntType, types.LongType):
        raise ValueError('the input must be an integer')

    if l < 0:
        raise ValueError('the input must be greater than 0')
    s = ''
    while l:
        s = s + chr(l & 255)
        l >>= 8

    return s


def str2long(s):
    """Convert a string to a long integer."""
    if type(s) not in (types.StringType, types.UnicodeType):
        raise ValueError('the input must be a string')

    l = 0
    for i in s:
        l <<= 8
        l |= ord(i)

    return l


def getPackage(i):
    if i >> 24 == 1:
        return "android:"
    return ""


def format_value(_type, _data, lookup_string=lambda ix: "<string>"):
    if _type == TYPE_STRING:
        return lookup_string(_data)

    elif _type == TYPE_ATTRIBUTE:
        return "?%s%08X" % (getPackage(_data), _data)

    elif _type == TYPE_REFERENCE:
        return "@%s%08X" % (getPackage(_data), _data)

    elif _type == TYPE_FLOAT:
        return "%f" % unpack("=f", pack("=L", _data))[0]

    elif _type == TYPE_INT_HEX:
        return "0x%08X" % _data

    elif _type == TYPE_INT_BOOLEAN:
        if _data == 0:
            return "false"
        return "true"

    elif _type == TYPE_DIMENSION:
        return "%f%s" % (complexToFloat(_data), DIMENSION_UNITS[_data & COMPLEX_UNIT_MASK])

    elif _type == TYPE_FRACTION:
        return "%f%s" % (complexToFloat(_data) * 100, FRACTION_UNITS[_data & COMPLEX_UNIT_MASK])

    elif TYPE_FIRST_COLOR_INT <= _type <= TYPE_LAST_COLOR_INT:
        return "#%08X" % _data

    elif TYPE_FIRST_INT <= _type <= TYPE_LAST_INT:
        return "%d" % long2int(_data)

    return "<0x%X, type 0x%02X>" % (_data, _type)


class AXMLPrinter(object):
    """
    Converter for AXML Files into a XML string
    """
    def __init__(self, raw_buff):
        self.axml = AXMLParser(raw_buff)
        self.xmlns = False

        self.buff = u''

        while True and self.axml.is_valid():
            _type = next(self.axml)

            if _type == START_DOCUMENT:
                self.buff += u'<?xml version="1.0" encoding="utf-8"?>\n'
            elif _type == START_TAG:
                self.buff += u'<' + self.getPrefix(self.axml.getPrefix()) + self.axml.getName() + u'\n'
                self.buff += self.axml.getXMLNS()

                for i in range(0, self.axml.getAttributeCount()):
                    prefix = self.getPrefix(self.axml.getAttributePrefix(i))
                    name = self.axml.getAttributeName(i)
                    value = self._escape(self.getAttributeValue(i))

                    # If the name is a system name AND the prefix is set, we have a problem.
                    # FIXME we are not sure how this happens, but a quick fix is to remove the prefix if it already in the name
                    if name.startswith(prefix):
                        prefix = u''

                    self.buff += u'{}{}="{}"\n'.format(prefix, name, value)

                self.buff += u'>\n'

            elif _type == END_TAG:
                self.buff += u"</%s%s>\n" % (
                    self.getPrefix(self.axml.getPrefix()), self.axml.getName())

            elif _type == TEXT:
                self.buff += u"%s\n" % self._escape(self.axml.getText())
            elif _type == END_DOCUMENT:
                break

    # pleed patch
    # FIXME should this be applied for strings directly?
    def _escape(self, s):
        # FIXME Strings might contain null bytes. Should they be removed?
        # We guess so, as normaly the string would terminate there...?!
        s = s.replace("\x00", "")
        # Other HTML Conversions
        s = s.replace("&", "&amp;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&apos;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        return escape(s)

    def is_packed(self):
        """
        Return True if we believe that the AXML file is packed
        If it is, we can not be sure that the AXML file can be read by a XML Parser

        :return: boolean
        """
        return self.axml.packerwarning

    def get_buff(self):
        return self.buff.encode('utf-8')

    def get_xml(self):
        """
        Get the XML as an UTF-8 string

        :return: str
        """
        return etree.tostring(self.get_xml_obj(), encoding="utf-8", pretty_print=True)

    def get_xml_obj(self):
        """
        Get the XML as an ElementTree object

        :return: :class:`~lxml.etree.Element`
        """
        parser = etree.XMLParser(recover=True, resolve_entities=False)
        tree = etree.fromstring(self.get_buff(), parser=parser)
        return tree

    def getPrefix(self, prefix):
        if prefix is None or len(prefix) == 0:
            return u''

        return prefix + u':'

    def getAttributeValue(self, index):
        """
        Wrapper function for format_value
        to resolve the actual value of an attribute in a tag
        :param index:
        :return:
        """
        _type = self.axml.getAttributeValueType(index)
        _data = self.axml.getAttributeValueData(index)

        return format_value(_type, _data, lambda _: self.axml.getAttributeValue(index))


# Constants for ARSC Files
RES_NULL_TYPE = 0x0000
RES_STRING_POOL_TYPE = 0x0001
RES_TABLE_TYPE = 0x0002
RES_XML_TYPE = 0x0003

# Chunk types in RES_XML_TYPE
RES_XML_FIRST_CHUNK_TYPE = 0x0100
RES_XML_START_NAMESPACE_TYPE = 0x0100
RES_XML_END_NAMESPACE_TYPE = 0x0101
RES_XML_START_ELEMENT_TYPE = 0x0102
RES_XML_END_ELEMENT_TYPE = 0x0103
RES_XML_CDATA_TYPE = 0x0104
RES_XML_LAST_CHUNK_TYPE = 0x017f

# This contains a uint32_t array mapping strings in the string
# pool back to resource identifiers.  It is optional.
RES_XML_RESOURCE_MAP_TYPE = 0x0180

# Chunk types in RES_TABLE_TYPE
RES_TABLE_PACKAGE_TYPE = 0x0200
RES_TABLE_TYPE_TYPE = 0x0201
RES_TABLE_TYPE_SPEC_TYPE = 0x0202
RES_TABLE_LIBRARY_TYPE = 0x0203

ACONFIGURATION_MCC = 0x0001
ACONFIGURATION_MNC = 0x0002
ACONFIGURATION_LOCALE = 0x0004
ACONFIGURATION_TOUCHSCREEN = 0x0008
ACONFIGURATION_KEYBOARD = 0x0010
ACONFIGURATION_KEYBOARD_HIDDEN = 0x0020
ACONFIGURATION_NAVIGATION = 0x0040
ACONFIGURATION_ORIENTATION = 0x0080
ACONFIGURATION_DENSITY = 0x0100
ACONFIGURATION_SCREEN_SIZE = 0x0200
ACONFIGURATION_VERSION = 0x0400
ACONFIGURATION_SCREEN_LAYOUT = 0x0800
ACONFIGURATION_UI_MODE = 0x1000


class ARSCParser(object):
    """
    Parser for resource.arsc files
    """
    def __init__(self, raw_buff):
        self.analyzed = False
        self._resolved_strings = None
        self.buff = bytecode.BuffHandle(raw_buff)

        self.header = ARSCHeader(self.buff)
        self.packageCount = unpack('<i', self.buff.read(4))[0]

        self.packages = {}
        self.values = {}
        self.resource_values = collections.defaultdict(collections.defaultdict)
        self.resource_configs = collections.defaultdict(lambda: collections.defaultdict(set))
        self.resource_keys = collections.defaultdict(
            lambda: collections.defaultdict(collections.defaultdict))
        self.stringpool_main = None

        # skip to the start of the first chunk
        self.buff.set_idx(self.header.start + self.header.header_size)

        data_end = self.header.start + self.header.size

        while self.buff.get_idx() <= data_end - ARSCHeader.SIZE:
            res_header = ARSCHeader(self.buff)

            if res_header.start + res_header.size > data_end:
                # this inner chunk crosses the boundary of the table chunk
                break

            if res_header.type == RES_STRING_POOL_TYPE and not self.stringpool_main:
                self.stringpool_main = StringBlock(self.buff, res_header)

            elif res_header.type == RES_TABLE_PACKAGE_TYPE:
                assert len(self.packages) < self.packageCount, "Got more packages than expected"

                current_package = ARSCResTablePackage(self.buff, res_header)
                package_name = current_package.get_name()
                package_data_end = res_header.start + res_header.size

                self.packages[package_name] = []

                # After the Header, we have the resource type symbol table
                self.buff.set_idx(current_package.header.start + current_package.typeStrings)
                type_sp_header = ARSCHeader(self.buff)
                assert type_sp_header.type == RES_STRING_POOL_TYPE, \
                    "Expected String Pool header, got %x" % type_sp_header.type
                mTableStrings = StringBlock(self.buff, type_sp_header)

                # Next, we should have the resource key symbol table
                self.buff.set_idx(current_package.header.start + current_package.keyStrings)
                key_sp_header = ARSCHeader(self.buff)
                assert key_sp_header.type == RES_STRING_POOL_TYPE, \
                    "Expected String Pool header, got %x" % key_sp_header.type
                mKeyStrings = StringBlock(self.buff, key_sp_header)

                # Add them to the dict of read packages
                self.packages[package_name].append(current_package)
                self.packages[package_name].append(mTableStrings)
                self.packages[package_name].append(mKeyStrings)

                pc = PackageContext(current_package, self.stringpool_main,
                                    mTableStrings, mKeyStrings)

                # skip to the first header in this table package chunk
                # FIXME is this correct? We have already read the first two sections!
                # self.buff.set_idx(res_header.start + res_header.header_size)
                # this looks more like we want: (???)
                self.buff.set_idx(res_header.start + res_header.header_size + type_sp_header.size + key_sp_header.size)

                # Read all other headers
                while self.buff.get_idx() <= package_data_end - ARSCHeader.SIZE:
                    pkg_chunk_header = ARSCHeader(self.buff)
                    log.debug("Found a header: {}".format(pkg_chunk_header))
                    if pkg_chunk_header.start + pkg_chunk_header.size > package_data_end:
                        # we are way off the package chunk; bail out
                        break

                    self.packages[package_name].append(pkg_chunk_header)

                    if pkg_chunk_header.type == RES_TABLE_TYPE_SPEC_TYPE:
                        self.packages[package_name].append(ARSCResTypeSpec(self.buff, pc))

                    elif pkg_chunk_header.type == RES_TABLE_TYPE_TYPE:
                        a_res_type = ARSCResType(self.buff, pc)
                        self.packages[package_name].append(a_res_type)
                        self.resource_configs[package_name][a_res_type].add(a_res_type.config)

                        log.debug("Config: {}".format(a_res_type.config))

                        entries = []
                        for i in range(0, a_res_type.entryCount):
                            current_package.mResId = current_package.mResId & 0xffff0000 | i
                            entries.append((unpack('<i', self.buff.read(4))[0], current_package.mResId))

                        self.packages[package_name].append(entries)

                        for entry, res_id in entries:
                            if self.buff.end():
                                break

                            if entry != -1:
                                ate = ARSCResTableEntry(self.buff, res_id, pc)
                                self.packages[package_name].append(ate)
                                if ate.is_weak():
                                    # FIXME we are not sure how to implement the FLAG_WEAk!
                                    # We saw the following: There is just a single Res_value after the ARSCResTableEntry
                                    # and then comes the next ARSCHeader.
                                    # Therefore we think this means all entries are somehow replicated?
                                    # So we do some kind of hack here. We set the idx to the entry again...
                                    # Now we will read all entries!
                                    # Not sure if this is a good solution though
                                    self.buff.set_idx(ate.start)
                    elif pkg_chunk_header.type == RES_TABLE_LIBRARY_TYPE:
                        log.warning("RES_TABLE_LIBRARY_TYPE chunk is not supported")
                    else:
                        # silently skip other chunk types
                        pass

                    # skip to the next chunk
                    self.buff.set_idx(pkg_chunk_header.start + pkg_chunk_header.size)

            # move to the next resource chunk
            self.buff.set_idx(res_header.start + res_header.size)

    def _analyse(self):
        if self.analyzed:
            return

        self.analyzed = True

        for package_name in self.packages:
            self.values[package_name] = {}

            nb = 3
            while nb < len(self.packages[package_name]):
                header = self.packages[package_name][nb]
                if isinstance(header, ARSCHeader):
                    if header.type == RES_TABLE_TYPE_TYPE:
                        a_res_type = self.packages[package_name][nb + 1]

                        language = a_res_type.config.get_language()
                        region = a_res_type.config.get_country()
                        if region == "\x00\x00":
                            locale = language
                        else:
                            locale = "{}-r{}".format(language, region)

                        c_value = self.values[package_name].setdefault(locale, {"public":[]})

                        entries = self.packages[package_name][nb + 2]
                        nb_i = 0
                        for entry, res_id in entries:
                            if entry != -1:
                                ate = self.packages[package_name][nb + 3 + nb_i]

                                self.resource_values[ate.mResId][a_res_type.config] = ate
                                self.resource_keys[package_name][a_res_type.get_type()][ate.get_value()] = ate.mResId

                                if ate.get_index() != -1:
                                    c_value["public"].append(
                                        (a_res_type.get_type(), ate.get_value(),
                                         ate.mResId))

                                if a_res_type.get_type() not in c_value:
                                    c_value[a_res_type.get_type()] = []

                                if a_res_type.get_type() == "string":
                                    c_value["string"].append(
                                        self.get_resource_string(ate))

                                elif a_res_type.get_type() == "id":
                                    if not ate.is_complex():
                                        c_value["id"].append(
                                            self.get_resource_id(ate))

                                elif a_res_type.get_type() == "bool":
                                    if not ate.is_complex():
                                        c_value["bool"].append(
                                            self.get_resource_bool(ate))

                                elif a_res_type.get_type() == "integer":
                                    c_value["integer"].append(
                                        self.get_resource_integer(ate))

                                elif a_res_type.get_type() == "color":
                                    c_value["color"].append(
                                        self.get_resource_color(ate))

                                elif a_res_type.get_type() == "dimen":
                                    c_value["dimen"].append(
                                        self.get_resource_dimen(ate))

                                nb_i += 1
                        nb += 3 + nb_i - 1  # -1 to account for the nb+=1 on the next line
                nb += 1

    def get_resource_string(self, ate):
        return [ate.get_value(), ate.get_key_data()]

    def get_resource_id(self, ate):
        x = [ate.get_value()]
        if ate.key.get_data() == 0:
            x.append("false")
        elif ate.key.get_data() == 1:
            x.append("true")
        return x

    def get_resource_bool(self, ate):
        x = [ate.get_value()]
        if ate.key.get_data() == 0:
            x.append("false")
        elif ate.key.get_data() == -1:
            x.append("true")
        return x

    def get_resource_integer(self, ate):
        return [ate.get_value(), ate.key.get_data()]

    def get_resource_color(self, ate):
        entry_data = ate.key.get_data()
        return [
            ate.get_value(),
            "#%02x%02x%02x%02x" % (
                ((entry_data >> 24) & 0xFF),
                ((entry_data >> 16) & 0xFF),
                ((entry_data >> 8) & 0xFF),
                (entry_data & 0xFF))
        ]

    def get_resource_dimen(self, ate):
        try:
            return [
                ate.get_value(), "%s%s" % (
                    complexToFloat(ate.key.get_data()),
                    DIMENSION_UNITS[ate.key.get_data() & COMPLEX_UNIT_MASK])
            ]
        except IndexError:
            log.debug("Out of range dimension unit index for %s: %s" % (
                complexToFloat(ate.key.get_data()),
                ate.key.get_data() & COMPLEX_UNIT_MASK))
            return [ate.get_value(), ate.key.get_data()]

    # FIXME
    def get_resource_style(self, ate):
        return ["", ""]

    def get_packages_names(self):
        return list(self.packages.keys())

    def get_locales(self, package_name):
        self._analyse()
        return list(self.values[package_name].keys())

    def get_types(self, package_name, locale):
        self._analyse()
        return list(self.values[package_name][locale].keys())

    def get_public_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["public"]:
                buff += '<public type="%s" name="%s" id="0x%08x" />\n' % (
                    i[0], i[1], i[2])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_string_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["string"]:
                if any(map(i[1].__contains__, '<&>')):
                    value = '<![CDATA[%s]]>' % i[1]
                else:
                    value = i[1]
                buff += '<string name="%s">%s</string>\n' % (i[0], value)
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_strings_resources(self):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'

        buff += "<packages>\n"
        for package_name in self.get_packages_names():
            buff += "<package name=\"%s\">\n" % package_name

            for locale in self.get_locales(package_name):
                buff += "<locale value=%s>\n" % repr(locale)

                buff += '<resources>\n'
                try:
                    for i in self.values[package_name][locale]["string"]:
                        buff += '<string name="%s">%s</string>\n' % (i[0], escape(i[1]))
                except KeyError:
                    pass

                buff += '</resources>\n'
                buff += '</locale>\n'

            buff += "</package>\n"

        buff += "</packages>\n"

        return buff.encode('utf-8')

    def get_id_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["id"]:
                if len(i) == 1:
                    buff += '<item type="id" name="%s"/>\n' % (i[0])
                else:
                    buff += '<item type="id" name="%s">%s</item>\n' % (i[0],
                                                                       escape(i[1]))
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_bool_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["bool"]:
                buff += '<bool name="%s">%s</bool>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_integer_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["integer"]:
                buff += '<integer name="%s">%s</integer>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_color_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["color"]:
                buff += '<color name="%s">%s</color>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_dimen_resources(self, package_name, locale='\x00\x00'):
        self._analyse()

        buff = '<?xml version="1.0" encoding="utf-8"?>\n'
        buff += '<resources>\n'

        try:
            for i in self.values[package_name][locale]["dimen"]:
                buff += '<dimen name="%s">%s</dimen>\n' % (i[0], i[1])
        except KeyError:
            pass

        buff += '</resources>\n'

        return buff.encode('utf-8')

    def get_id(self, package_name, rid, locale='\x00\x00'):
        self._analyse()

        try:
            for i in self.values[package_name][locale]["public"]:
                if i[2] == rid:
                    return i
        except KeyError:
            return None

    class ResourceResolver(object):
        def __init__(self, android_resources, config=None):
            self.resources = android_resources
            self.wanted_config = config

        def resolve(self, res_id):
            result = []
            self._resolve_into_result(result, res_id, self.wanted_config)
            return result

        def _resolve_into_result(self, result, res_id, config):
            configs = self.resources.get_res_configs(res_id, config)
            if configs:
                for config, ate in configs:
                    self.put_ate_value(result, ate, config)

        def put_ate_value(self, result, ate, config):
            if ate.is_complex():
                complex_array = []
                result.append((config, complex_array))
                for _, item in ate.item.items:
                    self.put_item_value(complex_array, item, config, complex_=True)
            else:
                self.put_item_value(result, ate.key, config, complex_=False)

        def put_item_value(self, result, item, config, complex_):
            if item.is_reference():
                res_id = item.get_data()
                if res_id:
                    self._resolve_into_result(
                        result,
                        item.get_data(),
                        self.wanted_config)
            else:
                if complex_:
                    result.append(item.format_value())
                else:
                    result.append((config, item.format_value()))

    def get_resolved_res_configs(self, rid, config=None):
        resolver = ARSCParser.ResourceResolver(self, config)
        return resolver.resolve(rid)

    def get_resolved_strings(self):
        self._analyse()
        if self._resolved_strings:
            return self._resolved_strings

        r = {}
        for package_name in self.get_packages_names():
            r[package_name] = {}
            k = {}

            for locale in self.values[package_name]:
                v_locale = locale
                if v_locale == '\x00\x00':
                    v_locale = 'DEFAULT'

                r[package_name][v_locale] = {}

                try:
                    for i in self.values[package_name][locale]["public"]:
                        if i[0] == 'string':
                            r[package_name][v_locale][i[2]] = None
                            k[i[1]] = i[2]
                except KeyError:
                    pass

                try:
                    for i in self.values[package_name][locale]["string"]:
                        if i[0] in k:
                            r[package_name][v_locale][k[i[0]]] = i[1]
                except KeyError:
                    pass

        self._resolved_strings = r
        return r

    def get_res_configs(self, rid, config=None):
        self._analyse()

        if not rid:
            raise ValueError("'rid' should be set")

        try:
            res_options = self.resource_values[rid]
            if len(res_options) > 1 and config:
                return [(
                    config,
                    res_options[config])]
            else:
                return list(res_options.items())

        except KeyError:
            return []

    def get_string(self, package_name, name, locale='\x00\x00'):
        self._analyse()

        try:
            for i in self.values[package_name][locale]["string"]:
                if i[0] == name:
                    return i
        except KeyError:
            return None

    def get_res_id_by_key(self, package_name, resource_type, key):
        try:
            return self.resource_keys[package_name][resource_type][key]
        except KeyError:
            return None

    def get_items(self, package_name):
        self._analyse()
        return self.packages[package_name]

    def get_type_configs(self, package_name, type_name=None):
        if package_name is None:
            package_name = self.get_packages_names()[0]
        result = collections.defaultdict(list)

        for res_type, configs in list(self.resource_configs[package_name].items()):
            if res_type.get_package_name() == package_name and (
                            type_name is None or res_type.get_type() == type_name):
                result[res_type.get_type()].extend(configs)

        return result


class PackageContext(object):
    def __init__(self, current_package, stringpool_main, mTableStrings,
                 mKeyStrings):
        self.stringpool_main = stringpool_main
        self.mTableStrings = mTableStrings
        self.mKeyStrings = mKeyStrings
        self.current_package = current_package

    def get_mResId(self):
        return self.current_package.mResId

    def set_mResId(self, mResId):
        self.current_package.mResId = mResId

    def get_package_name(self):
        return self.current_package.get_name()


class ARSCHeader(object):
    SIZE = 2 + 2 + 4

    def __init__(self, buff):
        self.start = buff.get_idx()
        self.type = unpack('<h', buff.read(2))[0]
        self.header_size = unpack('<h', buff.read(2))[0]
        self.size = unpack('<I', buff.read(4))[0]

    def __repr__(self):
        return "<ARSCHeader idx='0x{:08x}' type='{}' header_size='{}' size='{}'>".format(self.start, self.type, self.header_size, self.size)


class ARSCResTablePackage(object):
    def __init__(self, buff, header):
        self.header = header
        self.start = buff.get_idx()
        self.id = unpack('<I', buff.read(4))[0]
        self.name = buff.readNullString(256)
        self.typeStrings = unpack('<I', buff.read(4))[0]
        self.lastPublicType = unpack('<I', buff.read(4))[0]
        self.keyStrings = unpack('<I', buff.read(4))[0]
        self.lastPublicKey = unpack('<I', buff.read(4))[0]
        self.mResId = self.id << 24

    def get_name(self):
        name = self.name.decode("utf-16", 'replace')
        name = name[:name.find("\x00")]
        return name


class ARSCResTypeSpec(object):
    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent
        self.id = unpack('<b', buff.read(1))[0]
        self.res0 = unpack('<b', buff.read(1))[0]
        self.res1 = unpack('<h', buff.read(2))[0]
        self.entryCount = unpack('<I', buff.read(4))[0]

        self.typespec_entries = []
        for i in range(0, self.entryCount):
            self.typespec_entries.append(unpack('<I', buff.read(4))[0])


class ARSCResType(object):
    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent
        self.id = unpack('<b', buff.read(1))[0]
        self.res0 = unpack('<b', buff.read(1))[0]
        self.res1 = unpack('<h', buff.read(2))[0]
        self.entryCount = unpack('<i', buff.read(4))[0]
        self.entriesStart = unpack('<i', buff.read(4))[0]
        self.mResId = (0xff000000 & self.parent.get_mResId()) | self.id << 16
        self.parent.set_mResId(self.mResId)

        self.config = ARSCResTableConfig(buff)

    def get_type(self):
        return self.parent.mTableStrings.getString(self.id - 1)

    def get_package_name(self):
        return self.parent.get_package_name()

    def __repr__(self):
        return "ARSCResType(%x, %x, %x, %x, %x, %x, %x, %s)" % (
            self.start,
            self.id,
            self.res0,
            self.res1,
            self.entryCount,
            self.entriesStart,
            self.mResId,
            "table:" + self.parent.mTableStrings.getString(self.id - 1)
        )


class ARSCResTableConfig(object):
    @classmethod
    def default_config(cls):
        if not hasattr(cls, 'DEFAULT'):
            cls.DEFAULT = ARSCResTableConfig(None)
        return cls.DEFAULT

    def __init__(self, buff=None, **kwargs):
        if buff is not None:
            self.start = buff.get_idx()
            self.size = unpack('<I', buff.read(4))[0]
            self.imsi = unpack('<I', buff.read(4))[0]
            self.locale = unpack('<I', buff.read(4))[0]
            self.screenType = unpack('<I', buff.read(4))[0]
            self.input = unpack('<I', buff.read(4))[0]
            self.screenSize = unpack('<I', buff.read(4))[0]
            self.version = unpack('<I', buff.read(4))[0]

            self.screenConfig = 0
            self.screenSizeDp = 0

            if self.size >= 32:
                self.screenConfig = unpack('<I', buff.read(4))[0]

                if self.size >= 36:
                    self.screenSizeDp = unpack('<I', buff.read(4))[0]

            self.exceedingSize = self.size - 36
            if self.exceedingSize > 0:
                log.debug("Skipping padding bytes!")
                self.padding = buff.read(self.exceedingSize)
        else:
            self.start = 0
            self.size = 0
            self.imsi = \
                ((kwargs.pop('mcc', 0) & 0xffff) << 0) + \
                ((kwargs.pop('mnc', 0) & 0xffff) << 16)

            self.locale = 0
            for char_ix, char in kwargs.pop('locale', "")[0:4]:
                self.locale += (ord(char) << (char_ix * 8))

            self.screenType = \
                ((kwargs.pop('orientation', 0) & 0xff) << 0) + \
                ((kwargs.pop('touchscreen', 0) & 0xff) << 8) + \
                ((kwargs.pop('density', 0) & 0xffff) << 16)

            self.input = \
                ((kwargs.pop('keyboard', 0) & 0xff) << 0) + \
                ((kwargs.pop('navigation', 0) & 0xff) << 8) + \
                ((kwargs.pop('inputFlags', 0) & 0xff) << 16) + \
                ((kwargs.pop('inputPad0', 0) & 0xff) << 24)

            self.screenSize = \
                ((kwargs.pop('screenWidth', 0) & 0xffff) << 0) + \
                ((kwargs.pop('screenHeight', 0) & 0xffff) << 16)

            self.version = \
                ((kwargs.pop('sdkVersion', 0) & 0xffff) << 0) + \
                ((kwargs.pop('minorVersion', 0) & 0xffff) << 16)

            self.screenConfig = \
                ((kwargs.pop('screenLayout', 0) & 0xff) << 0) + \
                ((kwargs.pop('uiMode', 0) & 0xff) << 8) + \
                ((kwargs.pop('smallestScreenWidthDp', 0) & 0xffff) << 16)

            self.screenSizeDp = \
                ((kwargs.pop('screenWidthDp', 0) & 0xffff) << 0) + \
                ((kwargs.pop('screenHeightDp', 0) & 0xffff) << 16)

            self.exceedingSize = 0

    def get_language(self):
        x = self.locale & 0x0000ffff
        return chr(x & 0x00ff) + chr((x & 0xff00) >> 8)

    def get_country(self):
        x = (self.locale & 0xffff0000) >> 16
        return chr(x & 0x00ff) + chr((x & 0xff00) >> 8)

    def get_density(self):
        x = ((self.screenType >> 16) & 0xffff)
        return x

    def _get_tuple(self):
        return (
            self.imsi,
            self.locale,
            self.screenType,
            self.input,
            self.screenSize,
            self.version,
            self.screenConfig,
            self.screenSizeDp,
        )

    def __hash__(self):
        return hash(self._get_tuple())

    def __eq__(self, other):
        return self._get_tuple() == other._get_tuple()

    def __repr__(self):
        return "<ARSCResTableConfig '{}'>".format(repr(self._get_tuple()))


class ARSCResTableEntry(object):
    """
    See https://github.com/LineageOS/android_frameworks_base/blob/df2898d9ce306bb2fe922d3beaa34a9cf6873d27/include/androidfw/ResourceTypes.h#L1370
    """
    FLAG_COMPLEX = 1
    FLAG_PUBLIC = 2
    FLAG_WEAK = 4

    def __init__(self, buff, mResId, parent=None):
        self.start = buff.get_idx()
        self.mResId = mResId
        self.parent = parent
        self.size = unpack('<H', buff.read(2))[0]
        self.flags = unpack('<H', buff.read(2))[0]
        self.index = unpack('<I', buff.read(4))[0]

        if self.is_complex():
            self.item = ARSCComplex(buff, parent)
        else:
            # If FLAG_COMPLEX is not set, a Res_value structure will follow
            self.key = ARSCResStringPoolRef(buff, self.parent)

    def get_index(self):
        return self.index

    def get_value(self):
        return self.parent.mKeyStrings.getString(self.index)

    def get_key_data(self):
        return self.key.get_data_value()

    def is_public(self):
        return (self.flags & self.FLAG.PUBLIC) != 0

    def is_complex(self):
        return (self.flags & self.FLAG_COMPLEX) != 0

    def is_weak(self):
        return (self.flags & self.FLAG_WEAK) != 0

    def __repr__(self):
        return "<ARSCResTableEntry idx='0x{:08x}' mResId='0x{:08x}' size='{}' flags='0x{:02x}' index='0x{:x}' holding={}>".format(
            self.start,
            self.mResId,
            self.size,
            self.flags,
            self.index,
            self.item if self.is_complex() else self.key)


class ARSCComplex(object):
    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent

        self.id_parent = unpack('<I', buff.read(4))[0]
        self.count = unpack('<I', buff.read(4))[0]

        self.items = []
        for i in range(0, self.count):
            self.items.append((unpack('<I', buff.read(4))[0],
                               ARSCResStringPoolRef(buff, self.parent)))

    def __repr__(self):
        return "<ARSCComplex idx='0x{:08x}' parent='{}' count='{}'>".format(self.start, self.id_parent, self.count)


class ARSCResStringPoolRef(object):
    def __init__(self, buff, parent=None):
        self.start = buff.get_idx()
        self.parent = parent

        self.size, = unpack("<H", buff.read(2))
        self.res0, = unpack("<B", buff.read(1))
        assert self.res0 == 0, "res0 must be always zero!"
        self.data_type = unpack('<B', buff.read(1))[0]
        self.data = unpack('<I', buff.read(4))[0]

    def get_data_value(self):
        return self.parent.stringpool_main.getString(self.data)

    def get_data(self):
        return self.data

    def get_data_type(self):
        return self.data_type

    def get_data_type_string(self):
        return TYPE_TABLE[self.data_type]

    def format_value(self):
        return format_value(
            self.data_type,
            self.data,
            self.parent.stringpool_main.getString
        )

    def is_reference(self):
        return self.data_type == TYPE_REFERENCE

    def __repr__(self):
        return "<ARSCResStringPoolRef idx='0x{:08x}' size='{}' type='{}' data='0x{:08x}'>".format(
            self.start,
            self.size,
            TYPE_TABLE.get(self.data_type, "0x%x" % self.data_type),
            self.data)


def get_arsc_info(arscobj):
    buff = ""
    for package in arscobj.get_packages_names():
        buff += package + ":\n"
        for locale in arscobj.get_locales(package):
            buff += "\t" + repr(locale) + ":\n"
            for ttype in arscobj.get_types(package, locale):
                buff += "\t\t" + ttype + ":\n"
                try:
                    tmp_buff = getattr(arscobj, "get_" + ttype + "_resources")(
                        package, locale).decode("utf-8", 'replace').split("\n")
                    for i in tmp_buff:
                        buff += "\t\t\t" + i + "\n"
                except AttributeError:
                    pass
    return buff
