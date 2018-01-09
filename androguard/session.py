import hashlib

from androguard.core.analysis.analysis import *
from androguard.core.bytecodes.dvm import *
from androguard.decompiler.decompiler import *
from androguard.core import androconf

import pickle
import logging

log = logging.getLogger("androguard.session")


def Save(session, filename):
    """
    save your session!

    :param session: A Session object to save
    :param filename: output filename to save the session
    :type filename: string

    :Example:
        s = session.Session()
        session.Save(s, "msession.p")
    """
    with open(filename, "wb") as fd:
        pickle.dump(session, fd)


def Load(filename):
    """
      load your session!

      :param filename: the filename where the session has been saved
      :type filename: string

      :rtype: the elements of your session :)

      :Example:
          s = session.Load("mysession.p")
    """
    with open(filename, "rb") as fd:
        return pickle.load(fd)


class Session(object):
    def __init__(self, export_ipython=False):
        self._setupObjects()
        self.export_ipython = export_ipython

    def _setupObjects(self):
        self.analyzed_files = collections.OrderedDict()
        self.analyzed_digest = {}
        self.analyzed_apk = {}
        self.analyzed_dex = collections.OrderedDict()
        self.analyzed_vms = collections.OrderedDict()

    def reset(self):
        self._setupObjects()

    def isOpen(self):
        """
        Test if any file was analyzed in this session

        :return: `True` if any file was analyzed, `False` otherwise
        """
        return self.analyzed_digest != {}

    def addAPK(self, filename, data):
        """
        Add an APK file to the Session and run analysis on it.

        :param filename: (file)name of APK file
        :param data: binary data of the APK file
        :return: a tuple of SHA256 Checksum and APK Object
        """
        digest = hashlib.sha256(data).hexdigest()
        log.debug("add APK:%s" % digest)
        apk = APK(data, True)
        self.analyzed_apk[digest] = [apk]
        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename
        self.analyzed_vms[digest] = Analysis()
        log.debug("added APK:%s" % digest)
        return digest, apk

    def addDEX(self, filename, data, dx=None):
        """
        Add a DEX file to the Session and run analysis.

        :param filename: the (file)name of the DEX file
        :param data: binary data of the dex file
        :param dx: an existing Analysis Object (optional)
        :return: A tuple of SHA256 Hash, DalvikVMFormat Object and Analysis object
        """
        digest = hashlib.sha256(data).hexdigest()
        log.debug("add DEX:%s" % digest)

        log.debug("Parsing format ...")
        d = DalvikVMFormat(data)
        log.debug("added DEX:%s" % digest)

        if filename not in self.analyzed_files:
            self.analyzed_files[filename] = []

        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename

        if dx is None:
            dx = Analysis()

        dx.add(d)
        dx.create_xref()

        for d in dx.vms:
            d.set_decompiler(DecompilerDAD(d, dx))
            d.set_vmanalysis(dx)
        self.analyzed_dex[digest] = dx

        if self.export_ipython:
            log.debug("Exporting in ipython")
            d.create_python_export()

        return digest, d, dx

    def addDEY(self, filename, data, dx=None):
        digest = hashlib.sha256(data).hexdigest()
        log.debug("add DEY:%s" % digest)
        d = DalvikOdexVMFormat(data)
        log.debug("added DEY:%s" % digest)

        if filename not in self.analyzed_files:
            self.analyzed_files[filename] = []

        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename

        if self.export_ipython:
            d.create_python_export()

        if dx is None:
            dx = Analysis()

        dx.add(d)
        dx.create_xref()

        for d in dx.vms:
            d.set_decompiler(DecompilerDAD(d, dx))
            d.set_vmanalysis(dx)

        self.analyzed_dex[digest] = dx

        return digest, d, dx

    def add(self, filename, raw_data, dx=None):
        ret = androconf.is_android_raw(raw_data)
        digest = None
        if not ret:
            return None
        self.analyzed_files[filename] = []
        if ret == "APK":
            digest, apk = self.addAPK(filename, raw_data)
            dex_files = list(apk.get_all_dex())
            dx = self.analyzed_vms.get(digest)
            for dex in dex_files:
                _, d, dx = self.addDEX(filename, dex, dx)
        elif ret == "DEX":
            digest, d, _ = self.addDEX(filename, raw_data)
            dx = self.analyzed_dex.get(digest)
        elif ret == "DEY":
            digest, d, _ = self.addDEY(filename, raw_data, dx)
            dx = self.analyzed_dex.get(digest)
        else:
            return None

        return digest

    def get_classes(self):
        # NOTE: verify idx for this api.
        idx = 0
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            for vm in dx.vms:
                filename = self.analyzed_digest[digest]
                yield idx, filename, digest, vm.get_classes()
            idx += 1

    def get_analysis(self, current_class):
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            if dx.is_class_present(current_class.get_name()):
                return dx
        return None

    def get_format(self, current_class):
        return current_class.CM.vm

    def get_filename_by_class(self, current_class):
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            if dx.is_class_present(current_class.get_name()):
                return self.analyzed_digest[digest]
        return None

    def get_digest_by_class(self, current_class):
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            if dx.is_class_present(current_class.get_name()):
                return digest
        return None

    def get_strings(self):
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            yield digest, self.analyzed_digest[digest], dx.get_strings_analysis(
            )

    def get_nb_strings(self):
        nb = 0
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            nb += len(dx.get_strings_analysis())
        return nb

    def get_all_apks(self):
        for digest in self.analyzed_apk:
            yield digest, self.analyzed_apk[digest]

    def get_objects_apk(self, filename, digest=None):
        if digest is None:
            digests = self.analyzed_files.get(filename)
            # Negate to reduce tree
            if not digests:
                return None, None, None
            digest = digests[0]

        a = self.analyzed_apk[digest][0]
        dx = self.analyzed_vms[digest]
        return a, dx.vms, dx

    def get_objects_dex(self):
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            for vm in dx.vms:
                yield digest, vm, dx
