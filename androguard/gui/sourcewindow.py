from PySide import QtCore, QtGui
from androguard.core import androconf
from androguard.gui.helpers import display2classmethod, class2func, method2func, classdot2func, classdot2class, proto2methodprotofunc
from androguard.gui.highlighter import Highlighter
from androguard.gui.renamewindow import RenameDialog

from androguard.core.bytecodes.dvm import EncodedField, EncodedMethod
from androguard.decompiler.dad.decompile import DvMethod

import sys, os

BINDINGS_NAMES = ['NAME_PACKAGE', 'NAME_PROTOTYPE', 'NAME_SUPERCLASS', 'NAME_INTERFACE', 'NAME_FIELD', 'NAME_METHOD_PROTOTYPE', 'NAME_ARG', 'NAME_CLASS_ASSIGNMENT', 'NAME_PARAM', 'NAME_BASE_CLASS', 'NAME_METHOD_INVOKE', 'NAME_CLASS_NEW', 'NAME_CLASS_INSTANCE', 'NAME_VARIABLE', 'NAME_CLASS_EXCEPTION']

class SourceDocument(QtGui.QTextDocument):
    '''QTextDocument associated with the SourceWindow.'''

    def __init__(self, parent=None, lines=[]):
        super(SourceDocument, self).__init__(parent)
        self.parent = parent

        cursor = QtGui.QTextCursor(self) # position=0x0
        state = 0
        self.binding = {}

        # save the cursor position before each interesting element
        for section, L in lines:
            for t in L:
                if t[0] in BINDINGS_NAMES:
                    self.binding[cursor.position()] = t
                cursor.insertText(t[1])

#class SourceWindow(QtGui.QTextEdit):
class SourceWindow(QtGui.QTextBrowser):
    '''Each tab is implemented as a Source Window class.
       Attributes:
        mainwin: MainWindow
        path: class FQN
        title: last part of the class FQN
        class_item: ClassDefItem i.e. class.java object for which we create the tab
    '''

    def __init__(self, parent=None, win=None, path=None):
        super(SourceWindow, self).__init__(parent)
        androconf.debug("New source tab: %s" % path)

        self.mainwin = win
        self.path = path
        self.title = path.split("/")[-1].replace(';', '')

        self.ospath = "/".join(path.split("/")[:-1])[1:]
        self.osfile = self.title + ".html"
        try:
            os.makedirs(self.ospath)
        except OSError:
            pass

        arg = class2func(self.path)
        self.class_item = getattr(self.mainwin.d, arg)

        self.createActions()
        self.setReadOnly(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.CustomContextMenuHandler)

        # No need to call reload_java_sources() here because 
        # it is called in MainWindow.currentTabChanged() function
        # that will be called when displaying the tab

    def browse_to_method(self, method):
        '''Scroll to the right place were the method is.

           TODO: implement it, because does not work for now.
        '''

        #TODO: we need to find a way to scroll to the right place because
        #      moving the cursor is not enough. Indeed if it is already in the window
        #      it does not do nothing

        #TODO: idea, highlight the method in the screen so we do not have to search for it

        androconf.debug("Browsing to %s -> %s" % (self.path, method))

        # debug
#        if False:
#            for k, v in self.doc.infoBlocks.items():
#                print k
#                print v
#                print "-"*10

    def reload_java_sources(self):
        '''Reload completely the sources by asking Androguard
           to decompile it again. Useful when:
            - an element has been renamed to propagate the info
            - the current tab is changed because we do not know what user
              did since then, so we need to propagate previous changes as well
        '''

        androconf.debug("Getting sources for %s" % self.path)
        lines = self.class_item.get_source_ext()

        filename = os.path.join(self.ospath, self.osfile)
        androconf.debug("Writing file: %s" % filename)
        fd = open(filename, 'wb')
        for section, L in lines:
            for t in L:
