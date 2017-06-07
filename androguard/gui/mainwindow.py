from __future__ import print_function
from builtins import str
from builtins import range
from PyQt5 import QtCore, QtGui, QtWidgets

import androguard.session as session_module
from androguard.core import androconf
from androguard.gui.fileloading import FileLoadingThread
from androguard.gui.treewindow import TreeWindow
from androguard.gui.sourcewindow import SourceWindow
from androguard.gui.stringswindow import StringsWindow
from androguard.gui.methodswindow import MethodsWindow
from androguard.gui.resourceswindow import ResourcesWindow
from androguard.gui.apiwindow import APIWindow
from androguard.gui.binwindow import binWidget
from androguard.gui.DataModel import *

from androguard.gui.helpers import class2func

import os, imp


class TabsWindow(QtWidgets.QTabWidget):
    def __init__(self, bin_windows, parent=None):
        super(TabsWindow, self).__init__(parent)
        self.bin_windows = bin_windows
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.tabCloseRequestedHandler)
        self.currentChanged.connect(self.currentTabChanged)

        self.closeAllTabs = QtWidgets.QAction(
            "Close all tabs",
            self,
            triggered=self.actioncloseAllTabs)
        self.closeOtherTabs = QtWidgets.QAction(
            "Close other tabs",
            self,
            triggered=self.actioncloseOtherTabs)
        self.closeLeftTabs = QtWidgets.QAction(
            "Close left tabs",
            self,
            triggered=self.actioncloseLeftTabs)
        self.closeRightTabs = QtWidgets.QAction(
            "Close right tabs",
            self,
            triggered=self.actioncloseRightTabs)

    def actioncloseAllTabs(self):
        self.clear()

    def actioncloseOtherTabs(self):
        for i in range(self.currentIndex()-1, -1, -1):
            self.removeTab(i)

        for i in range(self.count(), self.currentIndex(), -1):
            self.removeTab(i)

    def actioncloseLeftTabs(self):
        for i in range(self.currentIndex()-1, -1, -1):
            self.removeTab(i)

    def actioncloseRightTabs(self):
        for i in range(self.count(), self.currentIndex(), -1):
            self.removeTab(i)

    def tabCloseRequestedHandler(self, index):
        self.removeTab(index)

    def currentTabChanged(self, index):
        androconf.debug("curentTabChanged -> %d (%s)" % (index, self.tabToolTip(index)))
        if index == -1:
            return

        current_title = self.tabToolTip(index)
        for title in self.bin_windows:
            if title != current_title:
                androconf.debug("Disable %s" % title)
                self.bin_windows[title].disable()

        if current_title in self.bin_windows:
            androconf.debug("Enable %s" % title)
            self.bin_windows[current_title].enable()


    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.closeAllTabs)
        menu.addAction(self.closeOtherTabs)
        menu.addAction(self.closeLeftTabs)
        menu.addAction(self.closeRightTabs)
        menu.exec_(event.globalPos())

