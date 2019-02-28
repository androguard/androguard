import hashlib
import os
import sys
import collections
from androguard.core.analysis.analysis import Analysis
from androguard.core.bytecodes.dvm import DalvikVMFormat, DalvikOdexVMFormat
from androguard.core.bytecodes.apk import APK
from androguard.decompiler.decompiler import DecompilerDAD
from androguard.core import androconf

import pickle
import logging
import datetime

log = logging.getLogger("androguard.session")


def Save(session, filename=None):
    """
    save your session to use it later.

    Returns the filename of the written file.
    If not filename is given, a file named `androguard_session_<DATE>.ag` will
    be created in the current working directory.
    `<DATE>` is a timestamp with the following format: `%Y-%m-%d_%H%M%S`.

    This function will overwrite existing files without asking.

    If the file could not written, None is returned.

    example::

        s = session.Session()
        session.Save(s, "msession.ag")

    :param session: A Session object to save
    :param filename: output filename to save the session
    :type filename: string

    """

    if not filename:
        filename = "androguard_session_{:%Y-%m-%d_%H%M%S}.ag".format(datetime.datetime.now())

    if os.path.isfile(filename):
        log.warning("{} already exists, overwriting!")

    # Setting the recursion limit according to the documentation:
    # https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled
    #
    # Some larger APKs require a high recursion limit.
    # Tested to be above 35000 for some files, setting to 50k to be sure.
    # You might want to set this even higher if you encounter problems
    reclimit = sys.getrecursionlimit()
    sys.setrecursionlimit(50000)
    saved = False
    try:
        with open(filename, "wb") as fd:
            pickle.dump(session, fd)
        saved = True
    except RecursionError:
        log.exception("Recursion Limit hit while saving. "
                      "Current Recursion limit: {}. "
                      "Please report this error!".format(sys.getrecursionlimit()))
        # Remove partially written file
        os.unlink(filename)

    sys.setrecursionlimit(reclimit)
    return filename if saved else None


def Load(filename):
    """
      load your session!

      example::

          s = session.Load("mysession.ag")

      :param filename: the filename where the session has been saved
      :type filename: string

      :rtype: the elements of your session :)

    """
    with open(filename, "rb") as fd:
        return pickle.load(fd)


