from builtins import chr, str

def decode(b):
    """
    Decode bytes as MUTF-8
    See https://docs.oracle.com/javase/6/docs/api/java/io/DataInput.html#modified-utf-8
    for more information

    :param b: bytes to decode
    :rtype: unicode (py2), str (py3)
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
            assert b2 >> 6 == 0b10, "Second byte of 2 byte sequence does not looks right."
            res += chr((x & 0x1f) << 6 | b2 & 0x3f)
        elif x >> 4 == 0b1110:
            # 3 byte Multichar
            b2 = next(b)
            b3 = next(b)
            assert b2 >> 6 == 0b10, "Second byte of 3 byte sequence does not looks right."
            assert b3 >> 6 == 0b10, "Third byte of 3 byte sequence does not looks right."
            res += chr((x & 0xf) << 12 | (b2 & 0x3f) << 6 | b3 & 0x3f)
        else:
            raise UnicodeDecodeError("Could not decode byte")

    return res
