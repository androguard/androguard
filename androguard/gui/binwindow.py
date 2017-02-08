from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import chr
from builtins import object
import string
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi

from .cemu import *
from .BinViewMode import *
from .DataModel import *
from .Banners import *

class SearchWindow(QtWidgets.QDialog):
    
    def __init__(self, parent, plugin, searchable):
        super(SearchWindow, self).__init__(parent)
        self.searchable = searchable
        self.parent = parent
        self.plugin = plugin
        self.oshow = super(SearchWindow, self).show

        root = os.path.dirname(sys.argv[0])

        self.ui = loadUi(os.path.join(root, './androguard/gui/search.ui'), baseinstance=self)
        self.ui.setWindowTitle('Search')
        self._lastText = ''

        self.initUI()

    def show(self):
        # TODO: remember position? resize plugin windows when parent resize?

        width = self.ui.size().width()+15
        height = self.ui.size().height()+15

        self.move((self.parent.width() - width) // 2, (self.parent.height() - height) // 2)
        self.ui.lineEdit.setText(self._lastText)
        self.ui.lineEdit.selectAll()
        self.oshow()

    def initUI(self):

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("/"), self, self.close, self.close)

        self.ui.pushButton.clicked.connect(self.onClicked)

        width = self.ui.size().width()+15
        height = self.ui.size().height()+15
        self.setFixedSize(width, height)

    def onClicked(self):
        text = self.ui.lineEdit.text()  
        text = str(text)

        hexstr = '0123456789abcdefABCDEF'
        if self.ui.checkHex.isChecked():
            T = text.split(' ')
            oldtext = text
            text = ''
            for t in T:
                if len(t) != 2:
                    reply = QtWidgets.QMessageBox.warning(self, 'Qiew', "Hex string with errors.", QtWidgets.QMessageBox.Ok)
                    self.close()
                    return

                if t[0] in hexstr and t[1] in hexstr:
                    o = int(t, 16)
                    text += chr(o)
                else:
                    reply = QtWidgets.QMessageBox.warning(self, 'Qiew', "Hex string with errors.", QtWidgets.QMessageBox.Ok)
                    self.close()
                    return


            self._lastText = oldtext

        else:
            self._lastText = text

        if self.ui.checkHex.isChecked() == False:
            text = text.encode('utf-8')

        idx = self.searchable.search(text)
        if idx == -1:
            reply = QtWidgets.QMessageBox.warning(self, 'Qiew', "Nothing found.", QtWidgets.QMessageBox.Ok)

        self.parent.viewMode.draw(refresh=True)
        self.close()

class Observable(object):
    def __init__(self):
        self.Callbacks = []

    def addHandler(self, h):
        if h not in self.Callbacks:
            self.Callbacks.append(h)

    def notify(self, viewMode):
        for cbk in self.Callbacks:
            cbk.changeViewMode(viewMode)


class Observer(object):
    def changeViewMode(self, viewMode):
        self._viewMode = viewMode

class Searchable(Observer):
    def __init__(self, dataModel, viewMode):
        self._viewMode = viewMode
        self._dataModel = dataModel
        self._lastIdx = -1
        self._lastText = ''

    def next(self, start=None):
        data = self._dataModel.getData()
        text = self._lastText

        if not start:
            idx = self._lastIdx + 1
        else:
            idx = start
        
        if idx > -1:
            self._search(data, text, idx)

    @property
    def lastText(self):
        return self._lastText
    
    def previous(self, start=None):
        data = self._dataModel.getData()
        text = self._lastText

        if not start:
            idx = self._lastIdx
        else:
            idx = start

        if idx > -1:
            self._search(data, text, idx, previous=True)

    def _search(self, data, text, start, previous=False):

        self._lastText = text
        if text == '':
            return -1

        if not previous:
            idx1 = string.find(data, text, start)
            text1 = '\0'.join(text)

            idx2 = string.find(data, text1, start)

            idx = idx1
            if idx1 == -1:
                idx = idx2
            else:
                if idx2 < idx1 and idx2 != -1:
                    idx = idx2

        else:
            idx1 = string.rfind(data, text, 0, start)
            text1 = '\0'.join(text)

            idx2 = string.rfind(data, text1, 0, start)

            idx = idx1

            if idx1 == -1:
                idx = idx2
            else:
                if idx2 > idx1 and idx2 != -1:
                    idx = idx2

        if idx > -1:
            self._lastIdx = idx

        if idx > -1:
            self._viewMode.selector.addSelection((idx, idx + len(text), QtGui.QBrush(QtGui.QColor(125, 0, 100)), 0.8) , type=TextSelection.SelectionType.NORMAL)
            self._viewMode.goTo(idx)

        return idx


    def search(self, text):
        data = self._dataModel.getData()
        return self._search(data, text, 0)


