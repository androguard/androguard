from __future__ import division
#
#  Format Viewer, Marius TIVADAR, 2014
#
#

from builtins import object
from PyQt5 import QtGui

class SelectionType(object):
    NORMAL = 0
    PERMANENT = 1
    TEXTHIGHLIGHT = 2

class Selection(object):
    def __init__(self, themes, viewMode):
        self.themes = themes
        self.viewMode = viewMode
        self.selecting = False
        self.Selections = []
        self.PermanentSelections = []
        self.MAX_SELECTIONS = 1
        self.defaultBrush = QtGui.QBrush(self.themes['selection'])

        self.last = 0
        self.HighlightSelections = []

    def drawSelection(self, qp, start, end, brush=None, opacity=0.4):
        raise "Not Implemented"

    def addSelection(self, t, type=None):
        if len(t) == 4:
            u, v, b, o = t
        else:
            u, v = t
            b, o = None, None

        if not o:
            o = 0.4

        if not b:
            b = self.defaultBrush

        if u - v == 0:
            return

        t = u, v, b, o

        if type == SelectionType.NORMAL:
            if len(self.Selections) >= self.MAX_SELECTIONS:

                self.Selections = []

            self.Selections.append(t)

        if type == SelectionType.PERMANENT:
            for w in self.PermanentSelections:
                if t[0] == w[0] and t[1] == w[1]:
                    return False

            # u, v not found
            self.PermanentSelections.append(t)

        if type == SelectionType.TEXTHIGHLIGHT:
            self.HighlightSelections.append(t)

        return True

    def removeSelection(self, u, v, type):
        if type == SelectionType.NORMAL:
            L = self.selectionStartOffset

        elif type == SelectionType.PERMANENT:
            L = self.PermanentSelections

        elif type == SelectionType.TEXTHIGHLIGHT:
            L = self.HighlightSelections

        else:
            raise "Selection type unknown"

        L[:] = [t for t in L if t[0] != u and t[1] != v]
        return

    def drawSelections(self, qp):
        # draw permanent
        for t in self.PermanentSelections:
            start, end, b, o = t
            self.drawSelection(qp, start, end, brush=b, opacity=o)

        # draw already selected
        for t in self.Selections:
            start, end, b, o = t
            self.drawSelection(qp, start, end)

        # 
        for t in self.HighlightSelections:
            start, end, b, o = t
            self.drawSelection(qp, start, end)
        self.HighlightSelections = []

        #draw current
        if self.selecting:
            self.drawSelection(qp, *self.getCurrentSelection())

    def resetSelections(self):
        self.Selections = []

    def startSelection(self):
        if self.selecting == False:
            self.selecting = True
            self.selectionStartOffset = self.viewMode.getCursorAbsolutePosition()
            if len(self.Selections) >= self.MAX_SELECTIONS:
                self.Selections = []

    def getCurrentSelection(self):
        if self.selecting:
            a = self.selectionStartOffset
            b = self.viewMode.getCursorAbsolutePosition() + 1
            if a < b:
                return a, b
            else:
                return b, a
        else:
            for s in self.Selections:
                u, v, b, o = s
                # pass auf! , in theory we could have more then one normal selection
                # so here the first one is returned.
                # but currently, by design we could only have one NORMAL selection
                return u, v

            #if self.last:
            #    return self.last

        return None
    
    def stopSelection(self):
        if self.selecting == True:
            u, v = self.getCurrentSelection()

            self.addSelection((u, v, QtGui.QBrush(self.themes['selection']), 0.4) , type=SelectionType.NORMAL)
            self.last = u, v

            self.selecting = False
            self.selectionStartOffset = None

    def highlightText(self):
        dataModel = self.viewMode.getDataModel()
        page = self.viewMode.getDisplayablePage()

        # for a search-in-page
        t = self.getCurrentSelection()

        if not t:
            # no selection
            return
        
        start, end = t

        if start == end:
            return

        text = dataModel.getStream(start, end)
        Exclude = [start]


        cols, rows = self.viewMode.getGeometry()

        # find all occurrence
        lenText = len(text)
        M = []
        idx = 0
        if lenText > 0:
            while idx < len(page):
                idx = page.find(text, idx, len(page))

                if idx == -1:
                    break
                M.append((idx, lenText))
                idx += lenText

        
        #Match = [(m.start(), m.end()) for m in re.finditer(bytes(text), bytes(page))]
        
        for start, end in M:
            #print start, end
            #self._makeSelection(qp, start, end, cols, rows)
            off = dataModel.getOffset()
            if off+start not in Exclude:
                #self._makeSelection(off + start, off + start + end, brush=QtGui.QBrush(QtGui.QColor(125, 255, 0)))
                #self.viewMode.selector.addSelection((off+start, off + start + end, QtGui.QBrush(QtGui.QColor(125, 255, 0)), 0.4))
                self.addSelection((off+start, off + start + end, QtGui.QBrush(self.themes['selection']), 0.4), type=SelectionType.TEXTHIGHLIGHT)


