#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APK archive + DEX structure via apkparser / dexparser.

Run::

    python -m examples.apk_and_dex [path/to.apk]
"""

from __future__ import annotations

import io

from apkparser import APK, OPTION_AXML, OPTION_PERMISSION, OPTION_SIGNATURE
from dexparser import DEXHelper

from examples.common import resolve_apk


def main(argv: list[str] | None = None) -> int:
    apk_path = resolve_apk(argv)
    raw = apk_path.read_bytes()
    apk = APK(
        io.BytesIO(raw),
        {
            OPTION_AXML: True,
            OPTION_SIGNATURE: True,
            OPTION_PERMISSION: True,
        },
    )

    assert apk.get_app_name() == "TestsAndroguardApplication"
    assert apk.axml and apk.axml.package == "tests.androguard"
    dex_names = list(apk.get_dex_names())
    assert "classes.dex" in dex_names, dex_names

    print("app:", apk.get_app_name())
    print("package:", apk.axml.package)
    print("main:", apk.get_main_activity())
    print("dex:", dex_names)

    dex_raw = apk.get_file("classes.dex")
    dh = DEXHelper.from_string(dex_raw)
    classes = list(dh.get_classes())
    methods = list(dh.get_methods())
    strings = list(dh.get_strings())
    assert len(classes) > 100
    assert len(methods) > 1000
    assert any("this is a test" in s for s in strings)

    sample = next(c for c in classes if "TestActivity" in c.name)
    print("sample class:", sample.name, "extends", sample.sname)
    print(f"classes={len(classes)} methods={len(methods)} strings={len(strings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
