from PySide import QtCore, QtGui

import getpass, time

from androguard.core import androconf
from androguard.gui.apkloading import ApkLoadingThread
from androguard.gui.treewindow import TreeWindow
from androguard.gui.sourcewindow import SourceWindow
from androguard.gui.androlyze import save_session
from androguard.gui.helpers import class2func

import os

class MainWindow(QtGui.QMainWindow):

    '''Main window:
       self.central: QTabWidget in center area
       self.editor: QTextEdit in self.central (deprecated)
       self.dock: QDockWidget in left area
       self.tree: QTreeWidget in self.dock
    '''

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setupFileMenu()
        self.setupHelpMenu()
        self.setupFont()
        self.setupCentral()
        self.setupDock()
        self.setupApkLoading()

        self.setCentralWidget(self.central)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)
        self.setWindowTitle("AndroGui")

        self.showStatus("AndroGui")

#        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+b"), self.tree, self.tree.actionXref)

        # debug
        if getpass.getuser() == 'cedric':
            self.openFile("/home/cedric/Desktop/bugweek/sieve.apk")
            #self.openFile("/home/cedric/Desktop/bugweek/av/com.trustgo.mobile.security-1.3.15-48.apk")
            #self.openFile("/home/cedric/Browser.apk")

    def showStatus(self, msg):
        androconf.debug(msg)
        self.statusBar().showMessage(msg)

    def about(self):
        QtGui.QMessageBox.about(self, "About AndroGui",
                "<p><b>AndroGui</b> is basically a Gui for Androguard :)." \
                "<br>So we named it AndroGui :p. </p>")

    def newFile(self):
        #TODO: fix
        #self.editor.clear()
        self.central.clear()

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

        #self.updateDock()
        self.updateDockWithTree()
        self.cleanCentral()

        self.showStatus("Analysis of %s done!" %
                str(self.apkLoadingThread.apk_path))

        # debug
        if getpass.getuser() == 'cedric' and False:
#            sourcewin = SourceWindow(win=self, path="Lcom/mwr/example/sieve/AuthServiceConnector;")
            sourcewin = SourceWindow(win=self, path="Lcom/mwr/example/sieve/MainLoginActivity;")
           # sourcewin.browse_to_method("firstLaunchResult")
            sourcewin.browse_to_method("login")

    def openFile(self, path=None):

        if not path:
            path = QtGui.QFileDialog.getOpenFileName(self, "Open File",
                    '', "APK Files (*.apk)")
            try:
                # Python v3.
                path = str(path[0], encoding='ascii')
            except TypeError:
                # Python v2.
                path = str(path[0])

        if path:
            self.showStatus("Analyzing %s..." % str(path))
            self.apkLoadingThread.load(path)

    def saveSession(self):
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

    def setupTree(self):
        self.tree = TreeWindow(win=self)
        self.tree.setWindowTitle("Tree model")

    def setupDock(self):
        self.setupTree()
        self.dock = QtGui.QDockWidget("Classes", self)
        self.dock.setWidget(self.tree)

#    def updateDock(self):
#        self.tree = TreeWindow(win=self)
#        self.tree.setWindowTitle("Tree model")
#        self.dock.setWidget(self.tree)

    def setupCentral(self):
        self.central = QtGui.QTabWidget()
        self.central.setTabsClosable(True)
        self.central.tabCloseRequested.connect(self.tabCloseRequestedHandler)
        self.central.currentChanged.connect(self.currentTabChanged)

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


    def setupFont(self):
        self.font = QtGui.QFont()
        self.font.setFamily('Courier')
        self.font.setFixedPitch(True)
        self.font.setPointSize(10)

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

    def updateDockWithTree(self):
        if self.tree:
            del self.tree
        self.tree = TreeWindow(win=self)
        self.tree.setWindowTitle("Tree model")
        self.dock.setWidget(self.tree)
        paths = self.d.get_classes_names(update=True)
        self.tree.insertTree(paths)
#        self.tree.expandItem(self.tree.topLevelItem(0))

    def openSourceWindow(self, path, method=""):
        #TODO: move the addTab here also? and get it out from SourceWindow?
        sourcewin = self.getMeSourceWindowIfExists(path)
        if not sourcewin:
            sourcewin = SourceWindow(win=self, path=path)
        if method:
            sourcewin.browse_to_method(method)
        self.central.setCurrentWidget(sourcewin)

    def getMeSourceWindowIfExists(self, path):
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

