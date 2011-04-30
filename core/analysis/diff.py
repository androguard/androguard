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

DEBUG = 0

def filter_meth_1( m1 ) :
   code = m1.get_code()
   bc = code.get_bc()
      
   buff = "" #m1.get_class_name() + m1.get_name() + m1.get_descriptor()

   for i in bc.get() :
      buff += "%s" % i.get_name()
      if i.type_ins_tag == 0 :
         for op in i.get_operands() :
            if "#" in op[0] :
               buff += "%s" % op
   
   return buff

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
         if DEBUG :
            print "DEBUG   " + "%02X" % ord(X[i-1])
     else:
         if j > 0 and (i == 0 or C[i][j-1] >= C[i-1][j]):
             getDiff(C, X, Y, i, j-1, a, r)
             a.append( (j-1, Y[j-1]) )
             if DEBUG :
               print "DEBUG + " + "%02X" % ord(Y[j-1])
         elif i > 0 and (j == 0 or C[i][j-1] < C[i-1][j]):
             getDiff(C, X, Y, i-1, j, a, r)
             r.append( (i-1, X[i-1]) )
             if DEBUG :
               print "DEBUG - " + "%02X" % ord(X[i-1])

def toString( bb, hS, rS ) :
   S = ""

   for i in bb.ins :
      ident = i.get_name()
      for op in i.get_operands() :
         if i.type_ins_tag == 0 :
            if "#" in op[0] :
               ident += "%s" % op

#      print i.get_name(), i.get_operands()
      if ident not in hS :
         hS[ ident ] = len(hS)
         rS[ chr( hS[ ident ] ) ] = ident

      S += chr( hS[ ident ] )

   return S

DIFF_INS_TAG = {
                  "ORIG" : 0,
                  "ADD" : 1,
                  "REMOVE" : 2
               }

class DiffBB :
   def __init__(self, bb1, bb2, info) :
      self.bb1 = bb1
      self.bb2 = bb2
      self.info = info

      self.start = self.bb1.start
      self.end = self.bb1.end
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
            if DEBUG :
               print nb, "ADD", off_add[ nb ][2].get_name(), off_add[ nb ][2].get_operands()
            self.ins.append( off_add[ nb ][2] )
            setattr( off_add[ nb ][2], "diff_tag", DIFF_INS_TAG["ADD"] )
            del off_add[ nb ]

         if nb in off_rm :
            if DEBUG : 
               print nb, "RM", off_rm[ nb ][2].get_name(), off_rm[ nb ][2].get_operands()
            self.ins.append( off_rm[ nb ][2] )
            setattr( off_rm[ nb ][2], "diff_tag", DIFF_INS_TAG["REMOVE"] )
            del off_rm[ nb ]
            ok = True

         if ok == False :
            self.ins.append( i ) 
            if DEBUG :
               print nb, i.get_name(), i.get_operands()

            setattr( i, "diff_tag", DIFF_INS_TAG["ORIG"] )

         nb += 1

      #print nb, off_add, off_rm

      nbmax = nb
      if off_add != {} :
         nbmax = sorted(off_add)[-1]
      if off_rm != {} :
         nbmax = max(nbmax, sorted(off_rm)[-1])

      while nb <= nbmax :
         if nb in off_add :
            if DEBUG :
               print nb, "ADD", off_add[ nb ][2].get_name(), off_add[ nb ][2].get_operands()
            self.ins.append( off_add[ nb ][2] )
            setattr( off_add[ nb ][2], "diff_tag", DIFF_INS_TAG["ADD"] )
            del off_add[ nb ]

         if nb in off_rm :
            if DEBUG : 
               print nb, "RM", off_rm[ nb ][2].get_name(), off_rm[ nb ][2].get_operands()
            self.ins.append( off_rm[ nb ][2] )
            setattr( off_rm[ nb ][2], "diff_tag", DIFF_INS_TAG["REMOVE"] )
            del off_rm[ nb ]
            
         nb += 1

      #print off_add, off_rm

   def set_childs(self, abb) :
      setattr( self.bb1.ins[-1], "childs", self.bb1.childs )

      for i in self.ins :
         if i == self.bb2.ins[-1] :

            childs = []
            for c in self.bb2.childs :
               if c[2].name in abb :
                  if DEBUG :
                     print "SET", c[2], abb[ c[2].name ]
                  childs.append( (c[0], c[1], abb[ c[2].name ]) )
               else :
                  if DEBUG :
                     print "SET ORIG", c
                  childs.append( c )

            setattr( i, "childs", childs )

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

      self.start = self.bb.start
      self.end = self.bb.end
      self.name = self.bb.name
      self.ins = self.bb.ins

   def set_childs(self, abb) :
      childs = []
      for c in self.bb.childs :
         if c[2].name in abb :
            if DEBUG :
               print "SET", c[2], abb[ c[2].name ]
            childs.append( (c[0], c[1], abb[ c[2].name ]) )
         else :
            if DEBUG :
               print "SET ORIG", c
            childs.append( c )

      setattr( self, "childs", childs )

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
   Y = toString( dbb.bb2, hS, rS )

   if DEBUG :
      print "DEBUG", repr(X), len(X)
      print "DEBUG", repr(Y), len(Y)

   m = len(X)
   n = len(Y)

   C = LCS( X, Y )
   a = []
   r = []

   getDiff(C, X, Y, m, n, a, r)
   if DEBUG :
      print "DEBUG", a, r

   if DEBUG :
      print "DEBUG ADD"
   for i in a :
      if DEBUG :
         print "DEBUG \t", i[0], dbb.bb2.ins[ i[0] ].get_name(), dbb.bb2.ins[ i[0] ].get_operands()
      final_add.append( (i[0], 0, dbb.bb2.ins[ i[0] ]) )

   if DEBUG :
      print "DEBUG REMOVE"
   for i in r :
      if DEBUG :
         print "DEBUG \t", i[0], dbb.bb1.ins[ i[0] ].get_name(), dbb.bb1.ins[ i[0] ].get_operands()
      final_rm.append( (i[0], 0, dbb.bb1.ins[ i[0] ]) )

   dbb.diff_ins( DiffINS( final_add, final_rm ) )