#                if t[0] in BINDINGS_NAMES:
#                    self.binding[cursor.position()] = t
                fd.write(t[1])
        fd.close()

        #TODO: delete doc when tab is closed? not deleted by "self" :(
        if hasattr(self, "doc"):
            del self.doc
        self.doc = SourceDocument(parent=self, lines=lines)
        self.setDocument(self.doc)

        #No need to save hightlighter. highlighBlock will automatically be called
        #because we passed the QTextDocument to QSyntaxHighlighter constructor
        Highlighter(self.doc)

    def createActions(self):
        self.xrefAct = QtGui.QAction("Xref from...", self,
                statusTip="List the references where this element is used",
                triggered=self.actionXref)
        self.gotoAct = QtGui.QAction("Go to...", self,
                statusTip="Go to element definition",
                triggered=self.actionGoto)
        self.renameAct = QtGui.QAction("Rename...", self,
                statusTip="Rename an element (class, method, ...)",
                triggered=self.actionRename)
        self.infoAct = QtGui.QAction("Info...", self,
                statusTip="Display info of an element (anything useful in the document)",
                triggered=self.actionInfo)

    def CustomContextMenuHandler(self, pos):
        menu = QtGui.QMenu(self)
        menu.addAction(self.xrefAct)
        menu.addAction(self.gotoAct)
        menu.addAction(self.renameAct)
        menu.addAction(self.infoAct)
        menu.exec_(QtGui.QCursor.pos())

    def actionXref(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selection = cursor.selection().toPlainText()
        androconf.debug("Xref asked for '%s' (%d, %d)" % (selection, start, end))

        if start not in self.doc.binding.keys():
            self.mainwin.showStatus("Xref not available. No info for: '%s'." % selection)
            return

        class_ = None
        method_ = None
        t = self.doc.binding[start]
        if t[0] == 'NAME_METHOD_PROTOTYPE':
            class_ = self.path
            method_ = t[1]
            if method_ == self.title:
                method_ = 'init'
        elif t[0] == 'NAME_METHOD_INVOKE':
            class_, method_ = t[2].split(' -> ')
            if class_ == 'this':
                class_ = self.path
            else:
                class_ = classdot2class(class_)
        elif t[0] == 'NAME_PROTOTYPE':
            class_ = classdot2class(t[2] + '.' + t[1])
        else:
            self.mainwin.showStatus("Xref not available. Info ok: '%s' but object not supported." % selection)
            return

        androconf.debug("Found corresponding method: %s -> %s in source file: %s" % (class_, method_, self.path))

        from androguard.gui.xrefwindow import XrefDialog
        xrefs_list = XrefDialog.get_xrefs_list(self.mainwin.d, path=class_, method=method_)
        if not xrefs_list:
            self.mainwin.showStatus("No xref returned")
            return

        xwin = XrefDialog(parent=self, win=self.mainwin, xrefs_list=xrefs_list, path=class_, method=method_)
        xwin.show()

    def actionRename(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selection = cursor.selection().toPlainText()
        androconf.debug("Rename asked for '%s' (%d, %d)" % (selection, start, end))

        if start not in self.doc.binding.keys():
            self.mainwin.showStatus("Rename not available. No info for: '%s'." % selection)
            return

        # Double check if we support the renaming for the type of 
        # object before poping a new window to the user
        t = self.doc.binding[start]
        if t[0] == 'NAME_METHOD_PROTOTYPE':
            class_ = self.path
            method_ = t[1]
            if method_ == self.title:
                method_ = 'init'
            androconf.debug("Found corresponding method: %s -> %s in source file: %s" % (class_, method_, self.path))
        elif t[0] == 'NAME_METHOD_INVOKE':
            class_, method_ = t[2].split(' -> ')
            if class_ == 'this':
                class_ = self.path
            androconf.debug("Found corresponding method: %s -> %s in source file: %s" % (class_, method_, self.path))
        elif t[0] == 'NAME_PROTOTYPE':
            class_ = t[2] + '.' + t[1]
            androconf.debug("Found corresponding class: %s in source file: %s" % (class_, self.path))
        elif t[0] == 'NAME_FIELD':
            field_ = t[1]
            androconf.debug("Found corresponding field: %s in source file: %s" % (field_, self.path))
        else:
            self.mainwin.showStatus("Rename not available. Info ok: '%s' but object not supported." % selection)
            return

        rwin = RenameDialog(parent=self, win=self.mainwin, element=selection, info=(start, end))
        rwin.show()

    def actionGoto(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selection = cursor.selection().toPlainText()
        androconf.debug("Goto asked for '%s' (%d, %d)" % (selection, start, end))

        if start not in self.doc.binding.keys():
            self.mainwin.showStatus("Goto not available. No info for: '%s'." % selection)
            return

        t = self.doc.binding[start]
        if t[0] == 'NAME_METHOD_INVOKE':
            class_, method_ = t[2].split(' -> ')
            if class_ == 'this':
                class_ = self.path
            else:
                class_ = classdot2class(class_)
        else:
            self.mainwin.showStatus("Goto not available. Info ok: '%s' but object not supported." % selection)
            return

        androconf.debug("Found corresponding method: %s -> %s in source file: %s" % (class_, method_, self.path))

        if not self.mainwin.doesClassExist(class_):
            self.mainwin.showStatus("Goto not available. Class: %s not in database." % class_)
            return

        self.mainwin.openSourceWindow(class_, method=method_)

    def actionInfo(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        androconf.debug("actionInfo asked for (%d, %d)" % (start, end))

        if start in self.doc.binding.keys():
            self.mainwin.showStatus(str(self.doc.binding[start]) + ' at position: (%d, %d)' % (start, end))
        else:
            self.mainwin.showStatus("No info available.")

    def method_name_exist(self, meth_name):
        '''Check if there is already a meth_name method in the current class
           It is useful before allowing to rename a method to check name does
           not already exist.
        '''

        methods = self.class_item.get_methods()
        for m in methods:
            if m.name == meth_name:
                return True
        return False

    def field_name_exist(self, field_name):
        '''Check if there is already a field_name field in the current class
           It is useful before allowing to rename a field to check name does
           not already exist.
        '''

        fields = self.class_item.get_fields()
        for f in fields:
            if f.name == field_name:
                return True
        return False

    def renameElement(self, oldname, newname, info):
        '''Called back after a user chose a new name for an element.
        '''

        androconf.debug("Renaming %s into %s in %s" % (oldname, newname, self.path))
        start, end = info
        try:
            t = self.doc.binding[start]
        except:
            self.mainwin.showStatus("Unexpected error in renameElement")
            return

        # Determine type of the to-be-renamed element and Androguard internal objects
        type_ = None
        if t[0] == 'NAME_METHOD_PROTOTYPE': # method definition in a class
            class_ = self.path
            method_ = t[1]
            if method_ == self.title:
                method_ = 'init'
            proto_ = proto2methodprotofunc(t[2].method.proto)
            androconf.debug("Found: class=%s, method=%s, proto=%s" % (class_, method_, proto_))
            type_ = "METHOD"
        elif t[0] == 'NAME_METHOD_INVOKE': # method call in a method
            class_, method_ = t[2].split(' -> ')
            class_ = classdot2class(class_)
            if class_ == 'this':
                class_ = self.path
            proto_ = proto2methodprotofunc("".join(t[3]) + t[4])
            androconf.debug("Found: class=%s, method=%s, proto=%s" % (class_, method_, proto_))
            type_ = "METHOD"
        elif t[0] == 'NAME_PROTOTYPE': # class definition on top of a class
            class_ = t[2] + '.' + t[1]
            package_ = t[2]
            androconf.debug("Found: package=%s, class=%s" % (package_, class_))
            type_ = "CLASS"
        elif t[0] == 'NAME_FIELD':
            field_item = t[3]
            type_ = "FIELD"
        else:
            self.mainwin.showStatus("Rename not available. Info found: '%s' but object not supported." % selection)
            return

        # Do the actual renaming
        if type_ == "METHOD":
            if self.method_name_exist(newname):
                self.mainwin.showStatus("Method name already exist")
                return

            class_item = getattr(self.mainwin.d, class2func(class_))
            try:
                method_item = getattr(class_item, method2func(method_))
            except AttributeError, e:
                androconf.debug("No attribute %s found for ClassDefItem" % method2func(method_))
                try:
                    method_name = method2func(method_) + '_' + proto_
                    androconf.debug("Backporting to method with prototype in attribute name: %s" % method_name)
                    method_item = getattr(class_item, method_name)
                except AttributeError, e:
                    raise e
            method_item.set_name(str(newname)) #unicode to ascii
        elif type_ == "CLASS":
            newname_class = classdot2class(package_ + '.' + newname)
            self.mainwin.showStatus("New name: %s" % newname_class)
            class_item = getattr(self.mainwin.d, classdot2func(class_))
            class_item.set_name(str(newname_class)) #unicode to ascii
            self.mainwin.updateDockWithTree()
        elif type_ == 'FIELD':
            if self.field_name_exist(newname):
                self.mainwin.showStatus("Field name already exist")
                return
            field_item.set_name(str(newname))
        else:
            self.mainwin.showStatus("Unsupported type: %s" % str(type_))
            return
        self.reload_java_sources()