class Session:
    """
    A Session is able to store multiple APK, DEX or ODEX files and can be pickled
    to disk in order to resume work later.

    The main function used in Sessions is probably :meth:`add`, which adds files
    to the session and performs analysis on them.

    Afterwards, the files can be gathered using methods such as
    :meth:`get_objects_apk`, :meth:`get_objects_dex` or :meth:`get_classes`.

    example::

        s = Session()
        digest = s.add("some.apk")

        print("SHA256 of the file: {}".format(digest))

        a, d, dx = s.get_objects_apk("some.apk", digest)
        print(a.get_package())

        # Reset the Session for a fresh set of files
        s.reset()

        digest2 = s.add("classes.dex")
        print("SHA256 of the file: {}".format(digest2))
        for h, d, dx in s.get_objects_dex():
            print("SHA256 of the DEX file: {}".format(h))


    """
    def __init__(self, export_ipython=False):
        """
        Create a new Session object

        :param export_ipython: set to True in order to create attributes for the
        use in iPython
        """
        self._setup_objects()
        self.export_ipython = export_ipython

    def save(self, filename=None):
        """
        Save the current session, see also :func:`~androguard.session.Save`.
        """
        return Save(self, filename)

    def _setup_objects(self):
        self.analyzed_files = collections.defaultdict(list)
        self.analyzed_digest = dict()
        self.analyzed_apk = dict()

        # Stores Analysis Objects
        # needs to be ordered to return the outermost element when searching for
        # classes
        self.analyzed_vms = collections.OrderedDict()

        # Dict of digest and DalvikVMFormat/DalvikOdexFormat
        # Actually not needed, as we have Analysis objects which store the DEX
        # files as well, but we do not remove it here for legacy reasons
        self.analyzed_dex = dict()

    def reset(self):
        """
        Reset the current session, delete all added files.
        """
        self._setup_objects()

    def isOpen(self):
        """
        Test if any file was analyzed in this session

        :return: `True` if any file was analyzed, `False` otherwise
        """
        return len(self.analyzed_digest) > 0

    def show(self):
        """
        Print information to stdout about the current session.
        Gets all APKs, all DEX files and all Analysis objects.
        """
        print("APKs in Session: {}".format(len(self.analyzed_apk)))
        for d, a in self.analyzed_apk.items():
            print("\t{}: {}".format(d, a))

        print("DEXs in Session: {}".format(len(self.analyzed_dex)))
        for d, dex in self.analyzed_dex.items():
            print("\t{}: {}".format(d, dex))

        print("Analysis in Session: {}".format(len(self.analyzed_vms)))
        for d, a in self.analyzed_vms.items():
            print("\t{}: {}".format(d, a))

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

        dx = Analysis()
        self.analyzed_vms[digest] = dx

        for dex in apk.get_all_dex():
            # we throw away the output... FIXME?
            self.addDEX(filename, dex, dx)

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

        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename

        self.analyzed_dex[digest] = d

        if dx is None:
            dx = Analysis()

        dx.add(d)
        dx.create_xref()

        # TODO: If multidex: this will called many times per dex, even if already set
        for d in dx.vms:
            # TODO: allow different decompiler here!
            d.set_decompiler(DecompilerDAD(d, dx))
            d.set_vmanalysis(dx)
        self.analyzed_vms[digest] = dx

        if self.export_ipython:
            log.debug("Exporting in ipython")
            d.create_python_export()

        return digest, d, dx

    def addDEY(self, filename, data, dx=None):
        """
        Add an ODEX file to the session and run the analysis
        """
        digest = hashlib.sha256(data).hexdigest()
        log.debug("add DEY:%s" % digest)
        d = DalvikOdexVMFormat(data)
        log.debug("added DEY:%s" % digest)

        self.analyzed_files[filename].append(digest)
        self.analyzed_digest[digest] = filename

        self.analyzed_dex[digest] = d

        if self.export_ipython:
            d.create_python_export()

        if dx is None:
            dx = Analysis()

        dx.add(d)
        dx.create_xref()

        for d in dx.vms:
            # TODO: allow different decompiler here!
            d.set_decompiler(DecompilerDAD(d, dx))
            d.set_vmanalysis(dx)

        self.analyzed_vms[digest] = dx

        return digest, d, dx

    def add(self, filename, raw_data=None, dx=None):
        """
        Generic method to add a file to the session.

        This is the main method to use when adding files to a Session!

        If an APK file is supplied, all DEX files are analyzed too.
        For DEX and ODEX files, only this file is analyzed (what else should be
        analyzed).

        Returns the SHA256 of the analyzed file.

        :param filename: filename to load
        :param raw_data: bytes of the file, or None to load the file from filename
        :param dx: An already exiting :class:`~androguard.core.analysis.analysis.Analysis` object
        :return: the sha256 of the file or None on failure
        """
        if not raw_data:
            log.debug("Loading file from '{}'".format(filename))
            with open(filename, "rb") as fp:
                raw_data = fp.read()

        ret = androconf.is_android_raw(raw_data)
        log.debug("Found filetype: '{}'".format(ret))
        if not ret:
            return None

        if ret == "APK":
            digest, _ = self.addAPK(filename, raw_data)
        elif ret == "DEX":
            digest, _, _ = self.addDEX(filename, raw_data, dx)
        elif ret == "DEY":
            digest, _, _ = self.addDEY(filename, raw_data, dx)
        else:
            return None

        return digest

    def get_classes(self):
        """
        Returns all Java Classes from the DEX objects as an array of DEX files.
        """
        for idx, digest in enumerate(self.analyzed_vms):
            dx = self.analyzed_vms[digest]
            for vm in dx.vms:
                filename = self.analyzed_digest[digest]
                yield idx, filename, digest, vm.get_classes()

    def get_analysis(self, current_class):
        """
        Returns the :class:`~androguard.core.analysis.analysis.Analysis` object
        which contains the `current_class`.

        :param current_class: The class to search for
        :type current_class: androguard.core.bytecodes.dvm.ClassDefItem
        :rtype: androguard.core.analysis.analysis.Analysis
        """
        for digest in self.analyzed_vms:
            dx = self.analyzed_vms[digest]
            if dx.is_class_present(current_class.get_name()):
                return dx
        return None

    def get_format(self, current_class):
        """
        Returns the :class:`~androguard.core.bytecodes.dvm.DalvikVMFormat` of a
        given :class:`~androguard.core.bytecodes.dvm.ClassDefItem`.

        :param current_class: A ClassDefItem
        """
        return current_class.CM.vm

    def get_filename_by_class(self, current_class):
        """
        Returns the filename of the DEX file where the class is in.

        Returns the first filename this class was present.
        For example, if you analyzed an APK, this should return the filename of
        the APK and not of the DEX file.

        :param current_class: ClassDefItem
        :returns: None if class was not found or the filename
        """
        for digest, dx in self.analyzed_vms.items():
            if dx.is_class_present(current_class.get_name()):
                return self.analyzed_digest[digest]
        return None

    def get_digest_by_class(self, current_class):
        """
        Return the SHA256 hash of the object containing the ClassDefItem

        Returns the first digest this class was present.
        For example, if you analyzed an APK, this should return the digest of
        the APK and not of the DEX file.
        """
        for digest, dx in self.analyzed_vms.items():
            if dx.is_class_present(current_class.get_name()):
                return digest
        return None

    def get_strings(self):
        """
        Yields all StringAnalysis for all unique Analysis objects
        """
        seen = []
        for digest, dx in self.analyzed_vms.items():
            if dx in seen:
                continue
            seen.append(dx)
            yield digest, self.analyzed_digest[digest], dx.get_strings_analysis()

    def get_nb_strings(self):
        """
        Return the total number of strings in all Analysis objects
        """
        nb = 0
        seen = []
        for digest, dx in self.analyzed_vms.items():
            if dx in seen:
                continue
            seen.append(dx)
            nb += len(dx.get_strings_analysis())
        return nb

    def get_all_apks(self):
        """
        Yields a list of tuples of SHA256 hash of the APK and APK objects
        of all analyzed APKs in the Session.
        """
        for digest, a in self.analyzed_apk.items():
            yield digest, a

    def get_objects_apk(self, filename=None, digest=None):
        """
        Returns APK, DalvikVMFormat and Analysis of a specified APK.

        You must specify either `filename` or `digest`.
        It is possible to use both, but in this case only `digest` is used.

        example::

            s = Session()
            digest = s.add("some.apk")
            a, d, dx = s.get_objects_apk(digest=digest)

        example::

            s = Session()
            filename = "some.apk"
            digest = s.add(filename)
            a, d, dx = s.get_objects_apk(filename=filename)

        :param filename: the filename of the APK file, only used of digest is None
        :param digest: the sha256 hash, as returned by :meth:`add` for the APK
        :returns: a tuple of (APK, [DalvikVMFormat], Analysis)
        """
        if not filename and not digest:
            raise ValueError("Must give at least filename or digest!")

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
        """
        Yields all dex objects inclduing their Analysis objects

        :returns: tuple of (sha256, DalvikVMFormat, Analysis)
        """
        # TODO: there is no variant like get_objects_apk
        for digest, d in self.analyzed_dex.items():
            yield digest, d, self.analyzed_vms[digest]

