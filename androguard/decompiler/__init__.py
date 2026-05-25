import sys

from .decompile import DvClass, DvMachine, DvMethod
from .decompiler import DecompilerDAD

__all__ = ["DecompilerDAD", "DvClass", "DvMachine", "DvMethod"]

sys.setrecursionlimit(5000)
