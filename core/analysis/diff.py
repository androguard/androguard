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

import hashlib

from error import error
from similarity import *


# Lorg/t0t0/androguard/TC/TCMod1; ()V,T1
#96 0x17e aget-object v4 , v6 , v8
#97 0x182 aget v5 , v8 , v8
#98 0x186 add-int/lit8 v8 , v8 , [#+ 1]
#99 0x18a add-int/2addr v7 , v8
#100 0x18c iput v7 , v12 , [field@ 14 Lorg/t0t0/androguard/TC/TCMod1; I TC1]
#101 0x190 add-int/lit8 v5 , v5 , [#+ 1]
#102 0x194 goto [+ -18]
#103 0x196 add-int/lit8 v4 , v4 , [#+ 1]
#104 0x19a goto [+ -25]

#96 0x17e aget-object v4 , v6 , v8
#97 0x182 aget v5 , v8 , v8
#98 0x186 add-int/2addr v7 , v8
#99 0x188 iput v7 , v12 , [field@ 14 Lorg/t0t0/androguard/TC/TCMod1; I TC1]
#100 0x18c add-int/lit8 v5 , v5 , [#+ 1]
#101 0x190 goto [+ -16]
#102 0x192 add-int/lit8 v4 , v4 , [#+ 1]
#103 0x196 goto [+ -23]
#104 0x198 new-instance v0 , [type@ 20 Lorg/t0t0/androguard/TC/TCA;]

def filter_ins_1( ins ) :
   return "%s%s" % (ins.get_name(), ins.get_operands())

def filter_sim_1( m1, m2, sim, name_attribute ) :
   e1 = getattr( m1, "entropy_" + name_attribute )
   e2 = getattr( m2, "entropy_" + name_attribute )

   ncd = sim.ncd( getattr(m1, name_attribute), getattr(m2, name_attribute) )

   return (max(e1, e2) - min(e1, e2)) + ncd

class CheckSum :
   def __init__(self, basic_block) :
      self.basic_block = basic_block
      self.buff = ""
      for i in basic_block.ins : 
         self.buff += i.get_name()

      self.hash = hashlib.sha256( self.buff ).hexdigest()

def filter_checksum_1( basic_block ) :
   return CheckSum( basic_block )

#   raise("ooo")


FILTER_NAME = "FILTER_NAME"
FILTER_INS = "FILTER_INS"
FILTER_SIM = "FILTER_SIM"
FILTER_CHECKSUM = "FILTER_CHECKSUM"
FILTERS = {
               "FILTER_1" : { FILTER_INS : filter_ins_1, FILTER_SIM : filter_sim_1, FILTER_CHECKSUM : filter_checksum_1 },
          }

class Method :
   def __init__(self, m, mx, sim) :
      self.m = m
      self.mx = mx
      self.sim = sim

   def add_attribute(self, name, func_ins, func_bb) :
      buff = ""

      bb = {}
      bbhash = {}

      code = self.m.get_code()
      bc = code.get_bc()
     
      for i in bc.get() :
         buff += func_ins( i )

      for i in self.mx.basic_blocks.get() :
         bb[ i.name ] = func_bb( i )
         bbhash[ bb[ i.name ].hash ] = bb[ i.name ]

      setattr(self, name, buff)

      setattr(self, "bb_" + name, bb)
      setattr(self, "bb_sha256_" + name, bbhash)
      setattr(self, "sha256_" + name, hashlib.sha256( buff ).hexdigest())
      setattr(self, "entropy_" + name, self.sim.entropy( buff ))
      
   def similarity(self, new_method, func, name_attribute) :
      x = None
      try :
         x = getattr( self, "hash_" + name_attribute )
      except AttributeError :
         setattr( self, "hash_" + name_attribute, {} )
         x = getattr( self, "hash_" + name_attribute )

      x[ new_method ] = func( self, new_method, self.sim, name_attribute )

   def sort(self, name_attribute, nb) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(), getattr( self, "entropy_" + name_attribute )

      x = getattr( self, "hash_" + name_attribute )

      z = sorted(x.iteritems(), key=lambda (k,v): (v,k))[ : nb ]

      for i in z :
         print "\t", i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), getattr( i[0], "entropy_" + name_attribute ), i[1]
         #e1 = getattr( self, "entropy_" + name_attribute )
         #e2 = getattr( i[0], "entropy_" + name_attribute )

         #if e1 != e2 :
         #print "\t", i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), getattr( i[0], "entropy_" + name_attribute ), i[1]

      setattr( self, "sort_" + name_attribute, z )

   def checksort(self, name_attribute, method) :
      z = getattr( self, "sort_" + name_attribute )
      for i in z :
         if method == i[0] :
            return True

      return False
   
   def diff(self, name_attribute):
      self.sim.set_compress_type( XZ_COMPRESS )

      z = getattr( self, "sort_" + name_attribute )
      
      bb1 = getattr( self, "bb_" + name_attribute )
      
      for b1 in bb1 :
         print b1, "0x%x" % bb1[ b1 ].basic_block.end
         for i in z :
            bb2 = getattr( i[0], "bb_" + name_attribute )
            b_z = {}

            bb2hash = getattr( i[0], "bb_sha256_" + name_attribute )
            
            if bb1[ b1 ].hash in bb2hash :
               b_z[ bb2hash[ bb1[ b1 ].hash ].basic_block.name ] = 0.0

            else :
               for b2 in bb2 :
                  #e1 = self.sim.entropy( bb1[ b1 ].buff )
                  #e2 = self.sim.entropy( bb2[ b2 ].buff )
               
                  #m = max(e1, e2) - min(e2, e1)
                  b_z[ b2 ] = self.sim.ncd( bb1[ b1 ].buff, bb2[ b2 ].buff )

            print "\t", sorted(b_z.iteritems(), key=lambda (k,v): (v,k))[ : 2]

      #h = [ i for i in self.mx.basic_blocks.get() ]
