from __future__ import division

import string
from time import time

from PyQt5 import QtGui, QtCore
from builtins import str

from androguard.gui.TextDecorators import RangePen
from androguard.gui.ViewMode import ViewMode
from androguard.gui.cemu import ConsoleEmulator, Directions
from androguard.gui import TextSelection

import logging
log = logging.getLogger("androguard.gui")


class BinViewMode(ViewMode):
    def __init__(self, themes, width, height, data, cursor, widget=None):
        super(BinViewMode, self).__init__()

        self.dataModel = data
        self.addHandler(self.dataModel)
        self.themes = themes

        self.width = width
        self.height = height

        self.cursor = cursor
        self.widget = widget

        self.refresh = True

        self.selector = TextSelection.DefaultSelection(themes, self)

        # background brush
        self.backgroundBrush = QtGui.QBrush(self.themes['background'])

        self.font = self.themes['font']

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self._fontWidth = fm.width('a')
        self._fontHeight = fm.height()

        self.textPen = QtGui.QPen(self.themes['pen'], 0, QtCore.Qt.SolidLine)
        self.resize(width, height)

        self.Paints = {}
        self.newPix = None
        self.Ops = []

    @property
    def fontWidth(self):
        return self._fontWidth

    @property
    def fontHeight(self):
        return self._fontHeight

    def startCaching(self):
        # cache
        self.cache()
        # t = threading.Thread(target=self.cache)
        # t.start()

    def isInCache(self, page):
        if page in self.Paints:
            return True

    def cache(self):

        for i in [1, 2]:
            # pix = self._getNewPixmap(self.width, self.height)
            if not self.isInCache(self.dataModel.getPageOffset(i)):
                pix = QtGui.QImage(self.width, self.height, QtGui.QImage.Format_ARGB32)
                self.scrollPages(1, cachePix=pix, pageOffset=i)
                self.Paints[self.dataModel.getPageOffset(i)] = pix

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def setTransformationEngine(self, engine):
        self.transformationEngine = engine
        self.original_textdecorator = engine

    def computeTextArea(self):
        self.COLUMNS = self.width // self.fontWidth
        self.ROWS = self.height // self.fontHeight
        self.notify(self.ROWS, self.COLUMNS)

    def drawAdditionals(self):
        self.newPix = self._getNewPixmap(self.width, self.height + self.SPACER)
        qp = QtGui.QPainter()
        qp.begin(self.newPix)
        qp.drawPixmap(0, 0, self.qpix)

        # self.transformationEngine.decorateText()

        # highlight selected text
        self.selector.highlightText()

        # draw other selections
        self.selector.drawSelections(qp)

        # draw our cursor
        self.drawCursor(qp)
        qp.end()

    def getPageOffset(self):
        return self.dataModel.getOffset()

    def getGeometry(self):
        return self.COLUMNS, self.ROWS

    def getColumnsbyRow(self, row):
        return self.COLUMNS

    def getDataModel(self):
        return self.dataModel

    def startSelection(self):
        self.selector.startSelection()

    def stopSelection(self):
        self.selector.stopSelection()

    def draw(self, refresh=False, row=0, howMany=0):
        if self.dataModel.getOffset() in self.Paints:
            self.refresh = False
            self.qpix = QtGui.QPixmap(self.Paints[self.dataModel.getOffset()])
            self.drawAdditionals()
            return

        if self.refresh or refresh:
            qp = QtGui.QPainter()
            qp.begin(self.qpix)
            start = time()
            if not howMany:
                howMany = self.ROWS

            self.drawTextMode(qp, row=row, howMany=howMany)
            end = time() - start
            log.debug('draw Time ' + str(end))
            self.refresh = False
            qp.end()

        #        self.Paints[self.dataModel.getOffset()] = QtGui.QPixmap(self.qpix)
        self.drawAdditionals()

    def draw2(self, qp, refresh=False):
        if self.refresh or refresh:
            start = time()
            self.drawTextMode(qp, howMany=self.ROWS)
            end = time() - start
            log.debug('draw2 Time ' + str(end))
            qp = QtGui.QPainter()
            qp.begin(self.qpix)

        self.drawAdditionals()

    def drawCursor(self, qp):
        cursorX, cursorY = self.cursor.getPosition()
        qp.setBrush(self.themes['background_cursor'])

        if self.isInEditMode():
            qp.setBrush(QtGui.QColor(255, 102, 179))

        qp.setOpacity(0.8)
        qp.drawRect(cursorX * self.fontWidth, cursorY * self.fontHeight, self.fontWidth, self.fontHeight + 2)
        qp.setOpacity(1)

    def scroll_h(self, dx):
        self.qpix.scroll(dx * self.fontWidth, 0, self.qpix.rect())

        qp = QtGui.QPainter()

        qp.begin(self.qpix)
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        factor = abs(dx)
        if dx < 0:
            qp.fillRect((self.COLUMNS - 1 * factor) * self.fontWidth, 0, factor * self.fontWidth,
                        self.ROWS * self.fontHeight + self.SPACER, self.backgroundBrush)
        if dx > 0:
            qp.fillRect(0, 0, factor * self.fontWidth, self.ROWS * self.fontHeight + self.SPACER, self.backgroundBrush)

        cemu = ConsoleEmulator(qp, self.ROWS, self.COLUMNS)

        page = self.transformationEngine.decorate()
        # scriem pe fiecare coloana in parte
        for column in range(factor):
            # fiecare caracter de pe coloana
            for i in range(self.ROWS):

                if dx < 0:
                    # cu (column) selectam coloana
                    idx = (i + 1) * self.COLUMNS - (column + 1)
                if dx > 0:
                    idx = i * self.COLUMNS + column

                # c = self.dataModel.getDisplayablePage()[idx]
                c = self.transformationEngine.getChar(idx)
                qp.setPen(self.transformationEngine.choosePen(idx))

                if self.transformationEngine.chooseBrush(idx) is not None:
                    qp.setBackgroundMode(1)
                    qp.setBackground(self.transformationEngine.chooseBrush(idx))


                #                self.decorate(qp, (idx, c), self.dataModel.getDisplayablePage())
                if dx < 0:
                    cemu.writeAt(self.COLUMNS - (column + 1), i, self.cp437(c))

                if dx > 0:
                    cemu.writeAt(column, i, self.cp437(c))

                qp.setBackgroundMode(0)
        qp.end()

    def scroll_v(self, dy, cachePix=None, pageOffset=None):
        start = time()

        if not cachePix:
            self.qpix.scroll(0, dy * self.fontHeight, self.qpix.rect())

        qp = QtGui.QPainter()

        if cachePix:
            qp.begin(cachePix)
        else:
            qp.begin(self.qpix)

        # self.font.setStyleHint(QtGui.QFont.AnyStyle, QtGui.QFont.PreferAntialias)
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        # TODO: while the characters are not all the same hight, when scrolling up on y axis, trails remains. We should also erase a Rect with SPACER in hight
        #       same problem when scrolling up.             
        factor = abs(dy)
        if dy < 0:
            qp.fillRect(0, (self.ROWS - factor) * self.fontHeight, self.fontWidth * self.COLUMNS,
                        factor * self.fontHeight + self.SPACER, self.backgroundBrush)

        if dy > 0:
            qp.fillRect(0, 0, self.fontWidth * self.COLUMNS, factor * self.fontHeight, self.backgroundBrush)

        cemu = ConsoleEmulator(qp, self.ROWS, self.COLUMNS)

        # page = self.dataModel.getDisplayablePage()
        page = self.transformationEngine.decorate(pageOffset=pageOffset)

        lastPen = None
        lastBrush = None

        # cate linii desenam
        k = time()
        for row in range(factor):
            # desenam caracterele
            # cemu.writeAt(0, row, str(page[row*self.COLUMNS:row*self.COLUMNS+self.COLUMNS]))

            for i in range(self.COLUMNS):

                if dy < 0:
                    idx = (self.ROWS - (row + 1)) * self.COLUMNS + i

                if dy > 0:
                    idx = i + (self.COLUMNS * row)

                c = self.transformationEngine.getChar(idx)

                nextPen = self.transformationEngine.choosePen(idx)
                if nextPen != lastPen:
                    qp.setPen(nextPen)
                    lastPen = nextPen

                qp.setBackgroundMode(0)
                nextBrush = self.transformationEngine.chooseBrush(idx)
                if nextBrush is not None:
                    qp.setBackgroundMode(1)

                    if nextBrush != lastBrush:
                        qp.setBackground(nextBrush)
                        lastBrush = nextBrush

                if dy < 0:
                    cemu.writeAt_c(i, self.ROWS - 1 - row, self.cp437(c))

                if dy > 0:
                    cemu.writeAt_c(i, row, self.cp437(c))

        # TODO: text decorator is taking too much! print time() - k
        qp.end()

        end = time() - start

    def scroll(self, dx, dy, cachePix=None, pageOffset=None):
        if not cachePix:
            if self.dataModel.getOffset() in self.Paints:
                self.draw()
                return

        if dx != 0:
            if self.dataModel.inLimits((self.dataModel.getOffset() - dx)):
                self.dataModel.slide(-dx)
                self.scroll_h(dx)

        if dy != 0:
            if self.dataModel.inLimits((self.dataModel.getOffset() - dy * self.COLUMNS)):
                self.dataModel.slide(-dy * self.COLUMNS)
                # import time
                # k = time.time()
                self.scroll_v(dy, cachePix, pageOffset)
                # print time.time() - k
            else:
                if dy <= 0:
                    pass
                    # self.dataModel.slideToLastPage()
                else:
                    self.dataModel.slideToFirstPage()

                if not cachePix:
                    self.draw(refresh=True)

        if not cachePix:
            self.draw()

    def scrollPages(self, number, cachePix=None, pageOffset=None):
        self.scroll(0, -number * self.ROWS, cachePix=cachePix, pageOffset=pageOffset)

    def getPixmap(self):
        for t in self.Ops:
            if len(t) == 1:
                t[0]()

            else:
                t[0](*t[1:])

        self.Ops = []

        if not self.newPix:
            self.draw()

        return self.newPix

    def resize(self, width, height):
        self.width = width - width % self.fontWidth
        self.height = height - height % self.fontHeight
        self.computeTextArea()
        self.qpix = self._getNewPixmap(self.width, self.height + self.SPACER)
        self.refresh = True

    def drawTextMode(self, qp, row=0, howMany=1):
        # draw background
        qp.fillRect(0, row * self.fontHeight, self.COLUMNS * self.fontWidth, howMany * self.fontHeight + self.SPACER,
                    self.backgroundBrush)

        # set text pen&font
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        cemu = ConsoleEmulator(qp, self.ROWS, self.COLUMNS)

        self.page = self.transformationEngine.decorate()

        cemu.gotoXY(0, row)

        for i, c in enumerate(self.getDisplayablePage()[row * self.COLUMNS:(row + howMany) * self.COLUMNS]):
            x = i + row * self.COLUMNS

            c = self.transformationEngine.getChar(x)

            qp.setPen(self.transformationEngine.choosePen(x))

            if self.transformationEngine.chooseBrush(x) is not None:
                qp.setBackgroundMode(1)
                qp.setBackground(self.transformationEngine.chooseBrush(x))

            cemu.write(self.cp437(c))
            qp.setBackgroundMode(0)

    def getCursorAbsolutePosition(self):
        x, y = self.cursor.getPosition()
        return self.dataModel.getOffset() + y * self.COLUMNS + x

    def moveCursor(self, direction):
        cursorX, cursorY = self.cursor.getPosition()

        if direction == Directions.Left:
            if cursorX == 0:
                if cursorY == 0:
                    self.scroll(1, 0)
                else:
                    self.cursor.moveAbsolute(self.COLUMNS - 1, cursorY - 1)
            else:
                self.cursor.move(-1, 0)

        if direction == Directions.Right:
            if self.getCursorAbsolutePosition() + 1 >= self.dataModel.getDataSize():
                return

            if cursorX == self.COLUMNS - 1:
                if cursorY == self.ROWS - 1:
                    self.scroll(-1, 0)
                else:
                    self.cursor.moveAbsolute(0, cursorY + 1)
            else:
                self.cursor.move(1, 0)

        if direction == Directions.Down:
            if self.getCursorAbsolutePosition() + self.COLUMNS >= self.dataModel.getDataSize():
                y, x = self.dataModel.getXYInPage(self.dataModel.getDataSize() - 1)
                self.cursor.moveAbsolute(x, y)
                return

            if cursorY == self.ROWS - 1:
                self.scroll(0, -1)
            else:
                self.cursor.move(0, 1)

        if direction == Directions.Up:
            if cursorY == 0:
                self.scroll(0, 1)
            else:
                self.cursor.move(0, -1)

        if direction == Directions.End:
            if self.dataModel.getDataSize() < self.getCursorAbsolutePosition() + self.ROWS * self.COLUMNS:
                y, x = self.dataModel.getXYInPage(self.dataModel.getDataSize() - 1)
                self.cursor.moveAbsolute(x, y)

            else:
                self.cursor.moveAbsolute(self.COLUMNS - 1, self.ROWS - 1)

        if direction == Directions.Home:
            self.cursor.moveAbsolute(0, 0)

        if direction == Directions.CtrlHome:
            self.dataModel.slideToFirstPage()
            self.draw(refresh=True)
            self.cursor.moveAbsolute(0, 0)

        if direction == Directions.CtrlEnd:
            self.dataModel.slideToLastPage()
            self.draw(refresh=True)
            self.moveCursor(Directions.End)

    def keyFilter(self):
        return [
            (QtCore.Qt.ControlModifier, QtCore.Qt.Key_Right),
            (QtCore.Qt.ControlModifier, QtCore.Qt.Key_Left),
            (QtCore.Qt.ControlModifier, QtCore.Qt.Key_Up),
            (QtCore.Qt.ControlModifier, QtCore.Qt.Key_Down),
            (QtCore.Qt.ControlModifier, QtCore.Qt.Key_End),
            (QtCore.Qt.ControlModifier, QtCore.Qt.Key_Home),

            (QtCore.Qt.NoModifier, QtCore.Qt.Key_Right),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_Left),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_Up),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_Down),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_End),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_Home),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_PageDown),
            (QtCore.Qt.NoModifier, QtCore.Qt.Key_PageUp)

        ]

    def anon(self, dx, dy):
        self.scroll(dx, dy)

        # scroll modifies datamodel offset, so we must do scroll and cursor
        # operations toghether

        y, x = self.dataModel.getXYInPage(self.dataModel.getDataSize() - 1)
        if self.getCursorAbsolutePosition() >= self.dataModel.getDataSize():
            y, x = self.dataModel.getXYInPage(self.dataModel.getDataSize() - 1)
            self.cursor.moveAbsolute(x, y)

        # we call draw() again because it was called before by scroll()
        # and the cursor is already painted but it's not in correct position
        # kinda hack, don't really like it
        self.draw()

    def handleEditMode(self, modifiers, key, event):
        if key in range(0, 256):
            offs = self.getCursorOffsetInPage()

            self.dataModel.setData_b(self.dataModel.getOffset() + offs, str(event.text()))

            z = self.dataModel.getOffset() + offs
            # TODO: sa nu se repete, tre original_transformengine
            self.transformationEngine = RangePen(self.original_textdecorator, z, z + 0,
                                                 QtGui.QPen(QtGui.QColor(218, 94, 242), 0, QtCore.Qt.SolidLine),
                                                 ignoreHighlights=True)

            self.moveCursor(Directions.Right)

            x, y = self.cursor.getPosition()

            self.draw(refresh=True, row=y, howMany=1)

    def handleKeyEvent(self, modifiers, key, event=None):
        if event.type() == QtCore.QEvent.KeyRelease:
            if key == QtCore.Qt.Key_Shift:
                self.stopSelection()
                return True

        if event.type() == QtCore.QEvent.KeyPress:
            if modifiers & QtCore.Qt.ShiftModifier:
                keys = [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up,
                        QtCore.Qt.Key_End, QtCore.Qt.Key_Home]
                if key in keys:
                    self.startSelection()

            if modifiers & QtCore.Qt.ControlModifier:
                if key == QtCore.Qt.Key_Right:
                    self.addop((self.anon, -1, 0))

                if key == QtCore.Qt.Key_Left:
                    self.addop((self.scroll, 1, 0))

                if key == QtCore.Qt.Key_Down:
                    self.addop((self.anon, 0, -1))

                if key == QtCore.Qt.Key_Up:
                    self.addop((self.scroll, 0, 1))

                if key == QtCore.Qt.Key_End:
                    self.moveCursor(Directions.CtrlEnd)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Home:
                    self.moveCursor(Directions.CtrlHome)
                    self.addop((self.draw,))

                return True

            else:  # elif modifiers == QtCore.Qt.NoModifier or modifiers == QtCore.Qt.ShiftModifier::

                if key == QtCore.Qt.Key_Escape:
                    self.selector.resetSelections()
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Left:
                    self.moveCursor(Directions.Left)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Right:
                    self.moveCursor(Directions.Right)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Down:
                    self.moveCursor(Directions.Down)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_End:
                    self.moveCursor(Directions.End)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Home:
                    self.moveCursor(Directions.Home)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Up:
                    self.moveCursor(Directions.Up)
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_PageDown:
                    self.addop((self.scrollPages, 1))

                if key == QtCore.Qt.Key_PageUp:
                    self.addop((self.scrollPages, -1))

                if self.isInEditMode():
                    self.handleEditMode(modifiers, key, event)

                return True

        return False

    def isEditable(self):
        return True

    def setEditMode(self, mode):
        super(BinViewMode, self).setEditMode(mode)

        letters = string.ascii_letters + string.digits + ' .;\':;=\"?-!()/\\_'

        # disable/enable shortcuts
        if not mode:
            self.transformationEngine = self.original_textdecorator
            self.transformationEngine.reset()
            self.draw(refresh=True)

    """
    def handleKeyPressEvent(self, modifier, key):
        if modifier == QtCore.Qt.ShiftModifier:
            #self.startSelection()
            return True

    def handleKeyReleaseEvent(self, modifier, key):
        if modifier == QtCore.Qt.ShiftModifier:
            self.stopSelection()
            return True
    """

    def addop(self, t):
        self.Ops.append(t)

    def getHeaderInfo(self):
        return 'Binary'
