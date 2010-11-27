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

import misc, hashlib, string, random

from networkx import DiGraph, all_pairs_dijkstra_path_length, simple_cycles
from networkx import draw_graphviz, write_dot

def INIT() :
   return WM_L2

# name, access_flags, descriptor
# initial value
# all access (write)
# all dependencies actions (read / write )
class Field :
   def __init__(self, _vm, _analysis) :
      self.__vm = _vm
      self.__analysis = _analysis

      self.__name, self.__access_flag, self.__descriptor = self.__analysis.get_like_field()

      self.generate_init()

   def generate_init(self) :
      pass

   def get_name(self) :
      return self.__name

   def get_access_flag(self) :
      return self.__access_flag

   def get_descriptor(self) :
      return self.__descriptor

class DepF :
   def __init__(self, field) :
      self.__field = field

      ############ create depency field graph #########
      self.__depth = 3 
      self.__width = 3 
      self.__cycle = 2
      
      self.__G = DiGraph()
      
      G = self.__G

      G.add_node( self._new_node(G) )
      self.__random( G, 0 )

      d = all_pairs_dijkstra_path_length( G )
      l = list( reversed( sorted( d, key=lambda key: len(d[key]) ) ) )
      for i in l :
         if self.__cycle == 0 :
            break

         d_tmp = sorted( d[i], key=lambda key: d[i][key] )
         G.add_edge( d_tmp[-1], i)
         self.__cycle = self.__cycle - 1

      print simple_cycles( G )

      print G.node
      print G.edge
      print G.degree()

      ############ Add field <-> higher #####################################
      # field F depends of the higher degree
      # F <---> sorted( G.degree(), key=lambda key : G.degree()[key] )[-1]
      #######################################################################
      
      degree = G.degree()
      high_degree = sorted( degree, key=lambda key : degree[key] )[-1]

      G.add_edge( field.get_name(), high_degree )
      G.add_edge( high_degree, field.get_name() )

      #draw_graphviz(G)
      #write_dot(G,'file.dot')
     
   def run(self, _vm, _analysis) : 
      ###############################################################
      ##  dict (method) of list ( offset / list (of instructions) ) #
      ##        - insert an element                                 #
      ##        - modify the offset with the new insertion          #
      ###############################################################
      list_OB = {} 

      ############ Create dependencies fields ############
      fields = { self.__field.get_name() : Field( _vm, _analysis ) }

      ############ Create the name, the initial value and all access of the field ############
      for i in self.__G.node :
         print i, "PRE ->", self.__G.predecessors( i ), self.__G.degree()[i]

         if i not in fields :
            fields[ i ] = Field( _vm, _analysis )
            _vm.insert_field( self.__field.get_class_name(), fields[ i ].get_name(), [ fields[ i ].get_access_flag(), fields[ i ].get_descriptor() ] ) 
            

      return

      ############ Create the depedency ############
      
      ############################################################################
      # Integer variables :
      # X -> Y 
      #         - a depth into the calcul
      #         Y = { LV + LLV + NLV } x { &, -, +, |, *, /, ^ } x { &&, || }
      #         if (Y != ?) {
      #                 X = ..... ;
      #         }
      #############################################################################
      # get a local variable
      #         - used into a loop
      #         - a parameter
      #         - a new one
      ############################################################################
      find = False

      print "F -->", self.__G.successors( self.__field.get_name() )
      taint_field = _analysis.get_tainted_field( self.__field.get_class_name(), self.__field.get_name(), self.__field.get_descriptor() )
      for path in taint_field.get_paths() :
         print "\t", path[0], "%s (%d-%d)" % (path[1].get_name(), path[1].get_start(), path[1].get_end()) , path[1].get_start() + path[2], 
         x = _analysis.get( path[1].get_method() )

         bb = x.get_break_block( path[1].get_start() + path[2] )
         print bb, bb.get_start(), bb.get_end()

         print "\t\t", x.get_local_variables()

         if path[0] == "R" and find == False :
            print "Insert"
            code = path[1].get_method().get_code()
            idx = code.get_relative_idx( bb.get_start() )
            size_r = code.inserts_at( idx, [ [ "iload_3" ], [ "iconst_0" ] ] )

            print size_r
            code.insert_at( idx + 2, [ "if_icmpge", (bb.get_end() - bb.get_start()) + 3 ] )

            find = True

      ##### Insert all modifications
      for m in list_OB :
         code = m.get_code()

         i = 0
         while i < len( list_OB[ m ] ) :
            v = list_OB[ m ][ i ]
            size_r = code.inserts_at( v[0], v[1] )

            j = i + 1
            while j < len( list_OB[ m ] ) :
               v1 = list_OB[ m ][ j ]
               if v1[0] > v[0] :
                  v1[0] += size_r
               j = j + 1
            i = i + 1


   def _new_node(self, G) :
      return "X%d" % (len(G.node))

   def _current_node(self, G) :
      return len(G.node) - 1
   
   def __random(self, G, depth) :
      if depth >= self.__depth : 
         return

      for i in range( random.randint(1, self.__width) ) :
         nd = self._new_node(G)
         G.add_edge( "X%d" % depth, nd )
         self.__random( G, self._current_node(G) )


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

      for i in self.__dependencies : 
         i.run( self.__vm, self.__analysis )

      self.__context[ "L_X" ].append( 20000 )
      self.__context[ "L_X" ].append( 20001 )
      self.__context[ "L_X" ].append( 20002 )

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
