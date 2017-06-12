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
import sys

from optparse import OptionParser

from androguard.core import *
from androguard.core.androconf import *
from androguard.core.bytecode import *
from androguard.core.bytecodes.dvm import *
from androguard.core.bytecodes.apk import *

from androguard.core.analysis.analysis import *
from androguard.decompiler.decompiler import *
from androguard.session import Session

from androguard.util import *
from androguard.misc import *

from IPython.terminal.embed import InteractiveShellEmbed
from traitlets.config import Config

option_0 = {
    'name': ('-s', '--shell'),
    'help': 'open an interactive shell to play more easily with objects',
    'action': 'count'
}
option_1 = {
    'name': ('-v', '--version'),
    'help': 'version of Androguard',
    'action': 'count'
}
option_2 = {
    'name': ('-d', '--debug'),
    'help': 'verbose mode',
    'action': 'count'
}

options = [option_0, option_1, option_2]


def interact():
    CONF["SESSION"] = Session(True)
    cfg = Config()
    ipshell = InteractiveShellEmbed(
        config=cfg,
        banner1="Androguard version %s" % ANDROGUARD_VERSION)
    init_print_colors()
    ipshell()


def main(options, arguments):
    if options.debug:
        set_debug()

    if options.shell != None:
        interact()

    elif options.version != None:
        print("Androguard version %s" % androconf.ANDROGUARD_VERSION)


if __name__ == "__main__":
    parser = OptionParser()
    for option in options:
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
