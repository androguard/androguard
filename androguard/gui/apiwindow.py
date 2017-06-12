from PyQt5 import QtCore, QtGui, QtWidgets
from androguard.gui.xrefwindow import XrefDialogMethod


class APIWindow(QtWidgets.QWidget):

    def __init__(self, parent=None, win=None, session=None):
        super(APIWindow, self).__init__(parent)
        self.mainwin = win
        self.session = session
        self.title = "API"

        self.filterPatternLineEdit = QtWidgets.QLineEdit()
        self.filterPatternLabel = QtWidgets.QLabel("&Filter method name pattern:")
        self.filterPatternLabel.setBuddy(self.filterPatternLineEdit)
        self.filterPatternLineEdit.textChanged.connect(self.filterRegExpChanged)

        self.methodswindow = APIValueWindow(self, win, session)

        sourceLayout = QtWidgets.QVBoxLayout()
        sourceLayout.addWidget(self.methodswindow)
        sourceLayout.addWidget(self.filterPatternLabel)
        sourceLayout.addWidget(self.filterPatternLineEdit)

        self.setLayout(sourceLayout)

    def filterRegExpChanged(self, value):
        regExp = QtCore.QRegExp(value)
        self.methodswindow.proxyModel.setFilterRegExp(regExp)


class APIValueWindow(QtWidgets.QTreeView):

    def __init__(self, parent=None, win=None, session=None):
        super(APIValueWindow, self).__init__(parent)
        self.mainwin = win
        self.session = session
        self.title = "API"

        self.reverse_methods = {}

        self.proxyModel = QtCore.QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)

        nb = 0
        for digest, d, dx in self.session.get_objects_dex():
            for external_class in dx.get_external_classes():
                nb += len(external_class.orig_class.methods)

        self.model = QtGui.QStandardItemModel(nb, 5,
                                              self)

        self.model.setHeaderData(0, QtCore.Qt.Horizontal, "Name")
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, "Class Name")
        self.model.setHeaderData(2, QtCore.Qt.Horizontal, "Prototype")
        self.model.setHeaderData(3, QtCore.Qt.Horizontal, "Digest")

        row = 0
        for digest, d, dx in self.session.get_objects_dex():
            for external_class in dx.get_external_classes():
                for method in list(external_class.orig_class.methods.values()):
                    self.model.setData(self.model.index(
                        row, 0, QtCore.QModelIndex()), method.get_name())
                    self.model.setData(self.model.index(
                        row, 1, QtCore.QModelIndex()), method.get_class_name())
                    self.model.setData(self.model.index(
                        row, 2, QtCore.QModelIndex()), method.get_descriptor())
                    self.model.setData(self.model.index(
                        row, 3, QtCore.QModelIndex()), digest)
                    self.reverse_methods[method.get_name() + method.get_class_name() + method.get_descriptor()
                                        ] = dx.get_method_analysis(method)
                    row += 1

        self.proxyModel.setSourceModel(self.model)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setModel(self.proxyModel)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.doubleClicked.connect(self.slotDoubleClicked)

    def slotDoubleClicked(self, mi):
        mi = self.proxyModel.mapToSource(mi)
        row = mi.row()
        column = mi.column()

        if column == 0:
            xwin = XrefDialogMethod(
                parent=self.mainwin,
                win=self.mainwin,
                method_analysis=self.reverse_methods[self.model.item(row).text() +
                                                     self.model.item(row, 1).text() + 
                                                     self.model.item(row, 2).text()])
            xwin.show()
