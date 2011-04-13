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

import androguard, analysis, misc
from bytecode import Dot

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use this filename', 'nargs' : 1 }
option_1 = { 'name' : ('-o', '--output'), 'help' : 'base directory to output all files', 'nargs' : 1 }

option_2 = { 'name' : ('-d', '--dot'), 'help' : 'display the file in human readable format', 'action' : 'count' }

option_3 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1, option_2, option_3]

def valid_class_name( class_name ):
   if class_name[-1] == ";" :
      return class_name[1:-1]
   return class_name

def create_directory( class_name, output ) :
   output_name = output
   if output_name[-1] != "/" :
      output_name = output_name + "/"

   try :
      os.makedirs( output_name + class_name )
   except OSError :
      pass

def create_directories( a, output ) :
   for vm in a.get_vms() :
      for class_name in vm.get_classes_names() :
         create_directory( valid_class_name( class_name ), output )

def export_apps_to_dot( a, output ) :
   output_name = output
   if output_name[-1] != "/" :
      output_name = output_name + "/"

   for vm in a.get_vms() :
      x = analysis.VM_BCA( vm )
      for method in vm.get_methods() :
         filename = output_name + valid_class_name( method.get_class_name() )
         if filename[-1] != "/" :
            filename = filename + "/"
        
         descriptor = method.get_descriptor()
         descriptor = descriptor.replace(";", "")
         descriptor = descriptor.replace(" ", "")
         descriptor = descriptor.replace("(", "-")
         descriptor = descriptor.replace(")", "-")
         descriptor = descriptor.replace("/", "_")

         filename = filename + method.get_name() + descriptor

         fd = open( filename + ".dot", "w")

         fd.write("digraph code {\n")
         fd.write("graph [bgcolor=white];\n")
         fd.write("node [color=lightgray, style=filled shape=box fontname=\"Courier\" fontsize=\"8\"];\n")

         fd.write( Dot(method, x.hmethods[ method ]) )

         fd.write("}\n")
         fd.close()

def main(options, arguments) :                    
   if options.input != None and options.output != None :
      a = androguard.Androguard( [ options.input ] )
      
      create_directories( a, options.output )

      if options.dot != None :
         export_apps_to_dot( a, options.output )

   elif options.version != None :
      print "Androdd version %s" % misc.VERSION

if __name__ == "__main__" :                                                     
   parser = OptionParser()
   for option in options :
      param = option['name']      
      del option['name']      
      parser.add_option(*param, **option)

   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)
