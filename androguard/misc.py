from androguard import session
from androguard.decompiler import decompiler
from androguard.core import androconf
import hashlib

import logging
log = logging.getLogger("androguard.misc")


def init_print_colors():
    from IPython.utils import coloransi, io
    androconf.default_colors(coloransi.TermColors)
    androconf.CONF["PRINT_FCT"] = io.stdout.write


def get_default_session():
    """
        Return the default Session from the configuration
        or create a new one, if the session is None.
    """
    if androconf.CONF["SESSION"] is None:
        androconf.CONF["SESSION"] = session.Session()
    return androconf.CONF["SESSION"]


def AnalyzeAPK(_file, session=None, raw=False):
    """
        Analyze an android application and setup all stuff for a more quickly analysis !

        :param session: A session (default None)
        :param _file: the filename of the android application or a buffer which represents the application
        :type _file: string or bytes

        :rtype: return the :class:`APK`, :class:`DalvikVMFormat`, and :class:`VMAnalysis` objects
    """
    log.debug("AnalyzeAPK")

    if not session:
        session = get_default_session()

    if raw:
        data = _file
        filename = hashlib.md5(_file).hexdigest()
    else:
        with open(_file, "rb") as fd:
            data = fd.read()
            filename = _file

    digest = session.add(filename, data)
    return session.get_objects_apk(filename, digest)


def AnalyzeDex(filename, session=None):
    """
        Analyze an android dex file and setup all stuff for a more quickly analysis !

        :param session: A session (Default None)
        :param filename: the filename of the android dex file or a buffer which represents the dex file
        :type filename: string

        :rtype: return the :class:`DalvikVMFormat`, and :class:`VMAnalysis` objects
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

        :rtype: return the :class:`DalvikOdexVMFormat`, and :class:`VMAnalysis` objects
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
