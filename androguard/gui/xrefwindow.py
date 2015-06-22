from PySide import QtCore, QtGui
from androguard.core import androconf
from androguard.gui.helpers import display2classmethod, class2func, classmethod2display, method2func


class XrefDialogClass(QtGui.QDialog):
    '''Dialog holding our Xref listview.
        parent: SourceWindow that started the new XrefDialog
        path: complete path of the class we are looking an xref from
        method (optional): method of the class we are looking xref from
        xrefs_list: the list of "Class -> Method" strings representing the xrefs

        path/method are used for the title of the window
        xrefs_list for the content of the QListView
    '''

    def __init__(self, parent=None, win=None, current_class=None, class_analysis=None):
        super(XrefDialogClass, self).__init__(parent)
        self.current_class = current_class
        self.class_analysis = class_analysis

        title = "Xrefs for the class %s" % current_class

        self.setWindowTitle(title)

        xrefs_list = []

        xrefs_from = class_analysis.get_xref_from()
        for ref_class in xrefs_from:
            for ref_method in xrefs_from[ref_class]:
                xrefs_list.append(('F', ref_class.get_vm_class(), ref_method))

        xrefs_to = class_analysis.get_xref_to()
        for ref_class in xrefs_to:
            for ref_method in xrefs_to[ref_class]:
                xrefs_list.append(('T', ref_class.get_vm_class(), ref_method))

        closeButton = QtGui.QPushButton("Close")
        closeButton.clicked.connect(self.close)

        xreflayout = QtGui.QGridLayout()
        xrefwin = XrefListView(self, win=win, xrefs=xrefs_list)
        xreflayout.addWidget(xrefwin, 0, 0)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(xreflayout)
        mainLayout.addLayout(buttonsLayout)

        self.setLayout(mainLayout)

class XrefDialogMethod(QtGui.QDialog):
    def __init__(self, parent=None, win=None, current_class=None, class_analysis=None, method_analysis=None):
        super(XrefDialogMethod, self).__init__(parent)
        self.current_class = current_class
        self.class_analysis = class_analysis
        self.method_analysis = method_analysis

        title = "Xrefs for the method %s" % self.method_analysis.method

        self.setWindowTitle(title)

        xrefs_list = []

        xrefs_from = self.method_analysis.get_xref_from()
        for ref_class, ref_method in xrefs_from:
            xrefs_list.append(('F', ref_class.get_vm_class(), ref_method))

        xrefs_to = self.method_analysis.get_xref_to()
        for ref_class, ref_method in xrefs_to:
            xrefs_list.append(('T', ref_class.get_vm_class(), ref_method))

        closeButton = QtGui.QPushButton("Close")
        closeButton.clicked.connect(self.close)

        xreflayout = QtGui.QGridLayout()
        xrefwin = XrefListView(self, win=win, xrefs=xrefs_list)
        xreflayout.addWidget(xrefwin, 0, 0)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(xreflayout)
        mainLayout.addLayout(buttonsLayout)

        self.setLayout(mainLayout)

class XrefDialogField(QtGui.QDialog):
    def __init__(self, parent=None, win=None, current_class=None, class_analysis=None, field_analysis=None):
        super(XrefDialogField, self).__init__(parent)
        self.current_class = current_class
        self.class_analysis = class_analysis
        self.field_analysis = field_analysis

        title = "Xrefs for the field %s" % self.field_analysis.field

        self.setWindowTitle(title)

        xrefs_list = []

        xrefs_read = self.field_analysis.get_xref_read()
        for ref_class, ref_method in xrefs_read:
            xrefs_list.append(('R', ref_class.get_vm_class(), ref_method))

        xrefs_write = self.field_analysis.get_xref_write()
        for ref_class, ref_method in xrefs_write:
            xrefs_list.append(('W', ref_class.get_vm_class(), ref_method))

        closeButton = QtGui.QPushButton("Close")
        closeButton.clicked.connect(self.close)

        xreflayout = QtGui.QGridLayout()
        xrefwin = XrefListView(self, win=win, xrefs=xrefs_list)
        xreflayout.addWidget(xrefwin, 0, 0)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(xreflayout)
        mainLayout.addLayout(buttonsLayout)

        self.setLayout(mainLayout)

