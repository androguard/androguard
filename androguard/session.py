from builtins import range
from builtins import object
import hashlib
import collections

from androguard.core import androconf
from androguard.core.bytecodes.apk import *
from androguard.core.bytecodes.dvm import *
from androguard.core.analysis.analysis import *
from androguard.decompiler.decompiler import *
from androguard.misc import save_session, load_session



def Save(session, filename):
    save_session(session, filename)

def Load(filename):
    return load_session(filename)

class Session(object):
    def __init__(self, export_ipython=False):
        self.setupObjects()
        self.export_ipython = export_ipython

    def setupObjects(self):
        self.analyzed_files = collections.OrderedDict()
        self.analyzed_digest = {}
        self.analyzed_apk = {}
        self.analyzed_dex = {}

    def reset(self):
        self.setupObjects()

    def isOpen(self):
        return self.analyzed_digest != {}

    def addAPK(self, filename, data):
        digest = hashlib.sha256(data).hexdigest()
        androconf.debug("add APK:%s" % digest)
        apk = APK(data, True)
        self.analyzed_apk[digest] = [apk]
        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename
        androconf.debug("added APK:%s" % digest)
        return (digest, apk)

    def addDEX(self, filename, data, dx=None):
        digest = hashlib.sha256(data).hexdigest()
        androconf.debug("add DEX:%s" % digest)

        androconf.debug("Parsing format ...")
        d = DalvikVMFormat(data)

        androconf.debug("Running analysis ...")
        dx = self.runAnalysis(d, dx)

        androconf.debug("added DEX:%s" % digest)

        self.analyzed_dex[digest] = (d, dx)
        if filename not in self.analyzed_files:
            self.analyzed_files[filename] = []

        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename

        if self.export_ipython:
            androconf.debug("Exporting in ipython")
            d.create_python_export()

        return (digest, d, dx)

    def addDEY(self, filename, data, dx=None):
        digest = hashlib.sha256(data).hexdigest()
        androconf.debug("add DEY:%s" % digest)

        d = DalvikOdexVMFormat(data)
        dx = self.runAnalysis(d, dx)

        androconf.debug("added DEY:%s" % digest)

        self.analyzed_dex[digest] = (d, dx)
        if filename not in self.analyzed_files:
            self.analyzed_files[filename] = []

        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename

        if self.export_ipython:
            d.create_python_export()

        return (digest, d, dx)

    def runAnalysis(self, d, dx=None):
        if dx == None:
            dx = Analysis(d)
        else:
            dx.add(d)

        dx.create_xref()

        d.set_decompiler(DecompilerDAD(d, dx))
        d.set_vmanalysis(dx)

        return dx

    def add(self, filename, raw_data, dx=None):
        ret = androconf.is_android_raw(raw_data)
        if ret:
            self.analyzed_files[filename] = []
            digest = hashlib.sha256(raw_data).hexdigest()
            if ret == "APK":
                apk_digest, apk = self.addAPK(filename, raw_data)
                dex_files = list(apk.get_all_dex())

                if dex_files:
                    dex_digest, _, dx = self.addDEX(filename, dex_files[0], dx)
                    self.analyzed_apk[digest].append(dex_digest)
                    for i in range(1, len(dex_files)):
                        dex_digest, _, _ = self.addDEX(filename, dex_files[i],
                                                       dx)
                        self.analyzed_apk[digest].append(dex_digest)
            elif ret == "DEX":
                self.addDEX(filename, raw_data, dx)
            elif ret == "DEY":
                self.addDEY(filename, raw_data, dx)
            else:
                return False
            return True
        return False

    def get_classes(self):
        idx = 0
        for filename in self.analyzed_files:
            for digest in self.analyzed_files[filename]:
                if digest in self.analyzed_dex:
                    d, _ = self.analyzed_dex[digest]
                    yield idx, filename, digest, d.get_classes()
            idx += 1

    def get_analysis(self, current_class):
        for digest in self.analyzed_dex:
            d, dx = self.analyzed_dex[digest]
            if dx.is_class_present(current_class.get_name()):
                return dx
        return None

    def get_format(self, current_class):
        for digest in self.analyzed_dex:
            d, dx = self.analyzed_dex[digest]
            if dx.is_class_present(current_class.get_name()):
                return d
        return None

    def get_filename_by_class(self, current_class):
        for digest in self.analyzed_dex:
            d, dx = self.analyzed_dex[digest]
            if dx.is_class_present(current_class.get_name()):
                return self.analyzed_digest[digest]
        return None

    def get_digest_by_class(self, current_class):
        for digest in self.analyzed_dex:
            d, dx = self.analyzed_dex[digest]
            if dx.is_class_present(current_class.get_name()):
                return digest
        return None

    def get_strings(self):
        for digest in self.analyzed_dex:
            d, dx = self.analyzed_dex[digest]
            yield digest, self.analyzed_digest[digest], dx.get_strings_analysis(
            )

    def get_nb_strings(self):
        nb = 0
        for digest in self.analyzed_dex:
            d, dx = self.analyzed_dex[digest]
            nb += len(dx.get_strings_analysis())
        return nb

    def get_all_apks(self):
        for digest in self.analyzed_apk:
            yield digest, self.analyzed_apk[digest]

    def get_objects_apk(self, filename):
        digest = self.analyzed_files.get(filename)
        if digest:
            a = self.analyzed_apk[digest[0]][0]

            d = None
            dx = None

            if len(self.analyzed_apk[digest[0]][1:]) == 1:
                dex_file = self.analyzed_dex[self.analyzed_apk[digest[0]][1]]
                d = dex_file[0]
                dx = dex_file[1]
            elif len(self.analyzed_apk[digest[0]][1:]) > 1:
                d = []
                dx = []
                for dex_file in self.analyzed_apk[digest[0]][1:]:
                    d.append(self.analyzed_dex[dex_file][0])
                    dx.append(self.analyzed_dex[dex_file][1])
            return a, d, dx
        return None

    def get_objects_dex(self):
        for digest in self.analyzed_dex:
            yield digest, self.analyzed_dex[digest][0], self.analyzed_dex[digest][1]