FILTER_NAME = "FILTER_NAME"
FILTER_METH = "FILTER_METH"
FILTER_SIM = "FILTER_SIM"
FILTER_CHECKSUM = "FILTER_CHECKSUM"
FILTER_SIM_BB = "FILTER_SIM_BB"
FILTER_DIFF_INS = "FILTER_DIFF_INS"

FILTERS = {
               "FILTER_1" : { FILTER_METH : filter_meth_1, 
                              FILTER_SIM : filter_sim_2, 
                              FILTER_SIM_BB : filter_sim_bb_1,
                              FILTER_DIFF_INS : filter_diff_ins_1,
                              FILTER_CHECKSUM : filter_checksum_1 
                            },
          }

DIFF_BB_TAG = { 
                  "ORIG" : 0,
                  "DIFF" : 1,
                  "NEW"  : 2
              }

class Method :
   def __init__(self, vm, vmx, m, sim) :
      self.m = m
      self.vm = vm
      self.vmx = vmx
      self.mx = vmx.get_method( m )

      self.sim = sim
      
   #######
   # Attribute :
   #    Method <-> sorted Methods 
   #
   #    Method <-> Methods[0] :
   #            
   #
   #
   #
   def add_attribute(self, name, func_meth, func_checksum_bb) :
      bb = {}
      bbhash = {}

      buff = func_meth( self.m )

      for i in self.mx.basic_blocks.get() :
         bb[ i.name ] = func_checksum_bb( i )
         
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

   def sort(self, name_attribute) :
      x = getattr( self, "hash_" + name_attribute )

      z = sorted(x.iteritems(), key=lambda (k,v): (v,k))

      #for i in z :
      #   print "\t", i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), i[1]

      setattr( self, "sort_" + name_attribute, z[:1] )

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
     
      ### Dict for diff basic blocks
         ### vm1 basic block : vm2 basic blocks -> value (0.0 to 1.0)
      diff_bb = {}

      ### List to get directly all diff basic blocks
      direct_diff_bb = []

      ### Dict for new basic blocks
      new_bb = {}

      ### Reverse Dict with matches diff basic blocks
      associated_bb = {}

      for b1 in bb1 :
         diff_bb[ bb1[ b1 ] ] = {}
         if DEBUG :
            print "DEBUG", b1, "0x%x" % bb1[ b1 ].basic_block.end
         for i in z :
            bb2 = getattr( i[0], "bb_" + name_attribute )
            b_z = diff_bb[ bb1[ b1 ] ] 

            bb2hash = getattr( i[0], "bb_sha256_" + name_attribute )
      
            # If b1 is in bb2 :
               # we can have one or more identical basic blocks to b1, we must add them
            if bb1[ b1 ].hash in bb2hash :
               for equal_bb in bb2hash[ bb1[ b1 ].hash ] :
                  b_z[ equal_bb.basic_block.name ] = 0.0 

            # If b1 is not in bb2 :
               # we must check similarities between all bb2
            else :
               for b2 in bb2 :
                  b_z[ b2 ] = func_sim_bb( bb1[ b1 ], bb2[ b2 ], self.sim, name_attribute )

            sorted_bb = sorted(b_z.iteritems(), key=lambda (k,v): (v,k))
             
            if DEBUG :
               print "\tDEBUG", sorted_bb[:2]

            for new_diff in sorted_bb :
               associated_bb[ new_diff[0] ] = bb1[ b1 ].basic_block

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
         dbb[ d.basic_block.name ] = DiffBB( d.basic_block, diff_bb[ d ][0].basic_block, diff_bb[ d ] )

      # Add all new basic blocks
      for n in new_bb :
         nbb[ new_bb[ n ].basic_block ] = NewBB( new_bb[ n ].basic_block )
         del associated_bb[ n ] 

      setattr(self, "dbb_" + name_attribute, dbb)
      setattr(self, "nbb_" + name_attribute, nbb)
     
      # Found diff instructions
      for d in dbb :
         func_diff_ins( dbb[d], self.sim, name_attribute )

      # Set new childs for diff basic blocks
         # The instructions will be tag with a new flag "childs"
      for d in dbb :
         dbb[ d ].set_childs( associated_bb )

      # Set new childs for new basic blocks
      for d in nbb :
         nbb[ d ].set_childs( associated_bb )

      # Create and tag all (orig/diff/new) basic blocks
      self.create_bbs( name_attribute )

   def create_bbs(self, name_attribute) :
      dbb = getattr(self, "dbb_" + name_attribute)
      nbb = getattr(self, "nbb_" + name_attribute)
      
      # For same block : 
         # tag = 0
      # For diff block :
         # tag = 1
      # For new block :
         # tag = 2
      l = []
      for bb in self.mx.basic_blocks.get() :
         if bb.name not in dbb :
            # add the original basic block
            setattr( bb, "bb_tag", DIFF_BB_TAG["ORIG"] )
            l.append( bb )
         else :
            # add the diff basic block
            setattr( dbb[ bb.name ], "bb_tag", DIFF_BB_TAG["DIFF"] )
            l.append( dbb[ bb.name ] )

      for i in nbb :
         # add the new basic block
         setattr( nbb[ i ], "bb_tag", DIFF_BB_TAG["NEW"] )
         l.append( nbb[ i ] )

      # Sorted basic blocks by addr (orig, new, diff)
      l = sorted(l, key = lambda x : x.start)
      setattr( self, "bbs_" + name_attribute, l ) 
     
   def getsha256(self, name_attribute) :
      return getattr(self, "sha256_" + name_attribute)

   def show(self, name_attribute, details=False) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(),
      print "with",

      z = getattr( self, "sort_" + name_attribute )
      for i in z :
         print i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), i[1]

      dbb = getattr(self, "dbb_" + name_attribute)
      nbb = getattr(self, "nbb_" + name_attribute)

      print "\tDIFF BASIC BLOCKS :"
      for d in dbb :
         print "\t\t", dbb[d].bb1.name, " --->", dbb[d].bb2.name, ":", dbb[d].info[1]
         if details :
            dbb[d].show()

      print "NEW BASIC BLOCKS :"
      for b in nbb :
         print "\t\t", nbb[b].name

      if details :
      # show diff !
         bytecode.PrettyShow2( getattr(self, "bbs_" +name_attribute) )

   def show2(self, details=False) :
      print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor()
      if details :
         bytecode.PrettyShow1( self.mx.basic_blocks.get() )

