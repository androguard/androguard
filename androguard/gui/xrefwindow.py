from PySide import QtCore, QtGui
from androguard.core import androconf
from androguard.gui.helpers import display2classmethod, class2func, classmethod2display, method2func
from androguard.gui.sourcewindow import SourceWindow

class XrefDialog(QtGui.QDialog):
    '''Dialog holding our Xref listview.
        parent: SourceWindow that started the new XrefDialog
        path: complete path of the class we are looking an xref from
        method (optional): method of the class we are looking xref from
        xrefs_list: the list of "Class -> Method" strings representing the xrefs

        path/method are used for the title of the window
        xrefs_list for the content of the QListView
    '''

    def __init__(self, parent=None, win=None, xrefs_list=None, path="", method=""):
        super(XrefDialog, self).__init__(parent)

        if not isinstance(xrefs_list, list) or len(xrefs_list) == 0:
            print "WARNING, bad XrefDialog creation"
            return
        
        if not method:
            title = "Xrefs to " + path.split("/")[-1]
        else:
            title = "Xrefs to " + path.split("/")[-1] + " -> " + method

        self.setWindowTitle(title)
        layout = QtGui.QGridLayout()
        xrefwin = XrefListView(self, win=win, xrefs=xrefs_list)
        layout.addWidget(xrefwin, 0, 0)
        self.setLayout(layout)

    @classmethod
    def get_xrefs_list(cls, d, path, method=""):
        '''Static method called before creating a XrefDialog 
           to check if there are xrefs to display
            path: complete path of the class we are looking an xref from
            method (optional): method of the class we are looking xref from
        '''

        arg = class2func(path)
        try:
            class_item = getattr(d, arg)
        except AttributeError:
            androconf.debug("no class: %s in DalvikVMFormat d" % arg)
            return None
        if not method:
            item = class_item
        else:
            arg2 = method2func(method)
            try:
                item = getattr(class_item, arg2)
            except AttributeError:
                androconf.debug("no method: %s in class: %s" % (arg2, arg))
                return None
        androconf.debug("Getting XREFs for: %s" % arg)
        if not hasattr(item, "XREFfrom"):
            androconf.debug("No xref found")
            return None

        return XrefDialog.get_xrefs_list_from_element(item)

    @classmethod
    def get_xrefs_list_from_element(cls, element):
        '''Helper for get_xrefs_list

           element is a ClassDefItem or MethodDefItem

           At the end of the function, we lost if we worked on
           a class or method but we do not care for now.
        '''

        xref_items = element.XREFfrom.items
        androconf.debug("%d XREFs found" % len(xref_items))
#        print xref_items
        xrefs = []
        for i in range(len(xref_items)):
            class_ = xref_items[i][0].get_class_name()
            method_ = xref_items[i][0].get_name()
            xrefs.append(classmethod2display(class_, method_))
#        print xrefs
        return xrefs

class XrefListView(QtGui.QListView):
    '''List view implemented inside the XrefDialog to list all the Xref of
       a particular class or method.
    '''

    def __init__(self, parent=None, win=None, xrefs=None):
        super(XrefListView, self).__init__(parent)

        self.setMinimumSize(600, 400) #TODO: adjust window depending on text displayed
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.mainwin = win
        self.parent = parent

        self.doubleClicked.connect(self.doubleClickedHandler)

        model = QtGui.QStandardItemModel(self)
        for x in xrefs:
            item = QtGui.QStandardItem(x)
            model.appendRow(item)
        self.setModel(model)

    def doubleClickedHandler(self, index):
        '''Signal sent by PySide when a QModelIndex element is clicked'''

        path, method = display2classmethod(index.data())
        self.mainwin.openSourceWindow(path, method)
        self.parent.close()
