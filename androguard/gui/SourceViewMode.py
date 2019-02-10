from __future__ import division
from builtins import range
from androguard.gui.ViewMode import ViewMode
from androguard.gui.cemu import ConsoleEmulator
from androguard.gui import TextSelection

from PyQt5 import QtGui, QtCore


class SourceViewMode(ViewMode):
    def __init__(self, themes, width, height, data, cursor, widget=None):
        super(SourceViewMode, self).__init__()

        self.themes = themes

        self.dataModel = data
        self.addHandler(self.dataModel)

        self.width = width
        self.height = height

        self.cursor = cursor
        self.widget = widget

        self.refresh = True

        # background brush
        self.backgroundBrush = QtGui.QBrush(self.themes['background'])

        # text font
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
        self.Ops = []
        self.newPix = None

        self.selector = TextSelection.DefaultSelection(themes, self)

        self.LINES = self.dataModel.current_class.get_source().split('\n')

    @property
    def fontWidth(self):
        return self._fontWidth

    @property
    def fontHeight(self):
        return self._fontHeight

    def setTransformationEngine(self, engine):
        self.transformationEngine = engine

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def resize(self, width, height):
        self.width = width - width % self.fontWidth
        self.height = height - height % self.fontHeight
        self.computeTextArea()
        self.qpix = self._getNewPixmap(self.width, self.height + self.SPACER)
        self.refresh = True

    def computeTextArea(self):
        self.COLUMNS = self.width // self.fontWidth
        self.ROWS = self.height // self.fontHeight
        self.notify(self.ROWS, self.COLUMNS)

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

    def getDataModel(self):
        return self.dataModel

    def getPageOffset(self):
        return self.dataModel.getOffset()

    def getGeometry(self):
        return self.COLUMNS, self.ROWS

    def draw(self, refresh=False):
        if self.dataModel.getOffset() in self.Paints:
            self.refresh = False
            self.qpix = QtGui.QPixmap(self.Paints[self.dataModel.getOffset()])
            self.drawAdditionals()
            return

        if self.refresh or refresh:
            qp = QtGui.QPainter()
            qp.begin(self.qpix)
            self.drawTextMode(qp)
            self.refresh = False
            qp.end()

        self.drawAdditionals()

    def drawAdditionals(self):
        self.newPix = self._getNewPixmap(self.width, self.height + self.SPACER)
        qp = QtGui.QPainter()
        qp.begin(self.newPix)
        qp.setWindow(-50, 0, self.COLUMNS * self.fontWidth, self.ROWS * self.fontHeight)

        qp.drawPixmap(0, 0, self.qpix)

        # self.transformationEngine.decorateText()

        # highlight selected text
        self.selector.highlightText()

        # draw other selections
        self.selector.drawSelections(qp)

        # draw our cursor
        self.drawCursor(qp)
        self.drawLine(qp)

        qp.end()

    def drawLine(self, qp):
        qp.fillRect(-50, 0, 50, self.ROWS * self.fontHeight, self.backgroundBrush)

    def drawTextMode(self, qp):
        # draw background
        qp.fillRect(0, 0, self.COLUMNS * self.fontWidth, self.ROWS * self.fontHeight, self.backgroundBrush)

        # set text pen&font
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        cemu = ConsoleEmulator(qp, self.ROWS, self.COLUMNS)
        # ast = self.dataModel.current_class.get_ast()

        for i in range(self.ROWS):
            if i < len(self.LINES):
                line = self.LINES[i]
                cemu.writeAt(0, i, line)

    def getCursorOffsetInPage(self):
        return 0

    def getCursorAbsolutePosition(self):
        offset = self.getCursorOffsetInPage()
        return self.dataModel.getOffset() + offset

    def drawCursor(self, qp):
        cursorX, cursorY = self.cursor.getPosition()

        xstart = cursorX
        width = 1

        qp.setBrush(QtGui.QColor(255, 255, 0))

        qp.setOpacity(0.5)
        qp.drawRect(xstart * self.fontWidth, cursorY * self.fontHeight, width * self.fontWidth, self.fontHeight + 2)
        qp.setOpacity(1)

    def handleKeyEvent(self, modifiers, key, event=None):
        pass

    def getColumnsbyRow(self, row):
        return 0
