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

from ctypes import cdll, c_float, c_uint, c_void_p, Structure, addressof, create_string_buffer, cast

#struct libncd {
#   void *orig;
#   unsigned int size_orig;
#   void *cmp;
#   unsigned size_cmp;

#   unsigned int *corig;
#   unsigned int *ccmp;
#};
class LIBNCD_T(Structure) :
   _fields_ = [("orig", c_void_p),
               ("size_orig", c_uint),
               ("cmp", c_void_p),
               ("size_cmp", c_uint),

               ("corig", c_uint),
               ("ccmp", c_uint),
              ]

ZLIB_COMPRESS =         0
BZ2_COMPRESS =          1
SMAZ_COMPRESS =         2
class NCD :
   def __init__(self, path="./libncd/libncd.so") :
      self._u = cdll.LoadLibrary( path )
      self._u.ncd.restype = c_float
      self._threads = []
      self._level = 9

      self.__libncd_t = LIBNCD_T()

      self.__cached = {
         ZLIB_COMPRESS : {},
         BZ2_COMPRESS : {},
         SMAZ_COMPRESS : {},
      }

   def set_level(self, level) :
      self._level = level

   
   def get_cached(self, s) :
      try :
         return self.__cached[ self._type ][ hashlib.md5( s ).hexdigest() ]
      except KeyError :
         return c_uint( 0 )

   def add_cached(self, s, v) :
      h = hashlib.md5( s ).hexdigest()
      if h not in self.__cached[ self._type ] :
         self.__cached[ self._type ][ h ] = v

   def get(self, s1, s2) :
      self.__libncd_t.orig = cast( s1, c_void_p ) 
      self.__libncd_t.size_orig = len(s1)

      self.__libncd_t.cmp = cast( s2, c_void_p )
      self.__libncd_t.size_cmp = len(s2)

      corig = self.get_cached(s1)
      ccmp = self.get_cached(s2)
      self.__libncd_t.corig = addressof( corig )
      self.__libncd_t.ccmp = addressof( ccmp )

      res = self._u.ncd( self._level, addressof( self.__libncd_t ) )
      
      self.add_cached(s1, corig)
      self.add_cached(s2, ccmp)

      return res

   def set_compress_type(self, t):
      self._type = t
      self._u.set_compress_type(t)

def benchmark(n, ref) :
   import itertools

   nb = 0
   idx = 0
   for i in itertools.permutations(ref) :
      perm = ''.join(j for j in i)
      res = n.get(ref, perm)
      if res < 0.2 :
         #print "\t", idx, res, ref, perm
         nb += 1
      idx += 1

   return nb, idx

TESTS = { "ZLIB"        : ZLIB_COMPRESS,
          "BZ2"         : BZ2_COMPRESS,
          "SMAZ"         : SMAZ_COMPRESS,
        }

if __name__ == "__main__" :
   try : 
      import psyco
      psyco.full()
   except ImportError:
      pass

   n = NCD()
  
   for i in TESTS :
      n.set_compress_type( TESTS[i] )
      print "* ", i 

      for j in range(1, 10) :
         n.set_level( j )
         print "level", j,

         print "\t -->", n.get("F1M2M2M4F1", "F2M3M3M1F2"),
         print "\t -->", n.get("FMMMF", "MMFF"),
         print "\t -->", n.get("FMMMF", "FMMMF"),

         print "\t bench -->", benchmark(n, "androgu")
