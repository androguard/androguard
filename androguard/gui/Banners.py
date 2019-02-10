from __future__ import division

from PyQt5 import QtGui, QtCore

from androguard.gui.cemu import ConsoleEmulator, enum


class Banner(object):
    def getOrientation(self):
        NotImplementedError('method not implemented.')

    def getDesiredGeometry(self):
        NotImplementedError('method not implemented.')

    def changeDisplay(self):
        return

    def setViewMode(self, viewMode):
        self.viewMode = viewMode

    def getPixmap(self):
        return self.qpix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)


Orientation = enum(Left=0, Bottom=1, Top=2)


class Observer(object):
    def changeViewMode(self, viewMode):
        self.setViewMode(viewMode)


class Banners(Observer):
    BOTTOM_SEPARATOR = 5

    def __init__(self):
        self._Banners = []
        self.separatorBottom = 5
        self.separatorLeft = 5
        self.separatorTop = 5

    def add(self, banner):
        self._Banners.append(banner)

    def banners(self):
        return self._Banners

    def getLeftOffset(self):
        offset = 0
        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Left:
                offset += banner.getDesiredGeometry()
                offset += self.separatorLeft

        return offset

    def getBottomOffset(self):
        offset = 0
        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Bottom:
                offset += banner.getDesiredGeometry()
                offset += self.separatorBottom

        return offset

    def getTopOffset(self):
        offset = 0
        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Top:
                offset += banner.getDesiredGeometry()
                offset += self.separatorTop

        return offset

    def resize(self, width, height):
        limit = self.getBottomOffset() + self.getTopOffset()
        for banner in self._Banners:
            # banners are not resizeable actually
            if banner.getOrientation() == Orientation.Left:
                banner.resize(banner.getDesiredGeometry(), height - limit + 4)  # +4 , make to look nice

            if banner.getOrientation() == Orientation.Bottom:
                banner.resize(width, banner.getDesiredGeometry())

            if banner.getOrientation() == Orientation.Top:
                banner.resize(width, banner.getDesiredGeometry())

    def setViewMode(self, viewMode):
        for banner in self._Banners:
            banner.setViewMode(viewMode)

    def draw(self, qp, offsetLeft, offsetBottom, maxY):

        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Top:
                banner.draw()
                qp.drawPixmap(offsetLeft - 4, offsetBottom, banner.getPixmap())
                offsetBottom += banner.getDesiredGeometry() + self.separatorLeft

        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Left:
                banner.draw()
                qp.drawPixmap(offsetLeft, offsetBottom, banner.getPixmap())
                offsetLeft += banner.getDesiredGeometry() + self.separatorLeft

        # initial offset + all offsets from all banners. We are doing this because Y growns down
        offsetBottom = maxY - self.getBottomOffset() + self.BOTTOM_SEPARATOR

        for banner in self._Banners:
            if banner.getOrientation() == Orientation.Bottom:
                banner.draw()
                qp.drawPixmap(offsetLeft, offsetBottom, banner.getPixmap())
                offsetBottom += banner.getDesiredGeometry() + self.separatorBottom


class FileAddrBanner(Banner):
    def __init__(self, themes, dataModel, viewMode):
        self.width = 0
        self.height = 0
        self.dataModel = dataModel
        self.viewMode = viewMode
        self.qpix = self._getNewPixmap(self.width, self.height)
        self.backgroundBrush = QtGui.QBrush(themes['background'])

        # text font
        self.font = themes['font']

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self.fontWidth = fm.width('a')
        self.fontHeight = fm.height()

        self.textPen = QtGui.QPen(QtGui.QColor(192, 192, 192), 0, QtCore.Qt.SolidLine)

    def getOrientation(self):
        return Orientation.Left

    def getDesiredGeometry(self):
        return 10 * self.fontWidth

    def setViewMode(self, viewMode):
        self.viewMode = viewMode

    def getPixmap(self):
        return self.qpix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def draw(self):
        qp = QtGui.QPainter()

        offset = self.viewMode.getPageOffset()
        columns, rows = self.viewMode.getGeometry()

        qp.begin(self.qpix)
        qp.fillRect(0, 0, self.width, self.height, self.backgroundBrush)
        qp.setPen(self.textPen)
        qp.setFont(self.font)

        for i in range(rows):
            s = '{0:08x}'.format(offset)
            qp.drawText(0 + 5, (i + 1) * self.fontHeight, s)
            columns = self.viewMode.getColumnsbyRow(i)
            offset += columns

        qp.end()

    def resize(self, width, height):
        self.width = width
        self.height = height

        self.qpix = self._getNewPixmap(self.width, self.height)


