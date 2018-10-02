#!/usr/bin/env python

from __future__ import print_function

import os
import sys
from argparse import ArgumentParser

from androguard import session
from androguard.core import androconf
from androguard.cli import export_apps_to_format


def get_parser():
    parser = ArgumentParser(description="Decompile an APK and create Control Flow Graphs")

    parser.add_argument("--version", "-v", action="store_true", default=False,
            help="Print androguard version and exit")
    parser.add_argument("--input", "-i",
            help="resources.arsc or APK to parse (legacy option)")
    parser.add_argument("file", nargs="?",
            help="resources.arsc or APK to parse")
    parser.add_argument("--output", "-o", required=True,
            help="output directory. If the output folder already exsist, it will"
            "be overwritten!")
    parser.add_argument("--format", "-f",
            help="Additionally write control flow graphs for each method,"
            "specify the format for example png, jpg, raw (write dot file), ...")
    parser.add_argument("--jar", "-j", action="store_true", default=False,
            help="Use DEX2JAR to create a JAR file")
    parser.add_argument("--limit", "-l",
            help="Limit to certain methods only by regex (default: '.*')")
    parser.add_argument("--decompiler", "-d",
            help="Use a different decompiler (default: DAD)")
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    if args.file and args.input:
        print("Can not give --input and positional argument! Please use only one of them!", file=sys.stderr)
        sys.exit(1)

    if args.version:
        print("Androaxml version %s" % androconf.ANDROGUARD_VERSION)
        sys.exit(0)

    if not args.input and not args.file:
        print("Give one file to decode!", file=sys.stderr)
        sys.exit(1)

    if args.input:
        fname = args.input
    else:
        fname = args.file

    s = session.Session()
    with open(fname, "rb") as fd:
        s.add(fname, fd.read())
    export_apps_to_format(fname, s, args.output, args.limit,
                          args.jar, args.decompiler, args.format)
