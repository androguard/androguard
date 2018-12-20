from androguard.session import Session
from androguard.decompiler import decompiler
from androguard.core import androconf
import hashlib
import re
import os
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis

import logging
log = logging.getLogger("androguard.misc")


def init_print_colors():
    from IPython.utils import coloransi, io
    androconf.default_colors(coloransi.TermColors)
    androconf.CONF["PRINT_FCT"] = io.stdout.write


def get_default_session():
    """
    Return the default Session from the configuration
    or create a new one, if the session in the configuration is None.
    """
    if androconf.CONF["SESSION"] is None:
        androconf.CONF["SESSION"] = Session()
    return androconf.CONF["SESSION"]


def AnalyzeAPK(_file, session=None, raw=False):
    """
    Analyze an android application and setup all stuff for a more quickly
    analysis!
    If session is None, no session is used at all. This is the default
    behaviour.
    If you like to continue your work later, it might be a good idea to use a
    session.
    A default session can be created by using :meth:`~get_default_session`.

    :param _file: the filename of the android application or a buffer which represents the application
    :type _file: string (for filename) or bytes (for raw)
    :param session: A session (default: None)
    :param raw: boolean if raw bytes are supplied instead of a filename
    :rtype: return the :class:`~androguard.core.bytecodes.apk.APK`, list of :class:`~androguard.core.bytecodes.dvm.DalvikVMFormat`, and :class:`~androguard.core.analysis.analysis.Analysis` objects
    """
    log.debug("AnalyzeAPK")

    if session:
        log.debug("Using existing session {}".format(session))
        if raw:
            data = _file
            filename = hashlib.md5(_file).hexdigest()
        else:
            with open(_file, "rb") as fd:
                data = fd.read()
                filename = _file

        digest = session.add(filename, data)
        return session.get_objects_apk(filename, digest)
    else:
        log.debug("Analysing without session")
        a = APK(_file, raw=raw)
        # FIXME: probably it is not necessary to keep all DalvikVMFormats, as
        # they are already part of Analysis. But when using sessions, it works
        # this way...
        d = []
        dx = Analysis()
        for dex in a.get_all_dex():
            df = DalvikVMFormat(dex, using_api=a.get_target_sdk_version())
            dx.add(df)
            d.append(df)
            df.set_decompiler(decompiler.DecompilerDAD(d, dx))

        dx.create_xref()

        return a, d, dx


def AnalyzeDex(filename, session=None):
    """
    Analyze an android dex file and setup all stuff for a more quickly analysis !

    :param filename: the filename of the android dex file or a buffer which represents the dex file
    :type filename: string
    :param session: A session (Default None)

    :rtype: return a tuple of (sha256hash, :class:`DalvikVMFormat`, :class:`Analysis`)
    """
    log.debug("AnalyzeDex")

    if not session:
        session = get_default_session()

    with open(filename, "rb") as fd:
        data = fd.read()

    return session.addDEX(filename, data)


def AnalyzeODex(filename, session=None):
    """
    Analyze an android odex file and setup all stuff for a more quickly analysis !

    :param filename: the filename of the android dex file or a buffer which represents the dex file
    :type filename: string
    :param session: The Androguard Session to add the ODex to (default: None)

    :rtype: return a tuple of (sha256hash, :class:`DalvikOdexVMFormat`, :class:`Analysis`)
    """
    log.debug("AnalyzeODex")

    if not session:
        session = get_default_session()

    with open(filename, "rb") as fd:
        data = fd.read()

    return session.addDEY(filename, data)


