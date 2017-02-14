from __future__ import absolute_import
from builtins import range
from builtins import object
from PyQt5 import QtGui, QtCore
import re
import string
from time import time
import sys
from . import TextSelection


class CTextDecorator(object):
    redPen = QtGui.QPen(QtGui.QColor(255, 0, 0))

    greenPen = QtGui.QPen(QtGui.QColor(255, 255, 0))
    whitePen = QtGui.QPen(QtGui.QColor(255, 255, 255))

    normalPen = QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine)        

    MZbrush = QtGui.QBrush(QtGui.QColor(128, 0, 0))
    grayBrush = QtGui.QBrush(QtGui.QColor(128, 128, 128))

    def __init__(self):
        pass

class TextDecorator(CTextDecorator):
    def __init__(self, viewmode):
        self.operations = []
        self.dataModel = viewmode.getDataModel()
        self.viewmode = viewmode
        self.penMap = {}
        self.brushMap = {}
        self.PenInterval = []

        self.normalPen = QtGui.QPen(QtGui.QColor(192, 192, 192), 1, QtCore.Qt.SolidLine)

        # if we want to generate T/F table
        self.Special =  string.ascii_letters + string.digits + ' .;\':;=\"?-!()/\\_'
        self.Special = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, False, False, False, False, True, True, 
                        True, False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, False, True, False, True, 
                        False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, 
                        True, True, True, False, True, False, False, True, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True,
                        True, True, True, True, True, True, True, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                        False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]


    def reset(self):
        self.penMap = {}
        self.brushMap = {}
        self.PenInterval = []

        
    def getDataModel(self):
        return self.dataModel

    def isText(self, c):
        """
        D = []
        for i in range(256):
            b = False
            if self.isText(chr(i)):
                b = True

            D.append(b)

        print D    
        sys.exit()
        """

        return self.Special[ord(c)]

    def getChar(self, idx):
        #self.page = self.getDataModel().getDisplayablePage()


        if idx < len(self.page):
            return self.page[idx]

        return 0


    def decorate(self, pageOffset=None):
        
        if pageOffset:
            self.page = self.viewmode.getDisplayablePage(pageOffset=pageOffset)
        else:    
            self.page = self.viewmode.getDisplayablePage()

        return self.page



    def addPenInterval(self, a, b, pen, ignoreHighlights=True):
        self.PenInterval.append((a, b, pen, ignoreHighlights))

    def choosePen(self, idx):
        key = self.dataModel.getOffset() + idx
        
        # if we do have a pen with that index, return it if it's different than default pen
        # otherwise, return the pen that was set in that interval
        # the priority here is de pen from other transformations, than interval pen
        for a, b, ignoreHighlights, pen in self.PenInterval:
            # in interval
            if a <= key <= b:
                if ignoreHighlights:
                    return pen

                if key in self.penMap:
                    if self.penMap[key] == self.normalPen:
                        return pen
                    else:
                        return self.penMap[key]
                else:
                    return pen

        if key in self.penMap:
            return self.penMap[key]

        return self.normalPen

    def chooseBrush(self, idx):
        off = self.dataModel.getOffset() + idx
        if off in self.brushMap:
            return self.brushMap[off]

        return None


class PageDecorator(TextDecorator):
    def __init__(self, decorated):
        pass

 
    def reset(self):
        self.decorated.reset()

        self.penMap = {}
        self.brushMap = {}
        self.PenInterval = []

    def getBrushMap(self):
        return self.brushMap

    def getPenMap(self):
        return self.penMap

    def doit(self):
        pass

    def getDataModel(self):
        return self.dataModel

class HighlightASCII(PageDecorator):
    def __init__(self, decorated):
        self.dataModel = decorated.getDataModel()
        self.penMap = decorated.penMap
        self.decorated = decorated
        super(HighlightASCII, self).__init__(decorated)
        self.dataModel = super(HighlightASCII, self).getDataModel()



    def decorate(self, pageOffset=None):
        page = self.decorated.decorate(pageOffset)

        self.PenInterval = self.decorated.PenInterval
        self.brushMap = self.decorated.brushMap
        self.penMap = self.decorated.penMap

        off = self.dataModel.getOffset()

        Match = [(m.start(), m.end()) for m in re.finditer(b'([a-zA-Z0-9\\-\\\\.%*:/? _<>]){4,}', page)]
        for s, e in Match:
            for i in range(e-s):
                idx = off + s + i
                if idx not in self.penMap:
                    self.penMap[off + s + i] = self.redPen


        self.page = page
        return self.page
        



class HighlightPrefix(PageDecorator):
    def __init__(self, decorated, text, additionalLength=0, brush=None, pen=None):
        super(HighlightPrefix, self).__init__(decorated)
        self.dataModel = decorated.getDataModel()
        self.decorated = decorated

        self.additionalLength = additionalLength
        self.brush = brush
        self.text = text
        self.pen = pen

    def decorate(self, pageOffset=None):
        page = self.decorated.decorate(pageOffset)

        self.PenInterval = self.decorated.PenInterval
        self.brushMap = self.decorated.brushMap
        self.penMap = self.decorated.penMap


        self.page = self.highliteWithPrefix(page, self.text, self.additionalLength, self.brush, self.pen)
        return self.page


    def highliteWithPrefix(self, page, text, additionalLength=0, brush=None, pen=None):



        # todo: nu am gasit o metoda mai eleganta pentru a selecta toate aparitiile ale lui text
        # regexp nu merg, "bad re expression"
        lenText = len(text)
        M = []
        idx = 0
        if lenText > 0:
            while idx < len(page):
                idx = page.find(text, idx, len(page))

                if idx == -1:
                    break

                M.append((idx, lenText + additionalLength))
                idx += lenText + additionalLength

        
        off = self.dataModel.getOffset()
        for start, length in M:
           
            for i in range(length):
                self.penMap[off + start + i] = pen
                self.brushMap[off + start + i] = brush


        return page

