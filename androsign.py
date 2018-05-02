#!/usr/bin/env python3
from __future__ import print_function
from androguard.core.bytecodes.apk import APK
from androguard.util import get_certificate_name_string
from argparse import ArgumentParser
import sys
import os
import hashlib
import traceback
from colorama import Fore, Back, Style
from asn1crypto import x509


def get_parser():
    parser = ArgumentParser(description="Return the fingerprint(s) of all certificates inside an APK")

    parser.add_argument("apk", nargs="+", help="APK(s) to extract the Fingerprint of Certificates from")
    parser.add_argument("--hash", default="sha1", help="Fingerprint Hash algorithm, default SHA1")
    parser.add_argument("--all", "-a", default=False, action="store_true", help="Print all supported hashes")
    parser.add_argument("--show", "-s", default=False, action="store_true",
            help="Additionally of printing the fingerprints, show more certificate information")

    return parser

def main():
    parser = get_parser()

    args = parser.parse_args()

    hashfunctions = dict(md5=hashlib.md5,
                         sha1=hashlib.sha1,
                         sha256=hashlib.sha256,
                         sha512=hashlib.sha512,
                        )

    if args.hash.lower() not in hashfunctions:
        print("Hash function {} not supported!".format(args.hash.lower()), file=sys.stderr)
        print("Use one of {}".format(", ".join(hashfunctions.keys())), file=sys.stderr)
        sys.exit(1)

    for path in args.apk:
        try:
            a = APK(path)

            print("{}, package: '{}'".format(os.path.basename(path), a.get_package()))
            print("Is signed v1: {}".format(a.is_signed_v1()))
            print("Is signed v2: {}".format(a.is_signed_v2()))

            certs = set(a.get_certificates_der_v2() + [a.get_certificate_der(x) for x in a.get_signature_names()])

            if len(certs) > 0:
                print("Found {} unique certificates".format(len(certs)))

            for cert in certs:
                if args.show:
                    x509_cert = x509.Certificate.load(cert)
                    print("Issuer:", get_certificate_name_string(x509_cert.issuer, short=True))
                    print("Subject:", get_certificate_name_string(x509_cert.subject, short=True))
                    print("Serial Number:", hex(x509_cert.serial_number))
                    print("Hash Algorithm:", x509_cert.hash_algo)
                    print("Signature Algorithm:", x509_cert.signature_algo)
                    print("Valid not before:", x509_cert['tbs_certificate']['validity']['not_before'].native)
                    print("Valid not after:", x509_cert['tbs_certificate']['validity']['not_after'].native)

                if not args.all:
                    print("{} {}".format(args.hash.lower(), hashfunctions[args.hash.lower()](cert).hexdigest()))
                else:
                    for k, v in hashfunctions.items():
                        print("{} {}".format(k, v(cert).hexdigest()))
                print()
        except:
            print(Fore.RED + "Error in {}".format(os.path.basename(path)) + Style.RESET_ALL, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

        if len(args.apk) > 1:
            print()


if __name__ == "__main__":
    main()
