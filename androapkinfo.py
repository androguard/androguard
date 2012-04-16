#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
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

import sys, os

from optparse import OptionParser

from androguard.core import androconf
from androguard.core.bytecodes import apk


option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use this filename', 'nargs' : 1 }
option_1 = { 'name' : ('-d', '--directory'), 'help' : 'directory : use this directory', 'nargs' : 1 }
option_2 = { 'name' : ('-v', '--version'), 'help' : 'version', 'action' : 'count' }

options = [option_0, option_1, option_2]

def main(options, arguments) :
    if options.input != None :
        ret_type = androconf.is_android( options.input ) 
        
        print os.path.basename(options.input), ":"
        if ret_type == "APK" :
            try :
                a = apk.APK( options.input )
                if a.is_valid_APK() :
                    a.show()
                else :
                    print "INVALID"
            except Exception, e :
                print "ERROR", e

    elif options.directory != None :
        for root, dirs, files in os.walk( options.directory, followlinks=True ) :
            if files != [] :
                for f in files :
                    real_filename = root
                    if real_filename[-1] != "/" :
                        real_filename += "/"
                    real_filename += f

                    ret_type = androconf.is_android( real_filename )
                    if ret_type == "APK"  :
                        print os.path.basename( real_filename ), ":"
                        try :
                            a = apk.APK( real_filename )
                            if a.is_valid_APK() :
                                a.show()
                            else :
                                print "INVALID APK"
                        except Exception, e :
                            print "ERROR", e
                            raise("oups")

    elif options.version != None :
        print "Androapkinfo version %s" % androconf.ANDROGUARD_VERSION

if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
