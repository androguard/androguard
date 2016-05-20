from PyQt5 import QtCore, QtGui, QtWidgets

from androguard.session import Session
from androguard.core import androconf
from androguard.gui.fileloading import FileLoadingThread
from androguard.gui.treewindow import TreeWindow
from androguard.gui.sourcewindow import SourceWindow
from androguard.gui.stringswindow import StringsWindow
from androguard.gui.binwindow import binWidget
from androguard.gui.DataModel import *

from androguard.gui.helpers import class2func

import os


class MainWindow(QtWidgets.QMainWindow):
    '''Main window:
       self.central: QTabWidget in center area
       self.dock: QDockWidget in left area
       self.tree: TreeWindow(QTreeWidget) in self.dock
    '''

    def __init__(self, parent=None, session=Session(), input_file=None):
        super(MainWindow, self).__init__(parent)
        self.session = session
        self.bin_windows = []

        self.setupSession()

        self.setupFileMenu()
        self.setupViewMenu()
        self.setupHelpMenu()

        self.setupCentral()
        self.setupEmptyTree()
        self.setupDock()
        self.setWindowTitle("Androguard GUI")

        self.showStatus("Androguard GUI")

        self.installEventFilter(self)

        if input_file != None:
            self.openFile(input_file)

    def eventFilter(self, watched, event):
        for bin_window in self.bin_windows:
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
        QtGui.QMessageBox.about(self, "About Androguard GUI",
                "<p><b>Androguard GUI</b> is basically a GUI for Androguard :)." \
                "<br>Have fun !</p>")

    def setupSession(self):
        self.fileLoadingThread = FileLoadingThread(self.session)
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

    def openFile(self, path=None):
        '''User clicked Open menu. Display a Dialog to ask which file to open.'''
        self.session.reset()

        if not path:
            path = QtGui.QFileDialog.getOpenFileName(
                self, "Open File", '',
                "Android Files (*.apk *.jar *.dex *.odex *.dey);;Androguard Session (*.ag)")
            path = str(path[0])

        if path:
            self.setupTree()
            self.showStatus("Analyzing %s..." % str(path))
            self.fileLoadingThread.load(path)

    def addFile(self, path=None):
        '''User clicked Open menu. Display a Dialog to ask which APK to open.'''
        if not self.session.isOpen():
            return

        if not path:
            path = QtGui.QFileDialog.getOpenFileName(
                self, "Add File", '',
                "Android Files (*.apk *.jar *.dex *.odex *.dey)")
            path = str(path[0])

        if path:
            self.showStatus("Analyzing %s..." % str(path))
            self.fileLoadingThread.load(path)

    def saveFile(self, path=None):
        '''User clicked Save menu. Display a Dialog to ask whwre to save.'''
        if not path:
            path = QtGui.QFileDialog.getSaveFileName(
                self, "Save File", '', "Androguard Session (*.ag)")
            path = str(path[0])

        if path:
            self.showStatus("Saving %s..." % str(path))
            self.saveSession(path)

    def saveSession(self, path):
        '''Save androguard session.'''
        try:
            self.session.save(path)
        except RuntimeError, e:
            androconf.error(str(e))
            # http://stackoverflow.com/questions/2134706/hitting-maximum-recursion-depth-using-pythons-pickle-cpickle
            androconf.error("Try increasing sys.recursionlimit")
            os.remove(path)
            androconf.warning("Session not saved")

    def quit(self):
        '''Clicked in File menu to exit or CTRL+Q to close main window'''
        QtGui.qApp.quit()

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
        self.central = QtWidgets.QTabWidget()
        self.central.setTabsClosable(True)
        self.central.tabCloseRequested.connect(self.tabCloseRequestedHandler)
        self.central.currentChanged.connect(self.currentTabChanged)
        self.setCentralWidget(self.central)

    def tabCloseRequestedHandler(self, index):
        self.central.removeTab(index)

    def currentTabChanged(self, index):
        androconf.debug("curentTabChanged -> %d" % index)
        if index == -1:
            return  # all tab closed

    def cleanCentral(self):
        #TOFIX: Removes all the pages, but does not delete them.
        self.central.clear()

    def setupFileMenu(self):
        fileMenu = QtWidgets.QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        fileMenu.addAction("&Add...", self.addFile, "Ctrl+A")
        fileMenu.addAction("&Save...", self.saveFile, "Ctrl+S")
        fileMenu.addAction("E&xit", self.quit, "Ctrl+Q")

    def setupViewMenu(self):
        viewMenu = QtWidgets.QMenu("&View", self)
        self.menuBar().addMenu(viewMenu)

        viewMenu.addAction("&Strings...", self.openStringsWindow)
        viewMenu.addAction("&APK...", self.openApkWindow)

    def setupHelpMenu(self):
        helpMenu = QtWidgets.QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QtWidgets.qApp.aboutQt)

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

    def openApkWindow(self):
        androconf.debug("openApkWindow for %s" % self.session.analyzed_apk)
        bin_window = binWidget(self, ApkModel(self.session.get_objects_apk(self.fileLoadingThread.file_path)[0]), "APK")
        bin_window.activateWindow()
        self.central.addTab(bin_window, bin_window.title)
        self.central.setCurrentWidget(bin_window)

        self.bin_windows.append(bin_window)

    def openBinWindow(self, current_class):
        androconf.debug("openBinWindow for %s" % current_class)
        bin_window = binWidget(self, DexClassModel(current_class), current_class.get_name())
        bin_window.activateWindow()
        self.central.addTab(bin_window, current_class.current_title)
        self.central.setCurrentWidget(bin_window)

        self.bin_windows.append(bin_window)

    def openSourceWindow(self, current_class, method=None):
        '''Main function to open a .java source window
           It checks if it already opened and open that tab,
           otherwise, initialize a new window.
        '''
        androconf.debug("openSourceWindow for %s" % current_class)

        sourcewin = self.getMeSourceWindowIfExists(current_class)
        if not sourcewin:
            current_filename = self.session.get_filename_by_class(current_class)
            current_digest = self.session.get_digest_by_class(current_class)

            sourcewin = SourceWindow(win=self,
                                     current_class=current_class,
                                     current_title=current_class.current_title,
                                     current_filename=current_filename,
                                     current_digest=current_digest,
                                     session=self.session)
            sourcewin.reload_java_sources()
            self.central.addTab(sourcewin, sourcewin.title)
            self.central.setTabToolTip(self.central.indexOf(sourcewin),
                                       current_class.get_name())

        if method:
            sourcewin.browse_to_method(method)

        self.central.setCurrentWidget(sourcewin)

    def getMeSourceWindowIfExists(self, current_class):
        '''Helper for openSourceWindow'''
        for idx in range(self.central.count()):
            if current_class.get_name() == self.central.tabToolTip(idx):
                androconf.debug("Tab %s already opened at: %d" %
                                (current_class.get_name(), idx))
                return self.central.widget(idx)
        return None

    def doesClassExist(self, path):
        arg = class2func(path)
        try:
            getattr(self.d, arg)
        except AttributeError:
            return False
        return True
