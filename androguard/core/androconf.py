# Allows type hinting of types not-yet-declared
# in Python >= 3.7
# see https://peps.python.org/pep-0563/
from __future__ import annotations


import os
import sys
import tempfile
from typing import Union

from androguard import __version__
from androguard.core.api_specific_resources import load_permission_mappings, load_permissions
ANDROGUARD_VERSION = __version__

from colorama import init, Fore
from loguru import logger

# initialize colorama, only has an effect on windows
init()


class InvalidResourceError(Exception):
    """
    Invalid Resource Erorr is thrown by load_api_specific_resource_module
    """
    pass


def is_ascii_problem(s: str) -> bool:
    """
    Test if a string contains other chars than ASCII

    :param androguard.core.mutf8.MUTF8String s: a string to test
    :return: True if string contains other chars than ASCII, False otherwise
    :rtype: bool
    """
    try:
        # As MUTF8Strings are actually bytes, we can simply check if they are ASCII or not
        s.decode("ascii")
        return False
    except (UnicodeEncodeError, UnicodeDecodeError):
        return True


default_conf = {
    ## Configuration for executables used by androguard
    # Assume the binary is in $PATH, otherwise give full path

    # Runtime variables
    #
    # A path to the temporary directory
    "TMP_DIRECTORY": tempfile.gettempdir(),

    # Function to print stuff
    "PRINT_FCT": sys.stdout.write,

    # Default API level, if requested API is not available
    "DEFAULT_API": 16,  # this is the minimal API version we have

    # Session, for persistence
    "SESSION": None,

    # Color output configuration
    "COLORS": {
        "OFFSET": Fore.YELLOW,
        "OFFSET_ADDR": Fore.GREEN,
        "INSTRUCTION_NAME": Fore.YELLOW,
        "BRANCH_FALSE": Fore.RED,
        "BRANCH_TRUE": Fore.GREEN,
        "BRANCH": Fore.BLUE,
        "EXCEPTION": Fore.CYAN,
        "BB": Fore.MAGENTA,
        "NOTE": Fore.RED,
        "NORMAL": Fore.RESET,
        "OUTPUT": {
            "normal": Fore.RESET,
            "registers": Fore.YELLOW,
            "literal": Fore.GREEN,
            "offset": Fore.MAGENTA,
            "raw": Fore.RED,
            "string": Fore.RED,
            "meth": Fore.CYAN,
            "type": Fore.BLUE,
            "field": Fore.GREEN,
        },
    },
}


class Configuration:
    instance = None

    def __init__(self) -> None:
        """
        A Wrapper for the CONF object
        This creates a singleton, which has the same attributes everywhere.
        """
        if not Configuration.instance:
            Configuration.instance = default_conf

    def __getattr__(self, item):
        return getattr(self.instance, item)

    def __getitem__(self, item):
        return self.instance[item]

    def __setitem__(self, key, value):
        self.instance[key] = value

    def __str__(self):
        return str(self.instance)

    def __repr__(self):
        return repr(self.instance)


CONF = Configuration()


def is_android(filename: str) -> str:
    """
    Return the type of the file

    :param filename : the filename
    :returns: "APK", "DEX", None
    """
    if not filename:
        return None

    with open(filename, "rb") as fd:
        f_bytes = fd.read()
        return is_android_raw(f_bytes)


def is_android_raw(raw: bytes) -> str:
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
        # check out 
    elif raw[0:3] == b"dex":
        val = "DEX"
    elif raw[0:3] == b"dey":
        val = "DEY"
    elif raw[0:4] == b"\x03\x00\x08\x00" or raw[0:4] == b"\x00\x00\x08\x00":
        val = "AXML"
    elif raw[0:4] == b"\x02\x00\x0C\x00":
        val = "ARSC"

    return val

def rrmdir(directory: str) -> None:
    """
    Recursivly delete a directory

    :param directory: directory to remove
    """
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(directory)


def make_color_tuple(color: str) -> tuple[int,int,int]:
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


def interpolate_tuple(startcolor: tuple[int,int,int], goalcolor: tuple[int,int,int], steps: int) -> list[str]:
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


def color_range(startcolor: tuple[int,int,int], goalcolor: tuple[int,int,int], steps: int) -> list[str]:
    """
    wrapper for interpolate_tuple that accepts colors as html ("#CCCCC" and such)
    """
    start_tuple = make_color_tuple(startcolor)
    goal_tuple = make_color_tuple(goalcolor)

    return interpolate_tuple(start_tuple, goal_tuple, steps)


def load_api_specific_resource_module(resource_name: str, api:Union[str,int,None]=None) -> dict:
    """
    Load the module from the JSON files and return a dict, which might be empty
    if the resource could not be loaded.

    If no api version is given, the default one from the CONF dict is used.

    :param resource_name: Name of the resource to load
    :param api: API version
    :return: dict
    """
    loader = dict(aosp_permissions=load_permissions,
                  api_permission_mappings=load_permission_mappings)

    if resource_name not in loader:
        raise InvalidResourceError("Invalid Resource '{}', not in [{}]".format(resource_name, ", ".join(loader.keys())))

    if not api:
        api = CONF["DEFAULT_API"]

    ret = loader[resource_name](api)

    if ret == {}:
        # No API mapping found, return default
        logger.warning("API mapping for API level {} was not found! "
                       "Returning default, which is API level {}".format(api, CONF['DEFAULT_API']))
        ret = loader[resource_name](CONF['DEFAULT_API'])

    return ret

