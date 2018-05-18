# The current version of Androguard
# Please use only this variable in any scripts,
# to keep the version number the same everywhere.
__version__ = "3.2.0"

# Aliases for commonly used stuff
from androguard.core.bytecodes.apk import APK
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.bytecodes.axml import AXMLPrinter, ARSCParser
from androguard.core.analysis.analysis import Analysis
