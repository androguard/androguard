#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""In-memory APK decode / rebuild (requires androguard[patch]).

Run::

    python -m examples.patch_decode [path/to.apk]
"""

from __future__ import annotations

from androguard import Application
from androguard.core import patch

from examples.common import require_modules, resolve_apk


def main(argv: list[str] | None = None) -> int:
    require_modules("apk_patch")
    apk_path = resolve_apk(argv)
    app = Application(apk_path)

    project = app.decode_project(only_manifest=True, no_res=True)
    assert project["entry_count"] > 0
    files = project["files"]
    assert any("AndroidManifest" in p for p in files), list(files)[:10]

    print(
        f"project_root={project['project_root']} "
        f"entries={project['entry_count']} "
        f"dex_classes={project['dex_class_count']}"
    )
    for path in sorted(files)[:15]:
        print(" ", path)

    rebuilt = patch.build(
        files,
        project_root=project["project_root"],
        sign=False,
    )
    assert rebuilt[:2] == b"PK"
    assert len(rebuilt) > 100
    print(f"rebuilt unsigned APK: {len(rebuilt)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
