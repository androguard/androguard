"""
High-level Android application model built from ecosystem parsers.
"""

from __future__ import annotations

import io
import re
from functools import update_wrapper
from pathlib import Path
from typing import BinaryIO, Iterator, Pattern, Union

from apkparser import APK, OPTION_AXML, OPTION_PERMISSION, OPTION_SIGNATURE
from dexparser import DEXHelper, MethodHelper

from androguard.core.bytecode import (
    BytecodeNotAvailable,
    disassemble_method_code,
    format_instruction,
)
from androguard.core.decompiler import (
    decompile_method as decompile_method_bytes,
    decompile_dex_to_dir,
    java_class_from_method,
    parse_method_selector,
)

PathLike = Union[str, Path]


class LazyProperty(property):
    def __init__(self, method, fget=None, fset=None, fdel=None, doc=None):
        self.method = method
        self.cache_name = f"_{method.__name__}"
        doc = doc or method.__doc__
        super().__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)
        update_wrapper(self, method)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if hasattr(instance, self.cache_name):
            return getattr(instance, self.cache_name)
        if self.fget is not None:
            result = self.fget(instance)
        else:
            result = self.method(instance)
        setattr(instance, self.cache_name, result)
        return result


def _read_source(
    source: Union[PathLike, bytes, BinaryIO],
) -> io.BytesIO:
    if isinstance(source, (str, Path)):
        return io.BytesIO(Path(source).read_bytes())
    if isinstance(source, bytes):
        return io.BytesIO(source)
    if isinstance(source, io.BytesIO):
        source.seek(0)
        return source
    return io.BytesIO(source.read())


class Application:
    """
    Unified view of one APK: manifest metadata, DEX helpers, and optional disassembly.

    Uses ``apkparser-ag`` for the archive layer and ``dexparser-ag`` (Rust core) for each
    ``classes*.dex`` via :meth:`DEXHelper.from_string`.
    """

    def __init__(
        self,
        source: Union[PathLike, bytes, BinaryIO],
        *,
        axml: bool = True,
        signature: bool = True,
        permissions: bool = True,
    ):
        options = {}
        if axml:
            options[OPTION_AXML] = True
        if signature:
            options[OPTION_SIGNATURE] = True
        if permissions:
            options[OPTION_PERMISSION] = True
        self._apk = APK(_read_source(source), options)

    @property
    def apk(self) -> APK:
        return self._apk

    @LazyProperty
    def dex(self) -> list[DEXHelper]:
        return [
            DEXHelper.from_string(raw)
            for raw in self._apk.get_all_dex()
        ]

    @LazyProperty
    def class_names(self) -> list[str]:
        names: list[str] = []
        for dh in self.dex:
            for cls in dh.get_classes():
                names.append(cls.name)
        return names

    @LazyProperty
    def strings(self) -> list[str]:
        out: list[str] = []
        for dh in self.dex:
            out.extend(dh.get_strings())
        return out

    @LazyProperty
    def methods(self) -> list[MethodHelper]:
        out: list[MethodHelper] = []
        for dh in self.dex:
            out.extend(dh.get_methods())
        return out

    def iter_methods(
        self,
        *,
        class_pattern: str | Pattern[str] | None = None,
        method_pattern: str | Pattern[str] | None = None,
        with_code: bool = False,
    ) -> Iterator[MethodHelper]:
        """
        Yield methods optionally filtered by regex on class and/or method name.

        Patterns match against Dalvik descriptors (e.g. ``Lcom/foo/Bar;``) and
        short method names (e.g. ``onCreate``).
        """
        class_re = (
            class_pattern
            if isinstance(class_pattern, re.Pattern)
            else re.compile(class_pattern)
            if class_pattern
            else None
        )
        method_re = (
            method_pattern
            if isinstance(method_pattern, re.Pattern)
            else re.compile(method_pattern)
            if method_pattern
            else None
        )
        for method in self.methods:
            if class_re and not class_re.search(method.class_name):
                continue
            if method_re and not method_re.search(method.name):
                continue
            if with_code and not method.get_code():
                continue
            yield method

    def iter_disassembly(
        self,
        method: MethodHelper,
        *,
        labels: bool = False,
    ) -> Iterator[str]:
        """Disassemble one method if dex-bytecode bindings are installed."""
        del labels  # reserved for future label support in CLI
        try:
            for ins in disassemble_method_code(method.get_code()):
                yield format_instruction(ins)
        except BytecodeNotAvailable:
            raise

    def _dex_blobs(self) -> list[tuple[str, bytes]]:
        return [
            (name, self._apk.get_file(name))
            for name in self._apk.get_dex_names()
        ]

    def decompile_method(
        self,
        method: MethodHelper,
        *,
        dex_index: int = 0,
    ) -> str:
        """
        Decompile one method to Java-like source (requires ``androguard[decompile]``).

        Searches DEX files starting at ``dex_index`` until the method is found.
        """
        blobs = self._dex_blobs()
        java_class = java_class_from_method(method.class_name)
        last_error: Exception | None = None
        for _name, raw in blobs[dex_index:]:
            try:
                return decompile_method_bytes(
                    raw, java_class, method.name
                )
            except ValueError as exc:
                last_error = exc
                continue
        if last_error:
            raise last_error
        raise ValueError(
            f"method not found: {java_class}#{method.name}"
        )

    def decompile_method_selector(self, selector: str) -> str:
        """Decompile using ``CLASS#METHOD`` (Java names, dex-decompiler style)."""
        java_class, method_name = parse_method_selector(selector)
        for _name, raw in self._dex_blobs():
            try:
                return decompile_method_bytes(
                    raw, java_class, method_name
                )
            except ValueError:
                continue
        raise ValueError(f"method not found: {selector}")

    def iter_decompiled_methods(
        self,
        *,
        class_pattern: str | None = None,
        method_pattern: str | None = None,
    ) -> Iterator[tuple[MethodHelper, str]]:
        """Yield ``(method, java_source)`` for each matching method with code."""
        for method in self.iter_methods(
            class_pattern=class_pattern,
            method_pattern=method_pattern,
            with_code=True,
        ):
            yield method, self.decompile_method(method)

    def decompile_apk_to_dir(
        self,
        base_path: str | Path,
        *,
        only_package: str | None = None,
        exclude: list[str] | None = None,
    ) -> None:
        """Decompile every ``classes*.dex`` in the APK under ``base_path``."""
        root = Path(base_path)
        root.mkdir(parents=True, exist_ok=True)
        for dex_name, raw in self._dex_blobs():
            sub = root / Path(dex_name).stem
            decompile_dex_to_dir(
                raw,
                str(sub),
                only_package=only_package,
                exclude=exclude,
            )

    def summary(self) -> dict[str, object]:
        """Short metadata dict suitable for logging or CLI output."""
        return {
            "app_name": self._apk.get_app_name(),
            "main_activity": self._apk.get_main_activity(),
            "package": self._apk.axml.package if self._apk.axml else "",
            "dex_files": list(self._apk.get_dex_names()),
            "classes": len(self.class_names),
            "strings": len(self.strings),
            "methods": len(self.methods),
            "signed": bool(
                self._apk.signature and self._apk.signature.is_signed()
            ),
        }
