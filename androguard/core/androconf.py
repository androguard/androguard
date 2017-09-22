import sys
import os
import logging
import types
import random
import string

from androguard import __version__
ANDROGUARD_VERSION = __version__


def is_ascii_problem(s):
    try:
        s.decode("ascii")
        return False
    except UnicodeDecodeError:
        return True


class Color(object):
    Normal = "\033[0m"
    Black = "\033[30m"
    Red = "\033[31m"
    Green = "\033[32m"
    Yellow = "\033[33m"
    Blue = "\033[34m"
    Purple = "\033[35m"
    Cyan = "\033[36m"
    Grey = "\033[37m"
    Bold = "\033[1m"


CONF = {
    "BIN_DED": "ded.sh",
    "PATH_DED": "./decompiler/ded/",
    "PATH_DEX2JAR": "./decompiler/dex2jar/",
    "BIN_DEX2JAR": "dex2jar.sh",
    "PATH_JAD": "./decompiler/jad/",
    "BIN_JAD": "jad",
    "BIN_WINEJAD": "jad.exe",
    "PATH_FERNFLOWER": "./decompiler/fernflower/",
    "BIN_FERNFLOWER": "fernflower.jar",
    "OPTIONS_FERNFLOWER": {"dgs": '1',
                           "asc": '1'},
    "PRETTY_SHOW": 1,
    "TMP_DIRECTORY": "/tmp/",
    # Full python or mix python/c++ (native)
    #"ENGINE" : "automatic",
    "ENGINE": "python",
    "RECODE_ASCII_STRING": False,
    "RECODE_ASCII_STRING_METH": None,
    "DEOBFUSCATED_STRING": True,
    #    "DEOBFUSCATED_STRING_METH" : get_deobfuscated_string,
    "PATH_JARSIGNER": "jarsigner",
    "COLORS": {
        "OFFSET": Color.Yellow,
        "OFFSET_ADDR": Color.Green,
        "INSTRUCTION_NAME": Color.Yellow,
        "BRANCH_FALSE": Color.Red,
        "BRANCH_TRUE": Color.Green,
        "BRANCH": Color.Blue,
        "EXCEPTION": Color.Cyan,
        "BB": Color.Purple,
        "NOTE": Color.Red,
        "NORMAL": Color.Normal,
        "OUTPUT": {
            "normal": Color.Normal,
            "registers": Color.Normal,
            "literal": Color.Green,
            "offset": Color.Purple,
            "raw": Color.Red,
            "string": Color.Red,
            "meth": Color.Cyan,
            "type": Color.Blue,
            "field": Color.Green,
        }
    },
    "PRINT_FCT": sys.stdout.write,
    "LAZY_ANALYSIS": False,
    "MAGIC_PATH_FILE": None,
    "DEFAULT_API": 19,
    "SESSION": None,
}

if os.path.exists(os.path.join(os.path.dirname(__file__), '..', '..', 'androgui.py')):
    CONF['data_prefix'] = os.path.join(os.path.dirname(__file__), '..', 'gui')
# workaround issue on OSX, where sys.prefix is not an installable location
elif sys.platform == 'darwin' and sys.prefix.startswith('/System'):
    CONF['data_prefix'] = os.path.join('.', 'share', 'androguard')
elif sys.platform == 'win32':
    CONF['data_prefix'] = os.path.join(sys.prefix, 'Scripts', 'androguard')
else:
    CONF['data_prefix'] = os.path.join(sys.prefix, 'share', 'androguard')

