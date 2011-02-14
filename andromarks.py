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

import sys, os, cmd, threading, re

from optparse import OptionParser

import androguard, wm, misc

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file to be check', 'nargs' : 1 }

option_1 = { 'name' : ('-x', '--xml'), 'help' : 'your xml watermark !', 'nargs' : 1 }
option_2 = { 'name' : ('-d', '--directory'), 'help' : 'the directory of files to check !', 'nargs' : 1 }

option_5 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1, option_2, option_5]

def main(options, arguments) :                    
   if options.version != None :
      print "Andromarks version %s" % misc.VERSION

   elif options.directory != None and options.xml != None :
      for root, dirs, files in os.walk( options.directory ) :
         if files != [] :
            for file in files :
               if ".class" in file :
                  print "FILE", file
                  _b = androguard.AndroguardS(root + "/" + file)
                  for class_name in _b.get_classes_names() :
                     androguard.WMCheck( _b, class_name, options.xml )

if __name__ == "__main__" :                                                     
   parser = OptionParser()
   for option in options :
      param = option['name']      
      del option['name']      
      parser.add_option(*param, **option)

   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)
