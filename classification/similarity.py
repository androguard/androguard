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

import zlib
from ctypes import cdll, c_float, c_int, c_uint, c_void_p, Structure, addressof, create_string_buffer, cast

#struct libsimilarity {
#   void *orig;
#   unsigned int size_orig;
#   void *cmp;
#   unsigned size_cmp;

#   unsigned int *corig;
#   unsigned int *ccmp;
#   
#   float res;
#};
class LIBSIMILARITY_T(Structure) :
    _fields_ = [("orig", c_void_p),
                ("size_orig", c_uint),
                ("cmp", c_void_p),
                ("size_cmp", c_uint),

                ("corig", c_uint),
                ("ccmp", c_uint),

                ("res", c_float),
               ]

ZLIB_COMPRESS =         0
BZ2_COMPRESS =          1
SMAZ_COMPRESS =         2
LZMA_COMPRESS =         3
XZ_COMPRESS =           4
SNAPPY_COMPRESS =       5
class SIMILARITY :
    def __init__(self, path="./libsimilarity/libsimilarity.so") :
        self._u = cdll.LoadLibrary( path )

        self._u.compress.restype = c_uint
        self._u.ncd.restype = c_int
        self._u.ncs.restype = c_int
        self._u.cmid.restype = c_int
        self._u.entropy.restype = c_float
        self._u.levenshtein.restype = c_uint

        self._level = 9

        self.__libsim_t = LIBSIMILARITY_T()

        self.__caches = {
           ZLIB_COMPRESS : {},
           BZ2_COMPRESS : {},
           SMAZ_COMPRESS : {},
           LZMA_COMPRESS : {},
           XZ_COMPRESS : {},
           SNAPPY_COMPRESS : {},
        }
        
        self.__rcaches = {
           ZLIB_COMPRESS : {},
           BZ2_COMPRESS : {},
           SMAZ_COMPRESS : {},
           LZMA_COMPRESS : {},
           XZ_COMPRESS : {},
           SNAPPY_COMPRESS : {},
        }
       
        self.__ecaches = {}

        self.set_compress_type( ZLIB_COMPRESS )

    def raz(self) :
        del self._u
        del self.__libsim_t

    def set_level(self, level) :
        self._level = level

    def get_in_caches(self, s) :
        try :
            return self.__caches[ self._type ][ zlib.adler32( s ) ]
        except KeyError :
            return c_uint( 0 )

    def get_in_rcaches(self, s1, s2) :
        try :
            return self.__rcaches[ self._type ][ zlib.adler32( s1 + s2 ) ]
        except KeyError :
            try :
                return self.__rcaches[ self._type ][ zlib.adler32( s2 + s1 ) ]
            except KeyError :
                return -1, -1

    def add_in_caches(self, s, v) :
        h = zlib.adler32( s )
        if h not in self.__caches[ self._type ] :
            self.__caches[ self._type ][ h ] = v
    
    def add_in_rcaches(self, s, v, r) :
        h = zlib.adler32( s )
        if h not in self.__rcaches[ self._type ] :
            self.__rcaches[ self._type ][ h ] = (v, r)

    def clear_caches(self) :
        for i in self.__caches :
            self.__caches[i] = {}

    def add_in_ecaches(self, s, v, r) :
        h = zlib.adler32( s )
        if h not in self.__ecaches :
            self.__ecaches[ h ] = (v, r)
    
    def get_in_ecaches(self, s1) :
        try :
            return self.__ecaches[ zlib.adler32( s1 ) ]
        except KeyError :
            return -1, -1

    def compress(self, s1) :
        res = self._u.compress( self._level, cast( s1, c_void_p ), len( s1 ) )
        return res

    def _sim(self, s1, s2, func) :
        end, ret = self.get_in_rcaches( s1, s2 )
        if end != -1 :
            return end, ret

        self.__libsim_t.orig = cast( s1, c_void_p )
        self.__libsim_t.size_orig = len(s1)

        self.__libsim_t.cmp = cast( s2, c_void_p )
        self.__libsim_t.size_cmp = len(s2)

        corig = self.get_in_caches(s1)
        ccmp = self.get_in_caches(s2)
        
        self.__libsim_t.corig = addressof( corig )
        self.__libsim_t.ccmp = addressof( ccmp )

        ret = func( self._level, addressof( self.__libsim_t ) )

        self.add_in_caches(s1, corig)
        self.add_in_caches(s2, ccmp)
        self.add_in_rcaches(s1+s2, self.__libsim_t.res, ret)

        return self.__libsim_t.res, ret

    def ncd(self, s1, s2) :
        return self._sim( s1, s2, self._u.ncd )

    def ncs(self, s1, s2) :
        return self._sim( s1, s2, self._u.ncs )

    def cmid(self, s1, s2) :
        return self._sim( s1, s2, self._u.cmid )

    def entropy(self, s1) :
        end, ret = self.get_in_ecaches( s1 )
        if end != -1 :
            return end, ret

        res = self._u.entropy( cast( s1, c_void_p ), len( s1 ) )
        self.add_in_ecaches( s1, res, 0 )
        
        return res, 0

    def levenshtein(self, s1, s2) :
        res = self._u.levenshtein( cast( s1, c_void_p ), len( s1 ), cast( s2, c_void_p ), len( s2 ) )
        return res, 0
    
    def set_compress_type(self, t):
        self._type = t
        self._u.set_compress_type(t)
