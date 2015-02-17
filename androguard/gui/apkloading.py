from androguard.core import androconf
from PySide import QtCore

from androguard.misc import *

import os.path

class ApkLoadingThread(QtCore.QThread):

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.apk_path = None
        self.session_path = None

    def load(self, apk_path):
        self.apk_path = apk_path
        if apk_path.endswith(".apk"):
            self.session_path = self.apk_path[:-4] + '.ag'
        elif apk_path.endswith(".ag"):
            self.session_path = apk_path
        else:
            return
        self.start(QtCore.QThread.LowestPriority)

    def load_androguard_session(self):
        if not self.apk_path.endswith(".apk") and not self.apk_path.endswith(".ag"):
            androconf.warning("Not loading session. APK not supported")
            return False
        if os.path.isfile(self.session_path):
            androconf.debug("Loading previous session")
            self.a, self.d, self.x = load_session(self.session_path)
            return True
        return False

    def run(self):
        if self.apk_path is not None:
            try:
                if not self.load_androguard_session():
                    self.a, self.d, self.x = AnalyzeAPK(self.apk_path,
                            decompiler="dad")
                self.emit(QtCore.SIGNAL("loadedApk(bool)"), True)
            except Exception as e:
                androconf.debug(e)
                self.emit(QtCore.SIGNAL("loadedApk(bool)"), False)
        else:
            self.emit(QtCore.SIGNAL("loadedApk(bool)"), False)
