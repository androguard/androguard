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
   def __init__(self, _vm, _analysis, _vm_generate, field, offsets, real=False) :
      self.__vm = _vm
      self.__analysis = _analysis
      self.__vm_generate = _vm_generate

      self.__field = field
      self.__offsets = offsets
      
      self.__real = real

      self.__init_offset = 0
      self.__init_value = None

      self.__access_offset = []

   def run(self, degree) :
      if self.__real == False :
         self.__init_method = self.__analysis.get_init_method()

         # Get the initial offset to add the field into the init method
         self.__init_offset = self.__offsets.add_offset( self.__analysis.next_free_block_offset( self.__init_method ) )
         
         # Generate the initial value of our field, and the bytecodes associated
         value = self.__analysis.get_random_integer_value( self.__init_method, self.__field.get_descriptor() )
         self.__init_value = self.__vm_generate.create_affectation( self.__init_method, [ 0, self.__field, value ] )

         for i in range(0, degree) :
            meth, off = self.__analysis.random_free_block_offset( "^\<init\>" )
            self.__access_offset.append( (False, meth, self.__offsets.add_offset( off ) ) )
      else :
         # Get all read/write access to our field
         taint_field = self.__analysis.get_tainted_field( self.__field.get_class_name(), self.__field.get_name(), self.__field.get_descriptor() )
         n = 0
         for i in taint_field.get_paths_access("RW") :
            self.__access_offset.append( (True, i.get_method(), self.__offsets.add_offset( i.get_idx() ) ) )

            n += 1
            if n == degree :
               break

         # insert fake write access to the real field
         if n < degree :
            raise("ooo")


   def insert_init(self) :
      """ return method object, init_offset (Offset object), init_value (a list of instructions ) """
      if self.__real == False :
         return self.__init_method, self.__init_offset, self.__init_value

      return None

   def show(self) :
      if self.__real == False :
         print self.__field.get_name(), self.__init_offset.get_idx(), self.__init_value
      else :
         print self.__field.get_name()

      for i in self.__access_offset :
         print "\t", i[0], i[1].get_name(), i[2].get_idx()

   def get_name(self) :
      return self.__field.get_name()

   def get_access_flag(self) :
      return self.__field.get_access_flag()

   def get_descriptor(self) :
      return self.__field.get_descriptor()

class Offset :
   def __init__(self, idx) :
      self.__idx = idx

   def get_idx(self) :
      return self.__idx

   def add_idx(self, off) :
      self.__idx += off

class DepF :
   def __init__(self, field) :
      self.__offsets = []

      self.__field = field

      ############ create depency field graph #########
      # Initial values to build the graph (depth, width, cycles)
      self.__depth = 3 
      self.__width = 3 
      self.__cycles = 2
      
      self.__G = DiGraph()
      
      G = self.__G

      G.add_node( self._new_node(G) )
      # Create randomlu the graph without cycle
      self.__random( G, 0 )

      # Find the best path to add cycles
      d = all_pairs_dijkstra_path_length( G )
      l = list( reversed( sorted( d, key=lambda key: len(d[key]) ) ) )
      for i in l :
         if self.__cycles == 0 :
            break

         d_tmp = sorted( d[i], key=lambda key: d[i][key] )
         G.add_edge( d_tmp[-1], i)
         self.__cycles = self.__cycles - 1

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

      # Link our protected field with the node which has the highest degree
      G.add_edge( field.get_name(), high_degree )
      G.add_edge( high_degree, field.get_name() )

      #draw_graphviz(G)
      #write_dot(G,'file.dot')
    
   def add_offset(self, idx) :
      x = Offset( idx ) 
      self.__offsets.append( x )
      return x

   def run(self, _vm, _analysis, _vm_generate) : 
      ###############################################################
      ##  dict (method) of list ( offset / list (of instructions) ) #
      ##        - insert an element                                 #
      ##        - modify the offset with the new insertion          #
      ###############################################################
      list_OB = {} 

      ############ Create dependencies fields ############
      fields = { self.__field.get_name() : Field( _vm, _analysis, _vm_generate, self.__field, self, True ) }
      fields[ self.__field.get_name() ].run( self.__G.degree()[ self.__field.get_name() ] )

      ############ Create the name, the initial value and all access of the field ############
      for i in self.__G.node :
         print i, "PRE ->", self.__G.predecessors( i ), self.__G.degree()[i]

         # We have not yet add this new field
         if i not in fields :
            name, access_flag, descriptor = _analysis.get_like_field()
            _vm.insert_field( self.__field.get_class_name(), name, [ access_flag, descriptor ] ) 
            
            fields[ i ] = Field( _vm, _analysis, _vm_generate, _vm.get_field_descriptor( self.__field.get_class_name(), name, descriptor ), self )
            fields[ i ].run( self.__G.degree()[i] )

      ########## Add all fields initialisation into the final list ############
      for i in fields :
         print "FIELD ->", i, 
         fields[ i ].show()
         
         x = fields[ i ].insert_init()
         if x != None :
            try :
               list_OB[ x[0] ].append( (x[1], x[2]) )
            except KeyError :
               list_OB[ x[0] ] = []
               list_OB[ x[0] ].append( (x[1], x[2]) )

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
         continue

         print "\t", path.get_access_flag(), "%s (%d-%d)" % (path.get_bb().get_name(), path.get_bb().get_start(), path.get_bb().get_end()) , path.get_bb().get_start() + path.get_idx(), 
         x = _analysis.get( path.get_bb().get_method() )

         bb = x.get_break_block( path.get_bb().get_start() + path.get_idx() )

         print "\t\t", x.get_local_variables()

         if path.get_access_flag() == "R" and find == False :
            o = self.add_offset( _analysis.prev_free_block_offset( path.get_method(), bb.get_start() ) )
      
            val = _analysis.next_free_block_offset( path.get_method(), o.get_idx() ) 

            if o.get_idx() == -1 or val == -1 :
               raise("ooop")

            #try :
            #   list_OB[ path.get_method() ].append( o, [ [ "iload_3" ], [ "iconst_0" ], [ "if_icmpge", val - o.get_idx() + 3 ] ] )
            #except KeyError :
            #   list_OB[ path.get_method() ] = []
            #   list_OB[ path.get_method() ].append( (o, [ [ "iload_3" ], [ "iconst_0" ], [ "if_icmpge", val - o.get_idx() + 3 ] ] ) )

            find = True

      ##### Insert all modifications
      for m in list_OB :
         code = m.get_code()

         i = 0
         while i < len( list_OB[ m ] ) :
            v = list_OB[ m ][ i ]

            print "INSERT ", v[0].get_idx(), v[1] 

            size_r = code.inserts_at( code.get_relative_idx( v[0].get_idx() ), v[1] )
            #code.show()

            j = i + 1
            while j < len( list_OB[ m ] ) :
               v1 = list_OB[ m ][ j ]
               if v1[0].get_idx() >= v[0].get_idx() :
                  v1[0].add_idx( size_r )
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
   def __init__(self, _vm, _analysis) :
      self.__vm = _vm
      self.__analysis = _analysis

      self.__vm_generate = self.__vm.get_generator()( self.__vm, self.__analysis )

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
         i.run( self.__vm, self.__analysis, self.__vm_generate )

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
