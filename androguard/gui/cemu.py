from builtins import object
from PyQt5 import QtGui

import logging
log = logging.getLogger("androguard.gui")


class Cursor(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def moveAbsolute(self, x, y):
        self.x = x
        self.y = y

    def getPosition(self):
        return self.x, self.y


def enum(**enums):
    return type('Enum', (), enums)


Directions = enum(Left=1, Right=2, Up=3, Down=4, End=5, Home=6, CtrlEnd=7, CtrlHome=8)


class ConsoleEmulator(object):
    def __init__(self, qp, rows, cols):
        self.qp = qp
        self._x = 0
        self._y = 0
        self._rows = rows
        self._cols = cols

        fm = QtGui.QFontMetrics(self.qp.font())
        self.fontWidth = fm.width('a')
        self.fontHeight = fm.height()

    def incrementPosition(self):
        if self._x < self._cols - 1:
            self._x += 1
        else:
            self._x = 0
            self._y += 1

    def newLine(self):
        self.LF()
        self.CR()

    def LF(self):
        if self._y < self._rows:
            self._y += 1

    def CR(self):
        self._x = 0

    def _validatePosition(self, x, y):
        if x >= self._cols:
            log.warning("x > cols")
            return False

        if y >= self._rows:
            log.warning("y > rows")
            return False
        return True

    def write(self, s, noBackgroudOnSpaces=False):
        background = self.qp.backgroundMode()
        for c in s:
            if self._validatePosition(self._x, self._y):
                if noBackgroudOnSpaces and c == ' ':
                    self.qp.setBackgroundMode(0)

                self.qp.drawText(self._x * self.fontWidth, self.fontHeight + self._y * self.fontHeight, c)
                self.incrementPosition()
        self.qp.setBackgroundMode(background)

    def write_c(self, c, noBackgroudOnSpaces=False):
        background = self.qp.backgroundMode()
        if self._validatePosition(self._x, self._y):
            if noBackgroudOnSpaces and c == ' ':
                self.qp.setBackgroundMode(0)

            self.qp.drawText(self._x * self.fontWidth, self.fontHeight + self._y * self.fontHeight, c)
            self.incrementPosition()
        self.qp.setBackgroundMode(background)

    def getXY(self):
        return self._x, self._y

    def writeAt(self, x, y, s, noBackgroudOnSpaces=False):
        self.gotoXY(x, y)
        self.write(s, noBackgroudOnSpaces)

    def writeAt_c(self, x, y, c, noBackgroudOnSpaces=False):
        self.gotoXY(x, y)
        self.write_c(c, noBackgroudOnSpaces)

    def writeLn(self):
        if True:  # self._validatePosition(self._x, self._y):
            self._y += 1
            self._x = 0

    def gotoXY(self, x, y):
        if self._validatePosition(x, y):
            self._x = x
            self._y = y
