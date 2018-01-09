import traceback

from PyQt5 import QtCore

import androguard.session as session
from androguard.core import androconf
import logging

log = logging.getLogger("androguard.gui")


class FileLoadingThread(QtCore.QThread):
    file_loaded = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.parent = parent

        self.file_path = None
        self.incoming_file = ()

    def load(self, file_path):
        self.file_path = file_path
        if file_path.endswith(".ag"):
            self.incoming_file = (file_path, 'SESSION')
        else:
            file_type = androconf.is_android(file_path)
            self.incoming_file = (file_path, file_type)
        self.start(QtCore.QThread.LowestPriority)

    def run(self):
        if self.incoming_file:
            try:
                file_path, file_type = self.incoming_file
                if file_type in ["APK", "DEX", "DEY"]:
                    ret = self.parent.session.add(file_path,
                                                  open(file_path, 'rb').read())
                    self.file_loaded.emit(ret)
                elif file_type == "SESSION":
                    self.parent.session = session.Load(file_path)
                    self.file_loaded.emit(True)
                else:
                    self.file_loaded.emit(False)
            except Exception as e:
                log.debug(e)
                log.debug(traceback.format_exc())
                self.file_loaded.emit(False)

            self.incoming_file = []
        else:
            self.file_loaded.emit(False)
