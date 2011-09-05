#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
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

import androguard, androconf, apk, dvm, msign

option_0 = { 'name' : ('-o', '--output'), 'help' : 'output database', 'nargs' : 1 }
option_1 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1]

LIST = [ 
            "basebridge.sign",
            "basebridge.b.sign",
            "basebridge.c.sign",
            "droiddream.sign", 
            "droiddream_included.sign", 
            "droiddream_light.sign", 
            "nickyspy.sign", 
            "dogowar.sign", 
            "geinimi.sign",
            "gingermaster.sign",
            "golddream.sign",
            "droidkungfu.sign",
            "droidkungfu2.sign",
            "wat.sign",
            "plankton.sign",
            "plankton.b.sign",
            "plankton.c.sign",
            "roguesppush.sign",
            "crusewind.sign",
            "yzhcsms.sign",
            "zitmo.sign",

            "rageagainstthecage_exploit.sign",
            "exploid_exploit.sign"
]

def main(options, arguments) :
    if options.version != None :
        print "RunAndrocsign version %s" % androconf.ANDROCSIGN_VERSION
        return

    s = msign.CSignature()
    for i in LIST :
        ret = s.add_file( open("signatures/" + i, "rb").read() )        

        if options.output != None :
            s.add_indb( ret, options.output )

if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