class MainWindow(QtWidgets.QMainWindow):
    '''Main window:
       self.central: QTabWidget in center area
       self.dock: QDockWidget in left area
       self.tree: TreeWindow(QTreeWidget) in self.dock
    '''

    def __init__(self, parent=None, session=session_module.Session(), input_file=None, input_plugin=None):
        super(MainWindow, self).__init__(parent)
        self.session = session
        self.bin_windows = {}

        self.setupFileMenu()
        self.setupViewMenu()
        self.setupPluginsMenu()
        self.setupHelpMenu()

        self.setupCentral()
        self.setupEmptyTree()
        self.setupDock()

        self.setupSession()

        self.setWindowTitle("Androguard GUI")

        self.showStatus("Androguard GUI")

        self.installEventFilter(self)

        self.input_plugin = input_plugin

        if input_file:
            self._openFile(input_file)

    def eventFilter(self, watched, event):
        for bin_window in list(self.bin_windows.values()):
            bin_window.eventFilter(watched, event)
        return False

    def showStatus(self, msg):
        '''Helper function called by any window to display a message
           in status bar.
        '''
        androconf.debug(msg)
        self.statusBar().showMessage(msg)

    def about(self):
        '''User clicked About menu. Display a Message box.'''
        QtWidgets.QMessageBox.about(self, "About Androguard GUI",
                "<p><b>Androguard GUI</b> is basically a GUI for Androguard :)." \
                "<br>Have fun !</p>")

    def setupSession(self):
        androconf.debug("Setup Session")
        self.fileLoadingThread = FileLoadingThread(self)
        self.fileLoadingThread.file_loaded.connect(self.loadedFile)

    def loadedFile(self, success):
        if not success:
            self.showStatus("Analysis of %s failed :(" %
                            str(self.fileLoadingThread.file_path))
            return

        self.updateDockWithTree()
        self.cleanCentral()

        self.showStatus("Analysis of %s done!" %
                        str(self.fileLoadingThread.file_path))
        if self.input_plugin:
            self._runPlugin(self.input_plugin)

    def openFile(self):
        self.session.reset()

        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File", '.',
            "Android Files (*.apk *.jar *.dex *.odex *.dey);;Androguard Session (*.ag)")

        self._openFile(filepath)

    def _openFile(self, filepath=None):
        if filepath:
            self.setupTree()
            self.showStatus("Analyzing %s..." % str(filepath))
            self.fileLoadingThread.load(filepath)

    def addFile(self):
        if not self.session.isOpen():
            return

        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Add File", '',
            "Android Files (*.apk *.jar *.dex *.odex *.dey)")

        if filepath:
            self.showStatus("Analyzing %s..." % str(filepath))
            self.fileLoadingThread.load(filepath)

    def saveFile(self):
        '''User clicked Save menu. Display a Dialog to ask whwre to save.'''
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save File", '', "Androguard Session (*.ag)")

        if filepath:
            self.showStatus("Saving %s..." % str(filepath))
            self.saveSession(filepath)

    def saveSession(self, filepath):
        '''Save androguard session.'''
        try:
            session_module.Save(self.session, filepath)
        except RuntimeError as e:
            androconf.error(str(e))
            os.remove(filepath)
            androconf.warning("Session not saved")

    def _runPlugin(self, filepath):
        androconf.debug("RUN plugin from %s" % filepath)
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        f, filename, description = imp.find_module(
            module_name,
            [os.path.dirname(filepath)])
        print(f, filename, description)
        mod = imp.load_module(module_name, f, filename, description)
        mod.PluginEntry(self.session)

    def openRunPluginWindow(self):
        filepath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File", '',
            "Python Files (*.py);;")

        if filepath:
            self._runPlugin(filepath)

    def closeEvent(self, event):
        '''Clicked [x] to close main window'''
        event.accept()

    def setupEmptyTree(self):
        '''Setup empty Tree at startup. '''
        if hasattr(self, "tree"):
            del self.tree
        self.tree = QtWidgets.QTreeWidget(self)
        self.tree.header().close()

    def setupDock(self):
        '''Setup empty Dock at startup. '''
        self.dock = QtWidgets.QDockWidget("Classes", self)
        self.dock.setWidget(self.tree)
        self.dock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)

    def setupTree(self):
        androconf.debug("Setup Tree")
        self.tree = TreeWindow(win=self, session=self.session)
        self.tree.setWindowTitle("Tree model")
        self.dock.setWidget(self.tree)

    def setupCentral(self):
        '''Setup empty window supporting tabs at startup. '''
        self.central = TabsWindow(self.bin_windows, self)
        self.setCentralWidget(self.central)

    def cleanCentral(self):
        self.central.actioncloseAllTabs()

    def setupFileMenu(self):
        androconf.debug("Setup File Menu")
        self.fileMenu = self.menuBar().addMenu("&File")

        self.fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        self.fileMenu.addAction("&Add...", self.addFile, "Ctrl+A")
        self.fileMenu.addAction("&Save...", self.saveFile, "Ctrl+S")
        self.fileMenu.addAction("E&xit", self.close, "Ctrl+Q")

    def setupViewMenu(self):
        androconf.debug("Setup View Menu")

        self.viewMenu = self.menuBar().addMenu("&View")

        self.viewMenu.addAction("&Strings...", self.openStringsWindow)
        self.viewMenu.addAction("&Methods...", self.openMethodsWindow)
        self.viewMenu.addAction("&API...", self.openAPIWindow)
        self.viewMenu.addAction("&APK...", self.openApkWindow)
        self.viewMenu.addAction("&Resources...", self.openResourcesWindow)

    def setupPluginsMenu(self):
        androconf.debug("Setup Plugins Menu")

        self.pluginsMenu = self.menuBar().addMenu("&Plugins")
        self.pluginsMenu.addAction("&Run...", self.openRunPluginWindow)

    def setupHelpMenu(self):
        androconf.debug("Setup Help Menu")

        self.helpMenu = self.menuBar().addMenu("&Help")

        self.helpMenu.addAction("&About", self.about)
        self.helpMenu.addAction("About &Qt", QtWidgets.qApp.aboutQt)

    def updateDockWithTree(self, empty=False):
        '''Update the classes tree. Called when
            - a new APK has been imported
            - a classe has been renamed (displayed in the tree)
        '''
        self.setupTree()
        self.tree.fill()

    def openStringsWindow(self):
        stringswin = StringsWindow(win=self, session=self.session)
        self.central.addTab(stringswin, stringswin.title)
        self.central.setTabToolTip(self.central.indexOf(stringswin),
                                   stringswin.title)
        self.central.setCurrentWidget(stringswin)

    def openMethodsWindow(self):
        methodswin = MethodsWindow(win=self, session=self.session)
        self.central.addTab(methodswin, methodswin.title)
        self.central.setTabToolTip(self.central.indexOf(methodswin),
                                   methodswin.title)
        self.central.setCurrentWidget(methodswin)

    def openResourcesWindow(self):
        resourceswin = ResourcesWindow(win=self, session=self.session)
        self.central.addTab(resourceswin, resourceswin.title)
        self.central.setTabToolTip(self.central.indexOf(resourceswin),
                                   resourceswin.title)
        self.central.setCurrentWidget(resourceswin)

    def openAPIWindow(self):
        apiwin = APIWindow(win=self, session=self.session)
        self.central.addTab(apiwin, apiwin.title)
        self.central.setTabToolTip(self.central.indexOf(apiwin),
                                   apiwin.title)
        self.central.setCurrentWidget(apiwin)

    def openApkWindow(self):
        androconf.debug("openApkWindow for %s" % self.session.analyzed_apk)
        bin_window = binWidget(self, ApkModel(self.session.get_objects_apk(self.fileLoadingThread.file_path)[0]), "APK")
        bin_window.activateWindow()
        self.central.addTab(bin_window, bin_window.title)
        self.central.setCurrentWidget(bin_window)

        self.bin_windows[bin_window.title] = bin_window

    def openBinWindow(self, current_class):
        androconf.debug("openBinWindow for %s" % current_class)

        bin_window = self.getMeOpenedWindowIfExists(current_class.current_title)
        if not bin_window:
            bin_window = binWidget(self, DexClassModel(current_class), current_class.get_name())
            bin_window.activateWindow()
            self.central.addTab(bin_window, current_class.current_title)
            self.central.setTabToolTip(self.central.indexOf(bin_window),
                                       current_class.current_title)

            self.bin_windows[current_class.current_title] = bin_window
            bin_window.enable()

        self.central.setCurrentWidget(bin_window)


    def openSourceWindow(self, current_class, method=None):
        '''Main function to open a decompile source window
           It checks if it already opened and open that tab,
           otherwise, initialize a new window.
        '''
        androconf.debug("openSourceWindow for %s" % current_class)

        sourcewin = self.getMeOpenedWindowIfExists(current_class.current_title + "(S)")
        if not sourcewin:
            current_filename = self.session.get_filename_by_class(current_class)
            current_digest = self.session.get_digest_by_class(current_class)

            sourcewin = SourceWindow(win=self,
                                     current_class=current_class,
                                     current_title=current_class.current_title + "(S)",
                                     current_filename=current_filename,
                                     current_digest=current_digest,
                                     session=self.session)
            sourcewin.reload_java_sources()
            self.central.addTab(sourcewin, sourcewin.title)
            self.central.setTabToolTip(self.central.indexOf(sourcewin),
                                       sourcewin.title)

        if method:
            sourcewin.browse_to_method(method)

        self.central.setCurrentWidget(sourcewin)

    def getMeOpenedWindowIfExists(self, name):
        for idx in range(self.central.count()):
            if name == self.central.tabToolTip(idx):
                androconf.debug("Tab %s already opened at: %d" %
                                (name, idx))
                return self.central.widget(idx)
        return None

    def doesClassExist(self, path):
        arg = class2func(path)
        try:
            getattr(self.d, arg)
        except AttributeError:
            return False
        return True
