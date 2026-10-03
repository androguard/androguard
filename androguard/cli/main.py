"""Androguard command-line interface."""

from __future__ import annotations

import argparse
import io
import sys

from androguard import __version__ as ANDROGUARD_VERSION
from androguard.application import Application
from androguard.cli.display import (
    print_class_names,
    print_cfg_edges,
    print_decode_project,
    print_disasm_header,
    print_disasm_line,
    print_emulate,
    print_error,
    print_findrefs,
    print_info,
    print_java,
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


def _build_parser() -> argparse.ArgumentParser:
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
        help="Write decompiled Java to a single file (first DEX only)",
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
        choices=["string", "type", "method", "field"],
        help="ASC findrefs kind (use with --findrefs-value)",
    )
    decompile.add_argument(
        "--findrefs-value",
        metavar="VALUE",
        help="Needle for --findrefs",
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
    return parser


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


def app(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print_version()
        return 0

    if not args.input:
        parser.error("the following arguments are required: -i/--input")

    if args.verbose:
        LOGGER.setLevel("DEBUG")

    with open(args.input, "rb") as fd:
        application = Application(io.BytesIO(fd.read()))

    summary = application.summary()
    print_summary(summary, args.input)

    if args.list_classes:
        print_class_names(application.class_names)

    if args.list_methods:
        print_methods(application.methods)

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
            print_java(application.getclass(args.getclass))
        except Exception as exc:
            print_error(str(exc))
            return 1
        return 0

    if getattr(args, "findrefs", None):
        if not args.findrefs_value:
            print_error("--findrefs requires --findrefs-value")
            return 1
        try:
            sites = application.findrefs(
                args.findrefs, args.findrefs_value
            )
        except Exception as exc:
            print_error(str(exc))
            return 1
        pool = None
        if not sites and args.findrefs == "string":
            needle = args.findrefs_value.casefold()
            pool = [s for s in application.strings if needle in s.casefold()]
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


if __name__ == "__main__":
    sys.exit(app())
