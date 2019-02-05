import builtins
from builtins import str
import struct


def chr(val):
    """
    Patched Version of builtins.chr, to work with narrow python builds
    In those versions, the function unichr does not work with inputs >0x10000

    This seems to be a problem usually on older windows builds.

    :param val: integer value of character
    :return: character
    """
    try:
        return builtins.chr(val)
    except ValueError as e:
        if "(narrow Python build)" in str(e):
            return struct.pack('i', val).decode('utf-32')
        else:
            raise e


def decode(b):
    """
    Decode bytes as MUTF-8
    See https://docs.oracle.com/javase/6/docs/api/java/io/DataInput.html#modified-utf-8
    for more information

    Surrogates will be returned as two 16 bit characters.

    :param b: bytes to decode
    :rtype: unicode (py2), str (py3) of 16bit chars
    :raises: UnicodeDecodeError if string is not decodable
    """
    res = u""

    b = iter(bytearray(b))

    for x in b:
        if x >> 7 == 0:
            # Single char:
            res += chr(x & 0x7f)
        elif x >> 5 == 0b110:
            # 2 byte Multichar
            b2 = next(b)
            if b2 >> 6 != 0b10:
                raise UnicodeDecodeError("Second byte of 2 byte sequence does not looks right.")

            res += chr((x & 0x1f) << 6 | b2 & 0x3f)
        elif x >> 4 == 0b1110:
            # 3 byte Multichar
            b2 = next(b)
            b3 = next(b)
            if b2 >> 6 != 0b10:
                raise UnicodeDecodeError("Second byte of 3 byte sequence does not looks right.")
            if b3 >> 6 != 0b10:
                raise UnicodeDecodeError("Third byte of 3 byte sequence does not looks right.")

            res += chr((x & 0xf) << 12 | (b2 & 0x3f) << 6 | b3 & 0x3f)
        else:
            raise UnicodeDecodeError("Could not decode byte")

    return res


class PeekIterator:
    """
    A quick'n'dirty variant of an Iterator that has a special function
    peek, which will return the next object but not consume it.
    """
    idx = 0

    def __init__(self, s):
        self.s = s

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx == len(self.s):
            raise StopIteration()
        self.idx = self.idx + 1
        return self.s[self.idx - 1]

    def next(self):
        # py2 compliance
        return self.__next__()

    def peek(self):
        if self.idx == len(self.s):
            return None
        return self.s[self.idx]


def patch_string(s):
    """
    Reorganize a String in such a way that surrogates are printable
    and lonely surrogates are escaped.

    :param s: input string
    :return: string with escaped lonely surrogates and 32bit surrogates
    """
    res = u''
    it = PeekIterator(s)
    for c in it:
        if (ord(c) >> 10) == 0b110110:
            # High surrogate
            # Check for the next
            n = it.peek()
            if n and (ord(n) >> 10) == 0b110111:
                # Next is a low surrogate! Merge them together
                res += chr(((ord(c) & 0x3ff) << 10 | (ord(n) & 0x3ff)) + 0x10000)
                # Skip next char, as we already consumed it
                next(it)
            else:
                # Lonely high surrogate
                res += u"\\u{:04x}".format(ord(c))
        elif (ord(c) >> 10) == 0b110111:
            # Lonely low surrogate
            res += u"\\u{:04x}".format(ord(c))
        else:
            # Looks like a normal char...
            res += c
    return res

