#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012/2013/2014, Anthony Desnos <desnos at t0t0.fr>
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

from argparse import ArgumentParser

from androguard.cli import androlyze_main

# Import commonly used classes
from androguard.core.androconf import *
from androguard.misc import *


def get_parser():
    parser = ArgumentParser(description="Open a IPython Shell and start reverse engineering")

    parser.add_argument("--shell", "-s", default=False, action="store_true", help="Will do nothing, this argument is just here for your convenience")
    parser.add_argument("--debug", "-d", "--verbose", default=False, action="store_true", help="Print log messages")
    parser.add_argument("--ddebug", "-dd", "--very-verbose", default=False, action="store_true", help="Print log messages (higher verbosity)")
    parser.add_argument("--no-session", default=False, action="store_true", help="Do not start an Androguard session")
    parser.add_argument("--version", "-v", default=False, action="store_true", help="Print the Androguard Version and exit")
    parser.add_argument("apk", default=None, nargs="?", help="Start the shell with the given APK. a, d, dx are available then. Loading might be slower in this case!")
    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    androlyze_main(args.debug, args.ddebug, args.no_session, args.apk)
