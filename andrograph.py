#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Tal Melamed <androguard at appsec.it>, Anthony Desnos <desnos at t0t0.fr>
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

import os, sys, subprocess

from optparse import OptionParser
from androguard.core.bytecodes import apk
from androguard.core import androconf


option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input (dex, apk)', 'nargs' : 1 }
options = [option_0]

def autograph( apk ):
  apk_name = os.path.basename( apk )
  apk_pkg = subprocess.check_output( "aapt dump badging " + apk + " | grep package:\ name | sed 's/versionCode.*//g' | sed 's/package: name=//g' | sed \"s/'//g\"", shell=True ).rstrip()
  print "+ File : "     + subprocess.check_output( "echo " + apk_name + " | grep --color=always " + apk_name, shell=True ),
  print "+ Package : "  + subprocess.check_output( "echo " + apk_pkg + " | grep -e . --color=always", shell=True ),
  print "+ MD5 : "      + subprocess.check_output( "md5sum " + apk + " | grep --color=always -o '[a-z0-9]\{32\}'", shell=True ),
  print "+ SHA1 : "     + subprocess.check_output( "sha1sum " + apk + " | grep --color=always -o '[a-z0-9]\{40\}'", shell=True ),
  print "+ SHA256 : "   + subprocess.check_output( "sha256sum " + apk + " | grep --color=always -o '[a-z0-9]\{64\}'", shell=True )



def main(options, arguments) :
    if options.input != None :
        ret_type = androconf.is_android( options.input )
        if ret_type == "APK" or ret_type == "DEX"  :
            autograph( options.input )
        else:
            print "input file should be apk/dex..."
            return 0


if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
      param = option['name']
      del option['name']
      parser.add_option(*param, **option)

      
   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments) 
