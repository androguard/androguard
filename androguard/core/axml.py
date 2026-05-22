"""
Binary XML and ARSC via the Python [axml](https://github.com/androguard/axml) library.

The Rust [axml-parser](https://github.com/androguard/axml-parser) crate is a port of
the same format support; apk-parser and Androguard use the Python implementation.
"""

from axml.arsc import ARSCParser, ARSCResTableConfig
from axml.axml import AXMLPrinter, namespace

__all__ = [
    "ARSCParser",
    "ARSCResTableConfig",
    "AXMLPrinter",
    "namespace",
]
