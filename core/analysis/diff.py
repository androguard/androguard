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

import bytecode

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

def filter_sim_2( m1, m2, sim, name_attribute ) :
   ncd1 = sim.ncd( m1.vmx.get_method_signature( m1.m, 1 ), m2.vmx.get_method_signature( m2.m, 1 ) )
   ncd2 = sim.ncd( getattr(m1, name_attribute), getattr(m2, name_attribute) )

   return (ncd1 + ncd2) / 2.0

def filter_sim_bb_1( bb1, bb2, sim, name_attribute ) :
   ncd = sim.ncd( bb1.buff, bb2.buff )

   return ncd

class CheckSum :
   def __init__(self, basic_block) :
      self.basic_block = basic_block
      self.buff = ""
      for i in basic_block.ins : 
         self.buff += i.get_name()

      #self.hash = hashlib.sha256( self.buff + "%d%d" % (len(basic_block.childs), len(basic_block.fathers)) ).hexdigest()
      self.hash = hashlib.sha256( self.buff ).hexdigest()

def filter_checksum_1( basic_block ) :
   return CheckSum( basic_block )

def LCS(X, Y):
     m = len(X)
     n = len(Y)
     # An (m+1) times (n+1) matrix
     C = [[0] * (n+1) for i in range(m+1)]
     for i in range(1, m+1):
         for j in range(1, n+1):
             if X[i-1] == Y[j-1]: 
                 C[i][j] = C[i-1][j-1] + 1
             else:
                 C[i][j] = max(C[i][j-1], C[i-1][j])
     return C

def getDiff(C, X, Y, i, j, a, r):
     if i > 0 and j > 0 and X[i-1] == Y[j-1]:
         getDiff(C, X, Y, i-1, j-1, a, r)
         print "DEBUG   " + "%02X" % ord(X[i-1])
     else:
         if j > 0 and (i == 0 or C[i][j-1] >= C[i-1][j]):
             getDiff(C, X, Y, i, j-1, a, r)
             a.append( (j-1, Y[j-1]) )
             print "DEBUG + " + "%02X" % ord(Y[j-1])
         elif i > 0 and (j == 0 or C[i][j-1] < C[i-1][j]):
             getDiff(C, X, Y, i-1, j, a, r)
             r.append( (i-1, X[i-1]) )
             print "DEBUG - " + "%02X" % ord(X[i-1])

def toString( bb, hS, rS ) :
   S = ""

   for i in bb.ins :
      ident = i.get_name()
      for op in i.get_operands() :
         if "#" in op[0] :
            ident += "%s" % op

#      print i.get_name(), i.get_operands()
      if ident not in hS :
         hS[ ident ] = len(hS)
         rS[ chr( hS[ ident ] ) ] = ident

      S += chr( hS[ ident ] )

   return S

class DiffBB :
   def __init__(self, bb1, bb2) :
      self.bb1 = bb1
      self.bb2 = bb2

      self.name = self.bb1.name

      self.di = None
      self.ins = []

   def diff_ins(self, di) :
      self.di = di

      off_add = {}
      off_rm = {}
      for i in self.di.add_ins :
         off_add[ i[0] ] = i

      for i in self.di.remove_ins :
         off_rm[ i[0] ] = i

      nb = 0
      for i in self.bb1.ins :
         ok = False
         if nb in off_add :
            print nb, "ADD", off_add[ nb ][2].get_name(), off_add[ nb ][2].get_operands()
            self.ins.append( off_add[ nb ][2] )
            setattr( off_add[ nb ][2], "tag", 1 )
            del off_add[ nb ]

         if nb in off_rm :
            print nb, "RM", off_rm[ nb ][2].get_name(), off_rm[ nb ][2].get_operands()
            self.ins.append( off_rm[ nb ][2] )
            setattr( off_rm[ nb ][2], "tag", 2 )
            del off_rm[ nb ]
            ok = True

         if ok == False :
            self.ins.append( i ) 
            print nb, i.get_name(), i.get_operands()

            setattr( i, "tag", 0 )

         nb += 1

   def show(self) :
      print "\tADD INSTRUCTIONS :"
      for i in self.di.add_ins :
         print "\t\t", i[0], i[1], i[2].get_name(), i[2].get_operands()

      print "\tREMOVE INSTRUCTIONS :"
      for i in self.di.remove_ins :
         print "\t\t", i[0], i[1], i[2].get_name(), i[2].get_operands()