BASE = "base"
METHODS = "methods"
HASHSUM = "hashsum" 
DIFFMETHODS = "diffmethods"
NEWMETHODS = "newmethods"
class Diff :
   def __init__(self, vm1, vm2, F=FILTERS) :
      self.vms = [ vm1, vm2 ]
      self.sim = SIMILARITY( "classification/libsimilarity/libsimilarity.so" )
      self.sim.set_compress_type( XZ_COMPRESS )

      self.F = FILTERS

      self.filters = {}
      
      for i in F :
         self.filters[ i ] = {}
         self.filters[ i ][ BASE ] = { FILTER_NAME : i }
         self.filters[ i ][ BASE ].update( FILTERS[ i ] )
         self.filters[ i ][ METHODS ] = {}
         self.filters[ i ][ HASHSUM ] = {}
         self.filters[ i ][ DIFFMETHODS ] = []
         self.filters[ i ][ NEWMETHODS ] = []

      for i in self.vms :
         for m in i[0].get_methods() :
            m = Method( i[0], i[1], m, self.sim ) 

            for fil in self.filters :
               if i[0] not in self.filters[fil][METHODS] :
                  self.filters[fil][METHODS][ i[0] ] = []
                  self.filters[fil][HASHSUM][ i[0] ] = []
        
               self.filters[fil][METHODS][ i[0] ].append( m )
               m.add_attribute( self.filters[fil][BASE][FILTER_NAME], self.filters[fil][BASE][FILTER_METH], self.filters[fil][BASE][FILTER_CHECKSUM] )
               self.filters[fil][HASHSUM][i[0]].append( m.getsha256( self.filters[fil][BASE][FILTER_NAME] ) )
      
      # Check if some methods in the first file has been modified
      for fil in self.filters :
         for j in self.filters[fil][METHODS][vm1[0]] :
            for i1 in self.filters[fil][METHODS] :
               if i1 != vm1[0] :
                  # B1 not at 0.0 in BB2
                  if j.getsha256( self.filters[fil][BASE][FILTER_NAME] ) not in self.filters[fil][HASHSUM][i1] :
                     for k in self.filters[fil][METHODS][i1] :
                        # B2 not at 0.0 in BB1
                        if k.getsha256( self.filters[fil][BASE][FILTER_NAME] ) not in self.filters[fil][HASHSUM][vm1[0]] :
                           j.similarity( k, self.filters[fil][BASE][FILTER_SIM], self.filters[fil][BASE][FILTER_NAME] )
                           if j not in self.filters[fil][DIFFMETHODS] :
                              self.filters[fil][DIFFMETHODS].append(j)

