#!/usr/bin/env python3
"""Androguard Gui"""
from __future__ import print_function

import argparse

from androguard.core import androconf
from androguard.cli import androgui_main


def get_parser():
    parser = argparse.ArgumentParser(description="Androguard GUI")
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument("-i", "--input_file", default=None)
    parser.add_argument("-p", "--input_plugin", default=None)
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    androgui_main(args.input_file, args.input_plugin)
