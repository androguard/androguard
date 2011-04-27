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

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis, dvm
from androbasedb import *
from misc import *

option_0 = { 'name' : ('-c', '--config'), 'help' : 'config filename', 'nargs' : 1 }

option_1 = { 'name' : ('-s', '--set'), 'help' : 'set attribute of a specific raw (id attr type value)', 'nargs' : 4 }
option_2 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }
options = [option_0, option_1, option_2]

def main(options, arguments) :
   if options.config == None :
      return

   dbname = configtodb( options.config )
   adb = AndroDB( dbname )

   if options.set != None :
      
      v = options.set[1]
      
      d = { options.set[1] : options.set[3] }
      if options.set[2] == "i" :
         d = { options.set[1] : int(options.set[3]) }
      else :
         raise("ooo")

      adb.set_apps_raw( int(options.set[0]), d )

if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
      param = option['name']
      del option['name']
      parser.add_option(*param, **option)
      
   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)    
