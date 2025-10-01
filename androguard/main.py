import argparse
import io
import sys

from . import Application
from .helper.logging import LOGGER


def initParser():
    parser = argparse.ArgumentParser(
        prog='androguard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Android Application',
    )

    parser.add_argument('-i', '--input', type=str, help='input Android file')

    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    args = parser.parse_args()
    return args


arguments = initParser()


def app():
    if arguments.input:
        with open(arguments.input, 'rb') as fd:
            a = Application(io.BytesIO(fd.read()))
            print(a.dex)
            print(a.dex)

            print(a.classes_names)
            print(len(a.classes_names))
            print(a.strings)
            print(len(a.strings))
            for method in a.methods:
                print("METHOD", method.name, method.type_method)

    return 0


if __name__ == '__main__':
    app()
