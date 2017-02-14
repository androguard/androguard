from builtins import str
from builtins import range
from PyQt5 import QtWidgets, QtGui

from androguard.core import androconf
from androguard.gui.xrefwindow import XrefDialogClass
from androguard.gui.sourcewindow import SourceWindow
from androguard.gui.helpers import classdot2class, Signature

class HashableQTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    
    # TODO this is a pure workaround to have a hash method!
    # It seems that for python2 is __hash__ available
    # But not on python3
    def __hash__(self):
        return hash(self.__str__())


class TreeWindow(QtWidgets.QTreeWidget):

    def __init__(self, parent=None, win=None, session=None):
        super(TreeWindow, self).__init__(parent)
        self.itemDoubleClicked.connect(self.itemDoubleClickedHandler)
        self.mainwin = win
        self.session = session
        self.createActions()
        self.header().close()
        self.root_path_node = ({}, self)

        self.setupCaches()

    def setupCaches(self):
        self._reverse_cache = {}

    def fill(self):
        '''Parse all the paths (['Lcom/example/myclass/MyActivity$1;', ...])
           and build a tree using the QTreeWidgetItem insertion method.'''
        androconf.debug("Fill classes tree")

        for idx, filename, digest, classes in self.session.get_classes():
            for c in sorted(classes, key=lambda c: c.name):
                sig = Signature(c)
                path_node = self.root_path_node

                path = None
                if sig.class_path == []:
                    path = '.'
                    if path not in path_node[0]:
                        path_node[0][path] = (
                            {}, HashableQTreeWidgetItem(path_node[1]))
                        path_node[0][path][1].setText(0, path)
                    path_node = path_node[0][path]
                else:
                    # Namespaces
                    for path in sig.class_path:
                        if path not in path_node[0]:
                            path_node[0][path] = (
                                {}, HashableQTreeWidgetItem(path_node[1]))
                            path_node[0][path][1].setText(0, path)
                        path_node = path_node[0][path]

                # Class
                path_node[0][path] = ({}, HashableQTreeWidgetItem(path_node[1]))

                class_name = sig.class_name

                if idx > 0:
                    class_name += "@%d" % idx

                c.current_title = class_name
                self._reverse_cache[path_node[0][path][1]] = (c, filename,
                                                              digest)

                path_node[0][path][1].setText(0, class_name)

    def itemDoubleClickedHandler(self, item, column):
        androconf.debug("item %s has been double clicked at column %s" %
                        (str(item), str(column)))
        if item.childCount() != 0:
            self.mainwin.showStatus("Sources not available.")
            return

        current_class, current_filename, current_digest = self._reverse_cache[
            item
        ]
        self.mainwin.openBinWindow(current_class)

    def createActions(self):
        self.xrefAct = QtWidgets.QAction(
            "Xref from/to",
            self,
            statusTip="List the references where this element is used",
            triggered=self.actionXref)
        self.expandAct = QtWidgets.QAction("Expand",
                                       self,
                                       statusTip="Expand all the subtrees",
                                       triggered=self.actionExpand)
        self.collapseAct = QtWidgets.QAction("Collapse",
                                         self,
                                         statusTip="Collapse all the subtrees",
                                         triggered=self.actionCollapse)

    def actionXref(self):
        item = self.currentItem()
        if item.childCount() != 0:
            self.mainwin.showStatus("Xref not availables")
            return

        current_class, _, _ = self._reverse_cache[item]

        current_analysis = self.session.get_analysis(current_class)
        if not current_analysis:
            self.mainwin.showStatus("No xref returned (no analysis object).")
            return

        class_analysis = current_analysis.get_class_analysis(
            current_class.get_name())
        if not class_analysis:
            self.mainwin.showStatus(
                "No xref returned (no class_analysis object).")
            return

        xwin = XrefDialogClass(parent=self.mainwin,
                               win=self.mainwin,
                               current_class=current_class,
                               class_analysis=class_analysis)
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
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.xrefAct)
        menu.addAction(self.expandAct)
        menu.addAction(self.collapseAct)
        menu.exec_(event.globalPos())
