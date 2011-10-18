#!/usr/bin/env python2.6

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

from xml.sax.saxutils import escape, unescape
import sys, hashlib, os
from optparse import OptionParser

PATH_INSTALL = "./"																																																			   
sys.path.append(PATH_INSTALL + "./")

import androguard, apk, dvm, analysis, ganalysis, androconf 

option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input', 'nargs' : 1 }
option_1 = { 'name' : ('-o', '--output'), 'help' : 'filename output of the xgmml', 'nargs' : 1 }
option_2 = { 'name' : ('-f', '--functions'), 'help' : 'include function calls', 'action' : 'count' }
option_3 = { 'name' : ('-e', '--externals'), 'help' : 'include extern function calls', 'action' : 'count' }
option_4 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1, option_2, option_3, option_4]

def main(options, arguments) :
    if options.input != None and options.output != None :
        ret_type = androconf.is_android( options.input )
        
        vm = None
        a = None
        if ret_type == "APK"  :
            a = apk.APK( options.input )
            if a.is_valid_APK() :
                vm = dvm.DalvikVMFormat( a.get_dex() )
            else :
                print "INVALID APK"
        elif ret_type == "DEX" :
            try :
                vm = dvm.DalvikVMFormat( open(options.input, "rb").read() )
            except Exception, e :
                print "INVALID DEX", e

        vmx = analysis.VMAnalysis( vm )
        gvmx = ganalysis.GVMAnalysis( vmx, a )

        gvmx.export_to_gexf( options.output )

if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
	  param = option['name']
	  del option['name']
	  parser.add_option(*param, **option)

	  
   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)	
