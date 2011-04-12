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


from error import error
from similarity import *

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
      setattr(self, "entropy_" + name, self.sim.entropy( buff ))

   def similarity(self, new_method, name_attribute) :
      x = getattr( self, "hash_" + name_attribute )

      x[ new_method ] = self.sim.ncd( getattr(self, name_attribute), getattr(new_method, name_attribute) )

      setattr(self, "hash_" + name_attribute, x)

   def show(self) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(), self.entropy

class Diff :
   def __init__(self, vms) :
      self.vms = vms
      self.sim = SIMILARITY( "classification/libsimilarity/libsimilarity.so" )
      self.methods = {} 

      for i in self.vms :
         self.methods[ i ] = []
         for m in i.get_vm().get_methods() :
            m = Method( m, i.get_analysis().hmethods[ m ], self.sim ) 
            self.methods[ i ].append( m ) 
            m.add_attribute( "filter_buff_1", filter_ins )

      for i in self.methods :
         for j in self.methods[i] :
            for i1 in self.methods :
               if i1 != i :
                  for k in self.methods[i1] :
                     j.similarity( k, "filter_buff_1" )
