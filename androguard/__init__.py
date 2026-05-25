# The current version of Androguard
# Please use only this variable in any scripts,
# to keep the version number the same everywhere.
__version__ = "4.1.3"

# Main exports for better type hints and IDE support
from androguard.misc import AnalyzeAPK, AnalyzeDex, get_default_session
from androguard.core.apk import APK
from androguard.core.dex import DEX
from androguard.core.analysis.analysis import Analysis
from androguard.session import Session

__all__ = [
    "__version__",
    "AnalyzeAPK",
    "AnalyzeDex", 
    "get_default_session",
    "APK",
    "DEX",
    "Analysis",
    "Session",
]