#      print "DEBUG DIFF METHODS"
      for fil in self.filters :
         for j in self.filters[fil][DIFFMETHODS] :
#            print "DEBUG", j, j.m.get_class_name(), j.m.get_name(), j.m.get_descriptor()
            j.sort( self.filters[fil][BASE][FILTER_NAME] )
            j.diff( self.filters[fil][BASE][FILTER_NAME], self.filters[fil][BASE][FILTER_SIM_BB], self.filters[fil][BASE][FILTER_DIFF_INS] )
#            j.show( self.filters[fil][BASE][FILTER_NAME] )

      # Check if some methods in the second file are totally new !
      for fil in self.filters :
         for j in self.filters[fil][METHODS][vm2[0]] :

            # new methods can't be in diff methods
            if j not in self.filters[fil][DIFFMETHODS] :
               # new methods hashs can't be in first file
               if j.getsha256( self.filters[fil][BASE][FILTER_NAME] ) not in self.filters[fil][HASHSUM][vm1[0]] :
                  ok = True
                  # new methods can't be compared to another one
                  for diff_method in self.filters[fil][DIFFMETHODS] :
                     #print diff_method, "--->", j
                     if diff_method.checksort( self.filters[fil][BASE][FILTER_NAME], j ) :
                        ok = False
                        break

                  if ok :
                     self.filters[fil][NEWMETHODS].append( j )
            
#      print "DEBUG NEW METHODS"
#      for fil in self.filters :
#         print "\tDEBUG", self.filters[fil][NEWMETHODS]
#         for method in self.filters[fil][NEWMETHODS] :
#            print "DEBUG", method.m.get_class_name(), method.m.get_name(), method.m.get_descriptor()

   def get_diff_methods(self) :
      return self.get_elem( DIFFMETHODS )

   def get_new_methods(self) :
      return self.get_elem( NEWMETHODS )
      
   def get_elem(self, attr) :
      d = {}
      for fil in self.filters :
         d[ fil ] = [ x for x in self.filters[fil][attr] ]
      return d


### SIM :
   # DATA : string, constant (int, float ...), clinit
   # CODE
      # exceptions
