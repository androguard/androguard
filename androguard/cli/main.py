"""Androguard command-line interface."""

from __future__ import annotations

import argparse
import io
import sys

from androguard.application import Application
from androguard.core.bytecode import BytecodeNotAvailable
from androguard.core.decompiler import DecompilerNotAvailable, parse_method_selector
from androguard.helper.logging import LOGGER


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="androguard",
        description="Analyze Android APK files using the Androguard ecosystem parsers.",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
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
        LOGGER.error(
            "With --disasm, set --class and/or --method (regex), or --limit N"
        )
        return 1

    count = 0
    for method in application.iter_methods(
        class_pattern=args.class_pattern,
        method_pattern=args.method_pattern,
        with_code=True,
    ):
        print(f"\n# {method.class_name}.{method.name}")
        try:
            for line in application.iter_disassembly(method):
                print(line)
        except BytecodeNotAvailable as exc:
            LOGGER.error("%s", exc)
            return 1
        count += 1
        if args.limit > 0 and count >= args.limit:
            break

    if count == 0:
        LOGGER.warning("No methods with code matched the given filters")
        return 1
    if args.verbose:
        LOGGER.info("Disassembled %d method(s)", count)
    return 0


def _run_decompilation(application: Application, args: argparse.Namespace) -> int:
    from androguard.core.decompiler import ensure_loaded

    try:
        ensure_loaded()
    except DecompilerNotAvailable as exc:
        LOGGER.error("%s", exc)
        return 1

    exclude = args.exclude or None

    if args.decompile_selector:
        try:
            parse_method_selector(args.decompile_selector)
            java = application.decompile_method_selector(
                args.decompile_selector
            )
        except ValueError as exc:
            LOGGER.error("%s", exc)
            return 1
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out:
                out.write(java)
            LOGGER.info("Wrote %s", args.output)
        else:
            print(java)
        return 0

    if args.output_dir:
        application.decompile_apk_to_dir(
            args.output_dir,
            only_package=args.only_package,
            exclude=exclude,
        )
        LOGGER.info("Decompiled APK to %s", args.output_dir)
        return 0

    if args.output and not args.decompile:
        LOGGER.error("--output requires --decompile or --decompile-method")
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
                LOGGER.info("Wrote %s", args.output)
                return 0
            LOGGER.error(
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
                print(f"\n// {method.class_name}.{method.name}")
                print(java)
                count += 1
                if args.limit > 0 and count >= args.limit:
                    break
        except DecompilerNotAvailable as exc:
            LOGGER.error("%s", exc)
            return 1
        except ValueError as exc:
            LOGGER.error("%s", exc)
            return 1

        if count == 0:
            LOGGER.warning("No methods matched for decompilation")
            return 1
        if args.verbose:
            LOGGER.info("Decompiled %d method(s)", count)
        return 0

    return 0


def app(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        LOGGER.setLevel("DEBUG")

    with open(args.input, "rb") as fd:
        application = Application(io.BytesIO(fd.read()))

    summary = application.summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

    if args.list_classes:
        for name in application.class_names:
            print(name)

    if args.list_methods:
        for method in application.methods:
            print(f"{method.class_name} -> {method.name}")

    if args.disasm:
        return _run_disassembly(application, args)

    if args.decompile or args.decompile_selector or args.output_dir:
        return _run_decompilation(application, args)

    return 0


if __name__ == "__main__":
    sys.exit(app())
