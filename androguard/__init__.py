"""
Androguard v5 — reverse engineering for Android applications.

Built on the Androguard ecosystem:

- `apkparser-ag` — [apk-parser](https://github.com/androguard/apk-parser)
- `dexparser-ag` — [dex-parser](https://github.com/androguard/dex-parser)
- `axml` — binary XML / ARSC ([axml-parser](https://github.com/androguard/axml-parser) is the Rust port)
- `dex-bytecode-py` (optional) — [dex-bytecode](https://github.com/androguard/dex-bytecode)
"""

from androguard.application import Application, LazyProperty
from androguard.core.apk import APK, OPTION_AXML, OPTION_PERMISSION, OPTION_SIGNATURE
from androguard.core.dex import (
    DEX,
    DEX_from_source,
    DEXHelper,
    MethodHelper,
)
from androguard.misc import AnalyzeAPK, AnalyzeDex

__all__ = [
    "APK",
    "Application",
    "AnalyzeAPK",
    "AnalyzeDex",
    "DEX",
    "DEX_from_source",
    "DEXHelper",
    "LazyProperty",
    "MethodHelper",
    "OPTION_AXML",
    "OPTION_PERMISSION",
    "OPTION_SIGNATURE",
]

__version__ = "5.0.0"
