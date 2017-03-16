from builtins import str
from PyQt5 import QtCore, QtGui, QtWidgets


class ResourcesWindow(QtWidgets.QWidget):

    def __init__(self, parent=None, win=None, session=None):
        super(ResourcesWindow, self).__init__(parent)
        self.mainwin = win
        self.session = session
        self.title = "Resources"

        self.filterPatternLineEdit = QtWidgets.QLineEdit()
        self.filterPatternLabel = QtWidgets.QLabel("&Filter resource integer pattern:")
        self.filterPatternLabel.setBuddy(self.filterPatternLineEdit)
        self.filterPatternLineEdit.textChanged.connect(self.filterRegExpChanged)

        self.resourceswindow = ResourcesValueWindow(self, win, session)

        sourceLayout = QtWidgets.QVBoxLayout()
        sourceLayout.addWidget(self.resourceswindow)
        sourceLayout.addWidget(self.filterPatternLabel)
        sourceLayout.addWidget(self.filterPatternLineEdit)

        self.setLayout(sourceLayout)

    def filterRegExpChanged(self, value):
        regExp = QtCore.QRegExp(value)
        self.resourceswindow.proxyModel.setFilterRegExp(regExp)


class ResourcesValueWindow(QtWidgets.QTreeView):

    def __init__(self, parent=None, win=None, session=None):
        super(ResourcesValueWindow, self).__init__(parent)
        self.mainwin = win
        self.session = session
        self.title = "Resources"

        self.proxyModel = QtCore.QSortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)

        string_resources = None
        for digest, apk in self.session.get_all_apks():
            a = apk[0]
            resources = a.get_android_resources()

            string_resources = resources.get_resolved_strings()
            nb = 0
            for p in string_resources:
                for l in string_resources[p]:
                    nb += len(string_resources[p][l])

        self.model = QtGui.QStandardItemModel(nb, 4,
                                              self)

        self.model.setHeaderData(0, QtCore.Qt.Horizontal, "Package name")
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, "Locale")
        self.model.setHeaderData(2, QtCore.Qt.Horizontal, "ID")
        self.model.setHeaderData(3, QtCore.Qt.Horizontal, "Value")

        row = 0
        for p_name in string_resources:
            for locale in string_resources[p_name]:
                for id_value in string_resources[p_name][locale]:
                    self.model.setData(self.model.index(
                        row, 0, QtCore.QModelIndex()), p_name)
                    self.model.setData(self.model.index(
                        row, 1, QtCore.QModelIndex()), str(locale))
                    self.model.setData(self.model.index(
                        row, 2, QtCore.QModelIndex()), str(id_value))
                    self.model.setData(self.model.index(
                        row, 3, QtCore.QModelIndex()),
                        string_resources[p_name][locale][id_value])
                    row += 1

        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterKeyColumn(2)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setModel(self.proxyModel)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
