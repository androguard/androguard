"""
APK archive access via [apk-parser](https://github.com/androguard/apk-parser).
"""

from apkparser import (
    APK,
    FileNotPresent,
    OPTION_AXML,
    OPTION_PERMISSION,
    OPTION_SIGNATURE,
)

__all__ = [
    "APK",
    "FileNotPresent",
    "OPTION_AXML",
    "OPTION_PERMISSION",
    "OPTION_SIGNATURE",
]