class binWidget(QtWidgets.QWidget, Observable):
  
    scrolled = QtCore.pyqtSignal(int, name='scroll')

    def __init__(self, parent, source, title):
        super(binWidget, self).__init__()
        Observable.__init__(self)
        self.parent = parent
        
        self.title = title
        self.active = False
        # offset for text window
        #self.data = mapped
        self.dataOffset = 0
        
        self.dataModel = source
        self.cursor = Cursor(0, 0)

        self.themes = {
            'font': QtGui.QFont('Monaco', 9, QtGui.QFont.Light),
            'background': QtGui.QColor(0x00, 0x2b, 0x36),
            'background_cursor': QtGui.QColor(255, 255, 0),
            'selection': QtGui.QColor(125, 255, 0),
            'pen': QtGui.QColor(0xb5, 0x89, 0x00)
            }

        self.multipleViewModes = []
        for view_mode in self.dataModel.GetViews():
            v = view_mode(self.themes, self.size().width(), self.size().height(), self.dataModel, self.cursor, self)
            textDecorator = HighlightASCII(TextDecorator(v))

            v.setTransformationEngine(textDecorator)

            self.multipleViewModes.append(v)

        self.viewMode = self.multipleViewModes[0]



        self.Banners = Banners()

        self.Banners.add(FileAddrBanner(self.themes, self.dataModel, self.viewMode)) 
        self.Banners.add(TopBanner(self.themes, self.dataModel, self.viewMode))
        self.Banners.add(BottomBanner(self.themes, self.dataModel, self.viewMode))

        self.offsetWindow_h = 0
        self.offsetWindow_v = 0
        self.searchable = Searchable(self.dataModel, self.viewMode)


        self.initUI()

        self.searchWindow = SearchWindow(self, None, self.searchable)

        self.addHandler(self.searchable)
        self.addHandler(self.Banners)

        self.notify(self.viewMode)  

    def enable(self):
        self.active = True

    def disable(self):
        self.active = False
        
    def scroll_from_outside(self, i):
        #print 'slot-signal ' + str(i)
        #self.scroll_pdown = True
        self.update()

    def initUI(self):
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.setMinimumSize(1, 30)
        self.activateWindow()
        self.setFocus()

    def switchViewMode(self):
        self.multipleViewModes = self.multipleViewModes[1:] + [self.multipleViewModes[0]]
        self.viewMode = self.multipleViewModes[0]

        # notify obervers
        self.notify(self.viewMode)

    def _resize(self):

        self.Banners.resize(self.size().width() - self.offsetWindow_h, self.size().height() - self.offsetWindow_v)

        # compute space ocupated by banners        
        offsetLeft = self.offsetWindow_h + self.Banners.getLeftOffset()
        offsetBottom   = self.offsetWindow_v + self.Banners.getBottomOffset() + self.Banners.getTopOffset()
        
        # resize window, substract space ocupated by banners
        self.viewMode.resize(self.size().width() - offsetLeft, self.size().height() - offsetBottom)

    # event handlers
    def resizeEvent(self, e):
        self._resize()


    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setOpacity(1)

        offsetLeft = self.offsetWindow_h + self.Banners.getLeftOffset()
        offsetBottom   = self.offsetWindow_v + self.Banners.getTopOffset()

        #self.viewMode.draw2(qp, refresh=True)
        #start = time()
        qp.drawPixmap(offsetLeft, offsetBottom, self.viewMode.getPixmap())
        #print 'Draw ' + str(time() - start)

        self.Banners.draw(qp, self.offsetWindow_h, self.offsetWindow_v, self.size().height())

      #  qp.drawPixmap(self.offsetWindow_h, self.size().height() - 50, self.banner.getPixmap())

       # qp.drawPixmap(20, 0, self.filebanner.getPixmap())
        qp.end()


    def eventFilter(self, watched, event):
        if not self.active:
            return False

        if event.type() == QtCore.QEvent.KeyRelease:
            key = event.key()
            modifiers = event.modifiers()
            if self.viewMode.handleKeyEvent(modifiers, key, event=event):
                self.update()


        if event.type() == QtCore.QEvent.KeyPress: 
            #TODO: should we accept only certain keys ?
            key = event.key()
            modifiers = event.modifiers()
            if key == QtCore.Qt.Key_F2:
                if self.viewMode.isEditable():
                    if self.viewMode.isInEditMode():
                        self.viewMode.setEditMode(False)
                    else:
                        self.viewMode.setEditMode(True)

                    self.viewMode.draw(refresh=False)
            # switch view mode
            if key == QtCore.Qt.Key_V:
                print('SWITCH VIEW')
                offs = self.viewMode.getCursorOffsetInPage()
                base = self.viewMode.getDataModel().getOffset()
                self.switchViewMode()
                self._resize()
                self.viewMode.goTo(base + offs)
                self.update()

            if key == QtCore.Qt.Key_S:
                print('OPEN SOURCE')
                self.parent.openSourceWindow(self.dataModel.current_class)

            import pyperclip
            if event.modifiers() & QtCore.Qt.ControlModifier:
                if key == QtCore.Qt.Key_Insert:
                    if self.viewMode.selector.getCurrentSelection():
                        a, b = self.viewMode.selector.getCurrentSelection()

                        #print a, b
                        hx = ''
                        for s in self.dataModel.getStream(a, b):
                            hx += '{:02x}'.format(s)

                        pyperclip.copy(hx)
                        del pyperclip
                        #print pyperclip.paste()
                     #   print 'coppied'
                
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                if key == QtCore.Qt.Key_Insert:
                    import re
                    hx = pyperclip.paste()
                    #print hx
                    L = re.findall(r'.{1,2}', hx, re.DOTALL)

                    array = ''
                    for s in L:
                        array += chr(int(s, 16))

                    #print 'write '
                    #print 'write'
                    #print array
                    self.dataModel.write(0, array)
                    self.viewMode.draw(True)
                    del pyperclip
                    #print array

                if key == QtCore.Qt.Key_F4:
                    self.unp = WUnpack(self, None)
                    self.unp.show()


            if key == QtCore.Qt.Key_F10:
                self.dataModel.flush()
                self.w = WHeaders(self, None)
                self.w.show()


            if not self.viewMode.isInEditMode():
                if key == QtCore.Qt.Key_Slash:
                    self.searchWindow.show()

                if key == QtCore.Qt.Key_N:
                    self.searchable.next(self.viewMode.getCursorAbsolutePosition() + 1)

                if key == QtCore.Qt.Key_B:
                    self.searchable.previous(self.viewMode.getCursorAbsolutePosition())

            # handle keys to view plugin
            if self.viewMode.handleKeyEvent(modifiers, key, event=event):
                event.accept()
                self.update()
                return True


        return False

    def setTextViewport(self, qp):
        qp.setViewport(self.offsetWindow_h, self.offsetWindow_v, self.size().width(), self.size().height())
        qp.setWindow(0, 0, self.size().width(), self.size().height())

    def needsSave(self):
        return self.dataModel.isDirty()

    def save(self):
        return self.dataModel.flush()