class NewBB :
   def __init__(self, bb) :
      self.bb = bb

class DiffINS :
   def __init__(self, add_ins, remove_ins) :
      self.add_ins = add_ins
      self.remove_ins = remove_ins

def filter_diff_ins_1( dbb, sim, name_attribute ) :
   final_add = []
   final_rm = []

   hS = {}
   rS = {}

   X = toString( dbb.bb1, hS, rS )
   print
   Y = toString( dbb.bb2, hS, rS )

   print "DEBUG", repr(X), len(X)
   print "DEBUG", repr(Y), len(Y)

   m = len(X)
   n = len(Y)

   C = LCS( X, Y )
   a = []
   r = []

   getDiff(C, X, Y, m, n, a, r)
   print "DEBUG", a, r

   print "DEBUG ADD"
   for i in a :
      print "DEBUG \t", i[0], dbb.bb2.ins[ i[0] ].get_name(), dbb.bb2.ins[ i[0] ].get_operands()
      final_add.append( (i[0], 0, dbb.bb2.ins[ i[0] ]) )

   print "DEBUG REMOVE"
   for i in r :
      print "DEBUG \t", i[0], dbb.bb1.ins[ i[0] ].get_name(), dbb.bb1.ins[ i[0] ].get_operands()
      final_rm.append( (i[0], 0, dbb.bb1.ins[ i[0] ]) )

   dbb.diff_ins( DiffINS( final_add, final_rm ) )

FILTER_NAME = "FILTER_NAME"
FILTER_INS = "FILTER_INS"
FILTER_SIM = "FILTER_SIM"
FILTER_CHECKSUM = "FILTER_CHECKSUM"
FILTER_SIM_BB = "FILTER_SIM_BB"
FILTER_DIFF_INS = "FILTER_DIFF_INS"
FILTERS = {
               "FILTER_1" : { FILTER_INS : filter_ins_1, 
                              FILTER_SIM : filter_sim_2, 
                              FILTER_SIM_BB : filter_sim_bb_1,
                              FILTER_DIFF_INS : filter_diff_ins_1,
                              FILTER_CHECKSUM : filter_checksum_1 
                            },
          }

