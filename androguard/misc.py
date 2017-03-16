from future import standard_library
standard_library.install_aliases()
from androguard.core import *
from androguard.core.bytecode import *
from androguard.core.bytecodes.dvm import *
from androguard.core.bytecodes.apk import *
from androguard.core.analysis.analysis import *
from androguard.decompiler.decompiler import *

from pickle import dumps, loads
from androguard.core import androconf


def init_print_colors():
    from IPython.utils import coloransi, io
    androconf.default_colors(coloransi.TermColors)
    CONF["PRINT_FCT"] = io.stdout.write


def save_session(l, filename):
    """
      save your session !

      :param l: a list of objects
      :type: a list of object
      :param filename: output filename to save the session
      :type filename: string

      :Example:
          save_session([a, vm, vmx], "msession.json")
  """
    with open(filename, "wb") as fd:
        fd.write(dumps(l, -1))


def load_session(filename):
    """
      load your session !

      :param filename: the filename where the session has been saved
      :type filename: string

      :rtype: the elements of your session :)

      :Example:
          a, vm, vmx = load_session("mysession.json")
  """
    return loads(read(filename, binary=False))


def AnalyzeAPK(filename, decompiler="dad", session=None):
    """
        Analyze an android application and setup all stuff for a more quickly analysis !

        :param filename: the filename of the android application or a buffer which represents the application
        :type filename: string
        :param decompiler: ded, dex2jad, dad (optional)
        :type decompiler: string

        :rtype: return the :class:`APK`, :class:`DalvikVMFormat`, and :class:`VMAnalysis` objects
    """
    androconf.debug("AnalyzeAPK")

    if not session:
        session = CONF["SESSION"]

    with open(filename, "rb") as fd:
        data = fd.read()

    session.add(filename, data)
    return session.get_objects_apk(filename)


def AnalyzeDex(filename, decompiler="dad", session=None):
    """
        Analyze an android dex file and setup all stuff for a more quickly analysis !

        :param filename: the filename of the android dex file or a buffer which represents the dex file
        :type filename: string

        :rtype: return the :class:`DalvikVMFormat`, and :class:`VMAnalysis` objects
    """
    androconf.debug("AnalyzeDex")

    if not session:
        session = CONF["SESSION"]

    with open(filename, "rb") as fd:
        data = fd.read()

    return session.addDEX(filename, data)


def AnalyzeODex(filename, decompiler="dad", session=None):
    """
        Analyze an android odex file and setup all stuff for a more quickly analysis !

        :param filename: the filename of the android dex file or a buffer which represents the dex file
        :type filename: string

        :rtype: return the :class:`DalvikOdexVMFormat`, and :class:`VMAnalysis` objects
    """
    androconf.debug("AnalyzeODex")

    if not session:
        session = CONF["SESSION"]

    with open(filename, "rb") as fd:
        data = fd.read()

    return session.addDEY(filename, data)


def RunDecompiler(d, dx, decompiler, session=None):
    """
        Run the decompiler on a specific analysis

        :param d: the DalvikVMFormat object
        :type d: :class:`DalvikVMFormat` object
        :param dx: the analysis of the format
        :type dx: :class:`VMAnalysis` object
        :param decompiler: the type of decompiler to use ("dad", "dex2jad", "ded")
        :type decompiler: string
    """
    if decompiler != None:
        androconf.debug("Decompiler ...")
        decompiler = decompiler.lower()
        if decompiler == "dex2jad":
            d.set_decompiler(DecompilerDex2Jad(
                d, androconf.CONF["PATH_DEX2JAR"], androconf.CONF["BIN_DEX2JAR"
                              ], androconf.CONF["PATH_JAD"],
                androconf.CONF["BIN_JAD"], androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler == "dex2fernflower":
            d.set_decompiler(DecompilerDex2Fernflower(
                d, androconf.CONF["PATH_DEX2JAR"], androconf.CONF[
                    "BIN_DEX2JAR"
                ], androconf.CONF["PATH_FERNFLOWER"], androconf.CONF[
                    "BIN_FERNFLOWER"
                ], androconf.CONF["OPTIONS_FERNFLOWER"
                                 ], androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler == "ded":
            d.set_decompiler(DecompilerDed(d, androconf.CONF["PATH_DED"],
                                           androconf.CONF["BIN_DED"],
                                           androconf.CONF["TMP_DIRECTORY"]))
        else:
            d.set_decompiler(DecompilerDAD(d, dx))