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
from lxml import etree
from argparse import ArgumentParser

from androguard.core import androconf
from androguard.core.bytecodes import apk
from androguard.util import read


def main(inp, outp=None):
    ret_type = androconf.is_android(inp)
    if ret_type == "APK":
        a = apk.APK(inp)
        axml = a.get_android_manifest_xml()
    elif ".xml" in inp:
        axml = apk.AXMLPrinter(read(inp)).get_xml_obj()
    else:
        print("Unknown file type")
        return

    buff = etree.tostring(axml, pretty_print=True, encoding="utf-8")
    if outp:
        with open(outp, "wb") as fd:
            fd.write(buff)
    else:
        print(buff.decode("UTF-8"))


if __name__ == "__main__":
    parser = ArgumentParser(description="Parses the AndroidManifest.xml either"
            "direct or from a given APK and prints in XML format or saves to"
            "file."
            "This tool can also be used to process any AXML encoded file, for"
            "example from the layout directory.")

    parser.add_argument("--output", "-o",
            help="filename to save the decoded AndroidManifest.xml to")
    parser.add_argument("--version", "-v", action="store_true", default=False,
            help="Print androguard version and exit")

    parser.add_argument("--input", "-i",
            help="AndroidManifest.xml or APK to parse (legacy option)")
    parser.add_argument("file", nargs="?",
            help="AndroidManifest.xml or APK to parse")
    args = parser.parse_args()


    if args.file and args.input:
        print("Can not give --input and positional argument! Please use only one of them!")
        sys.exit(1)

    if args.version:
        print("Androaxml version %s" % androconf.ANDROGUARD_VERSION)
        sys.exit(0)

    if not args.input and not args.file:
        print("Give one file to decode!")
        sys.exit(1)

    if args.file:
        main(args.file, args.output)
    elif args.input:
        main(args.input, args.output)

