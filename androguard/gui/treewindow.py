from PySide import QtCore, QtGui

import getpass

from androguard.core import androconf
from androguard.gui.helpers import classmethod2display
from androguard.gui.xrefwindow import XrefDialog
from androguard.gui.sourcewindow import SourceWindow

class TreeWindow(QtGui.QTreeWidget):
    '''TODO
    '''

    def __init__(self, parent=None, win=None):

        super(TreeWindow, self).__init__(parent)
        self.itemDoubleClicked.connect(self.itemDoubleClickedHandler)
        self.mainwin = win
        self.createActions()

    def insertTree(self, paths):
        '''Parse all the paths (['Lcom/sogeti/example/myclass/MyActivity$1;', ...])
           and build a tree using the QTreeWidgetItem insertion method.

           NB: This algo works because in alphabetical order thanks to sort()
        '''

        header = QtGui.QTreeWidgetItem(["Tree"])
        self.setHeaderItem(header)

        paths.sort()
        d = {} # dict of QTreeWodgetItem indexed by paths (already browsed)
        for p in paths:
#            print "-"*20
#            print "handling: " + str(p)
#            print d
            elements = p.split("/")
            #add folders if does not exist
            for i in range(len(elements)):
                parent_str = "/".join(elements[:i])
                current_str = elements[i]
                path = (parent_str, current_str)
                if path not in d.keys():
#                    print "adding (%s,%s)" % path
                    if not parent_str:
                        e = QtGui.QTreeWidgetItem(self, [elements[i]])
                    else:
                        elements2 = parent_str.split("/")
                        # we are sure it exists due to algorithm
                        e = QtGui.QTreeWidgetItem(d[("/".join(elements2[:-1]), elements2[-1])], [elements[i]])
                    d[path] = e
                    #debug
                    if getpass.getuser() == "cedric":
                        self.expandItem(e) #HAX to expand all items during loading

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
        path = "/".join(path_elts)
        return path, path_elts

    def itemDoubleClickedHandler(self, item, column):
        '''Signal sent by PySide when a tree element is clicked'''

#        print "item %s has been double clicked at column %s" % (str(item), str(column))
        path, path_elts = self.item2path(item)

        if ";" not in path:
            self.mainwin.showStatus("Sources not available. %s is not a class" % path)
            return

        self.mainwin.openSourceWindow(path)

    def createActions(self):
        self.xrefAct = QtGui.QAction("Xref from...", self,
#                shortcut=QtGui.QKeySequence("CTRL+B"),
                statusTip="List the references where this element is used",
                triggered=self.actionXref)

    def actionXref(self):
        item = self.currentItem()
        path, path_elts = self.item2path(item)
        if ";" not in path:
            self.mainwin.showStatus("Xref not available. %s is not a class" % path)
            return

        xrefs_list = XrefDialog.get_xrefs_list(self.mainwin.d, path=path)
        if not xrefs_list:
            androconf.debug("No xref returned")
            return
        xwin = XrefDialog(parent=self.mainwin, win=self.mainwin, xrefs_list=xrefs_list, path=path)
        xwin.show()

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        menu.addAction(self.xrefAct)
        menu.exec_(event.globalPos())

