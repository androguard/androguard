from __future__ import division

from PyQt5 import QtGui, QtCore
from builtins import hex
from builtins import range

from androguard.core.bytecodes import dvm
from androguard.gui import TextSelection
from androguard.gui.ViewMode import ViewMode
from androguard.gui.cemu import ConsoleEmulator, Directions

import logging
log = logging.getLogger("androguard.gui")

MNEMONIC_COLUMN = 30
MNEMONIC_WIDTH = 30


class InstructionView(object):
    def __init__(self, ins):
        self.ins = ins
        self._indexTable = []
        self._Operands = []
        self._Comments = []
        self.loaded = False

    def AddComment(self, cmt):
        self._Comments.append(cmt)

    def Load(self):
        if self.loaded:
            return

        H = self.get_hex().split(' ')
        for i, h in enumerate(H):
            self._indexTable += [(i * 3, len(h), h)]

        self._indexTable += [(MNEMONIC_COLUMN, len(self.get_name()), self.get_name())]

        i = 0
        offset = 0
        for operand in self.ins.get_operands(0):
            value = None
            if operand[0] == dvm.OPERAND_REGISTER:
                value = [operand[0], "v%d" % operand[1]]

            elif operand[0] == dvm.OPERAND_LITERAL:
                value = [operand[0], "%d" % operand[1]]

            elif operand[0] == dvm.OPERAND_RAW:
                value = [operand[0], "%s" % operand[1]]

            elif operand[0] == dvm.OPERAND_OFFSET:
                value = [operand[0], "%d" % operand[1]]

            elif operand[0] & dvm.OPERAND_KIND:
                if operand[0] == (dvm.OPERAND_KIND + dvm.KIND_STRING):
                    value = [operand[0], "%s" % operand[2]]

                elif operand[0] == (dvm.OPERAND_KIND + dvm.KIND_METH):
                    value = [operand[0], "%s" % operand[2]]

                elif operand[0] == (dvm.OPERAND_KIND + dvm.KIND_FIELD):
                    value = [operand[0], "%s" % operand[2]]

                elif operand[0] == (dvm.OPERAND_KIND + dvm.KIND_TYPE):
                    value = [operand[0], "%s" % operand[2]]

            if value:
                if offset > 0:
                    offset += 1

                t = (offset + MNEMONIC_COLUMN + MNEMONIC_WIDTH, len(value[1]), value[1])
                self._indexTable += [t]
                self._Operands.append(value)
                offset += len(value[1])

        self.loaded = True

    def get_hex(self):
        return self.ins.get_hex()

    def get_length(self):
        return self.ins.get_length() * 2

    def get_name(self):
        return self.ins.get_name()

    def get_operands(self, idx=-1):
        return self._Operands

    def get_symbol(self):
        return None

    def get_output(self):
        return self.ins.get_output()

    def tokens(self):
        return self._indexTable

    def get_comments(self):
        return self._Comments

    @property
    def indexTable(self):
        return self._indexTable

    def getSelectionWidth(self, cx):
        for i, t in enumerate(self.indexTable):
            idx, length, value = t
            if cx == idx:
                return length

        return 0

    def getEndCursor(self):
        idx, length, value = self.indexTable[-1]
        return idx

    def getNearestCursor(self, cx):
        if cx > self.getEndCursor():
            return self.getEndCursor()

        i = len(self.indexTable) - 1
        while i > 0:
            idx, length, value = self.indexTable[i]
            if cx >= idx:
                return idx
            i -= 1

        return 0

    def getNextCursor(self, cx, direction=''):
        for i, t in enumerate(self.indexTable):
            idx, length, value = t
            if cx == idx:
                break

        if direction == Directions.Right:
            if i < len(self.indexTable) - 1:
                idx, length, value = self.indexTable[i + 1]
            else:
                return 0, 1

        if direction == Directions.Left:
            if i > 0:
                idx, length, value = self.indexTable[i - 1]
            else:
                return 0, -1

        return idx, 0

    def getSelectedToken(self, cx):
        for i, t in enumerate(self._indexTable):
            idx, length, value = t
            if cx == idx:
                return t

        return None, None, None


