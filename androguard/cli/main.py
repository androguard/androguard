"""Androguard command-line interface.

Supports ASC-style subcommands::

    androguard findrefs [--thread N] app.apk string token -o refs.txt
    androguard getclass [--thread N] app.apk com.example.Main -o Main.java
    androguard listclass app.apk --prefix com.example
    androguard listmethod app.apk --class com.example.Main -f onCreate
    androguard liststring app.apk -f https
    androguard getmanifest app.apk -o AndroidManifest.xml
    androguard export app.apk -d out/

and the legacy flag form (``-i`` / ``--input``)::

    androguard -i app.apk --findrefs string --findrefs-value token
"""

from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from pathlib import Path

from androguard import __version__ as ANDROGUARD_VERSION
from androguard.application import Application
from androguard.cli.display import (
    print_class_names,
    print_components,
    print_cfg_edges,
    print_decode_project,
    print_disasm_header,
    print_disasm_line,
    print_emulate,
    print_error,
    print_findrefs,
    print_info,
    print_java,
    print_manifest,
    print_methods,
    print_scan_vulns,
    print_summary,
    print_version,
    print_warning,
)
from androguard.core.bytecode import BytecodeNotAvailable
from androguard.core.decompiler import (
    DecompilerNotAvailable,
    parse_method_selector,
)
from androguard.helper.logging import LOGGER

_ASC_COMMANDS = frozenset(
    {
        "getclass",
        "listclass",
        "listmethod",
        "liststring",
        "getmanifest",
        "listcomponents",
        "findrefs",
        "export",
        "version",
    }
)

_FINDREFS_KINDS = (
    "string",
    "type",
    "method",
    "field",
    "extends",
    "impl",
)


@contextmanager
def _rayon_threads(n: int | None):
    """Pin Rayon parallelism for native Rust extras; no-op when unset."""
    if n is None or n <= 0:
        yield
        return
    key = "RAYON_NUM_THREADS"
    prev = os.environ.get(key)
    os.environ[key] = str(n)
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = prev


def _write_text(path: str | None, text: str, *, also_stdout: bool = True) -> None:
    if path:
        Path(path).write_text(
            text if text.endswith("\n") else text + "\n",
            encoding="utf-8",
            errors="replace",
        )
    if also_stdout or not path:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _write_lines(path: str | None, lines: list[str], *, also_stdout: bool = True) -> None:
    text = "\n".join(lines)
    if lines:
        text += "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8", errors="replace")
        if not also_stdout:
            return
    if also_stdout or not path:
        sys.stdout.write(text)


def _add_thread_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--thread",
        "--threads",
        dest="threads",
        type=int,
        default=None,
        metavar="N",
        help="Rayon worker count for native Rust extras (omitted = default)",
    )


def _add_output_arg(p: argparse.ArgumentParser, *, help_text: str) -> None:
    p.add_argument("-o", "--output", metavar="FILE", help=help_text)


def _build_asc_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="androguard",
        description="Analyze Android APK files (ASC-style subcommands).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  androguard getclass app.apk com.example.Main -o Main.java
  androguard findrefs --thread 8 app.apk string token -o refs.txt
  androguard findrefs app.apk extends android.app.Activity
  androguard findrefs app.apk method notify --class Main --fuzzy-class
  androguard listclass app.apk --prefix com.example
  androguard listmethod app.apk --class com.example.Main -f onCreate
  androguard liststring app.apk -f https
  androguard getmanifest app.apk -o AndroidManifest.xml
  androguard export app.apk -d workspace/output/pkg/
