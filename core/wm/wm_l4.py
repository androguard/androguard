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

import random

def INIT() :
   return WM_L4

class WM_L4 :
   def __init__(self, vm, method, analysis) :
      self.__vm = vm
      self.__method = method
      self.__analysis = analysis

      self.__context = {  
                           "L_X" : [],
                           "OP_BIND" : {},
                       }

   
   def get_name(self) :
      return "WM_OP"

   def __init_context(self) :
      self.__context[ "OP_BIND" ][ '&' ] = self.new_randint()
      self.__context[ "OP_BIND" ][ '|' ] = self.new_randint()
      self.__context[ "OP_BIND" ][ '-' ] = self.new_randint()
      self.__context[ "OP_BIND" ][ '+' ] = self.new_randint()
      self.__context[ "OP_BIND" ][ '^' ] = self.new_randint()

   def run(self) :
      x = self.__analysis.get(self.__method)

      if self.__context[ "OP_BIND" ] == {} :
         self.__init_context()

      for i in x.get_bb() :
         v = 0
         for j in i.get_ops() :
            v = v + self.__context[ "OP_BIND" ][ j ]
        
         if v != 0 :
            self.__context[ "L_X" ].append( v )
      
   def new_randint(self) :
      x = random.randint(300, 1000)
      
      for i in self.__context[ "OP_BIND" ] :
         if self.__context[ "OP_BIND" ][i] == x :
            self.new_randint()

      return x

   def challenge(self, external_wm) :
      return external_wm.get_context()["L_X"]

   def get(self) :
      return self.__context["L_X"]
   
   def set_context(self, values) :
      for x in values :
         self.__context[ x ] = values[ x ]

   def get_context(self) :
      return self.__context

   def get_export_context(self) :
      return { "OP_BIND" : self.__context["OP_BIND"] }

   def get_import_context(self) :
      return { "OP_BIND" : self.__context["OP_BIND"] }
