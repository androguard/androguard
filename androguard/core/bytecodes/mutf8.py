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


class MUTF8String():
    def __init__(self, data, raw=True):
        if isinstance(data, MUTF8String):
            self.__encoded = data.__encoded
            self.__decoded = data.__decoded
        else:
            self.__encoded = None
            self.__decoded = None
            if raw:
                self.__encoded = data
            else:
                self.__decoded = data

    @classmethod
    def from_bytes(cls, data):
        return cls(bytes(data))

    @classmethod
    def from_str(cls, data):
        return cls(data, raw=False)

    @classmethod
    def join(cls, data, spacing=b''):
        array = []
        for i in data:
            try:
                array.append(i.bytes)
            except AttributeError:
                if isinstance(i, bytes):
                    array.append(i)
                else:
                    array.append(encode(i))
        return MUTF8String.from_bytes(spacing.join(array))

    @property
    def bytes(self):
        if self.__encoded is None:
            self.__encoded = encode(self.__decoded)
        return self.__encoded

    @property
    def string(self):
        if self.__decoded is None:
            self.__decoded = decode(self.__encoded)
        return self.__decoded

    def replace(self, old, new):
        try:
            return MUTF8String.from_bytes(self.bytes.replace(old, new))
        except TypeError:
            return MUTF8String.from_bytes(self.bytes.replace(encode(old), encode(new)))

    def find(self, sub):
        try:
            return self.bytes.find(sub)
        except TypeError:
            return self.bytes.find(encode(sub))

    def split(self, sub):
        try:
            return self.bytes.split(sub)
        except TypeError:
            return self.bytes.split(encode(sub))

    def startswith(self, sub):
        try:
            return self.bytes.startswith(sub)
        except TypeError:
            return self.bytes.startswith(encode(sub))

    def __add__(self, other):
        try:
            return MUTF8String.from_bytes(self.bytes + other.bytes)
        except AttributeError:
            return MUTF8String.from_bytes(self.bytes + encode(other))

    def __getitem__(self, item):
        return MUTF8String.from_bytes(self.bytes[item])

    def __repr__(self):
        return "<mutf8.MUTF8String {}>".format(self.__str__())

    def __str__(self):
        return self.string.encode('utf8', errors='backslashreplace').decode('utf8')

    def __format__(self, format_spec):
        return format(self.string, format_spec)

    def __hash__(self):
        return hash(self.bytes)

    def __len__(self):
        return len(self.bytes)

    def __lt__(self, other):
        try:
            return self.bytes.__lt__(other.bytes)
        except AttributeError:
            if isinstance(other, bytes):
                return self.bytes.__lt__(other)
            elif isinstance(other, str):
                return self.bytes.__lt__(MUTF8String.from_str(other).bytes)
            else:
                raise TypeError('{} is not supported'.format(type(other)))

    def __le__(self, other):
        try:
            return self.bytes.__le__(other.bytes)
        except AttributeError:
            if isinstance(other, bytes):
                return self.bytes.__le__(other)
            elif isinstance(other, str):
                return self.bytes.__le__(MUTF8String.from_str(other).bytes)
            else:
                raise TypeError('{} is not supported'.format(type(other)))

    def __eq__(self, other):
        try:
            return self.bytes.__eq__(other.bytes)
        except AttributeError:
            if isinstance(other, bytes):
                return self.bytes.__eq__(other)
            elif isinstance(other, str):
                return self.bytes.__eq__(MUTF8String.from_str(other).bytes)
            else:
                raise TypeError('{} is not supported'.format(type(other)))

    def __ne__(self, other):
        try:
            return self.bytes.__ne__(other.bytes)
        except AttributeError:
            if isinstance(other, bytes):
                return self.bytes.__ne__(other)
            elif isinstance(other, str):
                return self.bytes.__ne__(MUTF8String.from_str(other).bytes)
            else:
                raise TypeError('{} is not supported'.format(type(other)))

    def __gt__(self, other):
        try:
            return self.bytes.__gt__(other.bytes)
        except AttributeError:
            if isinstance(other, bytes):
                return self.bytes.__gt__(other)
            elif isinstance(other, str):
                return self.bytes.__gt__(MUTF8String.from_str(other).bytes)
            else:
                raise TypeError('{} is not supported'.format(type(other)))

    def __ge__(self, other):
        try:
            return self.bytes.__ge__(other.bytes)
        except AttributeError:
            if isinstance(other, bytes):
                return self.bytes.__ge__(other)
            elif isinstance(other, str):
                return self.bytes.__ge__(MUTF8String.from_str(other).bytes)
            else:
                raise TypeError('{} is not supported'.format(type(other)))
