#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2015, Tal Melamed <androguard at appsec.it>
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

import os, sys, hashlib

from optparse import OptionParser
from androguard.core.bytecodes import apk
from androguard.core import androconf


option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input (dex, apk)', 'nargs' : 1 }
options = [option_0]

def autograph( path ):
  app = open(path, 'rb').read()
  apk_name = os.path.basename( path )
  print "File: " + apk_name
  print "Package :" + apk.APK(path).get_package()
  print "MD5 :" + hashlib.md5(app).hexdigest()
  print "SHA1: " + hashlib.sha1(app).hexdigest()
  print "SHA224: " + hashlib.sha224(app).hexdigest()
  print "SHA256: " + hashlib.sha256(app).hexdigest()
  print "SHA384: " + hashlib.sha384(app).hexdigest()
  print "SHA512: " + hashlib.sha512(app).hexdigest()
  
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
