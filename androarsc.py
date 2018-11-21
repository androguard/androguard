#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import sys
from argparse import ArgumentParser

from androguard.core import androconf
from androguard.core.bytecodes import apk
from androguard.util import read
from androguard.cli import androarsc_main as main

if sys.version_info.major == 2:
    # Patch sys.stdout to avoid problems with unicode when piping
    # See also https://wiki.python.org/moin/PrintFails for more information
    import codecs
    import locale
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout);


if __name__ == "__main__":
    parser = ArgumentParser(description="Decode resources.arsc either directly"
            "from a given file or from an APK.")

    parser.add_argument("--version", "-v", action="store_true", default=False,
            help="Print androguard version and exit")
    parser.add_argument("--input", "-i",
            help="resources.arsc or APK to parse (legacy option)")
    parser.add_argument("file", nargs="?",
            help="resources.arsc or APK to parse")
    parser.add_argument("--output", "-o",
            help="filename to save the decoded resources to")
    parser.add_argument("--package", "-p",
            help="Show only resources for the given package name (default: the first package name found)")
    parser.add_argument("--locale", "-l",
            help="Show only resources for the given locale (default: '\\x00\\x00')")
    parser.add_argument("--type", "-t",
            help="Show only resources of the given type (default: public)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list-packages", action="store_true", default=False,
            help="List all package names and exit")
    group.add_argument("--list-locales", action="store_true", default=False,
            help="List all locales and exit")
    group.add_argument("--list-types", action="store_true", default=False,
            help="List all types and exit")

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

    ret_type = androconf.is_android(fname)
    if ret_type == "APK":
        a = apk.APK(fname)
        arscobj = a.get_android_resources()
    elif ret_type == "ARSC":
        arscobj = apk.ARSCParser(read(fname))
    else:
        print("Unknown file type!", file=sys.stderr)
        sys.exit(1)

    if args.list_packages:
        print("\n".join(arscobj.get_packages_names()))
        sys.exit(0)

    if args.list_locales:
        for p in arscobj.get_packages_names():
            print("In Package:", p)
            print("\n".join(map(lambda x: "  \\x00\\x00" if x == "\x00\x00" else
                "  {}".format(x), sorted(arscobj.get_locales(p)))))
        sys.exit(0)

    if args.list_types:
        for p in arscobj.get_packages_names():
            print("In Package:", p)
            for locale in sorted(arscobj.get_locales(p)):
                print("  In Locale: {}".format("\\x00\\x00" if locale == "\x00\x00" else
                    locale))
                print("\n".join(map("    {}".format, sorted(arscobj.get_types(p,
                    locale)))))
        sys.exit(0)


    main(arscobj, outp=args.output, package=args.package, typ=args.type, locale=args.locale)
