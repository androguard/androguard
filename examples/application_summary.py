#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-level Application summary and method filters.

Run::

    python -m examples.application_summary [path/to.apk]
"""

from __future__ import annotations

from androguard import Application

from examples.common import resolve_apk


def main(argv: list[str] | None = None) -> int:
    apk_path = resolve_apk(argv)
    app = Application(apk_path)

    summary = app.summary()
    assert summary["package"] == "tests.androguard", summary
    assert summary["classes"] > 100, summary
    assert summary["methods"] > 1000, summary
    assert "TestActivity" in (summary["main_activity"] or "")

    print("summary:", summary)
    print("first classes:")
    for name in app.class_names[:5]:
        print(" ", name)

    matches = list(
        app.iter_methods(
            class_pattern=r"TestActivity",
            method_pattern=r"^onCreate$",
            with_code=True,
        )
    )
    assert len(matches) == 1, matches
    method = matches[0]
    print(f"method: {method.class_name}.{method.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
