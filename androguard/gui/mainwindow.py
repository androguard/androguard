from PySide import QtCore, QtGui

from androguard.misc import save_session
from androguard.core import androconf
from androguard.gui.apkloading import ApkLoadingThread
from androguard.gui.treewindow import TreeWindow
from androguard.gui.sourcewindow import SourceWindow
from androguard.gui.helpers import class2func

import os

class MainWindow(QtGui.QMainWindow):

    '''Main window:
       self.central: QTabWidget in center area
       self.dock: QDockWidget in left area
       self.tree: TreeWindow(QTreeWidget) in self.dock
    '''

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setupApkLoading()

        self.setupFileMenu()
        self.setupHelpMenu()

        self.setupCentral()
        self.setupEmptyTree()
        self.setupDock()
        self.setWindowTitle("AndroGui")

        self.showStatus("AndroGui")

    def showStatus(self, msg):
        '''Helper function called by any window to display a message
           in status bar.
        '''
        androconf.debug(msg)
        self.statusBar().showMessage(msg)

    def about(self):
        '''User clicked About menu. Display a Message box.'''
        QtGui.QMessageBox.about(self, "About AndroGui",
                "<p><b>AndroGui</b> is basically a Gui for Androguard :)." \
                "<br>So we named it AndroGui :p. </p>")

    def newFile(self):
        #TODO: by replacing newFile with closeFile
        # and close androguard saved info and save .ag?
        self.cleanCentral()

    def setupApkLoading(self):
        self.apkLoadingThread = ApkLoadingThread()
        self.connect(self.apkLoadingThread,
                QtCore.SIGNAL("loadedApk(bool)"),
                self.loadedApk)

    def loadedApk(self, success):
        if not success:
            self.showStatus("Analysis of %s failed :(" %
                    str(self.apkLoadingThread.apk_path))
            return

        self.a = self.apkLoadingThread.a
        self.d = self.apkLoadingThread.d
        self.x = self.apkLoadingThread.x

        self.updateDockWithTree()
        self.cleanCentral()

        self.showStatus("Analysis of %s done!" %
                str(self.apkLoadingThread.apk_path))

    def openFile(self, path=None):
        '''User clicked Open menu. Display a Dialog to ask which APK to open.'''
        if not path:
            path = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                    '', "APK Files (*.apk)")
            path = str(path[0])

        if path:
            self.showStatus("Analyzing %s..." % str(path))
            self.apkLoadingThread.load(path)

    def saveSession(self):
        '''Save androguard session to same name as APK name except ending with .ag'''
        if not hasattr(self, "a") or not hasattr(self, "d") or not hasattr(self, "x"):
            print "WARNING: session not saved because no Dalvik elements"
            return
        try:
            save_session([self.a, self.d, self.x], self.apkLoadingThread.session_path)
        except RuntimeError, e:
            print "ERROR:" + str(e)
            #http://stackoverflow.com/questions/2134706/hitting-maximum-recursion-depth-using-pythons-pickle-cpickle
            print "Try increasing sys.recursionlimit"
            os.remove(self.apkLoadingThread.session_path)
            print "WARNING: session not saved"

    def quit(self):
        '''Clicked in File menu to exit or CTRL+Q to close main window'''

        self.saveSession()
        QtGui.qApp.quit()

    def closeEvent(self, event):
        '''Clicked [x] to close main window'''

        self.saveSession()
        event.accept()

    def setupEmptyTree(self):
        '''Setup empty Tree at startup. '''
        if hasattr(self, "tree"):
            del self.tree
        self.tree = QtGui.QTreeWidget(self)
        self.tree.header().close()

    def setupDock(self):
        '''Setup empty Dock at startup. '''
        self.dock = QtGui.QDockWidget("Classes", self)
        self.dock.setWidget(self.tree)
        self.dock.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)

    def setupCentral(self):
        '''Setup empty window supporting tabs at startup. '''
        self.central = QtGui.QTabWidget()
        self.central.setTabsClosable(True)
        self.central.tabCloseRequested.connect(self.tabCloseRequestedHandler)
        self.central.currentChanged.connect(self.currentTabChanged)
        self.setCentralWidget(self.central)

    def tabCloseRequestedHandler(self, index):
        self.central.removeTab(index)

    def currentTabChanged(self, index):
        androconf.debug("curentTabChanged -> %d" % index)
        if index == -1:
            return # all tab closed
        sourcewin = self.central.widget(index)
        sourcewin.reload_java_sources()

    def cleanCentral(self):
        #TOFIX: Removes all the pages, but does not delete them.
        self.central.clear()

    def setupFileMenu(self):
        fileMenu = QtGui.QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&New...", self.newFile, "Ctrl+N")
        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        fileMenu.addAction("E&xit", self.quit, "Ctrl+Q")

    def setupHelpMenu(self):
        helpMenu = QtGui.QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QtGui.qApp.aboutQt)

    def updateDockWithTree(self, empty=False):
        '''Update the classes tree. Called when
            - a new APK has been imported
            - a classe has been renamed (displayed in the tree)
        '''
        if not hasattr(self, "d"):
            androconf.debug("updateDockWithTree failed because no dalvik initialized")
            return
        if hasattr(self, "tree"):
            del self.tree
        self.tree = TreeWindow(win=self)
        self.tree.setWindowTitle("Tree model")
        self.dock.setWidget(self.tree)
        paths = self.d.get_classes_names(update=True)
        self.tree.insertTree(paths)

    def openSourceWindow(self, path, method=""):
        '''Main function to open a .java source window
           It checks if it already opened and open that tab,
           otherwise, initialize a new window.
        '''
        sourcewin = self.getMeSourceWindowIfExists(path)
        if not sourcewin:
            sourcewin = SourceWindow(win=self, path=path)
            self.central.addTab(sourcewin, sourcewin.title)
            self.central.setTabToolTip(self.central.indexOf(sourcewin), sourcewin.path)
        if method:
            sourcewin.browse_to_method(method)
        self.central.setCurrentWidget(sourcewin)

    def getMeSourceWindowIfExists(self, path):
        '''Helper for openSourceWindow'''
        for idx in range(self.central.count()):
            if path == self.central.tabToolTip(idx):
                androconf.debug("Tab %s already opened at: %d" % (path, idx))
                return self.central.widget(idx)
        return None

    def doesClassExist(self, path):
        arg = class2func(path)
        try:
            getattr(self.d, arg)
        except AttributeError:
            return False
        return True

