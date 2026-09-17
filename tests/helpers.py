# -*- coding: utf-8 -*-
"""Shared paths and helpers for Androguard tests."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
DATA_DIR = TEST_DIR / "data"
APK_DIR = DATA_DIR / "APK"

TEST_APK = APK_DIR / "TestActivity.apk"
MULTIDEX_APK = APK_DIR / "app-prod-debug.apk"
UNSIGNED_APK = APK_DIR / "TestActivity_unsigned.apk"
TEST_DEX = APK_DIR / "Test.dex"
FILL_ARRAYS_DEX = APK_DIR / "FillArrays.dex"
EXCEPTION_DEX = APK_DIR / "ExceptionHandling.dex"


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


HAS_DECOMPILER = has_module("dex_decompiler")
HAS_BYTECODE = has_module("dex_bytecode_py")
HAS_ARM_DISASM = has_module("arm_disassembler")
HAS_ARM_DECOMP = has_module("arm_decompiler")
HAS_PATCH = has_module("apk_patch")
HAS_ARM = HAS_ARM_DISASM and HAS_ARM_DECOMP


def file_exists(path: Path | str) -> bool:
    return Path(path).is_file()


def read_apk_bytes(path: Path | str) -> bytes:
    return Path(path).read_bytes()


def open_apk_stream(path: Path | str) -> io.BytesIO:
    return io.BytesIO(read_apk_bytes(path))


def oncreate_method(app):
    """Return the TestActivity.onCreate MethodHelper (raises StopIteration if missing)."""
    return next(
        app.iter_methods(
            class_pattern=r"TestActivity",
            method_pattern=r"^onCreate$",
            with_code=True,
        )
    )
