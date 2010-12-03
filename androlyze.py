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

import androguard, misc

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use this filename', 'nargs' : 1 }

option_1 = { 'name' : ('-d', '--display'), 'help' : 'display the file in human readable format', 'action' : 'count' }

option_2 = { 'name' : ('-m', '--method'), 'help' : 'display method(s) respect with a regexp', 'nargs' : 1 }
option_3 = { 'name' : ('-f', '--field'), 'help' : 'display field(s) respect with a regexp', 'nargs' : 1 }

option_4 = { 'name' : ('-s', '--shell'), 'help' : 'open a shell to interact more easily with objects', 'action' : 'count' }

option_5 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1, option_2, option_3, option_4, option_5]

class ConfClass:
    def configure(self, cnf):
        self.__dict__ = cnf.__dict__.copy()
    def __repr__(self):
        return str(self)
    def __str__(self):
        s="Version    = %s\n" % misc.VERSION
        keys = self.__class__.__dict__.copy()
        keys.update(self.__dict__)
        keys = keys.keys()
        keys.sort()
        for i in keys:
            if i[0] != "_":
                s += "%-10s = %s\n" % (i, repr(getattr(self, i)))
        return s[:-1]

class Conf(ConfClass):
   session = ""

def interact() :
   conf = Conf()
   try:
      import rlcompleter, readline, atexit
   except ImportError:
      pass
   else:
      histfile = os.path.join(os.environ["HOME"], ".androlyze_history")
      atexit.register(readline.write_history_file, histfile)
   try:
      readline.read_history_file(histfile)
   except IOError:
      pass

   import bytecode, jvm, dvm, analysis

   mydict = {
      # *VM Format
      "JVMFormat" : jvm.JVMFormat,
      "DalvikVMFormat" : dvm.DalvikVMFormat,

      # Androguard
      "AndroguardS" : androguard.AndroguardS,
      "Androguard" : androguard.Androguard,

      # Androguard VM*
      "VM_int" : androguard.VM_int,
      "VM_INT_AUTO" : androguard.VM_INT_AUTO,
      "VM_INT_BASIC_MATH_FORMULA" : androguard.VM_INT_BASIC_MATH_FORMULA,
      "VM_INT_BASIC_PRNG" : androguard.VM_INT_BASIC_PRNG,

      # Androguard Analysis
      "VMBCA" : analysis.VMBCA,
   }

   import __builtin__
   __builtin__.__dict__.update(globals())
   __builtin__.__dict__.update(mydict)

   class InterpCompleter(rlcompleter.Completer):
      def global_matches(self, text):
         matches = []
         n = len(text)       
         for lst in [dir(__builtin__), session.keys()]:
            for word in lst:            
               if word[:n] == text and word != "__builtins__":               
                  matches.append(word)
         return matches


      def attr_matches(self, text):
         m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
         if not m :
            return

         expr, attr = m.group(1, 3)
         try:
            object = eval(expr)
         except:
            object = eval(expr, session)

         words = filter(lambda x: x[0] != "_", dir(object))
         
         matches = []
         n = len(attr)
         for word in words:
            if word[:n] == attr and word != "__builtins__":
               matches.append("%s.%s" % (expr, word))
         return matches

   readline.set_completer(InterpCompleter().complete)
   readline.parse_and_bind("C-o: operate-and-get-next")
   readline.parse_and_bind("tab: complete")

   session={"conf": conf}
               
   code.interact(banner="Welcome to Androlyze %s" % misc.VERSION, local=session)

def main(options, arguments) :                    
   if options.shell != None :
      interact()
   
   elif options.input != None :
      _a = androguard.AndroguardS( options.input )
      
      if options.display != None :
         _a.show()
      elif options.method != None :
         for method in _a.get("method", options.method) :
            method.show()
      elif options.field != None :
         for field in _a.get("field", options.field) :
            field.show()

   elif options.version != None :
      print "Androlyze version %s" % misc.VERSION

if __name__ == "__main__" :                                                     
   parser = OptionParser()
   for option in options :
      param = option['name']      
      del option['name']      
      parser.add_option(*param, **option)

   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)
