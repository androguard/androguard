def decode(b):
    size = len(b)
    ord_array = [None] * size
    ord_index = 0

    b = iter(b)

    for x in b:
        if x >> 7 == 0:
            # Single char:
            ord_array[ord_index] = x & 0x7f
        elif x >> 5 == 0b110:
            # 2 byte Multichar
            b2 = next(b)
            if b2 >> 6 != 0b10:
                raise UnicodeDecodeError(
                    "Second byte of 2 byte sequence does not looks right.")

            ord_array[ord_index] = (x & 0x1f) << 6 | b2 & 0x3f
        elif x >> 4 == 0b1110:
            # 3 byte Multichar
            b2 = next(b)
            b3 = next(b)
            if b2 >> 6 != 0b10:
                raise UnicodeDecodeError(
                    "Second byte of 3 byte sequence does not looks right.")
            if b3 >> 6 != 0b10:
                raise UnicodeDecodeError(
                    "Third byte of 3 byte sequence does not looks right.")

            ord_array[ord_index] = (x & 0xf) << 12 | (
                b2 & 0x3f) << 6 | b3 & 0x3f
        else:
            raise UnicodeDecodeError("Could not decode byte")
        ord_index += 1

    chr_array = [""]*size
    chr_index = 0
    while chr_index < size:
        c = ord_array[chr_index]
        if c is None:
            break
        if (c >> 10) == 0b110110:
            n = None
            try:
                n = ord_array[chr_index + 1]
            except:
                pass
            if n and (n >> 10) == 0b110111:
                chr_array[chr_index] = chr(
                    ((c & 0x3ff) << 10 | (n & 0x3ff)) + 0x10000)
                chr_index += 1
            else:
                chr_array[chr_index] = chr(c)
        else:
            chr_array[chr_index] = chr(c)
        chr_index += 1

    return "".join(chr_array)


def encode(s):
    b = [b""]*len(s)
    ord_array = [i for i in map(lambda x: ord(x), s)]
    for x in ord_array:
        if (x == 0) or ((x <= 0x7ff) and (x >= 0x80)):
            b1 = ((x & 0x7c0) >> 6 | 0xc0).to_bytes(1, 'big')
            b2 = ((x & 0x3f) | 0x80).to_bytes(1, 'big')
            b.append(b1 + b2)
        elif (x <= 0x7f):
            b1 = x.to_bytes(1, 'big')
            b.append(b1)
        elif (x >= 0x800) and (x <= 0xffff):
            b1 = ((x & 0xf000) >> 12 | 0xe0).to_bytes(1, 'big')
            b2 = ((x & 0xfff) >> 6 | 0x80).to_bytes(1, 'big')
            b3 = ((x & 0x3f) | 0x80).to_bytes(1, 'big')
            b.append(b1 + b2 + b3)
        else:
            a = x - 0x10000
            s1 = ((a >> 10) | 0xd800)
            s2 = ((a & 0x3ff) | 0xdc00)
            b1 = ((s1 & 0xf000) >> 12 | 0xe0).to_bytes(1, 'big')
            b2 = ((s1 & 0xfff) >> 6 | 0x80).to_bytes(1, 'big')
            b3 = ((s1 & 0x3f) | 0x80).to_bytes(1, 'big')
            b4 = ((s2 & 0xf000) >> 12 | 0xe0).to_bytes(1, 'big')
            b5 = ((s2 & 0xfff) >> 6 | 0x80).to_bytes(1, 'big')
            b6 = ((s2 & 0x3f) | 0x80).to_bytes(1, 'big')
            b.append(b1 + b2 + b3 + b4 + b5 + b6)
    return b"".join(b)


class MUTF8String(bytes):
    def __new__(cls, b):
        return bytes.__new__(cls, b)

    def __init__(self, b):
        self.__decoded = None

    @classmethod
    def from_str(cls, s):
        try:
            c = cls(encode(s))
        except TypeError as e:
            try:
                c = cls(s)
            except:
                raise e
        c.__decoded = s
        return c

    @classmethod
    def join(cls, data, spacing=b''):
        return MUTF8String(spacing.join(data))

    def replace(self, old, new, count=None):
        if count is None:
            try:
                return MUTF8String(bytes.replace(self, old, new))
            except TypeError:
                return MUTF8String(bytes.replace(self, encode(old), encode(new)))
        else:
            try:
                return MUTF8String(bytes.replace(self, old, new, count))
            except TypeError:
                return MUTF8String(bytes.replace(self, encode(old), encode(new), count))

    def find(self, sub):
        try:
            return bytes.find(self, sub)
        except TypeError:
            return bytes.find(self, encode(sub))

    def split(self, sep=None, maxsplit=-1):
        try:
            return [MUTF8String(i) for i in bytes.split(self, sep, maxsplit)]
        except TypeError:
            return [MUTF8String(i) for i in bytes.split(self, encode(sep), maxsplit)]

    def rsplit(self, sep=None, maxsplit=-1):
        try:
            return [MUTF8String(i) for i in bytes.rsplit(self, sep, maxsplit)]
        except TypeError:
            return [MUTF8String(i) for i in bytes.rsplit(self, encode(sep), maxsplit)]

    def lstrip(self, sub):
        try:
            return MUTF8String(bytes.lstrip(self, sub))
        except TypeError:
            return MUTF8String(bytes.lstrip(self, encode(sub)))

    def startswith(self, sub):
        try:
            return bytes.startswith(self, sub)
        except TypeError:
            return bytes.startswith(self, encode(sub))

    def __hash__(self):
        return bytes.__hash__(self)

    def __add__(self, other):
        try:
            return MUTF8String(bytes.__add__(self, other))
        except TypeError:
            return MUTF8String(bytes.__add__(self, encode(other)))

    def __getitem__(self, key):
        item = super(MUTF8String, self).__getitem__(key)
        if isinstance(item, int):
            return MUTF8String(item.to_bytes(1, byteorder='big'))
        else:
            return MUTF8String(item)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if not self.__decoded:
            self.__decoded = decode(self).encode('utf8', errors='backslashreplace').decode('utf8')
        return self.__decoded

    def __lt__(self, other):
        if isinstance(other, bytes):
            return bytes.__lt__(self, other)
        elif isinstance(other, str):
            return bytes.__lt__(self, encode(other))
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, bytes):
            return bytes.__le__(self, other)
        elif isinstance(other, str):
            return bytes.__le__(self, encode(other))
        else:
            return NotImplemented

    def __eq__(self, other):
        if isinstance(other, bytes):
            return bytes.__eq__(self, other)
        elif isinstance(other, str):
            return bytes.__eq__(self, encode(other))
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, bytes):
            return bytes.__ne__(self, other)
        elif isinstance(other, str):
            return bytes.__ne__(self, encode(other))
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, bytes):
            return bytes.__gt__(self, other)
        elif isinstance(other, str):
            return bytes.__gt__(self, encode(other))
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, bytes):
            return bytes.__ge__(self, other)
        elif isinstance(other, str):
            return bytes.__ge__(self, encode(other))
        else:
            return NotImplemented