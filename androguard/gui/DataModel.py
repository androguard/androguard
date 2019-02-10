from __future__ import division

import os
import mmap

from androguard.gui.BinViewMode import BinViewMode
from androguard.gui.HexViewMode import HexViewMode
from androguard.gui.DisasmViewMode import DisasmViewMode
from androguard.gui.SourceViewMode import SourceViewMode

import logging
log = logging.getLogger("androguard.gui")


class Observer(object):
    def update_geometry(self):
        NotImplementedError('method not implemented.')


class DataModel(Observer):
    def __init__(self, data):
        self._dataOffset = 0
        self.rows = self.cols = 0
        self.data = data
        self._lastOffset = 0
        self._dirty = False

    @property
    def dataOffset(self):
        return self._dataOffset

    @dataOffset.setter
    def dataOffset(self, value):
        log.debug("DATA OFFSET %s", value)
        self._lastOffset = self._dataOffset
        self._dataOffset = value

    def getLastOffset(self):
        return self._lastOffset

    def inLimits(self, x):
        if 0 <= x < len(self.data):
            return True

        return False

    def slide(self, off):
        if self.inLimits(self.dataOffset + off):
            self.dataOffset += off

    def goTo(self, off):
        if self.inLimits(off):
            self.dataOffset = off

    def offsetInPage(self, off):
        if self.dataOffset <= off <= self.dataOffset + self.rows * self.cols:
            return True

        return False

    def update_geometry(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def slideLine(self, factor):
        self.slide(factor * self.cols)

    def slidePage(self, factor):
        self.slide(factor * self.cols * self.rows)

    def slideToLastPage(self):
        if self.rows * self.cols > len(self.data):
            return

        self.dataOffset = len(self.data) - self.cols * self.rows

    def slideToFirstPage(self):
        self.dataOffset = 0

    def getXYInPage(self, off):
        off -= self.dataOffset
        x, y = off // self.cols, off % self.cols
        return x, y

    def getPageOffset(self, page):
        return self.getOffset() + page * self.rows * self.cols

    def getQWORD(self, offset, asString=False):
        if offset + 8 > len(self.data):
            return None

        b = bytearray(self.data[offset:offset + 8])

        d = ((b[7] << 56) | (b[6] << 48) | (b[5] << 40) | (b[4] << 32) | (b[3] << 24) | (b[2] << 16) | (b[1] << 8) | (
        b[0])) & 0xFFFFFFFFFFFFFFFF

        if not asString:
            return d

        s = '{0:016X}'.format(d)

        return s

    def getDWORD(self, offset, asString=False):
        if offset + 4 >= len(self.data):
            return None

        b = bytearray(self.data[offset:offset + 4])

        d = ((b[3] << 24) | (b[2] << 16) | (b[1] << 8) | (b[0])) & 0xFFFFFFFF

        if not asString:
            return d

        s = '{0:08X}'.format(d)

        return s

    def getWORD(self, offset, asString=False):
        if offset + 2 > len(self.data):
            return None

        b = bytearray(self.data[offset:offset + 2])

        d = ((b[1] << 8) | (b[0])) & 0xFFFF

        if not asString:
            return d

        s = '{0:04X}'.format(d)

        return s

    def getBYTE(self, offset, asString=False):
        if offset + 1 > len(self.data):
            return None

        b = bytearray(self.data[offset:offset + 1])

        d = (b[0]) & 0xFF

        if not asString:
            return d

        s = '{0:02X}'.format(d)

        return s

    def getChar(self, offset):
        if offset < 0:
            return None

        if offset >= len(self.data):
            return None

        return self.data[offset]

    def getStream(self, start, end):
        return bytearray(self.data[start:end])

    def getOffset(self):
        return self.dataOffset

    def getData(self):
        return self.data

    def isDirty(self):
        return self._dirty

    def setData_b(self, offset, b):
        if self.inLimits(offset):
            self.data[offset] = b
            self._dirty = True
            return True

        return False

    def setData_s(self, u, v, s):
        self.data[u:v] = s
        self._dirty = True
        return True

    def getDataSize(self):
        return len(self.data)

    @property
    def source(self):
        return ''

    def flush(self):
        raise NotImplementedError('method not implemented.')

    def write(self):
        raise NotImplementedError('method not implemented.')

    def close(self):
        pass

    def size(self):
        pass


class FileDataModel(DataModel):
    def __init__(self, filename):
        self._filename = filename

        self._f = open(filename, "rb")

        # memory-map the file, size 0 means whole file
        self._mapped = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_COPY)

        super(FileDataModel, self).__init__(self._mapped)

    @property
    def source(self):
        return self._filename

    def flush(self):
        self._f.close()
        # open for writing
        try:
            self._f = open(self._filename, "r+b")
        except OSError as e:
            log.exception("File could not be opened for writing: %s", e)
            # could not open for writing
            return False
        self._f.write(self._mapped)

        return True

    def close(self):
        self._mapped.close()
        self._f.close()

    def write(self, offset, stream):
        self._mapped.seek(offset)
        self._mapped.write(stream)

    def size(self):
        return os.path.getsize(self._filename)


import io


class MyStringIO(io.StringIO, object):
    def __init__(self, data):
        self.raw = data
        super(MyStringIO, self).__init__(data)

    def __len__(self):
        return len(self.raw)


class MyByte(bytearray):
    def __init__(self, data):
        self.raw = data
        self._pointer = 0
        super(MyByte, self).__init__(data)

    def __len__(self):
        return len(self.raw)

    def seek(self, a, b=0):
        if b == 0:
            self._pointer = a
        elif b == 1:
            self._pointer += a
        elif b == 2:
            self._pointer = len(self.raw) - b
        else:
            return

        return

    def read(self, size):
        if self._pointer + size > len(self.raw):
            return ''

        data = str(self.raw[self._pointer:self._pointer + size])
        self._pointer += size
        return data


class BufferDataModel(DataModel):
    def __init__(self, data, name):
        self._filename = name
        self.raw = data
        super(BufferDataModel, self).__init__(data)

    @property
    def source(self):
        return self._filename

    def flush(self):
        return False

    def close(self):
        return

    #    def write(self, offset, stream):
    #        self._mapped.seek(offset)
    #        self._mapped.write(stream)

    def size(self):
        return len(self.data)


class ApkModel(DataModel):
    def __init__(self, apkobj):
        self._filename = str(apkobj)
        self.raw = apkobj.get_raw()
        self.data = MyByte(self.raw)

        super(ApkModel, self).__init__(self.data)

    def GetViews(self):
        return [BinViewMode, HexViewMode]

    @property
    def source(self):
        return self._filename

    def flush(self):
        return False

    def close(self):
        return

    def size(self):
        return len(self.data)


class DexClassModel(DataModel):
    def __init__(self, current_class, dx):
        """

        :param current_class: a ClassDefItem
        :param dx: a Analysis object
        """
        self.current_class = current_class
        self._filename = current_class.get_name()
        self.dx = dx

        raw = self.GetRawData(current_class)
        super(DexClassModel, self).__init__(raw)

    def GetRawData(self, current_class):
        buff = bytearray()
        self.ins_size = 0
        for method in current_class.get_methods():
            for ins in method.get_instructions():
                buff += ins.get_raw()
                self.ins_size += ins.get_length() * 2
        return buff

    def GetViews(self):
        return [DisasmViewMode, SourceViewMode, HexViewMode]

    @property
    def source(self):
        return self._filename

    def flush(self):
        return False

    def close(self):
        return

    def getDataSize(self):
        return self.ins_size
