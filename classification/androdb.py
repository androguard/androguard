#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>
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

import sys, hashlib, os

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, LargeBinary, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import declarative_base

from optparse import OptionParser
from xml.dom import minidom

import IPython.ipapi
from IPython.Shell import IPShellEmbed

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis, dvm
from androbasedb import *
from misc import *

option_0 = { 'name' : ('-c', '--config'), 'help' : 'config filename', 'nargs' : 1 }
option_1 = { 'name' : ('-i', '--input'), 'help' : 'input filename (APK, dex)', 'nargs' : 1 }
option_2 = { 'name' : ('-s', '--shell'), 'help' : 'open a shell to interact more easily with objects', 'action' : 'count' }
option_3 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }
option_4 = { 'name' : ('-d', '--directory'), 'help' : 'add all files (dex,apk) from a specific directory', 'nargs' : 1 }
options = [option_0, option_1, option_2, option_3, option_4]

def interact() :
    ipshell = IPShellEmbed(banner="AndroDB version %s" % VERSION)
    ipshell()

def main(options, arguments) :
    if options.shell != None :
        interact()

    if options.config == None :
        return

    dbname = configtodb( options.config )
    adb = AndroDB( dbname )

    if options.directory != None :
        for root, dirs, files in os.walk( options.directory ) :
            if files != [] :
                for f in files :
                    if ".apk" in f :
                        adb.add_apk_raw( root + "/" + f )
                        # copy files
    elif options.input != None :
        adb.add_apk_raw( options.input )
        # copy file

if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
