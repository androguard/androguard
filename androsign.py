#!/usr/bin/env python3
from __future__ import print_function
from argparse import ArgumentParser

from androguard.cli import androsign_main


def get_parser():
    parser = ArgumentParser(description="Return the fingerprint(s) of all certificates inside an APK")

    parser.add_argument("apk", nargs="+", help="APK(s) to extract the Fingerprint of Certificates from")
    parser.add_argument("--hash", default="sha1", help="Fingerprint Hash algorithm, default SHA1")
    parser.add_argument("--all", "-a", default=False, action="store_true", help="Print all supported hashes")
    parser.add_argument("--show", "-s", default=False, action="store_true",
            help="Additionally of printing the fingerprints, show more certificate information")

    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    androsign_main(args.apk, args.hash, args.all, args.show)