""",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"androguard {ANDROGUARD_VERSION}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    getclass_p = sub.add_parser("getclass", help="Decompile one class (ASC getclass)")
    _add_thread_arg(getclass_p)
    _add_output_arg(getclass_p, help_text="Also write Java to this file")
    getclass_p.add_argument("apk_path", help="Path to the input APK")
    getclass_p.add_argument("dalvik_class", help="Java or Dalvik class name")

    listclass_p = sub.add_parser("listclass", help="List class names")
    _add_thread_arg(listclass_p)
    _add_output_arg(listclass_p, help_text="Write class names to this file")
    listclass_p.add_argument("--prefix", help="Filter by package/class prefix")
    listclass_p.add_argument("apk_path", help="Path to the input APK")

    listmethod_p = sub.add_parser("listmethod", help="List Dalvik method descriptors")
    _add_thread_arg(listmethod_p)
    _add_output_arg(listmethod_p, help_text="Write method list to this file")
    listmethod_p.add_argument(
        "--class",
        dest="class_name",
        help="Exact class (Java or Dalvik)",
    )
    listmethod_p.add_argument(
        "-f",
        "--filter",
        dest="name_filter",
        help="Case-insensitive method-name substring",
    )
    listmethod_p.add_argument("apk_path", help="Path to the input APK")

    liststring_p = sub.add_parser("liststring", help="List DEX string-pool values")
    _add_thread_arg(liststring_p)
    _add_output_arg(liststring_p, help_text="Write strings to this file")
    liststring_p.add_argument(
        "-f",
        "--filter",
        dest="str_filter",
        help="Case-insensitive substring filter",
    )
    liststring_p.add_argument("apk_path", help="Path to the input APK")

    manifest_p = sub.add_parser("getmanifest", help="Decode AndroidManifest.xml")
    _add_output_arg(manifest_p, help_text="Also write XML to this file")
    manifest_p.add_argument("apk_path", help="Path to the input APK")

    components_p = sub.add_parser(
        "listcomponents",
        help="List Android components (activities, services, receivers, providers)",
    )
    _add_thread_arg(components_p)
    components_p.add_argument(
        "--type",
        dest="component_type",
        choices=["all", "activity", "service", "receiver", "provider"],
        default="all",
        help="Filter by component type (default: all)",
    )
    components_p.add_argument(
        "--exported-only",
        action="store_true",
        help="Only display exported components",
    )
    components_p.add_argument("apk_path", help="Path to the input APK")

    findrefs_p = sub.add_parser(
        "findrefs",
        help="Find code refs (string|type|method|field|extends|impl)",
    )
    _add_thread_arg(findrefs_p)
    findrefs_p.add_argument("apk_path", help="Path to the input APK")
    find_sub = findrefs_p.add_subparsers(dest="find_type", required=True)

    for kind, value_help in (
        ("string", "Fuzzy string pattern"),
        ("type", "Fuzzy type / class name"),
        ("extends", "Superclass (Java or Dalvik)"),
        ("impl", "Interface (Java or Dalvik)"),
    ):
        kp = find_sub.add_parser(kind, help=f"findrefs {kind}")
        _add_output_arg(kp, help_text="Also write hits to this file")
        kp.add_argument("value", help=value_help)

    for kind in ("method", "field"):
        kp = find_sub.add_parser(kind, help=f"findrefs {kind}")
        _add_output_arg(kp, help_text="Also write hits to this file")
        kp.add_argument("name", nargs="?", default=None, help=f"{kind} name")
        kp.add_argument(
            "--class",
            dest="class_name",
            default=None,
            help="Owning class (exact unless --fuzzy-class)",
        )
        kp.add_argument(
            "--fuzzy-class",
            action="store_true",
            help="Treat --class as a substring",
        )

    export_p = sub.add_parser("export", help="Decompile all classes to a directory")
    _add_thread_arg(export_p)
    export_p.add_argument(
        "-d",
        "--output-dir",
        required=True,
        metavar="DIR",
        help="Output directory for decompiled Java",
    )
    export_p.add_argument("--only-package", metavar="PKG", help="Package filter")
    export_p.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PKG",
        help="Exclude package prefix (repeatable)",
    )
    export_p.add_argument("apk_path", help="Path to the input APK")

    ver = sub.add_parser("version", help="Print version")
    ver.add_argument("apk_path", nargs="?", help=argparse.SUPPRESS)

    return parser


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="androguard",
        description="Analyze Android APK files using the Androguard ecosystem parsers.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"androguard {ANDROGUARD_VERSION}",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["version"],
        help="Print the Androguard version and exit (no APK required)",
    )
    parser.add_argument(
        "-i",
        "--input",
        metavar="APK",
        help="Path to an APK file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--thread",
        "--threads",
        dest="threads",
        type=int,
        default=None,
        metavar="N",
        help="Rayon worker count for native Rust extras",
    )
    disasm = parser.add_argument_group(
        "disassembly",
        "Dalvik disassembly (requires androguard[disasm])",
    )
    disasm.add_argument(
        "--disasm",
        action="store_true",
        help="Disassemble methods that match the filters below",
    )
    disasm.add_argument(
        "--class",
        dest="class_pattern",
        metavar="REGEXP",
        help="Regex on class (Dalvik descriptor or Java name)",
    )
    disasm.add_argument(
        "--method",
        dest="method_pattern",
        metavar="REGEXP",
        help="Regex on method name (e.g. 'onCreate' or '<init>')",
    )
    disasm.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N matching methods (0 = no limit)",
    )
    disasm.add_argument(
        "--cfg",
        action="store_true",
        help="Print Dalvik CFG edges for matching methods (with --disasm)",
    )
    decompile = parser.add_argument_group(
        "decompilation",
        "Java decompilation (requires androguard[decompile])",
    )
    decompile.add_argument(
        "--decompile",
        action="store_true",
        help="Decompile methods or the whole APK (see filters and output options)",
    )
    decompile.add_argument(
        "--decompile-method",
        dest="decompile_selector",
        metavar="CLASS#METHOD",
        help="Decompile one method: Java CLASS#METHOD (e.g. tests.androguard.TestActivity#onCreate)",
    )
    decompile.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write decompiled Java / findrefs / lists to a file",
    )
    decompile.add_argument(
        "-d",
        "--output-dir",
        metavar="DIR",
        help="Write decompiled sources to a directory (per classes*.dex subfolder)",
    )
    decompile.add_argument(
        "--only-package",
        metavar="PKG",
        help="Only decompile classes in this package (e.g. tests.androguard)",
    )
    decompile.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PKG",
        help="Exclude package prefix (repeatable, e.g. android.)",
    )
    decompile.add_argument(
        "--getclass",
        metavar="CLASS",
        help="Decompile a single class (ASC getclass; Java or Dalvik name)",
    )
    decompile.add_argument(
        "--findrefs",
        metavar="KIND",
        choices=list(_FINDREFS_KINDS),
        help="ASC findrefs kind (use with --findrefs-value)",
    )
    decompile.add_argument(
        "--findrefs-value",
        metavar="VALUE",
        help="Needle for --findrefs",
    )
    decompile.add_argument(
        "--findrefs-class",
        metavar="CLASS",
        help="Restrict method/field findrefs to this class",
    )
    decompile.add_argument(
        "--findrefs-fuzzy-class",
        action="store_true",
        help="Treat --findrefs-class as a substring",
    )
    decompile.add_argument(
        "--scan-vulns",
        action="store_true",
        help="Run vulnerability detectors on all DEX files",
    )
    decompile.add_argument(
        "--emulate",
        metavar="CLASS#METHOD",
        help="Emulate one method (Java CLASS#METHOD)",
    )
    patch = parser.add_argument_group(
        "apk-patch",
        "Decode/rebuild via apk-patch (requires androguard[patch])",
    )
    patch.add_argument(
        "--decode-project",
        action="store_true",
        help="Decode APK to in-memory project and list entry paths",
    )
    parser.add_argument(
        "--list-classes",
        action="store_true",
        help="Print all class names from DEX",
    )
    parser.add_argument(
        "--list-methods",
        action="store_true",
        help="Print all method signatures",
    )
    parser.add_argument(
        "--list-strings",
        action="store_true",
        help="Print DEX string-pool values",
    )
    parser.add_argument(
        "--getmanifest",
        action="store_true",
        help="Print decoded AndroidManifest.xml",
    )
    parser.add_argument(
        "--manifest",
        "--show-manifest",
        dest="show_manifest",
        action="store_true",
        help="Print decoded AndroidManifest.xml with syntax highlighting",
    )
    parser.add_argument(
        "--list-components",
        action="store_true",
        help="List Android components (activities, services, receivers, providers)",
    )
    parser.add_argument(
        "--component-type",
        choices=["all", "activity", "service", "receiver", "provider"],
        default="all",
        help="Filter --list-components by component type (default: all)",
    )
    parser.add_argument(
        "--exported-only",
        action="store_true",
        help="Only display exported components with --list-components",
    )
    return parser


def _open_app(apk_path: str) -> Application:
    # Pass path (not BytesIO) so findrefs/getclass can mmap on native.
    return Application(apk_path)


def _run_disassembly(application: Application, args: argparse.Namespace) -> int:
    if not args.class_pattern and not args.method_pattern and args.limit <= 0:
        print_error(
            "With --disasm, set --class and/or --method (regex), or --limit N"
        )
        return 1

    count = 0
    for method in application.iter_methods(
        class_pattern=args.class_pattern,
        method_pattern=args.method_pattern,
        with_code=True,
    ):
        print_disasm_header(method.class_name, method.name)
        try:
            if getattr(args, "cfg", False):
                blocks = application.method_basic_blocks(method)
                print_cfg_edges(
                    application.method_cfg_edges(method),
                    len(blocks),
                )
            for line in application.iter_disassembly(method):
                print_disasm_line(line)
        except BytecodeNotAvailable as exc:
            print_error(str(exc))
            return 1
        count += 1
        if args.limit > 0 and count >= args.limit:
            break

    if count == 0:
        print_warning("No methods with code matched the given filters")
        return 1
    if args.verbose:
        print_info(f"Disassembled {count} method(s)")
    return 0


def _run_decompilation(application: Application, args: argparse.Namespace) -> int:
    from androguard.core.decompiler import ensure_loaded

    try:
        ensure_loaded()
    except DecompilerNotAvailable as exc:
        print_error(str(exc))
        return 1

    exclude = args.exclude or None

    if args.decompile_selector:
        try:
            parse_method_selector(args.decompile_selector)
            java = application.decompile_method_selector(
                args.decompile_selector
            )
        except ValueError as exc:
            print_error(str(exc))
            return 1
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out:
                out.write(java)
            print_info(f"Wrote {args.output}")
        else:
            print_java(java)
        return 0

    if args.output_dir:
        n = application.decompile_apk_to_dir(
            args.output_dir,
            only_package=args.only_package,
            exclude=exclude,
        )
        if n == 0:
            if args.only_package:
                print_error(
                    "No classes matched --only-package "
                    f"{args.only_package!r} in this APK "
                    "(multi-DEX APKs only write matching packages; "
                    "check the package name, e.g. tests.androguard vs "
                    "androguard.test)"
                )
            else:
                print_error("No classes were decompiled from this APK")
            return 1
        print_info(f"Decompiled {n} class(es) to {args.output_dir}")
        return 0

    if args.output and not args.decompile:
        print_error("--output requires --decompile or --decompile-method")
        return 1

    if args.decompile:
        if not args.class_pattern and not args.method_pattern and args.limit <= 0:
            if args.output:
                from androguard.core.decompiler import decompile_dex

                blobs = application._dex_blobs()
                java = decompile_dex(
                    blobs[0][1],
                    only_package=args.only_package,
                    exclude=exclude,
                )
                with open(args.output, "w", encoding="utf-8") as out:
                    out.write(java)
                print_info(f"Wrote {args.output}")
                return 0
            print_error(
                "With --decompile, set --class/--method (regex), "
                "--decompile-method CLASS#METHOD, -d DIR, or -o FILE"
            )
            return 1

        count = 0
        try:
            for method, java in application.iter_decompiled_methods(
                class_pattern=args.class_pattern,
                method_pattern=args.method_pattern,
            ):
                print_java(
                    java,
                    heading=f"// {method.class_name}.{method.name}",
                )
                count += 1
                if args.limit > 0 and count >= args.limit:
                    break
        except DecompilerNotAvailable as exc:
            print_error(str(exc))
            return 1
        except ValueError as exc:
            print_error(str(exc))
            return 1

        if count == 0:
            print_warning("No methods matched for decompilation")
            return 1
        if args.verbose:
            print_info(f"Decompiled {count} method(s)")
        return 0

    return 0


def _format_findrefs_lines(kind: str, sites: list) -> list[str]:
    lines: list[str] = []
    for s in sites:
        cls = s.get("class_name") or ""
        meth = s.get("method_name") or ""
        if kind in ("extends", "impl") or not meth:
            lines.append(cls)
        else:
            off = s.get("file_offset")
            loc = f"{cls}#{meth}"
            if off is not None:
                loc = f"{loc}@{off}"
            lines.append(loc)
    return lines


def _run_asc(argv: list[str]) -> int:
    parser = _build_asc_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print_version()
        return 0

    apk = args.apk_path
    if not Path(apk).is_file():
        print_error(f"APK not found: {apk}")
        return 1

    threads = getattr(args, "threads", None)
    with _rayon_threads(threads):
        try:
            application = _open_app(apk)
        except Exception as exc:
            print_error(str(exc))
            return 1

        if args.command == "getclass":
            try:
                java = application.getclass(args.dalvik_class)
            except Exception as exc:
                print_error(str(exc))
                return 1
            _write_text(args.output, java, also_stdout=True)
            return 0

        if args.command == "listclass":
            names = list(application.class_names)
            prefix = getattr(args, "prefix", None)
            if prefix:
                p = prefix.replace(".", "/")
                names = [
                    n
                    for n in names
                    if n.replace(".", "/").startswith(p)
                    or n.lstrip("L").startswith(p.lstrip("L"))
                ]
            _write_lines(args.output, names, also_stdout=not args.output)
            if args.output:
                print_info(f"Wrote {len(names)} class(es) to {args.output}")
            return 0

        if args.command == "listmethod":
            try:
                lines = application.listmethod(
                    class_name=args.class_name,
                    filter=args.name_filter,
                )
            except Exception as exc:
                print_error(str(exc))
                return 1
            _write_lines(args.output, lines, also_stdout=not args.output)
            if args.output:
                print_info(f"Wrote {len(lines)} method(s) to {args.output}")
            return 0

        if args.command == "liststring":
            try:
                lines = application.liststring(filter=args.str_filter)
            except DecompilerNotAvailable as exc:
                # Fallback: dexparser string pool via Application.strings
                needle = (args.str_filter or "").casefold()
                lines = [
                    s
                    for s in application.strings
                    if not needle or needle in s.casefold()
                ]
                if needle and not lines:
                    print_error(str(exc))
                    return 1
            except Exception as exc:
                print_error(str(exc))
                return 1
            _write_lines(args.output, lines, also_stdout=not args.output)
            if args.output:
                print_info(f"Wrote {len(lines)} string(s) to {args.output}")
            return 0

        if args.command == "getmanifest":
            try:
                xml = application.get_manifest_xml()
            except Exception as exc:
                print_error(str(exc))
                return 1
            _write_text(args.output, xml, also_stdout=True)
            return 0

        if args.command == "listcomponents":
            try:
                comps = application.get_components(
                    component_type=args.component_type,
                    exported_only=args.exported_only,
                )
            except Exception as exc:
                print_error(str(exc))
                return 1
            print_components(comps)
            return 0

        if args.command == "findrefs":
            kind = args.find_type
            if kind in ("method", "field"):
                value = args.name
                if not value and not args.class_name:
                    print_error(f"findrefs {kind} needs a name and/or --class")
                    return 1
                value = value or ""
                class_name = args.class_name
                fuzzy = bool(args.fuzzy_class)
            else:
                value = args.value
                class_name = None
                fuzzy = False
            try:
                sites = application.findrefs(
                    kind,
                    value,
                    class_name=class_name,
                    fuzzy_class=fuzzy,
                )
            except Exception as exc:
                print_error(str(exc))
                return 1
            lines = _format_findrefs_lines(kind, sites)
            out_path = getattr(args, "output", None)
            if out_path:
                _write_lines(out_path, lines, also_stdout=False)
            print_findrefs(kind, value, sites)
            return 0

        if args.command == "export":
            try:
                n = application.decompile_apk_to_dir(
                    args.output_dir,
                    only_package=args.only_package,
                    exclude=args.exclude or None,
                )
            except DecompilerNotAvailable as exc:
                print_error(str(exc))
                return 1
            except Exception as exc:
                print_error(str(exc))
                return 1
            if n == 0:
                print_error("No classes were decompiled from this APK")
                return 1
            print_info(f"Exported {n} class(es) to {args.output_dir}")
            return 0

    print_error(f"unknown command {args.command!r}")
    return 1


def _run_legacy(argv: list[str] | None) -> int:
    parser = _build_legacy_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print_version()
        return 0

    if not args.input:
        parser.error("the following arguments are required: -i/--input")

    if args.verbose:
        LOGGER.setLevel("DEBUG")

    with _rayon_threads(getattr(args, "threads", None)):
        try:
            application = _open_app(args.input)
        except Exception as exc:
            print_error(str(exc))
            return 1

        summary = application.summary()
        print_summary(summary, args.input)

        if args.list_classes:
            print_class_names(application.class_names)

        if args.list_methods:
            print_methods(application.methods)

        if getattr(args, "list_strings", False):
            try:
                strings = application.liststring()
            except Exception:
                strings = list(application.strings)
            _write_lines(args.output, strings, also_stdout=not args.output)

        if getattr(args, "getmanifest", False):
            try:
                xml = application.get_manifest_xml()
            except Exception as exc:
                print_error(str(exc))
                return 1
            _write_text(args.output, xml, also_stdout=True)
            return 0

        if getattr(args, "show_manifest", False):
            try:
                xml = application.get_manifest_xml()
            except Exception as exc:
                print_error(str(exc))
                return 1
            print_manifest(xml)
            return 0

        if getattr(args, "list_components", False):
            try:
                comps = application.get_components(
                    component_type=args.component_type,
                    exported_only=args.exported_only,
                )
                print_components(comps)
            except Exception as exc:
                print_error(str(exc))
                return 1
            return 0

        if getattr(args, "scan_vulns", False):
            try:
                findings = application.scan_vulns()
            except DecompilerNotAvailable as exc:
                print_error(str(exc))
                return 1
            print_scan_vulns(findings)
            return 0

        if getattr(args, "getclass", None):
            try:
                java = application.getclass(args.getclass)
            except Exception as exc:
                print_error(str(exc))
                return 1
            if args.output:
                _write_text(args.output, java, also_stdout=False)
                print_info(f"Wrote {args.output}")
            else:
                print_java(java)
            return 0

        if getattr(args, "findrefs", None):
            if not args.findrefs_value:
                print_error("--findrefs requires --findrefs-value")
                return 1
            try:
                sites = application.findrefs(
                    args.findrefs,
                    args.findrefs_value,
                    class_name=getattr(args, "findrefs_class", None),
                    fuzzy_class=bool(
                        getattr(args, "findrefs_fuzzy_class", False)
                    ),
                )
            except Exception as exc:
                print_error(str(exc))
                return 1
            pool = None
            if not sites and args.findrefs == "string":
                needle = args.findrefs_value.casefold()
                pool = [
                    s for s in application.strings if needle in s.casefold()
                ]
            if args.output:
                _write_lines(
                    args.output,
                    _format_findrefs_lines(args.findrefs, sites),
                    also_stdout=False,
                )
            print_findrefs(
                args.findrefs, args.findrefs_value, sites, pool=pool
            )
            return 0

        if getattr(args, "emulate", None):
            try:
                cls, meth = parse_method_selector(args.emulate)
                result = application.emulate(cls, meth)
            except Exception as exc:
                print_error(str(exc))
                return 1
            print_emulate(result)
            return 0

        if getattr(args, "decode_project", False):
            try:
                project = application.decode_project(no_res=True)
            except Exception as exc:
                print_error(str(exc))
                return 1
            print_decode_project(project)
            return 0

        if args.disasm:
            return _run_disassembly(application, args)

        if args.decompile or args.decompile_selector or args.output_dir:
            return _run_decompilation(application, args)

    return 0


def app(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and not argv[0].startswith("-") and argv[0] in _ASC_COMMANDS:
        return _run_asc(argv)
    return _run_legacy(argv)


if __name__ == "__main__":
    sys.exit(app())
