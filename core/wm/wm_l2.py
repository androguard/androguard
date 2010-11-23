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

import misc
import hashlib

from networkx import DiGraph, draw_graphviz, write_dot

import random

def INIT() :
   return WM_L2

class DepF :
   def __init__(self, field) :
      G = DiGraph()
     
      ############ field -> profondeur, largeur, cycle ############

      self.__depth = 3
      self.__width = 3 
      self.__cycle = 2

      G.add_node( self._new_node(G) )

      self.__random( G, 0, self.__width, self.__cycle )

      print G.node
      print G.edge

      draw_graphviz(G)
      write_dot(G,'file.dot')

   def _new_node(self, G) :
      return "X%d" % (len(G.node))

   def _current_node(self, G) :
      return len(G.node) - 1
   
   def __random(self, G, depth, width, cycle) :
      if depth >= self.__depth : 
         return

      for i in range( random.randint(1, width) ) :
         nd = self._new_node(G)
         G.add_edge( "X%d" % depth, nd )
         self.__random( G, self._current_node(G), width, cycle )


class WM_L2 :
   def __init__(self, vm, analysis) :
      self.__vm = vm
      self.__analysis = analysis

      self.__dependencies = []

      self.__context = {
                           "L_X" : [],
                       }

   def run(self) :
      for field in self.__vm.get_fields() :
      #   if random.randint(0, 1) == 1 :
         self.__dependencies.append( DepF( field ) )
         break

      raise("ooop")

      self.__context[ "L_X" ].append( 
                                       misc.str2long( hashlib.md5( self.__context[ "STRING" ] ).hexdigest() ) 
                                    )

   def challenge(self, external_wm) :
      return []

   def get(self) :
      return self.__context[ "L_X" ]

   def set_context(self, values) :
      for x in values :
         self.__context[ x ] = values[ x ]

   def get_context(self) :
      return self.__context

   def get_export_context(self) :
      return self.__context

   def get_import_context(self) :
      return {}