class Method :
   def __init__(self, vm, vmx, m, sim) :
      self.m = m
      self.vm = vm
      self.vmx = vmx
      self.mx = vmx.get_method( m )

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
         
         try :
            bbhash[ bb[ i.name ].hash ].append( bb[ i.name ] )
         except KeyError :
            bbhash[ bb[ i.name ].hash ] = []
            bbhash[ bb[ i.name ].hash ].append( bb[ i.name ] )

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
   
   def diff(self, name_attribute, func_sim_bb, func_diff_ins):
      self.sim.set_compress_type( XZ_COMPRESS )

      z = getattr( self, "sort_" + name_attribute )
      bb1 = getattr( self, "bb_" + name_attribute )
      
      diff_bb = {}
      direct_diff_bb = []
      new_bb = {}

      for b1 in bb1 :
         diff_bb[ bb1[ b1 ] ] = {}
         print b1, "0x%x" % bb1[ b1 ].basic_block.end
         for i in z :
            bb2 = getattr( i[0], "bb_" + name_attribute )
            b_z = diff_bb[ bb1[ b1 ] ] 

            bb2hash = getattr( i[0], "bb_sha256_" + name_attribute )
            
            if bb1[ b1 ].hash in bb2hash :
               for equal_bb in bb2hash[ bb1[ b1 ].hash ] :
                  b_z[ equal_bb.basic_block.name ] = 0.0 
            else :
               for b2 in bb2 :
                  b_z[ b2 ] = func_sim_bb( bb1[ b1 ], bb2[ b2 ], self.sim, name_attribute )

            sorted_bb = sorted(b_z.iteritems(), key=lambda (k,v): (v,k))
            
            print "\t", sorted_bb[:2]

            for new_diff in sorted_bb :
               if new_diff[1] == 0.0 :
                  direct_diff_bb.append( new_diff[0] )
          
            if sorted_bb[0][1] != 0.0 :
               diff_bb[ bb1[ b1 ] ] = (bb2[ sorted_bb[0][0] ], sorted_bb[0][1])
               direct_diff_bb.append( sorted_bb[0][0] )
            else :
               del diff_bb[ bb1[ b1 ] ]

      for i in z :
         bb2 = getattr( i[0], "bb_" + name_attribute )
         for b2 in bb2 :
            if b2 not in direct_diff_bb :
               new_bb[ b2 ] = bb2[ b2 ]

      dbb = {}
      nbb = {}
      # Add all different basic blocks 
      for d in diff_bb :
         dbb[ d.basic_block.name ] = DiffBB( d.basic_block, diff_bb[ d ][0].basic_block )
      # Add all new basic blocks
      for n in new_bb :
         nbb[ new_bb[ n ].basic_block ] = NewBB( new_bb[ n ].basic_block )

      setattr(self, "dbb_" + name_attribute, dbb)
      setattr(self, "nbb_" + name_attribute, nbb)
     
      # Found diff instructions
      for d in dbb :
         func_diff_ins( dbb[d], self.sim, name_attribute )

   def getsha256(self, name_attribute) :
      return getattr(self, "sha256_" + name_attribute)

   def show(self, name_attribute) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor()

      dbb = getattr(self, "dbb_" + name_attribute)
      nbb = getattr(self, "nbb_" + name_attribute)

      print "DIFF_BB"
      for d in dbb :
         print "\t", dbb[d].bb1.name, " --->", dbb[d].bb2.name
         dbb[d].show()

      print "NEW_BB", nbb

      paths = []
      for i in self.mx.basic_blocks.get() :
         val = 0 
         if len(i.childs) > 1 :
            val = 1
         elif len(i.childs) == 1 :
            val = 2

         for j in i.childs :
            paths.append( ( j[0], j[1], val ) )
            if val == 1 :
               val = 0

      print paths

      for d in dbb :
         print dbb[d].bb2.childs

      bytecode.PrettyShow3( self.mx.basic_blocks.get() )

      raise("ooo")

      l = []
      for bb in self.mx.basic_blocks.get() :
         if bb.name not in dbb :
            l.append( bb )
         else :
            l.append( dbb[ bb.name ] )

      bytecode.PrettyShow4( l )

      raise("ooo")
#      nb = 0
#      idx = 0
#      for bb in self.mx.basic_blocks.get() :
#         if bb.name not in dbb :
#            for i in bb.ins :
#               bytecode.PrettyShow2( idx, nb, i, 0 )
#               idx += ( i.get_length() )
#               nb += 1
#         else :
#            for i in dbb[ bb.name ].ins :
#               bytecode.PrettyShow2( idx, nb, i, i.tag )
              
#               if i.tag == 0 or i.tag == 2 :
#                  idx += ( i.get_length() )
#                  nb += 1

      #nb = 0
      #idx = 0
      #for i in self.__bytecodes :
      #   bytecode.PrettyShow( idx, paths, nb, i )                                                                                                                                                                                 
      #   idx += ( i.get_length() )
      #   nb += 1


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
            m = Method( i.get_vm(), i.get_analysis(), m, self.sim ) 

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
            j.diff( self.filters[fil][BASE][FILTER_NAME], self.filters[fil][BASE][FILTER_SIM_BB], self.filters[fil][BASE][FILTER_DIFF_INS] )
            j.show( self.filters[fil][BASE][FILTER_NAME] )

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