def default_colors(obj):
    CONF["COLORS"]["OFFSET"] = obj.Yellow
    CONF["COLORS"]["OFFSET_ADDR"] = obj.Green
    CONF["COLORS"]["INSTRUCTION_NAME"] = obj.Yellow
    CONF["COLORS"]["BRANCH_FALSE"] = obj.Red
    CONF["COLORS"]["BRANCH_TRUE"] = obj.Green
    CONF["COLORS"]["BRANCH"] = obj.Blue
    CONF["COLORS"]["EXCEPTION"] = obj.Cyan
    CONF["COLORS"]["BB"] = obj.Purple
    CONF["COLORS"]["NOTE"] = obj.Red
    CONF["COLORS"]["NORMAL"] = obj.Normal

    CONF["COLORS"]["OUTPUT"]["normal"] = obj.Normal
    CONF["COLORS"]["OUTPUT"]["registers"] = obj.Normal
    CONF["COLORS"]["OUTPUT"]["literal"] = obj.Green
    CONF["COLORS"]["OUTPUT"]["offset"] = obj.Purple
    CONF["COLORS"]["OUTPUT"]["raw"] = obj.Red
    CONF["COLORS"]["OUTPUT"]["string"] = obj.Red
    CONF["COLORS"]["OUTPUT"]["meth"] = obj.Cyan
    CONF["COLORS"]["OUTPUT"]["type"] = obj.Blue
    CONF["COLORS"]["OUTPUT"]["field"] = obj.Green


def disable_colors():
    """ Disable colors from the output (color = normal)"""
    for i in CONF["COLORS"]:
        if isinstance(CONF["COLORS"][i], dict):
            for j in CONF["COLORS"][i]:
                CONF["COLORS"][i][j] = Color.normal
        else:
            CONF["COLORS"][i] = Color.normal


def remove_colors():
    """ Remove colors from the output (no escape sequences)"""
    for i in CONF["COLORS"]:
        if isinstance(CONF["COLORS"][i], dict):
            for j in CONF["COLORS"][i]:
                CONF["COLORS"][i][j] = ""
        else:
            CONF["COLORS"][i] = ""


def enable_colors(colors):
    for i in colors:
        CONF["COLORS"][i] = colors[i]


def save_colors():
    c = {}
    for i in CONF["COLORS"]:
        if isinstance(CONF["COLORS"][i], dict):
            c[i] = {}
            for j in CONF["COLORS"][i]:
                c[i][j] = CONF["COLORS"][i][j]
        else:
            c[i] = CONF["COLORS"][i]
    return c


def long2int(l):
    if l > 0x7fffffff:
        l = (0x7fffffff & l) - 0x80000000
    return l


def long2str(l):
    """Convert an integer to a string."""
    if type(l) not in (types.IntType, types.LongType):
        raise ValueError('the input must be an integer')

    if l < 0:
        raise ValueError('the input must be greater than 0')
    s = ''
    while l:
        s = s + chr(l & 255)
        l >>= 8

    return s


def str2long(s):
    """Convert a string to a long integer."""
    if type(s) not in (types.StringType, types.UnicodeType):
        raise ValueError('the input must be a string')

    l = 0
    for i in s:
        l <<= 8
        l |= ord(i)

    return l


def random_string():
    return random.choice(string.letters) + ''.join([random.choice(
        string.letters + string.digits) for i in range(10 - 1)])


def is_android(filename):
    """Return the type of the file

        @param filename : the filename
        @rtype : "APK", "DEX", None
    """
    if not filename:
        return None

    with open(filename, "rb") as fd:
        f_bytes = fd.read()
        return is_android_raw(f_bytes)


def is_android_raw(raw):
    """
        Returns a string that describes the type of file, for common Android
        specific formats
    """
    val = None

    # We do not check for META-INF/MANIFEST.MF,
    # as you also want to analyze unsigned APKs...
    # AndroidManifest.xml should be in every APK.
    # classes.dex and resources.arsc are not required!
    # if raw[0:2] == b"PK" and b'META-INF/MANIFEST.MF' in raw:
    # TODO this check might be still invalid. A ZIP file with stored APK inside would match as well.
    # probably it would be better to rewrite this and add more sanity checks.
    if raw[0:2] == b"PK" and b'AndroidManifest.xml' in raw:
        val = "APK"
    elif raw[0:3] == b"dex":
        val = "DEX"
    elif raw[0:3] == b"dey":
        val = "DEY"
    elif raw[0:4] == b"\x03\x00\x08\x00":
        val = "AXML"
    elif raw[0:4] == b"\x02\x00\x0C\x00":
        val = b"ARSC"

    return val