class DisasmViewMode(ViewMode):
    def __init__(self, themes, width, height, data, cursor, widget=None):
        super(DisasmViewMode, self).__init__()

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
        self.font = themes['font']

        # font metrics. assume font is monospaced
        self.font.setKerning(False)
        self.font.setFixedPitch(True)
        fm = QtGui.QFontMetrics(self.font)
        self._fontWidth = fm.width('a')
        self._fontHeight = fm.height()

        self.FlowHistory = []
        self.CACHE_OPCODES = []
        self.CACHE_IDX_OPCODES = {}
        self.CACHE_IDX_OPCODES_OFF = {}

        self.OPCODES = []

        vm_analysis = self.dataModel.dx

        methods = [i for i in self.dataModel.current_class.get_methods()]
        log.debug(methods)
        methods = sorted(methods, key=lambda x: x.get_address(), reverse=True)

        offset = 0
        cnt = 0
        for method in methods:
            mx = vm_analysis.get_method(method)
            for DVMBasicMethodBlockInstruction in method.get_instructions():
                # for DVMBasicMethodBlock in mx.basic_blocks.gets():
                #    for DVMBasicMethodBlockInstruction in DVMBasicMethodBlock.get_instructions():
                ins = InstructionView(DVMBasicMethodBlockInstruction)
                self.CACHE_OPCODES.append(ins)
                self.CACHE_IDX_OPCODES[offset] = ins
                self.CACHE_IDX_OPCODES_OFF[offset] = cnt
                offset += ins.get_length()
                cnt += 1

        self.max_offset = offset

        log.debug(sorted(self.CACHE_IDX_OPCODES_OFF.keys()))

        self.textPen = QtGui.QPen(self.themes['pen'], 0, QtCore.Qt.SolidLine)
        self.resize(width, height)

        self.Paints = {}

        self.Ops = []
        self.newPix = None

        self.selector = TextSelection.DisasmSelection(themes, self)

    def GetLengthOpcodes(self):
        length = 0
        for i in self.CACHE_OPCODES:
            length += i.get_length()
        return length

    def FeedOpcodes(self, cnt):
        log.debug('FEED %s', cnt)
        self.OPCODES = []
        for i in range(0, min(cnt, len(self.CACHE_OPCODES))):
            ins = self.CACHE_OPCODES[i]
            ins.Load()
            self.OPCODES.append(ins)

    @property
    def fontWidth(self):
        return self._fontWidth

    @property
    def fontHeight(self):
        return self._fontHeight

    def setTransformationEngine(self, engine):
        self.transformationEngine = engine

    def resize(self, width, height):
        self.width = width - width % self.fontWidth
        self.height = height - height % self.fontHeight
        self.computeTextArea()
        self.qpix = self._getNewPixmap(self.width, self.height + self.SPACER)
        self.refresh = True

        self.FeedOpcodes(self.ROWS)

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

    def getPageOffset(self):
        return self.dataModel.getOffset()

    def getGeometry(self):
        return self.COLUMNS, self.ROWS

    def getDataModel(self):
        return self.dataModel

    def startSelection(self):
        self.selector.startSelection()

    def stopSelection(self):
        self.selector.stopSelection()

    def getCursorOffsetInPage(self):
        x, y = self.cursor.getPosition()

        preY = sum([asm.get_length() for asm in self.OPCODES[:y]])

        if len(self.OPCODES) - 1 < y:
            return 0

        asm = self.OPCODES[y]

        if x < len(asm.get_hex()):
            postY = x // 3
        else:
            postY = asm.get_length()

        return preY + postY

    def getCursorAbsolutePosition(self):
        offset = self.getCursorOffsetInPage()
        return self.dataModel.getOffset() + offset

    def drawCursor(self, qp):
        cursorX, cursorY = self.cursor.getPosition()

        log.debug("%s / %s", cursorX, cursorY)

        xstart = cursorX

        if cursorY not in self.OPCODES:
            log.warning("Impossible to find instruction at cursor %d, %d" % (cursorY, len(self.OPCODES)))
            return

        asm = self.OPCODES[cursorY]
        width = asm.getSelectionWidth(xstart)

        qp.setBrush(QtGui.QColor(255, 255, 0))

        qp.setOpacity(0.5)
        qp.drawRect(xstart * self.fontWidth,
                    cursorY * self.fontHeight,
                    width * self.fontWidth,
                    self.fontHeight + 2)
        qp.setOpacity(1)

    def drawSelected(self, qp):
        qp.setFont(self.font)

        cursorX, cursorY = self.cursor.getPosition()

        if len(self.OPCODES) - 1 < cursorY:
            return

        asm = self.OPCODES[cursorY]
        _, width, text = asm.getSelectedToken(cursorX)

        for i, asm in enumerate(self.OPCODES):
            for idx, length, value in asm.tokens():
                # skip current cursor position
                if cursorY == i and cursorX == idx:
                    continue

                # check every line, if match, select it
                if value == text:
                    qp.setOpacity(0.4)
                    brush = QtGui.QBrush(QtGui.QColor(0, 255, 0))
                    qp.fillRect(idx * self.fontWidth,
                                i * self.fontHeight + 2,
                                width * self.fontWidth,
                                self.fontHeight,
                                brush)
                    qp.setOpacity(1)

    def drawBranch(self, qp):
        qp.fillRect(-50, 0, 50, self.ROWS * self.fontHeight, self.backgroundBrush)

    def drawBranch2(self, qp):

        cursorX, cursorY = self.cursor.getPosition()

        if len(self.OPCODES) - 1 < cursorY:
            return

        asm = self.OPCODES[cursorY]

        if asm.isBranch():

            tsize = sum([o.size for o in self.OPCODES])
            msize = sum([o.size for o in self.OPCODES[:cursorY]])

            half = self.fontHeight // 2

            # branch address
            target = asm.branchAddress()
            if target is None:
                return

            screenVA = self._getVA(self.dataModel.getOffset())
            if screenVA < target < self._getVA(self.dataModel.getOffset()) + tsize - self.OPCODES[-1].size:
                # branch target is in screen

                sz = 0
                for i, t in enumerate(self.OPCODES):
                    sz += t.size
                    if sz + self._getVA(self.dataModel.getOffset()) >= target:
                        break

                qp.setPen(QtGui.QPen(QtGui.QColor(0, 192, 0), 1, QtCore.Qt.SolidLine))

                # draw the three lines

                qp.drawLine(-5, cursorY * self.fontHeight + self.fontHeight // 2, -30, cursorY * self.fontHeight + half)

                qp.drawLine(-30, cursorY * self.fontHeight + self.fontHeight // 2, -30,
                            (i + 1) * self.fontHeight + half)

                qp.drawLine(-30, (i + 1) * self.fontHeight + half, -15, (i + 1) * self.fontHeight + half)

                # draw arrow
                points = [QtCore.QPoint(-15, (i + 1) * self.fontHeight + half - 5),
                          QtCore.QPoint(-15, (i + 1) * self.fontHeight + half + 5),
                          QtCore.QPoint(-5, (i + 1) * self.fontHeight + half), ]
                needle = QtGui.QPolygon(points)
                qp.setBrush(QtGui.QBrush(QtGui.QColor(0, 128, 0)))
                qp.drawPolygon(needle)



            elif target > screenVA:
                # branch is at greater address, out of screen

                qp.setPen(QtGui.QPen(QtGui.QColor(0, 192, 0), 1, QtCore.Qt.DotLine))

                # draw the two lines
                qp.drawLine(-5, cursorY * self.fontHeight + self.fontHeight // 2, -30, cursorY * self.fontHeight + half)
                qp.drawLine(-30, cursorY * self.fontHeight + self.fontHeight // 2, -30,
                            (self.ROWS - 2) * self.fontHeight + half)

                # draw arrow
                points = [QtCore.QPoint(-25, (self.ROWS - 2) * self.fontHeight + half),
                          QtCore.QPoint(-35, (self.ROWS - 2) * self.fontHeight + half),
                          QtCore.QPoint(-30, (self.ROWS - 2) * self.fontHeight + 2 * half), ]
                needle = QtGui.QPolygon(points)
                qp.setBrush(QtGui.QBrush(QtGui.QColor(0, 128, 0)))
                qp.drawPolygon(needle)

            else:
                # upper arrow
                # branch is at lower address, out of screen

                qp.setPen(QtGui.QPen(QtGui.QColor(0, 192, 0), 1, QtCore.Qt.DotLine))

                # draw the two lines
                qp.drawLine(-5, cursorY * self.fontHeight + self.fontHeight // 2, -30, cursorY * self.fontHeight + half)
                qp.drawLine(-30, cursorY * self.fontHeight + self.fontHeight // 2, -30, 1 * self.fontHeight + half)

                # draw arrow
                points = [QtCore.QPoint(-25, 1 * self.fontHeight + half),
                          QtCore.QPoint(-35, 1 * self.fontHeight + half),
                          QtCore.QPoint(-30, 1 * self.fontHeight), ]
                needle = QtGui.QPolygon(points)
                qp.setBrush(QtGui.QBrush(QtGui.QColor(0, 128, 0)))
                qp.drawPolygon(needle)

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

        #        self.Paints[self.dataModel.getOffset()] = QtGui.QPixmap(self.qpix)
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

        self.drawBranch(qp)
        self.drawSelected(qp)

        qp.end()

    def _getNewPixmap(self, width, height):
        return QtGui.QPixmap(width, height)

    def getColumnsbyRow(self, row):
        if row < len(self.OPCODES):
            obj = self.OPCODES[row]
            return obj.get_length()
        else:
            return 0

    def _getVA(self, offset):
        if self.plugin:
            return self.plugin.hintDisasmVA(offset)
        return 0

    def _drawRow(self, qp, cemu, row, asm, offset=-1):
        log.debug('DRAW AN INSTRUCTION %s %s %s %s %s', asm, row, asm.get_name(), len(asm.get_operands(offset)), hex(self.getPageOffset()))

        qp.setPen(QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine))

        hex_data = asm.get_hex()

        # write hexdump
        cemu.writeAt(0, row, hex_data)

        # fill with spaces
        cemu.write((MNEMONIC_COLUMN - len(hex_data)) * ' ')

        # let's color some branch instr
        # if asm.isBranch():
        #    qp.setPen(QtGui.QPen(QtGui.QColor(255, 80, 0)))
        # else:
        qp.setPen(QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine))

        mnemonic = asm.get_name()
        cemu.write(mnemonic)

        # leave some spaces
        cemu.write((MNEMONIC_WIDTH - len(mnemonic)) * ' ')

        if asm.get_symbol():
            qp.setPen(QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine))
            cemu.write_c('[')

            qp.setPen(QtGui.QPen(QtGui.QColor('yellow'), 1, QtCore.Qt.SolidLine))
            cemu.write(asm.get_symbol())

            qp.setPen(QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine))
            cemu.write_c(']')

        self._write_operands(asm, qp, cemu, offset)
        self._write_comments(asm, qp, cemu, offset)

    def _write_comments(self, asm, qp, cemu, offset):
        comments = asm.get_comments()
        if comments:
            cemu.write(30 * ' ')

            qp.setPen(QtGui.QPen(QtGui.QColor(82, 192, 192), 1, QtCore.Qt.SolidLine))
            cemu.write('; "{0}"'.format(' '.join(comments)))

    def _write_operands(self, asm, qp, cemu, offset):
        qp.setPen(QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine))

        operands = asm.get_operands(offset)
        for operand in operands:
            qp.save()

            if operand[0] == dvm.OPERAND_REGISTER:
                qp.setPen(QtGui.QPen(QtGui.QColor('white')))
                cemu.write("%s" % operand[1])

            elif operand[0] == dvm.OPERAND_LITERAL:
                qp.setPen(QtGui.QPen(QtGui.QColor('yellow')))
                cemu.write("%s" % operand[1])

            elif operand[0] == dvm.OPERAND_RAW:
                qp.setPen(QtGui.QPen(QtGui.QColor('red')))
                cemu.write("%s" % operand[1])

            elif operand[0] == dvm.OPERAND_OFFSET:
                qp.setPen(QtGui.QPen(QtGui.QColor('purple')))
                cemu.write("%s" % operand[1])

            elif operand[0] & dvm.OPERAND_KIND:
                if operand[0] == (dvm.OPERAND_KIND + dvm.KIND_STRING):
                    qp.setPen(QtGui.QPen(QtGui.QColor('red')))
                    cemu.write("%s" % operand[1])

                elif operand[0] == (dvm.OPERAND_KIND + dvm.KIND_METH):
                    qp.setPen(QtGui.QPen(QtGui.QColor('cyan')))
                    cemu.write("%s" % operand[1])

                elif operand[0] == (dvm.OPERAND_KIND + dvm.KIND_FIELD):
                    qp.setPen(QtGui.QPen(QtGui.QColor('green')))
                    cemu.write("%s" % operand[1])

                elif operand[0] == (dvm.OPERAND_KIND + dvm.KIND_TYPE):
                    qp.setPen(QtGui.QPen(QtGui.QColor('blue')))
                    cemu.write("%s" % operand[1])

            cemu.write(" ")
            qp.restore()

    def _write_instruction2(self, asm, qp, cemu):
        s = asm.operands
        idx = 0
        qp.setPen(QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine))

        for tok in asm.lexer:
            if tok.lexpos > idx:
                cemu.write(s[idx:tok.lexpos])
                idx = tok.lexpos

            qp.save()
            if tok.type == 'REGISTER':
                qp.setPen(QtGui.QPen(QtGui.QColor('white')))

            if tok.type == 'NUMBER':
                qp.setPen(QtGui.QPen(QtGui.QColor('green')))

            cemu.write(tok.value)

            qp.restore()
            idx = tok.lexpos + len(tok.value)

        if idx < len(s):
            cemu.write(s[idx:])

    def drawTextMode(self, qp):
        log.debug('OFFSET %s', self.dataModel.getOffset())
        # draw background
        qp.fillRect(0, 0, self.COLUMNS * self.fontWidth, self.ROWS * self.fontHeight, self.backgroundBrush)

        # set text pen&font
        qp.setFont(self.font)
        qp.setPen(self.textPen)

        cemu = ConsoleEmulator(qp, self.ROWS, self.COLUMNS)

        offset = 0
        for i in range(self.ROWS):
            if i < len(self.OPCODES):
                asm = self.OPCODES[i]
                self._drawRow(qp, cemu, i, asm, offset)
                offset += asm.get_length()

    def _getRowInPage(self, offset):

        offset -= self.dataModel.getOffset()
        size = 0
        for i, asm in enumerate(self.OPCODES):
            if size + asm.get_length() > offset:
                return i
            size += asm.get_length()

        return None

    def _getOffsetOfRow(self, row):
        # of course, it could be done nicely, not like this
        size = 0
        for i, asm in enumerate(self.OPCODES):
            if i == row:
                return size

            size += asm.get_length()

        return None

    def goTo(self, offset):
        log.debug("GOTO %s", offset)

        tsize = sum([opcode.get_length() for opcode in self.OPCODES])

        if self.dataModel.getOffset() + tsize > offset > self.dataModel.getOffset():
            # if in current page, move cursor
            row = self._getRowInPage(offset)
            off_row = self._getOffsetOfRow(row)
            diff = offset - self.dataModel.getOffset() - off_row  # self.OPCODES[row].size

            if row is not None:
                self.cursor.moveAbsolute(diff * 3, row)

            self.draw(refresh=False)
        else:
            # else, move page
            self.dataModel.goTo(offset)
            self.FeedOpcodes(self.ROWS)
            self.cursor.moveAbsolute(0, 0)
            self.draw(refresh=True)

        # TODO: getDisplayablePage() won't contain what we want to disasm. we will use dataModel
        #      in this view, getDisplayablePage will contain disasm text, because that is what is displayed

        if self.widget:
            self.widget.update()

    def scrollPages(self, number, cachePix=None, pageOffset=None):
        self.scroll(0, -number * self.ROWS, cachePix=cachePix, pageOffset=pageOffset)

    def scroll_v(self, dy, cachePix=None, pageOffset=None):
        log.debug('scroll_v %s %s %s %s', dy, cachePix, pageOffset, hex(self.getCursorAbsolutePosition()))

        RowsToDraw = []
        factor = abs(dy)
        # repeat as many rows we have scrolled
        for row in range(factor):
            current_idx = None
            if dy < 0:
                tsize = sum([asm.get_length() for asm in self.OPCODES])
                current_offset = self.dataModel.getOffset() + tsize
                if current_offset not in self.CACHE_IDX_OPCODES_OFF:
                    log.debug('INVALID OFFSET %s', hex(current_offset))
                    return

                current_idx = self.CACHE_IDX_OPCODES_OFF[current_offset] - 1
                log.debug("IDX %s %s", current_idx, hex(current_offset))

                if current_idx + 1 >= len(self.CACHE_OPCODES):
                    log.debug('END OF DATA')
                    return

                current_idx += 1

            if dy >= 0:
                current_offset = self.dataModel.getOffset()
                current_idx = self.CACHE_IDX_OPCODES_OFF[current_offset]
                log.debug("IDX %s %s", current_idx, hex(current_offset))
                # start = self.CACHE_OPCODES[self.CACHE_IDX_OPCODES_OFF[self.getCursorAbsolutePosition()]-1]
                current_idx -= 1

            newins = self.CACHE_OPCODES[current_idx]

            if dy < 0:
                self.dataModel.slide(self.OPCODES[0].get_length())
                del self.OPCODES[0]

            if dy >= 0:
                self.dataModel.slide(-newins.get_length())
                del self.OPCODES[len(self.OPCODES) - 1]

            if dy < 0:
                self.OPCODES.append(newins)

            if dy > 0:
                self.OPCODES.insert(0, newins)

            if dy < 0:
                RowsToDraw.append((self.ROWS + row, newins))

            if dy > 0:
                RowsToDraw.append((-row - 1, newins))

        log.debug('ROW TO DRAW %s', RowsToDraw)
        if len(RowsToDraw) < abs(dy):
            # maybe we couldn't draw dy rows (possible we reached the beginning of the data to early), recalculate dy
            dy = len(RowsToDraw) * dy / abs(dy)
            factor = abs(dy)

        if not cachePix:
            self.qpix.scroll(0, dy * self.fontHeight, self.qpix.rect())

        qp = QtGui.QPainter()
        if cachePix:
            qp.begin(cachePix)
        else:
            qp.begin(self.qpix)

        qp.setFont(self.font)
        qp.setPen(self.textPen)

        # erase rows that will disappear
        if dy < 0:
            qp.fillRect(0, (self.ROWS - factor) * self.fontHeight, self.fontWidth * self.COLUMNS,
                        factor * self.fontHeight, self.backgroundBrush)

        if dy > 0:
            qp.fillRect(0, 0, self.fontWidth * self.COLUMNS, factor * self.fontHeight, self.backgroundBrush)

        cemu = ConsoleEmulator(qp, self.ROWS, self.COLUMNS)

        for row, asm in RowsToDraw:
            asm.Load()
            self._drawRow(qp, cemu, dy + row, asm)

        qp.end()

    def scroll(self, dx, dy, cachePix=None, pageOffset=None):
        log.debug('scroll %s %s %s %s %s', dx, dy, self.dataModel.inLimits((self.dataModel.getOffset() - dx)), 'offset',
              self.dataModel.getOffset())
        if dx != 0:
            if self.dataModel.inLimits((self.dataModel.getOffset() - dx)):
                self.dataModel.slide(dx)
                self.draw(refresh=True)
                # self.scroll_h(dx)

        if dy != 0:
            if dy > 0:
                if self.dataModel.getOffset() == 0:
                    log.debug('OFFSET == 0')
                    return

            if dy < 0:
                tsize = sum([asm.get_length() for asm in self.OPCODES])

                if self.dataModel.getOffset() + tsize == self.dataModel.getDataSize():
                    log.debug('END')
                    return

            self.scroll_v(dy, cachePix, pageOffset)

    def moveCursor(self, direction):
        cursorX, cursorY = self.cursor.getPosition()

        if direction == Directions.Left:
            asm = self.OPCODES[cursorY]

            if cursorX == 0:
                if cursorY == 0:
                    # if first line, scroll
                    self.scroll(0, 1)
                    self.cursor.moveAbsolute(0, 0)
                else:
                    # move to last token from previous line
                    asm_prev = self.OPCODES[cursorY - 1]
                    idx = asm_prev.getEndCursor()
                    self.cursor.moveAbsolute(idx, cursorY - 1)
            else:
                x, dy = asm.getNextCursor(cursorX, direction=Directions.Left)
                self.cursor.move(-(cursorX - x), dy)

        if direction == Directions.Right:
            asm = self.OPCODES[cursorY]
            x, dy = asm.getNextCursor(cursorX, direction=Directions.Right)

            if cursorY == self.ROWS - 1 and dy > 0:
                self.scroll(0, -1)
                self.cursor.moveAbsolute(0, cursorY)

            else:
                if cursorY + dy >= len(self.OPCODES):
                    dy = 0

                self.cursor.move(x - cursorX, dy)

        if direction == Directions.Down:
            if cursorY == self.ROWS - 1:
                # move cursor to first token
                self.scroll(0, -1)
                self.cursor.moveAbsolute(0, cursorY)
            else:
                # move next line, to nearest token on columns
                if cursorY + 1 < len(self.OPCODES):
                    asm = self.OPCODES[cursorY + 1]
                    x = asm.getNearestCursor(cursorX)
                    self.cursor.moveAbsolute(x, cursorY + 1)

        if direction == Directions.Up:
            if cursorY == 0:
                # move cursor to first token
                self.scroll(0, 1)
                self.cursor.moveAbsolute(0, cursorY)
            else:
                # move next line, to nearest token on columns
                asm = self.OPCODES[cursorY - 1]
                x = asm.getNearestCursor(cursorX)
                self.cursor.moveAbsolute(x, cursorY - 1)

        if direction == Directions.End:
            pass

        if direction == Directions.Home:
            self.cursor.moveAbsolute(0, 0)

        if direction == Directions.CtrlHome:
            self.goTo(0)

        if direction == Directions.CtrlEnd:
            self.dataModel.slideToLastPage()
            self.draw(refresh=True)
            self.cursor.moveAbsolute(self.COLUMNS - 1, self.ROWS - 1)

    def _followBranch(self):
        cursorX, cursorY = self.cursor.getPosition()
        asm = self.OPCODES[cursorY]

        if asm.isBranch():
            value = asm.branchAddress()
            if value:
                fofs = self.plugin.disasmVAtoFA(value)
                if fofs is not None:
                    rowOfs = self._getOffsetOfRow(cursorY)
                    if rowOfs is not None:
                        self.FlowHistory.append(rowOfs + self.dataModel.getOffset())
                        self.goTo(fofs)

    def _followBranchHistory(self):
        if len(self.FlowHistory) > 0:
            offset = self.FlowHistory[-1]
            del self.FlowHistory[-1]
            self.goTo(offset)

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

            if modifiers == QtCore.Qt.ControlModifier:
                if key == QtCore.Qt.Key_Right:
                    self.dataModel.slide(1)
                    self.addop((self.scroll, -1, 0))

                if key == QtCore.Qt.Key_Left:
                    self.dataModel.slide(-1)
                    self.addop((self.scroll, 1, 0))

                if key == QtCore.Qt.Key_Down:
                    self.addop((self.scroll, 0, -1))
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Up:
                    self.addop((self.scroll, 0, 1))
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_End:
                    # not supported
                    pass

                if key == QtCore.Qt.Key_Home:
                    self.moveCursor(Directions.CtrlHome)
                    self.addop((self.draw,))
                    # self.draw()

                return True

            else:  # elif modifiers == QtCore.Qt.NoModifier:

                if key == QtCore.Qt.Key_Escape:
                    self.selector.resetSelections()
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Left:
                    self.moveCursor(Directions.Left)
                    self.addop((self.draw,))
                    # self.draw()

                if key == QtCore.Qt.Key_Right:
                    self.moveCursor(Directions.Right)
                    self.addop((self.draw,))
                    # self.draw()

                if key == QtCore.Qt.Key_Down:
                    self.moveCursor(Directions.Down)
                    self.addop((self.draw,))
                    # self.draw()

                if key == QtCore.Qt.Key_End:
                    self.moveCursor(Directions.End)
                    self.addop((self.draw,))
                    # self.draw()

                if key == QtCore.Qt.Key_Home:
                    self.moveCursor(Directions.Home)
                    self.addop((self.draw,))
                    # self.draw()

                if key == QtCore.Qt.Key_Up:
                    self.moveCursor(Directions.Up)
                    self.addop((self.draw,))
                    # self.draw()

                if key == QtCore.Qt.Key_PageDown:
                    self.addop((self.scrollPages, 1))
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_PageUp:
                    self.addop((self.scrollPages, -1))
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Return:
                    self.addop((self._followBranch,))
                    self.addop((self.draw,))

                if key == QtCore.Qt.Key_Escape:
                    self.addop((self._followBranchHistory,))
                    self.addop((self.draw,))

                return True

        return False

    def addop(self, t):
        self.Ops.append(t)

    def getHeaderInfo(self):
        return 'Disasm listing'
