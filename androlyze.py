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

import sys, os, cmd, threading, code, re

from optparse import OptionParser

from androguard import *
from bytecode import *
from jvm import *
from dvm import *
from analysis import *

from misc import *

import IPython.ipapi
from IPython.Shell import IPShellEmbed

from cPickle import dumps, loads

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use this filename', 'nargs' : 1 }

option_1 = { 'name' : ('-d', '--display'), 'help' : 'display the file in human readable format', 'action' : 'count' }

option_2 = { 'name' : ('-m', '--method'), 'help' : 'display method(s) respect with a regexp', 'nargs' : 1 }
option_3 = { 'name' : ('-f', '--field'), 'help' : 'display field(s) respect with a regexp', 'nargs' : 1 }

option_4 = { 'name' : ('-s', '--shell'), 'help' : 'open a shell to interact more easily with objects', 'action' : 'count' }

option_5 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

option_6 = { 'name' : ('-p', '--pretty'), 'help' : 'pretty print !', 'action' : 'count' }

option_7 = { 'name' : ('-x', '--xpermissions'), 'help' : 'show paths of permissions', 'action' : 'count' }

options = [option_0, option_1, option_2, option_3, option_4, option_5, option_6, option_7]

def save_session(l, filename) :
   fd = open(filename, "w")
   fd.write( dumps(l, -1) )
   fd.close()

def load_session(filename) :
   return loads( open(filename, "r").read() ) 

def interact() :
   ipshell = IPShellEmbed(banner="Androlyze version %s" % VERSION)
   ipshell()

def main(options, arguments) :                    
   if options.shell != None :
      interact()
   
   elif options.input != None :
      _a = AndroguardS( options.input )
      _x = None

      if options.display != None :
         if options.pretty != None :
            _x = analysis.VM_BCA( _a.get_vm() )
            _a.pretty_show( _x )
         else :
            _a.show()

      elif options.method != None :
         for method in _a.get("method", options.method) :
            if options.pretty != None :
               _x = analysis.VM_BCA( _a.get_vm() )
               method.pretty_show( _x )
            else :
               method.show()
      
      elif options.field != None :
         for field in _a.get("field", options.field) :
            field.show()
      
      elif options.xpermissions != None :
         _x = analysis.VM_BCA( _a.get_vm() )
         perms_access = _x.tainted_packages.get_permissions( [] )
         for perm in perms_access :
            print "PERM : ", perm
            for path in perms_access[ perm ] :
               print "\t%s %s %s (@%s-0x%x)  ---> %s %s %s" % ( path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), \
                                                                path.get_bb().get_name(), path.get_bb().start + path.get_idx(), \
                                                                path.get_class_name(), path.get_name(), path.get_descriptor())

   elif options.version != None :
      print "Androlyze version %s" % VERSION

if __name__ == "__main__" :                                                     
   parser = OptionParser()
   for option in options :
      param = option['name']      
      del option['name']      
      parser.add_option(*param, **option)

   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)