def RunDecompiler(d, dx, decompiler_name):
    """
    Run the decompiler on a specific analysis

    :param d: the DalvikVMFormat object
    :type d: :class:`DalvikVMFormat` object
    :param dx: the analysis of the format
    :type dx: :class:`VMAnalysis` object
    :param decompiler: the type of decompiler to use ("dad", "dex2jad", "ded")
    :type decompiler: string
    """
    if decompiler_name is not None:
        log.debug("Decompiler ...")
        decompiler_name = decompiler_name.lower()
        # TODO put this into the configuration object and make it more dynamic
        # e.g. detect new decompilers and so on...
        if decompiler_name == "dex2jad":
            d.set_decompiler(decompiler.DecompilerDex2Jad(
                d,
                androconf.CONF["BIN_DEX2JAR"],
                androconf.CONF["BIN_JAD"],
                androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler_name == "dex2fernflower":
            d.set_decompiler(decompiler.DecompilerDex2Fernflower(
                d,
                androconf.CONF["BIN_DEX2JAR"],
                androconf.CONF["BIN_FERNFLOWER"],
                androconf.CONF["OPTIONS_FERNFLOWER"],
                androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler_name == "ded":
            d.set_decompiler(decompiler.DecompilerDed(
                d,
                androconf.CONF["BIN_DED"],
                androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler_name == "jadx":
            d.set_decompiler(decompiler.DecompilerJADX(d, dx, jadx=androconf.CONF["BIN_JADX"]))
        else:
            d.set_decompiler(decompiler.DecompilerDAD(d, dx))


def sign_apk(filename, keystore, storepass):
    """
    Use jarsigner to sign an APK file.

    :param filename: APK file on disk to sign (path)
    :param keystore: path to keystore
    :param storepass: your keystorage passphrase
    """
    from subprocess import Popen, PIPE, STDOUT
    # TODO use apksigner instead of jarsigner
    cmd = Popen([androconf.CONF["BIN_JARSIGNER"], "-sigalg", "MD5withRSA",
                 "-digestalg", "SHA1", "-storepass", storepass, "-keystore",
                 keystore, filename, "alias_name"],
                stdout=PIPE,
                stderr=STDOUT)
    stdout, stderr = cmd.communicate()


def clean_file_name(filename, unique=True, replace="_", force_nt=False):
    """
    Return a filename version, which has no characters in it which are forbidden.
    On Windows these are for example <, /, ?, ...

    The intention of this function is to allow distribution of files to different OSes.

    :param filename: string to clean
    :param unique: check if the filename is already taken and append an integer to be unique (default: True)
    :param replace: replacement character. (default: '_')
    :param force_nt: Force shortening of paths like on NT systems (default: False)
    :return: clean string
    """

    if re.match(r'[<>:"/\\|?* .\x00-\x1f]', replace):
        raise ValueError("replacement character is not allowed!")

    path, fname = os.path.split(filename)
    # For Windows see: https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
    # Other operating systems seems to be more tolerant...

    # Not allowed filenames, attach replace character if necessary
    if re.match(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', fname):
        fname += replace

    # reserved characters
    fname = re.sub(r'[<>:"/\\|?*\x00-\x1f]', replace, fname)
    # Do not end with dot or space
    fname = re.sub(r'[ .]$', replace, fname)

    if force_nt or os.name == 'nt':
        PATH_MAX_LENGTH = 230  # give extra space for other stuff...
        # Check filename length limit, usually a problem on older Windows versions
        if len(fname) > PATH_MAX_LENGTH:
            if "." in fname:
                f, ext = fname.rsplit(".", 1)
                fname = "{}.{}".format(f[:PATH_MAX_LENGTH-(len(ext)+1)], ext)
            else:
                fname = fname[:PATH_MAX_LENGTH]

        # Special behaviour... On Windows, there is also a problem with the maximum path length in explorer.exe
        # maximum length is limited to 260 chars, so use 250 to have room for other stuff
        if len(os.path.abspath(os.path.join(path, fname))) > 250:
            fname = fname[:250 - (len(os.path.abspath(path)) + 1)]

    if unique:
        counter = 0
        origname = fname
        while os.path.isfile(os.path.join(path, fname)):
            if "." in fname:
                # assume extension
                f, ext = origname.rsplit(".", 1)
                fname = "{}_{}.{}".format(f, counter, ext)
            else:
                fname = "{}_{}".format(origname, counter)
            counter += 1

    return os.path.join(path, fname)