class HighlightWideChar(PageDecorator):
    def __init__(self, decorated):
        super(HighlightWideChar, self).__init__(decorated)

        self.dataModel = decorated.getDataModel()
        self.decorated = decorated


    def decorate(self, pageOffset=None):
        self.page = self.decorated.decorate(pageOffset)

        self.PenInterval = self.decorated.PenInterval
        self.brushMap = self.decorated.brushMap
        self.penMap = self.decorated.penMap


        self.page = self.highliteWidechar2(self.page)
        return self.page




    def highliteWidechar2(self, page):
        
        pageStart = self.dataModel.getOffset()
        pageEnd   = pageStart  + len(page)

        touched = False
        #for s, e in self.Intervals:
        #    touched = True

        if not touched:
            # expand
            Match = [(m.start(), m.end()) for m in re.finditer(r'([a-zA-Z0-9\-\\.%*:/? ]\x00){4,}', page)]
            for s, e in Match:
                for i in range(e-s):
                    #print i
                    self.penMap[pageStart + s + i] = QtGui.QPen(QtGui.QColor(255, 255, 0))

                # get rid of '\x00'
                string = page[s:e:2]
                l = len(string)
                # copy string that has no zeros
                page[s:s + l] = string
                # fill with zeros the remaining space
                page[s + l: s + 2*l] = '\x00'*l


        return page


    ### todo: other way to highlight widechar, should test and see which one is faster
    """
    def _changeText(self, page, page_start, I):
        page_end = page_start + len(page)
        for obj in I:
            if obj['s'] >= page_start and obj['e'] <= page_end:
                page[obj['s']-page_start:obj['e']-page_start] = obj['text']


    def _expand(self, page, off, start, end):
        I = []
        start = start - off
        end = end - off
        i = start
        while i < end:

            if i+1 < end:
                if page[i+1] == 0 and self.isText(chr(page[i])):
                    k = 0
                    for j in xrange(i, end, 2):
                        if j + 1 < end:
                            if self.isText(chr(page[j])) and page[j+1] == 0:
                                k += 1
                            else:
                                break
                    if k > 4:
                        if i+k*2 <= end:
                        
                            obj = {}
                            obj['s'] = off + i + 1
                            obj['e'] = off + i + k * 2

                            for idx, j in enumerate(range(i+1, i + k*2)):
                                if j > i + k:
                                    page[j] = 0
                                    #self.penMap[j] = self.greenPen

                                elif j+idx+1 < end:
                                    page[j] = page[j + idx + 1]
                                    self.penMap[off + j] = self.greenPen
                                    
                            obj['text'] = page[i+1:i+k*2]
                            I.append(obj)
                            self.penMap[off + i] = self.greenPen
                            i += k*2

            i = i + 1

        return I
        pass
    


    def highliteWidechar(self, page):
        off = self.dataModel.getOffset()
        page_end = off  + len(page)
        touched = False
        #print '-------'
        for idx, iv in enumerate(self.Intervals):
            #print 'acum aici'
            # in interval
            s, e, I = iv

            #print s ,e
            #print page_end
            page_start = off
            if off >= s:
                touched = True
                if page_end <= e:
                    self._changeText(page, off, I)
                else:
                    if off <= e:
                        I2 = self._expand(page, off, e, page_end)
                        for obj in I2:
                            I.append(obj)
                        e = page_end
                        self.Intervals[idx] = (s, e, I)
                    else:
                        # suntem cu mai multe pagini mai jos
                        touched = False

            else:
                if page_end <= e and page_end >= s:
                    # scrolled up
                    I2 = self._expand(page, off, page_start, s)
                    for obj in I2:
                        I.append(obj)
                    s = page_start
                    self.Intervals[idx] = (s, e, I)
                    touched = True
                else:
                    # out of this interval
                    touched = False


        if not touched or touched:
            #print 'aici'
            self.Intervals.append((off, page_end, self._expand(page, off, off, page_end)))
        

    """


class RangePen(PageDecorator):
    def __init__(self, decorated, a, b, pen, ignoreHighlights=True):
        super(RangePen, self).__init__(decorated)

        self.dataModel = decorated.getDataModel()
        self.decorated = decorated
        self.a = a
        self.b = b
        self.pen = pen
        self.already = False
        self.ignoreHighlights = ignoreHighlights

    def decorate(self, pageOffset=None):
        self.page = self.decorated.decorate(pageOffset)
        self.PenInterval = self.decorated.PenInterval
        self.brushMap = self.decorated.brushMap
        self.penMap = self.decorated.penMap

        if not self.already:
            self.addPenInterval(self.a, self.b, self.ignoreHighlights, self.pen)
            self.already = True

        return self.page