class XrefDialogString(QtGui.QDialog):
    def __init__(self, parent=None, win=None, string_analysis=None):
        super(XrefDialogString, self).__init__(parent)
        self.string_analysis = string_analysis

        title = "Xrefs for the string %s" % self.string_analysis.value

        self.setWindowTitle(title)

        xrefs_list = []

        xrefs_from = self.string_analysis.get_xref_from()
        for ref_class, ref_method in xrefs_from:
            xrefs_list.append(('F', ref_class.get_vm_class(), ref_method))

        closeButton = QtGui.QPushButton("Close")
        closeButton.clicked.connect(self.close)

        xreflayout = QtGui.QGridLayout()
        xrefwin = XrefListView(self, win=win, xrefs=xrefs_list)
        xreflayout.addWidget(xrefwin, 0, 0)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(xreflayout)
        mainLayout.addLayout(buttonsLayout)

        self.setLayout(mainLayout)

class XrefDialog(QtGui.QDialog):
    '''Dialog holding our Xref listview.
        parent: SourceWindow that started the new XrefDialog
        path: complete path of the class we are looking an xref from
        method (optional): method of the class we are looking xref from
        xrefs_list: the list of "Class -> Method" strings representing the xrefs

        path/method are used for the title of the window
        xrefs_list for the content of the QListView
    '''

    def __init__(self, parent=None, win=None, xrefs_list=None, method=""):
        super(XrefDialog, self).__init__(parent)

        if not isinstance(xrefs_list, list) or len(xrefs_list) == 0:
            androconf.warning("Bad XrefDialog creation")
            return

        if not method:
            title = "Xrefs to %s" % path.split("/")[-1]
        else:
            title = "Xrefs to %s -> %s" % (path.split("/")[-1], method)

        self.setWindowTitle(title)
        layout = QtGui.QGridLayout()
        xrefwin = XrefListView(self, win=win, xrefs=xrefs_list)
        layout.addWidget(xrefwin, 0, 0)
        self.setLayout(layout)

    @classmethod
    def get_xrefs_list(cls, class_item, method=None):
        '''Static method called before creating a XrefDialog
           to check if there are xrefs to display
            method (optional): method of the class we are looking xref from
        '''
        androconf.debug("Getting XREF for %s" % class_item)

        item = class_item
        if method:
            item = method

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
        for xref_item in xref_items:
            class_ = xref_item[0].get_class_name()
            method_ = xref_item[0].get_name()
            descriptor_ = xref_item[0].get_descriptor()
            xrefs.append(classmethod2display(class_, method_, descriptor_))
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
        self.xrefs = xrefs

        self.doubleClicked.connect(self.doubleClickedHandler)

        model = QtGui.QStandardItemModel(self)
        for x in xrefs:
            value = "%s:%s" % (x[0], x[2])
            item = QtGui.QStandardItem(value)
            model.appendRow(item)
        self.setModel(model)

    def doubleClickedHandler(self, index):
        '''Signal sent by PySide when a QModelIndex element is clicked'''
        print "doubleClickedHandler", index, index.data()

        xref_method = None
        xref_class = None
        for xref in self.xrefs:
            if str(xref[2]) == index.data()[2:]:
                xref_method = xref[2]
                xref_class = xref[1]

        if xref_method:
            print type(xref_class), type(xref_method)
            self.mainwin.openSourceWindow(current_class=xref_class,
                                          method=xref_method)
            self.parent.close()
            return

        self.mainwin.showStatus("Impossible to find the xref ....")
        return