class DefaultSelection(Selection):
    def __init__(self, themes, viewMode):
        super(DefaultSelection, self).__init__(themes, viewMode)
        self.MAX_SELECTIONS = 1

    def _makeSelection(self, qp, start, end, brush):
        if not brush:
            brush = QtGui.QBrush(self.themes['selection'])
        dataModel = self.viewMode.getDataModel()
        off = dataModel.getOffset()
        length = len(self.viewMode.getDisplayablePage())
        cols, rows = self.viewMode.getGeometry()

        # return if out of view
        if end < off:
            return

        if start > off + length:
            return

        if start < off:
            d0 = 0
        else:
            d0 = start - off

        if end > off + length:
            d1 = length
        else:
            d1 = end - off
        
        mark = True
        height = 14

        qp.setOpacity(0.4)
        while mark:
            if d0 // cols == d1 // cols:
                qp.fillRect((d0%cols)*8, (d0 // cols) * height, (d1-d0) * 8, 1 * height, brush)
                d0 += (d1 - d0)
            else:    
                qp.fillRect((d0%cols)*8, (d0 // cols)*height, (cols - d0%cols)*8, 1*height, brush)
                d0 += (cols - d0%cols)

            if (d1 - d0 <= 0):
                mark = False
        qp.setOpacity(1)

    def drawSelection(self, qp, start, end, brush=None, opacity=0.4):
        if not brush:
            brush = QtGui.QBrush(self.themes['selection'])

        dataModel = self.viewMode.getDataModel()
        off = dataModel.getOffset()
        length = len(self.viewMode.getDisplayablePage())
        cols, rows = self.viewMode.getGeometry()

        # return if out of view
        if end < off:
            return

        if start > off + length:
            return

        if start < off:
            d0 = 0
        else:
            d0 = start - off

        if end > off + length:
            d1 = length
        else:
            d1 = end - off
        
        mark = True
        height = self.viewMode.fontHeight
        width = self.viewMode.fontWidth

        qp.setOpacity(opacity)

        offset = 2

        while mark:
            if d0 // cols == d1 // cols:
                qp.fillRect((d0%cols)*width, (d0 // cols)*height + offset, (d1-d0)*width, 1*height, brush)
                d0 += (d1 - d0)
            else:    
                qp.fillRect((d0%cols)*width, (d0 // cols)*height + offset, (cols - d0%cols)*width, 1*height, brush)
                d0 += (cols - d0%cols)

            if (d1 - d0 <= 0):
                mark = False
        qp.setOpacity(1)



class HexSelection(Selection):
    def __init__(self, themes, viewMode):
        super(HexSelection, self).__init__(themes, viewMode)
        self.MAX_SELECTIONS = 1

    def drawSelection(self, qp, start, end, brush=None, opacity=0.4):
        if not brush:
            brush = QtGui.QBrush(self.themes['selection'])

        dataModel = self.viewMode.getDataModel()
        off = dataModel.getOffset()
        length = len(self.viewMode.getDisplayablePage())
        cols, rows = self.viewMode.getGeometry()

        # return if out of view
        if end < off:
            return

        if start > off + length:
            return

        if start < off:
            d0 = 0
        else:
            d0 = start - off

        if end > off + length:
            d1 = length
        else:
            d1 = end - off
        
        mark = True
        height = self.viewMode.fontHeight
        width = self.viewMode.fontWidth

        qp.setOpacity(opacity)
        while mark:
            if d0 // cols == d1 // cols:
                # +2 is an offset for letters
                qp.fillRect(3*(d0%cols)*width,                    (d0 // cols)*height+2, 3*(d1-d0)*width - width, 1*height, brush)
                qp.fillRect(3*cols*width + self.viewMode.gap*width + (d0%cols)*width, (d0 // cols)*height+2, (d1-d0)*width,           1*height, brush)

                d0 += (d1 - d0)
            else:    
                qp.fillRect(3*(d0%cols)*width,                    (d0 // cols)*height+2, 3*(cols - d0%cols)*width - width, 1*height, brush)
                qp.fillRect(3*cols*width + self.viewMode.gap*width + (d0%cols)*width, (d0 // cols)*height+2, (cols - d0%cols)*width,       1*height, brush)

                d0 += (cols - d0%cols)

            if (d1 - d0 <= 0):
                mark = False
        qp.setOpacity(1)


class DisasmSelection(Selection):
    def __init__(self, themes, viewMode):
        super(DisasmSelection, self).__init__(themes, viewMode)
        self.MAX_SELECTIONS = 1

    def drawSelection(self, qp, start, end, brush=None, opacity=0.4):
        if not brush:
            brush = QtGui.QBrush(self.themes['selection'])

        dataModel = self.viewMode.getDataModel()
        off = dataModel.getOffset()
        length = sum([o.size for o in self.viewMode.OPCODES])        # TODO: not nice!
        cols, rows = self.viewMode.getGeometry()

        # return if out of view
        if end < off:
            return

        if start > off + length:
            return

        if start < off:
            d0 = 0
        else:
            d0 = start - off

        if end > off + length:
            d1 = length
        else:
            d1 = end - off
        
        mark = True
        height = self.viewMode.fontHeight
        width = self.viewMode.fontWidth

        qp.setOpacity(opacity)

        offset = 2

        size = 0
        for i, asm in enumerate(self.viewMode.OPCODES):
            if size + asm.size > d0 and size <= d1:

                    # compute x offset
                    x = d0-size
                    if size > d0:
                        x = 0

                    # compute width
                    w = asm.size
                    if size + asm.size > d1:
                        w = d1 - size

                    qp.fillRect(x*3*width, i*height + offset, (w-x)*3*width - width, 1*height, brush)

            size += asm.size

        qp.setOpacity(1)
