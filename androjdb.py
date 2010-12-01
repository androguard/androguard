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

import sys
from optparse import OptionParser

from subprocess import Popen, PIPE, STDOUT

option_0 = { 'name' : ('-c', '--classpath'), 'help' : 'classpath', 'nargs' : 1 }

options = [ option_0 ]


#compile = Popen([ "/usr/bin/javac", "VM.java" ], stdout=PIPE, stderr=STDOUT)                                                                                                                                                
#stdout, stderr = compile.communicate()
def main(options, arguments) :
   print options, arguments

   compile = Popen([ "/usr/bin/jdb", "-classpath", options.classpath, arguments[0] ], stdout=PIPE, stderr=PIPE, stdin=PIPE)
   #stdout, stderr = compile.communicate()
   #print stdout, stderr

   log = compile.stdout.readline()
   print log
   compile.stdin.write("run\n")

   while(compile.poll() == None):
      log = compile.stdout.readline()
      print log

if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
      param = option['name']
      del option['name']
      parser.add_option(*param, **option)

   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)