# Init Logger
log_andro = logging.getLogger("androguard")

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
log_andro.addHandler(console_handler)
log_runtime = logging.getLogger("androguard.runtime")  # logs at runtime
log_interactive = logging.getLogger("androguard.interactive")  # logs in interactive functions
log_loading = logging.getLogger("androguard.loading")  # logs when loading andro


def set_lazy():
    CONF["LAZY_ANALYSIS"] = True


def set_debug():
    log_andro.setLevel(logging.DEBUG)


def set_info():
    log_andro.setLevel(logging.INFO)


def get_debug():
    return log_andro.getEffectiveLevel() == logging.DEBUG


def warning(x):
    """
    Print out message x and the current traceback (if any)

    :param x: String to be printed on stderr
    """
    log_runtime.warning(x)
    if sys.exc_info()[0] is not None:
        import traceback
        traceback.print_exc()


def error(x):
    """
    Print out a message and raise an exception
    TODO should this really raise an exception?

    :param x: String to be printed on stderr
    """
    log_runtime.error(x)
    raise ()


def debug(x):
    log_runtime.debug(x)


def info(x):
    log_runtime.info(x)


def set_options(key, value):
    CONF[key] = value


def save_to_disk(buff, output):
    with open(output, "w") as fd:
        fd.write(buff)


def rrmdir(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(directory)


def make_color_tuple(color):
    """
    turn something like "#000000" into 0,0,0
    or "#FFFFFF into "255,255,255"
    """
    R = color[1:3]
    G = color[3:5]
    B = color[5:7]

    R = int(R, 16)
    G = int(G, 16)
    B = int(B, 16)

    return R, G, B


def interpolate_tuple(startcolor, goalcolor, steps):
    """
    Take two RGB color sets and mix them over a specified number of steps.  Return the list
    """
    # white

    R = startcolor[0]
    G = startcolor[1]
    B = startcolor[2]

    targetR = goalcolor[0]
    targetG = goalcolor[1]
    targetB = goalcolor[2]

    DiffR = targetR - R
    DiffG = targetG - G
    DiffB = targetB - B

    buffer = []

    for i in range(0, steps + 1):
        iR = R + (DiffR * i // steps)
        iG = G + (DiffG * i // steps)
        iB = B + (DiffB * i // steps)

        hR = str.replace(hex(iR), "0x", "")
        hG = str.replace(hex(iG), "0x", "")
        hB = str.replace(hex(iB), "0x", "")

        if len(hR) == 1:
            hR = "0" + hR
        if len(hB) == 1:
            hB = "0" + hB

        if len(hG) == 1:
            hG = "0" + hG

        color = str.upper("#" + hR + hG + hB)
        buffer.append(color)

    return buffer


def color_range(startcolor, goalcolor, steps):
    """
    wrapper for interpolate_tuple that accepts colors as html ("#CCCCC" and such)
    """
    start_tuple = make_color_tuple(startcolor)
    goal_tuple = make_color_tuple(goalcolor)

    return interpolate_tuple(start_tuple, goal_tuple, steps)


def load_api_specific_resource_module(resource_name, api):
    # Those two imports are quite slow.
    from androguard.core.api_specific_resources.aosp_permissions.aosp_permissions import AOSP_PERMISSIONS
    from androguard.core.api_specific_resources.api_permission_mappings.api_permission_mappings import AOSP_PERMISSIONS_MAPPINGS

    if resource_name == "aosp_permissions":
        mod = AOSP_PERMISSIONS
    elif resource_name == "api_permission_mappings":
        mod = AOSP_PERMISSIONS_MAPPINGS
    else:
        error("Invalid resource: %s" % resource_name)

    if not api:
        api = CONF["DEFAULT_API"]
    value = mod.get(api)
    if value:
        return value
    return mod.get('9')
