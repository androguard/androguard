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

def filter_ins( ins ) :
   return "%s%s" % (ins.get_name(), ins.get_operands())

FILTERS = [ 
            ("FILTER_1", filter_ins),

          ]


class Method :
   def __init__(self, m, mx, sim) :
      self.m = m
      self.mx = mx
      self.sim = sim

   def add_attribute(self, name, func) :
      buff = ""

      code = self.m.get_code()
      bc = code.get_bc()
     
      for i in bc.get() :
         buff += func( i )

      setattr(self, name, buff)
      setattr(self, "sha256_" + name, hashlib.sha256( buff ).hexdigest())
      setattr(self, "entropy_" + name, self.sim.entropy( buff ))
      
   def similarity(self, new_method, name_attribute) :
      x = None
      try :
         x = getattr( self, "hash_" + name_attribute )
      except AttributeError :
         setattr( self, "hash_" + name_attribute, {} )
         x = getattr( self, "hash_" + name_attribute )

      x[ new_method ] = self.sim.ncd( getattr(self, name_attribute), getattr(new_method, name_attribute) )

   def sort(self, name_attribute, nb) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(), getattr( self, "entropy_" + name_attribute )

      x = getattr( self, "hash_" + name_attribute )

      z = sorted(x.iteritems(), key=lambda (k,v): (v,k))[ : nb ]

      for i in z :
         e1 = getattr( self, "entropy_" + name_attribute )
         e2 = getattr( i[0], "entropy_" + name_attribute )

         #if e1 != e2 :
         print "\t", i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), getattr( i[0], "entropy_" + name_attribute ), i[1]

   def getsha256(self, name_attribute) :
      return getattr(self, "sha256_" + name_attribute)

   def show(self) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor()

class Diff :
   def __init__(self, vm1, vm2) :
      self.vms = [ vm1, vm2 ]
      self.sim = SIMILARITY( "classification/libsimilarity/libsimilarity.so" )
      self.sim.set_compress_type( XZ_COMPRESS )
      self.methods = {}
      self.hashsum = {}
      
      self.diffmethods = []

      
      for i in self.vms :
         self.methods[ i ] = []
         self.hashsum[ i ] = [] 
         for m in i.get_vm().get_methods() :
            m = Method( m, i.get_analysis().hmethods[ m ], self.sim ) 
            self.methods[ i ].append( m ) 
            m.add_attribute( "filter_buff_1", filter_ins )
            self.hashsum[i].append( m.getsha256( "filter_buff_1" ) ) 

      for j in self.methods[vm1] :
         for i1 in self.methods :
            if j.getsha256( "filter_buff_1" ) in self.hashsum[i1] :
               continue

            for k in self.methods[i1] :
               j.similarity( k, "filter_buff_1" )
               if j not in self.diffmethods :
                  self.diffmethods.append(j)

      for j in self.diffmethods :
         j.sort( "filter_buff_1", 3 )
