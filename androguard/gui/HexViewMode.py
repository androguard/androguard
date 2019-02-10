from __future__ import division

import string

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
from builtins import hex
from builtins import str

from androguard.gui.TextDecorators import RangePen
from androguard.gui.ViewMode import ViewMode
from androguard.gui.cemu import Directions, ConsoleEmulator
from androguard.gui import TextSelection
import os

class HexViewMode(ViewMode):
    def __init__(self, themes, width, height, data, cursor, widget=None):
        super(HexViewMode, self).__init__()

        self.dataModel = data
        self.width = width
        self.height = height

        self.refresh = True
        self.selector = TextSelection.HexSelection(themes, self)
        self.widget = widget

        self.addHandler(self.dataModel)

        # background brush
        self.backgroundBrush = QtGui.QBrush(themes['background'])

        # text font
        self.font = themes['font']

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self._fontWidth = fm.width('a')
        self._fontHeight = fm.height()

        self.Special = string.ascii_letters + string.digits + ' .;\':;=\"?-!()/\\_'

        self.textPen = QtGui.QPen(themes['pen'], 1, QtCore.Qt.SolidLine)

        self.cursor = cursor

        self.HexColumns = [1, 4, 8, 16, 32, 36, 40]
        self.idxHexColumns = 3  # 32 columns

        self.newPix = None
        self.Ops = []
        self.gap = 5

        self.highpart = True
        self.resize(width, height)

        self.ann_w = Annotation(self.widget, self)

    @property
    def fontWidth(self):
        return self._fontWidth

    @property
    def fontHeight(self):
        return self._fontHeight

    def setTransformationEngine(self, engine):
        self.transformationEngine = engine
        self.original_textdecorator = engine

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def getPixmap(self):
        # return self.qpix

        for t in self.Ops:
            if len(t) == 1:
                t[0]()

            else:
                t[0](*t[1:])

        self.Ops = []

        if not self.newPix:
            self.draw()

        return self.newPix

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

    def getPageOffset(self):
        return self.dataModel.getOffset()

    def getCursorAbsolutePosition(self):
        x, y = self.cursor.getPosition()
        return self.dataModel.getOffset() + y * self.COLUMNS + x

    def computeTextArea(self):
        self.COLUMNS = self.HexColumns[self.idxHexColumns]
        self.CON_COLUMNS = self.width // self.fontWidth
        self.ROWS = self.height // self.fontHeight
        self.notify(self.ROWS, self.COLUMNS)

    def resize(self, width, height):
        self.width = width - width % self.fontWidth
        self.height = height - height % self.fontHeight
        self.computeTextArea()
        self.qpix = self._getNewPixmap(self.width, self.height + self.SPACER)
        self.refresh = True

    def changeHexColumns(self):
        if self.idxHexColumns == len(self.HexColumns) - 1:
            self.idxHexColumns = 0
        else:
            self.idxHexColumns += 1

        # if screen is ont big enough, retry
        if self.HexColumns[self.idxHexColumns] * (3 + 1) + self.gap >= self.CON_COLUMNS:
            self.changeHexColumns()
            return

        self.resize(self.width, self.height)

    def scroll(self, dx, dy):
        if dx != 0:
            if self.dataModel.inLimits((self.dataModel.getOffset() - dx)):
                self.dataModel.slide(-dx)
                self.scroll_h(dx)

        if dy != 0:
            if self.dataModel.inLimits((self.dataModel.getOffset() - dy * self.COLUMNS)):
                self.dataModel.slide(-dy * self.COLUMNS)
                self.scroll_v(dy)
            else:
                if dy <= 0:
                    pass
                    # self.dataModel.slideToLastPage()
                else:
                    self.dataModel.slideToFirstPage()
                self.draw(refresh=True)

        self.draw()

    def scrollPages(self, number):
        self.scroll(0, -number * self.ROWS)

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

        # draw dword lines
        for i in range(self.COLUMNS // 4)[1:]:
            xw = i * 4 * 3 * self.fontWidth - 4
            qp.setPen(QtGui.QColor(0, 255, 0))
            qp.drawLine(xw, 0, xw, self.ROWS * self.fontHeight)

        qp.end()

    def scroll_h(self, dx):
        gap = self.gap

        # hex part
        self.qpix.scroll(dx * 3 * self.fontWidth, 0, QtCore.QRect(0, 0, self.COLUMNS * 3 * self.fontWidth,
                                                                  self.ROWS * self.fontHeight + self.SPACER))
        # text part
        self.qpix.scroll(dx * self.fontWidth, 0,
                         QtCore.QRect((self.COLUMNS * 3 + gap) * self.fontWidth, 0, self.COLUMNS * self.fontWidth,
                                      self.ROWS * self.fontHeight + self.SPACER))

        qp = QtGui.QPainter()

        qp.begin(self.qpix)
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        factor = abs(dx)

        # There are some trails from the characters, when scrolling. trail == number of pixel to erase near the character
        trail = 5

        textBegining = self.COLUMNS * 3 + gap
        if dx < 0:
            # hex
            qp.fillRect((self.COLUMNS - 1 * factor) * 3 * self.fontWidth, 0, factor * self.fontWidth * 3,
                        self.ROWS * self.fontHeight + self.SPACER, self.backgroundBrush)
            # text
            qp.fillRect((textBegining + self.COLUMNS - 1 * factor) * self.fontWidth, 0, factor * self.fontWidth + trail,
                        self.ROWS * self.fontHeight + self.SPACER, self.backgroundBrush)
        if dx > 0:
            # hex
            qp.fillRect(0, 0, factor * 3 * self.fontWidth, self.ROWS * self.fontHeight + self.SPACER,
                        self.backgroundBrush)
            # text
            qp.fillRect(textBegining * self.fontWidth - trail, 0, factor * self.fontWidth + trail,
                        self.ROWS * self.fontHeight + self.SPACER, self.backgroundBrush)

        cemu = ConsoleEmulator(qp, self.ROWS, self.CON_COLUMNS)

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

                if len(self.getDisplayablePage()) > idx:
                    qp.setPen(self.transformationEngine.choosePen(idx))
                else:
                    break

                if self.transformationEngine.chooseBrush(idx) is not None:
                    qp.setBackgroundMode(1)
                    qp.setBackground(self.transformationEngine.chooseBrush(idx))

                c = self.getDisplayablePage()[idx]

                hex_s = str(hex(c)[2:]).zfill(2) + ' '

                if dx < 0:
                    cemu.writeAt((self.COLUMNS - (column + 1)) * 3, i, hex_s, noBackgroudOnSpaces=True)
                    cemu.writeAt(textBegining + self.COLUMNS - (column + 1), i, self.cp437(c))

                if dx > 0:
                    cemu.writeAt(column * 3, i, hex_s, noBackgroudOnSpaces=True)
                    cemu.writeAt(textBegining + column, i, self.cp437(c))

                qp.setBackgroundMode(0)

        qp.end()

    def scroll_v(self, dy):
        self.qpix.scroll(0, dy * self.fontHeight, self.qpix.rect())

        qp = QtGui.QPainter()

        qp.begin(self.qpix)
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        factor = abs(dy)

        cemu = ConsoleEmulator(qp, self.ROWS, self.CON_COLUMNS)

        if dy < 0:
            cemu.gotoXY(0, self.ROWS - factor)
            qp.fillRect(0, (self.ROWS - factor) * self.fontHeight, self.fontWidth * self.CON_COLUMNS,
                        factor * self.fontHeight + self.SPACER, self.backgroundBrush)

        if dy > 0:
            cemu.gotoXY(0, 0)
            qp.fillRect(0, 0, self.fontWidth * self.CON_COLUMNS, factor * self.fontHeight, self.backgroundBrush)

        page = self.transformationEngine.decorate()

        # how many rows
        for row in range(factor):
            # for every column
            for i in range(self.COLUMNS):

                if dy < 0:
                    # we write from top-down, so get index of the first row that will be displayed
                    # this is why we have factor - row
                    idx = i + (self.ROWS - (factor - row)) * self.COLUMNS
                if dy > 0:
                    idx = i + (self.COLUMNS * row)

                qp.setPen(self.transformationEngine.choosePen(idx))

                if self.transformationEngine.chooseBrush(idx) is not None:
                    qp.setBackgroundMode(1)
                    qp.setBackground(self.transformationEngine.chooseBrush(idx))

                if len(self.getDisplayablePage()) > idx:
                    c = self.getDisplayablePage()[idx]
                else:
                    break

                if i == self.COLUMNS - 1:
                    hex_s = str(hex(c)[2:]).zfill(2)
                else:
                    hex_s = str(hex(c)[2:]).zfill(2) + ' '

                # write hex representation
                cemu.write(hex_s, noBackgroudOnSpaces=True)

                # save hex position
                x, y = cemu.getXY()
                # write text
                cemu.writeAt(self.COLUMNS * 3 + self.gap + (i % self.COLUMNS), y, self.cp437(c))

                # go back to hex chars
                cemu.gotoXY(x, y)

                qp.setBackgroundMode(0)

            cemu.writeLn()
        qp.end()

    def draw(self, refresh=False, row=0, howMany=0):
        if self.refresh or refresh:
            qp = QtGui.QPainter()
            qp.begin(self.qpix)

            if not howMany:
                howMany = self.ROWS

            self.drawTextMode(qp, row=row, howMany=howMany)
            self.refresh = False
            qp.end()

        self.drawAdditionals()

    def drawTextMode(self, qp, row=0, howMany=1):

        # draw background
        qp.fillRect(0, row * self.fontHeight, self.CON_COLUMNS * self.fontWidth,
                    howMany * self.fontHeight + self.SPACER, self.backgroundBrush)

        # set text pen&font
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        cemu = ConsoleEmulator(qp, self.ROWS, self.CON_COLUMNS)

        page = self.transformationEngine.decorate()

        cemu.gotoXY(0, row)

        for i, c in enumerate(self.getDisplayablePage()[row * self.COLUMNS:(
            row + howMany) * self.COLUMNS]):  # TODO: does not apply all decorators

            w = i + row * self.COLUMNS

            if (w + 1) % self.COLUMNS == 0:
                hex_s = str(hex(c)[2:]).zfill(2)
            else:
                hex_s = str(hex(c)[2:]).zfill(2) + ' '

            qp.setPen(self.transformationEngine.choosePen(w))

            if self.transformationEngine.chooseBrush(w) is not None:
                qp.setBackgroundMode(1)
                qp.setBackground(self.transformationEngine.chooseBrush(w))

            # write hex representation
            cemu.write(hex_s, noBackgroudOnSpaces=True)
            # save hex position
            x, y = cemu.getXY()
            # write text
            cemu.writeAt(self.COLUMNS * 3 + self.gap + (w % self.COLUMNS), y, self.cp437(c))
            # go back to hex chars
            cemu.gotoXY(x, y)
            if (w + 1) % self.COLUMNS == 0:
                cemu.writeLn()

            qp.setBackgroundMode(0)

    def moveCursor(self, direction):
        # TODO: have to move this, don't like it
        if self.isInEditMode():
            if not self.highpart:
                self.highpart = True

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

    def drawCursor(self, qp):
        qp.setBrush(QtGui.QColor(255, 255, 0))
        if self.isInEditMode():
            qp.setBrush(QtGui.QColor(255, 102, 179))

        cursorX, cursorY = self.cursor.getPosition()

        columns = self.HexColumns[self.idxHexColumns]
        if cursorX > columns:
            self.cursor.moveAbsolute(columns - 1, cursorY)

        # get cursor position again, maybe it was moved
        cursorX, cursorY = self.cursor.getPosition()

        qp.setOpacity(0.8)
        if self.isInEditMode():
            qp.setOpacity(0.5)
        # cursor on text
        qp.drawRect((self.COLUMNS * 3 + self.gap + cursorX) * self.fontWidth, cursorY * self.fontHeight + 2,
                    self.fontWidth, self.fontHeight)

        # cursor on hex
        if not self.isInEditMode():
            qp.drawRect(cursorX * 3 * self.fontWidth, cursorY * self.fontHeight + 2, 2 * self.fontWidth,
                        self.fontHeight)
        else:
            if self.highpart:
                qp.drawRect(cursorX * 3 * self.fontWidth, cursorY * self.fontHeight + 2, 1 * self.fontWidth,
                            self.fontHeight)
            else:
                qp.drawRect(cursorX * 3 * self.fontWidth + self.fontWidth, cursorY * self.fontHeight + 2,
                            1 * self.fontWidth, self.fontHeight)

        qp.setOpacity(1)

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

        if str(event.text()).lower() in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e',
                                         'f']:

            offs = self.getCursorOffsetInPage()

            b = self.dataModel.getBYTE(self.dataModel.getOffset() + offs)
            if b is None:
                return

            z = int(str(event.text()), 16)

            # compute nibble
            if self.highpart:
                b = ((z << 4) | (b & 0x0F)) & 0xFF
            else:
                b = ((b & 0xF0) | (z & 0x0F)) & 0xFF

            block = modifiers == QtCore.Qt.AltModifier and self.selector.getCurrentSelection()

            # change block or single byte
            if block:
                # multiple, with ALT key
                if self.selector.getCurrentSelection():
                    u, v = self.selector.getCurrentSelection()

                    for x in range(u, v):
                        b = self.dataModel.getBYTE(x)
                        if self.highpart:
                            b = ((z << 4) | (b & 0x0F)) & 0xFF
                        else:
                            b = ((b & 0xF0) | (z & 0x0F)) & 0xFF

                        self.dataModel.setData_b(x, chr(b))
            else:
                self.dataModel.setData_b(self.dataModel.getOffset() + offs, chr(b))

            if block:
                self.transformationEngine = RangePen(self.original_textdecorator, u, v,
                                                     QtGui.QPen(QtGui.QColor(218, 94, 242), 0, QtCore.Qt.SolidLine),
                                                     ignoreHighlights=True)
            else:
                z = self.dataModel.getOffset() + offs
                # TODO: sa nu se repete, tre original_transformengine
                self.transformationEngine = RangePen(self.original_textdecorator, z, z + 0,
                                                     QtGui.QPen(QtGui.QColor(218, 94, 242), 0, QtCore.Qt.SolidLine),
                                                     ignoreHighlights=True)

            # se if we are at end of row, we must also redraw previous line
            highpart = self.highpart

            # for block mode, move cursor
            if not block:
                x, old_y = self.cursor.getPosition()

                if not self.highpart:
                    self.moveCursor(Directions.Right)

                x, y = self.cursor.getPosition()

            if highpart:
                self.highpart = False
            else:
                self.highpart = True

            if block:
                self.draw(refresh=True)
            else:
                self.draw(refresh=True, row=y, howMany=1)
                if y > old_y:
                    self.draw(refresh=True, row=y - 1, howMany=1)

    def handleKeyEvent(self, modifiers, key, event=None):
        if event.type() == QtCore.QEvent.KeyRelease:
            if key == QtCore.Qt.Key_Shift:
                self.stopSelection()
                return True

        if event.type() == QtCore.QEvent.KeyPress:

            if modifiers == QtCore.Qt.ShiftModifier:
                keys = [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up,
                        QtCore.Qt.Key_End, QtCore.Qt.Key_Home]
                if key in keys:
                    self.startSelection()

                if key == QtCore.Qt.Key_Question:
                    self.annotationWindow()

            if modifiers == QtCore.Qt.AltModifier:
                if key == QtCore.Qt.Key_A:
                    self.add_annotation(1)
                    return True

            if modifiers == QtCore.Qt.ControlModifier:
                if key == QtCore.Qt.Key_A:
                    self.add_annotation(2)

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

            else:  # selif modifiers == QtCore.Qt.NoModifier:

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

                if key == QtCore.Qt.Key_F6:
                    self.changeHexColumns()
                    x, y = self.cursor.getPosition()

                    columns = self.HexColumns[self.idxHexColumns]
                    if x > columns:
                        self.cursor.moveAbsolute(columns - 1, y)
                    self.addop((self.draw,))

                if self.isInEditMode():
                    self.handleEditMode(modifiers, key, event)

                return True

        return False

    def isEditable(self):
        return True

    def setEditMode(self, mode):
        super(HexViewMode, self).setEditMode(mode)
        if not mode:
            self.highpart = True
            self.transformationEngine = self.original_textdecorator
            self.transformationEngine.reset()
            self.draw(refresh=True)

    def addop(self, t):
        self.Ops.append(t)

    def getHeaderInfo(self):
        s = ''
        for i in range(self.HexColumns[self.idxHexColumns]):
            s += '{0} '.format('{0:x}'.format(i).zfill(2))

        s += self.gap * ' ' + 'Text'
        return s

    def annotationWindow(self):
        w = self.ann_w.treeWidget

        w.setDragEnabled(True)
        w.viewport().setAcceptDrops(True)
        w.setDropIndicatorShown(True)

        self.ann_w.show()

    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def selectionChanged(self, selected, deselected):
        item = self.ann_w.treeWidget.currentItem()
        if item:
            offset = item.getOffset()
            size = item.getSize()
            u = offset
            v = offset + size
            self.selector.addSelection((u, v, QtGui.QBrush(QtGui.QColor(125, 255, 0)), 0.2),
                                       type=TextSelection.SelectionType.NORMAL)
            self.goTo(u)

    @QtCore.pyqtSlot("QTreeWidgetItem*, int")
    def itemChanged(self, item, column):

        ID_NAME = 0
        ID_DESCRIPTION = 4

        s = str(item.text(column))

        if column == ID_NAME:
            item.setName(s)

        if column == ID_DESCRIPTION:
            item.setDescription(s)

    def add_annotation(self, mode):
        QtCore.QObject.connect(self.ann_w.treeWidget.selectionModel(),
                               QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.selectionChanged)
        QtCore.QObject.connect(self.ann_w.treeWidget, QtCore.SIGNAL('itemChanged(QTreeWidgetItem*, int)'),
                               self.itemChanged)

        ID_NAME = 0
        ID_OFFSET = 1
        ID_SIZE = 2
        ID_VALUE = 3
        ID_DESCRIPTION = 4
        ID_COLOR = 5

        if self.selector.getCurrentSelection():
            u, v = self.selector.getCurrentSelection()
        else:
            return

        import random
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)

        opacity = 0.4
        if mode == 2:
            opacity = 0.25

        qcolor = QtGui.QColor(r, g, b)
        added = self.selector.addSelection((u, v, QtGui.QBrush(qcolor), opacity),
                                           type=TextSelection.SelectionType.PERMANENT)

        #        if not added:
        #            return

        t = self.ann_w.treeWidget

        row = AnnonItem(None, self.ann_w.treeWidget, qcolor.name())
        row.setFlags(QtCore.Qt.ItemIsSelectable |
                     QtCore.Qt.ItemIsEnabled |
                     QtCore.Qt.ItemIsEditable |
                     QtCore.Qt.ItemIsDropEnabled |
                     QtCore.Qt.ItemIsDragEnabled)

        t.setAcceptDrops(True)
        t.setDragEnabled(True)
        t.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

        delegate = NoEditDelegate()
        t.setItemDelegateForColumn(1, delegate)
        t.setItemDelegateForColumn(2, delegate)
        t.setItemDelegateForColumn(3, delegate)
        t.setItemDelegateForColumn(5, delegate)

        row.setName(self.ann_w.newFieldName())
        row.setOffset(u)
        # row.setText(ID_NAME, 'field_0')
        # row.setText(ID_OFFSET, hex(u))

        size = v - u
        # row.setText(ID_SIZE, hex(size))
        row.setSize(size)

        value = ''
        if size == 1:
            value = self.dataModel.getBYTE(u, asString=True)
        elif size == 2:
            value = self.dataModel.getWORD(u, asString=True)
        elif size == 4:
            value = self.dataModel.getDWORD(u, asString=True)
        else:
            value = repr(str(self.dataModel.getStream(u, v)))

        # row.setText(ID_VALUE, value)
        row.setValue(value)

        # cmb.setCurrentIndex(cmb.findData(w))

        if mode == 2:
            self.ann_w.treeWidget.addTopLevelItem(row)

        if mode == 1:
            selected = t.selectedItems()
            if len(selected) == 1:
                selected = selected[0]
            else:
                selected = t.topLevelItem(0)

            if selected:
                selected.addChild(row)

        t.expandItem(row)

        # cmb = QColorButton()
        # cmb.setColor(qcolor.name())
        # self.ann_w.treeWidget.setItemWidget(row, ID_COLOR, cmb)

        self.ann_w.treeWidget.setItemWidget(row, ID_COLOR, row.cmb)

        # self.ann_w.treeWidget.openPersistentEditor(row, 0)
        # self.ann_w.treeWidget.editItem(row, 0)
        # self.ann_w.treeWidget.editItem(row, 3)


class NoEditDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(NoEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        return None


class AnnonItem(QtWidgets.QTreeWidgetItem):
    ID_NAME = 0
    ID_OFFSET = 1
    ID_SIZE = 2
    ID_VALUE = 3
    ID_DESCRIPTION = 4
    ID_COLOR = 5

    def __init__(self, x, parent, color):
        super(AnnonItem, self).__init__(x)
        self._color = color
        self._t_parent = parent

        self.cmb = QColorButton()
        self.cmb.setColor(self._color)

        # self._t_parent.setItemWidget(self, self.ID_COLOR, self.cmb)

    def setName(self, name):
        self._name = name
        self.setText(self.ID_NAME, name)

    def getName(self):
        return self._name

    def setOffset(self, offset):
        self._offset = offset
        self.setText(self.ID_OFFSET, hex(offset))

    def getOffset(self):
        return self._offset

    def setSize(self, size):
        self._size = size
        self.setText(self.ID_SIZE, hex(size))

    def getSize(self):
        return self._size

    def setValue(self, value):
        self._value = value
        self.setText(self.ID_VALUE, value)

    def getValue(self):
        return self._value

    def setDescription(self, description):
        self._description = description
        self.setText(self.ID_DESCRIPTION, description)

    def getDescription(self):
        return self._description


class QColorButton(QtWidgets.QPushButton):
    """
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).
    """

    '''
    based on http://martinfitzpatrick.name/article/qcolorbutton-a-color-selector-tool-for-pyqt/
    '''
    colorChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self.setMaximumWidth(32)
        self.pressed.connect(self.onColorPicker)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit()

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        """
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        """
        dlg = QtGui.QColorDialog(QtGui.QColor(self._color), None)

        # if self._color:
        #    dlg.setCurrentColor(QtGui.QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            self.setColor(None)

        return super(QColorButton, self).mousePressEvent(e)


class ComboBoxItem(QtWidgets.QComboBox):
    def __init__(self, item, column):
        super(ComboBoxItem, self).__init__()

        self.item = item
        self.column = column


class Annotation(QtWidgets.QDialog):
    _fieldIdx = 0

    def __init__(self, parent, view):
        super(Annotation, self).__init__(parent)

        self.parent = parent
        self.view = view
        self.oshow = super(Annotation, self).show

        root = os.path.dirname(os.path.realpath(__file__))
        self.ui = loadUi(os.path.join(root, 'annotation.ui'), baseinstance=self)

        #        self.ei = ImportsEventFilter(plugin, self.ui.treeWidgetImports)

        self.ei = treeEventFilter(view, self.ui.treeWidget)
        self.ui.treeWidget.installEventFilter(self.ei)

        self.initUI()

    def newFieldName(self):
        name = 'field_{}'.format(self._fieldIdx)
        self._fieldIdx += 1
        return name

    def show(self):
        # TODO: remember position? resize plugin windows when parent resize?
        pwidth = self.parent.parent.size().width()
        pheight = self.parent.parent.size().height()

        width = self.ui.treeWidget.size().width() + 15
        height = self.ui.treeWidget.size().height() + 15

        self.setGeometry(pwidth - width - 15, pheight - height, width, height)
        self.setFixedSize(width, height)

        self.oshow()

    def initUI(self):
        self.setWindowTitle('Annotations')
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+/"), self, self.close, self.close)


class treeEventFilter(QtCore.QObject):
    def __init__(self, view, widget):
        super(QtCore.QObject, self).__init__()
        self.widget = widget
        self.view = view

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Delete:
                # get RVA column from treeView

                item = self.widget.currentItem()

                offset = item.getOffset()  # int(str(item.text(1)),0)
                size = item.getSize()  # int(str(item.text(2)),0)
                u = offset
                v = offset + size

                self.view.selector.removeSelection(u, v, TextSelection.SelectionType.PERMANENT)
                # TODO: remove tree!

                item.parent().removeChild(item)
                # self.widget.takeTopLevelItem(self.widget.indexOfTopLevelItem(item))
                # rva = self.widget.indexFromItem(item, 1).data().toString()

        return False