#      for val in self.diff_4( self.m ) :
#         print val
#
#      l = self.diff_4( self.m )
#      for i in z :
#         print "\t", self.diff_4( i[0].m, l )

   def diff_4(self, m) :
      code = m.get_code()
      bc = code.get_bc()
      
      l = []
      j = 0
      buff = ""
      for i in bc.get() :
         if j != 0 and j % 4 == 0 :
            yield self.sim.entropy( buff ), j
            buff = ""

         buff += i.get_name()
         buff += "%s" % i.get_operands()

         j += 1

   def diff_5(self, m, ref) :
      code = m.get_code()
      bc = code.get_bc()

      l = []
      j = 0
      buff = ""
      for i in bc.get() :
         if j != 0 and j % 4 == 0 :
            l.append( self.sim.entropy( buff ) )
            buff = ""

         buff += i.get_name()
         buff += "%s" % i.get_operands()

         j += 1
      return l

   def getsha256(self, name_attribute) :
      return getattr(self, "sha256_" + name_attribute)

   def show(self) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor()

BASE = "base"
METHODS = "methods"
HASHSUM = "hashsum" 
DIFFMETHODS = "diffmethods"
NEWMETHODS = "newmethods"
class Diff :
   def __init__(self, vm1, vm2) :
      self.vms = [ vm1, vm2 ]
      self.sim = SIMILARITY( "classification/libsimilarity/libsimilarity.so" )
      self.sim.set_compress_type( XZ_COMPRESS )

      self.filters = {}

      for i in FILTERS :
         self.filters[ i ] = {}
         self.filters[ i ][ BASE ] = { FILTER_NAME : i }
         self.filters[ i ][ BASE ].update( FILTERS[ i ] )
         self.filters[ i ][ METHODS ] = {}
         self.filters[ i ][ HASHSUM ] = {}
         self.filters[ i ][ DIFFMETHODS ] = []
         self.filters[ i ][ NEWMETHODS ] = []

      for i in self.vms :
         for m in i.get_vm().get_methods() :
            m = Method( m, i.get_analysis().hmethods[ m ], self.sim ) 

            for fil in self.filters :
               if i not in self.filters[fil][METHODS] :
                  self.filters[fil][METHODS][ i ] = []
                  self.filters[fil][HASHSUM][ i ] = []
        
               self.filters[fil][METHODS][ i ].append( m )

               m.add_attribute( self.filters[fil][BASE][FILTER_NAME], self.filters[fil][BASE][FILTER_INS], self.filters[fil][BASE][FILTER_CHECKSUM] )
               
               self.filters[fil][HASHSUM][i].append( m.getsha256( self.filters[fil][BASE][FILTER_NAME] ) )

      
      # Check if some methods in the first file has been modified
      for fil in self.filters :
         for j in self.filters[fil][METHODS][vm1] :
            for i1 in self.filters[fil][METHODS] :
               if j.getsha256( self.filters[fil][BASE][FILTER_NAME] ) in self.filters[fil][HASHSUM][i1] :
                  continue

               for k in self.filters[fil][METHODS][i1] :
                  j.similarity( k, self.filters[fil][BASE][FILTER_SIM], self.filters[fil][BASE][FILTER_NAME] )
                  if j not in self.filters[fil][DIFFMETHODS] :
                     self.filters[fil][DIFFMETHODS].append(j)
      
      print "DIFF METHODS"
      for fil in self.filters :
         for j in self.filters[fil][DIFFMETHODS] :
            print j
            j.sort( self.filters[fil][BASE][FILTER_NAME], 1 )
            j.diff( self.filters[fil][BASE][FILTER_NAME] )

      # Check if some methods in the second file are totally new !
      for fil in self.filters :
         for j in self.filters[fil][METHODS][vm2] :
            for i1 in self.filters[fil][METHODS] :
               if j.getsha256( self.filters[fil][BASE][FILTER_NAME] ) in self.filters[fil][HASHSUM][i1] :
                  continue
           
               if j not in self.filters[fil][NEWMETHODS] :
                  ok = True
                  for diff_method in self.filters[fil][DIFFMETHODS] :
                     if diff_method.checksort( self.filters[fil][BASE][FILTER_NAME], j ) :
                        ok = False
                        break
                  if ok :
                     self.filters[fil][NEWMETHODS].append( j )

      print "NEW METHODS"
      for fil in self.filters :
         print "\t", self.filters[fil][NEWMETHODS]
