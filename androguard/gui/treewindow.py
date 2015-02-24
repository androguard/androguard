from PySide import QtCore, QtGui

from androguard.core import androconf
from androguard.gui.xrefwindow import XrefDialog
from androguard.gui.sourcewindow import SourceWindow
from androguard.gui.helpers import classdot2class, Signature

class TreeWindow(QtGui.QTreeWidget):
    '''TODO
    '''

    def __init__(self, parent=None, win=None):

        super(TreeWindow, self).__init__(parent)
        self.itemDoubleClicked.connect(self.itemDoubleClickedHandler)
        self.mainwin = win
        self.createActions()
        self.header().close()

    def fill(self, classes):
        '''Parse all the paths (['Lcom/sogeti/example/myclass/MyActivity$1;', ...])
           and build a tree using the QTreeWidgetItem insertion method.'''

        root_path_node = ({}, self)
        for c in sorted(classes, key=lambda c: c.name):
            sig = Signature(c)
            path_node = root_path_node
            # Namespaces
            for path in sig.class_path:
                if path not in path_node[0]:
                    path_node[0][path] = ({},
                            QtGui.QTreeWidgetItem(path_node[1]))
                    path_node[0][path][1].setText(0, path)
                path_node = path_node[0][path]
            # Class
            path_node[0][path] = ({},
                    QtGui.QTreeWidgetItem(path_node[1]))
            path_node[0][path][1].setText(0, sig.class_name)

    def item2path(self, item, column=0):
        '''Browse all parents from QTreeWidgetItem item
           in order to rebuild the complete path
           Return both complete path (ex: "Landroid/support/AccessibilityServiceInfoCompat$1;")
           and path_elts (ex: [u'Landroid', u'support', u'AccessibilityServiceInfoCompat$1;'])
        '''

        path_elts = []
        while item is not None:
#            print item.text(column)
            path_elts.append(item.text(column))
            item = item.parent()
        path_elts.reverse()
        path = ".".join(path_elts)
        path = classdot2class(path)
        return path, path_elts

    def itemDoubleClickedHandler(self, item, column):
        '''Signal sent by PySide when a tree element is clicked'''

#        print "item %s has been double clicked at column %s" % (str(item), str(column))
        path, path_elts = self.item2path(item)

        if item.childCount() != 0:
            self.mainwin.showStatus("Sources not available. %s is not a class" % path)
            return
        self.mainwin.openSourceWindow(path)

    def createActions(self):
        self.xrefAct = QtGui.QAction("Xref from...", self,
#                shortcut=QtGui.QKeySequence("CTRL+B"),
                statusTip="List the references where this element is used",
                triggered=self.actionXref)
        self.expandAct = QtGui.QAction("Expand...", self,
                statusTip="Expand all the subtrees",
                triggered=self.actionExpand)
        self.collapseAct = QtGui.QAction("Collapse...", self,
                statusTip="Collapse all the subtrees",
                triggered=self.actionCollapse)

    def actionXref(self):
        item = self.currentItem()
        path, path_elts = self.item2path(item)
        if item.childCount() != 0:
            self.mainwin.showStatus("Xref not available. %s is not a class" % path)
            return

        xrefs_list = XrefDialog.get_xrefs_list(self.mainwin.d, path=path)
        if not xrefs_list:
            self.mainwin.showStatus("No xref returned.")
            return
        xwin = XrefDialog(parent=self.mainwin, win=self.mainwin, xrefs_list=xrefs_list, path=path)
        xwin.show()

    def expand_children(self, item):
        self.expandItem(item)
        for i in range(item.childCount()):
            self.expand_children(item.child(i))

    def actionExpand(self):
        self.expand_children(self.currentItem())

    def collapse_children(self, item):
        for i in range(item.childCount()):
            self.collapse_children(item.child(i))
        self.collapseItem(item)

    def actionCollapse(self):
        self.collapse_children(self.currentItem())

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        menu.addAction(self.xrefAct)
        menu.addAction(self.expandAct)
        menu.addAction(self.collapseAct)
        menu.exec_(event.globalPos())

