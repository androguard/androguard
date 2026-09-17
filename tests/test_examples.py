# -*- coding: utf-8 -*-
"""Execute ``examples/`` scripts as regression tests."""

from __future__ import annotations

import importlib
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable

from tests.helpers import (
    HAS_ARM,
    HAS_BYTECODE,
    HAS_DECOMPILER,
    HAS_PATCH,
    TEST_APK,
    file_exists,
)

# (module name, optional skip predicate returning reason or None)
_EXAMPLES: list[tuple[str, Callable[[], str | None]]] = [
    ("examples.application_summary", lambda: None),
    ("examples.apk_and_dex", lambda: None),
    (
        "examples.disassemble",
        lambda: None if HAS_BYTECODE else "dex-bytecode not installed",
    ),
    (
        "examples.decompile",
        lambda: None if HAS_DECOMPILER else "dex-decompiler not installed",
    ),
    (
        "examples.arm",
        lambda: None if HAS_ARM else "arm bindings not installed",
    ),
    (
        "examples.patch_decode",
        lambda: None if HAS_PATCH else "apk-patch not installed",
    ),
]


def _run_example(module_name: str) -> int:
    mod = importlib.import_module(module_name)
    buf = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(err):
        try:
            return int(mod.main([]))
        except SystemExit as exc:
            if exc.code in (0, None):
                return 0
            if isinstance(exc.code, int):
                return exc.code
            return 1


@unittest.skipUnless(file_exists(TEST_APK), "TestActivity.apk not present")
class ExamplesAsTests(unittest.TestCase):
    def test_run_all_modules_listed(self):
        from examples.run_all import EXAMPLES

        self.assertEqual(
            [name for name, _ in _EXAMPLES],
            list(EXAMPLES),
        )


def _make_test(module_name: str, skip_reason: Callable[[], str | None]):
    def test(self):
        reason = skip_reason()
        if reason:
            self.skipTest(reason)
        code = _run_example(module_name)
        self.assertEqual(
            code,
            0,
            f"{module_name} exited with {code}",
        )

    test.__name__ = f"test_{module_name.rsplit('.', 1)[-1]}"
    test.__doc__ = f"Run {module_name}"
    return test


for _mod, _skip in _EXAMPLES:
    _fn = _make_test(_mod, _skip)
    setattr(ExamplesAsTests, _fn.__name__, _fn)


if __name__ == "__main__":
    unittest.main()
