from future import standard_library

standard_library.install_aliases()
from androguard import session
from androguard.core.bytecodes.dvm import *
from androguard.decompiler.decompiler import *
from androguard.core.androconf import CONF


def init_print_colors():
    from IPython.utils import coloransi, io
    androconf.default_colors(coloransi.TermColors)
    CONF["PRINT_FCT"] = io.stdout.write


def get_default_session():
    """
        Return the default Session from the configuration
        or create a new one, if the session is None.
    """
    if CONF["SESSION"] is None:
        CONF["SESSION"] = session.Session()
    return CONF["SESSION"]


def AnalyzeAPK(filename, session=None):
    """
        Analyze an android application and setup all stuff for a more quickly analysis !

        :param session: A session (default None)
        :param filename: the filename of the android application or a buffer which represents the application
        :type filename: string

        :rtype: return the :class:`APK`, :class:`DalvikVMFormat`, and :class:`VMAnalysis` objects
    """
    androconf.debug("AnalyzeAPK")

    if not session:
        session = get_default_session()

    with open(filename, "rb") as fd:
        data = fd.read()

    session.add(filename, data)
    return session.get_objects_apk(filename)


def AnalyzeDex(filename, session=None):
    """
        Analyze an android dex file and setup all stuff for a more quickly analysis !

        :param session: A session (Default None)
        :param filename: the filename of the android dex file or a buffer which represents the dex file
        :type filename: string

        :rtype: return the :class:`DalvikVMFormat`, and :class:`VMAnalysis` objects
    """
    androconf.debug("AnalyzeDex")

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
    androconf.debug("AnalyzeODex")

    if not session:
        session = get_default_session()

    with open(filename, "rb") as fd:
        data = fd.read()

    return session.addDEY(filename, data)


def RunDecompiler(d, dx, decompiler):
    """
        Run the decompiler on a specific analysis

        :param d: the DalvikVMFormat object
        :type d: :class:`DalvikVMFormat` object
        :param dx: the analysis of the format
        :type dx: :class:`VMAnalysis` object
        :param decompiler: the type of decompiler to use ("dad", "dex2jad", "ded")
        :type decompiler: string
    """
    if decompiler is not None:
        androconf.debug("Decompiler ...")
        decompiler = decompiler.lower()
        if decompiler == "dex2jad":
            d.set_decompiler(DecompilerDex2Jad(
                d,
                androconf.CONF["PATH_DEX2JAR"],
                androconf.CONF["BIN_DEX2JAR"],
                androconf.CONF["PATH_JAD"],
                androconf.CONF["BIN_JAD"],
                androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler == "dex2fernflower":
            d.set_decompiler(DecompilerDex2Fernflower(
                d,
                androconf.CONF["PATH_DEX2JAR"],
                androconf.CONF["BIN_DEX2JAR"],
                androconf.CONF["PATH_FERNFLOWER"],
                androconf.CONF["BIN_FERNFLOWER"],
                androconf.CONF["OPTIONS_FERNFLOWER"],
                androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler == "ded":
            d.set_decompiler(DecompilerDed(
                d,
                androconf.CONF["PATH_DED"],
                androconf.CONF["BIN_DED"],
                androconf.CONF["TMP_DIRECTORY"]))
        else:
            d.set_decompiler(DecompilerDAD(d, dx))