class BottomBanner(Banner):
    def __init__(self, themes, dataModel, viewMode):
        self.width = 0
        self.height = 0
        self.dataModel = dataModel
        self.viewMode = viewMode
        self.backgroundBrush = QtGui.QBrush(themes['background'])

        self.qpix = self._getNewPixmap(self.width, self.height)

        # text font
        self.font = themes['font']

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self.fontWidth = fm.width('a')
        self.fontHeight = fm.height()

        self.textPen = QtGui.QPen(themes['pen'], 0, QtCore.Qt.SolidLine)

    def getOrientation(self):
        return Orientation.Bottom

    def getDesiredGeometry(self):
        return 60

    def setViewMode(self, viewMode):
        self.viewMode = viewMode

    def draw(self):
        qp = QtGui.QPainter()
        qp.begin(self.qpix)

        qp.fillRect(0, 0, self.width, self.height, self.backgroundBrush)
        qp.setPen(self.textPen)
        qp.setFont(self.font)

        cemu = ConsoleEmulator(qp, self.height // self.fontHeight, self.width // self.fontWidth)

        dword = self.dataModel.getDWORD(self.viewMode.getCursorAbsolutePosition(), asString=True)
        if dword is None:
            dword = '----'

        sd = 'DWORD: {0}'.format(dword)

        pos = 'POS: {0:08x}'.format(self.viewMode.getCursorAbsolutePosition())

        qword = self.dataModel.getQWORD(self.viewMode.getCursorAbsolutePosition(), asString=True)
        if qword is None:
            qword = '----'
        sq = 'QWORD: {0}'.format(qword)

        byte = self.dataModel.getBYTE(self.viewMode.getCursorAbsolutePosition(), asString=True)
        if byte is None:
            byte = '-'

        sb = 'BYTE: {0}'.format(byte)

        cemu.writeAt(1, 0, pos)
        cemu.writeAt(17, 0, sd)
        cemu.writeAt(35, 0, sq)
        cemu.writeAt(62, 0, sb)

        qp.drawLine(15 * self.fontWidth + 5, 0, 15 * self.fontWidth + 5, 50)
        qp.drawLine(33 * self.fontWidth + 5, 0, 33 * self.fontWidth + 5, 50)
        qp.drawLine(59 * self.fontWidth + 5, 0, 59 * self.fontWidth + 5, 50)
        qp.drawLine(71 * self.fontWidth + 5, 0, 71 * self.fontWidth + 5, 50)

        if self.viewMode.selector.getCurrentSelection():
            u, v = self.viewMode.selector.getCurrentSelection()
            if u != v:
                pen = QtGui.QPen(QtGui.QColor(51, 153, 255), 0, QtCore.Qt.SolidLine)
                qp.setPen(pen)

                cemu.writeAt(73, 0, 'Selection: ')
                cemu.write('{0:x}:{1}'.format(u, v - u))
        else:
            pen = QtGui.QPen(QtGui.QColor(128, 128, 128), 0, QtCore.Qt.SolidLine)
            qp.setPen(pen)

            cemu.writeAt(73, 0, '<no selection>')

        """
        qp.drawLine(self.fontWidth*(len(pos) + 1) + 15, 0, self.fontWidth*(len(pos) + 1) + 15, 50)
        qp.drawLine(self.fontWidth*(len(pos + sd) + 1) + 3*15, 0, self.fontWidth*(len(pos + sd) + 1) + 3*15, 50)
        qp.drawLine(self.fontWidth*(len(pos + sd + sq) + 1) + 5*15, 0, self.fontWidth*(len(pos + sd + sq) + 1) + 5*15, 50)
        qp.drawLine(self.fontWidth*(len(pos + sd + sq + sb) + 1) + 8*15, 0, self.fontWidth*(len(pos + sd + sq + sb) + 1) + 8*15, 50)
        """
        # qp.drawLine(270, 0, 270, 50)
        # qp.drawLine(480, 0, 480, 50)
        # qp.drawLine(570, 0, 570, 50)
        """
        # position
        qp.drawText(0 + 5, self.fontHeight, pos)
        # separator
        qp.drawLine(120, 0, 120, 50)

        # dword
        qp.drawText(130 + 5, self.fontHeight, sd)
        # separator
        qp.drawLine(270, 0, 270, 50)

        # qword
        qp.drawText(280 + 5, self.fontHeight, sq)
        # separator
        qp.drawLine(480, 0, 480, 50)

        # byte
        qp.drawText(490 + 5, self.fontHeight, sb)
        # separator
        qp.drawLine(570, 0, 570, 50)
        """

        qp.end()

        pass

    def getPixmap(self):
        return self.qpix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.qpix = self._getNewPixmap(self.width, self.height)


class TopBanner(Banner):
    def __init__(self, themes, dataModel, viewMode):
        self.width = 0
        self.height = 0
        self.dataModel = dataModel
        self.viewMode = viewMode

        self.qpix = self._getNewPixmap(self.width, self.height)
        self.backgroundBrush = QtGui.QBrush(themes['background'])

        # text font
        self.font = themes['font']

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self.fontWidth = fm.width('a')
        self.fontHeight = fm.height()

        self.textPen = QtGui.QPen(themes['pen'], 0, QtCore.Qt.SolidLine)

    def getOrientation(self):
        return Orientation.Top

    def getDesiredGeometry(self):
        return 26  # 22

    def setViewMode(self, viewMode):
        self.viewMode = viewMode

    def draw(self):
        # i don't really like this in terms of arhitecture. We have
        # artificially introduced getHeaderInfo() in Views. Then we had one top
        # banner implemented per plugin. I will think to a better solution

        qp = QtGui.QPainter()
        qp.begin(self.qpix)

        qp.fillRect(0, 0, self.width, self.height, self.backgroundBrush)
        qp.setPen(self.textPen)
        qp.setFont(self.font)

        cemu = ConsoleEmulator(qp, self.height // self.fontHeight, self.width // self.fontWidth)

        cemu.writeAt(1, 0, 'FileAddr')

        offset = 11

        text = self.viewMode.getHeaderInfo()

        cemu.writeAt(offset, 0, text)

        qp.end()

    def getPixmap(self):
        return self.qpix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.qpix = self._getNewPixmap(self.width, self.height)
