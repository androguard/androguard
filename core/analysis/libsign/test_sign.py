#!/usr/bin/env python

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

import sys, itertools, time, os, random
from ctypes import cdll, c_float, c_int, c_uint, c_void_p, Structure, addressof, create_string_buffer, cast, POINTER
# id --> unsigned int
#
class RESULTCHECK_T(Structure) :
    pass
RESULTCHECK_T._fields_ = [ ("id", c_uint),
                           ("value", c_float),
                           ("start", c_uint),
                           ("end", c_uint),
                           ("next", POINTER(RESULTCHECK_T)),
                         ]

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

DEBUG = 0

NCD_SIGNATURES = {
                "s1" : "B[SSSP1SP1IP1]B[P1P1SP1P1]B[P1SP1IP1]B[P1P1SP1]B[IS]B[S]B[IS]B[SP0]B[P0SP1P1SP1P1SP1P1F1SP0SP1P1SP1P1SP1P1P1SP0SP1P1SP1P1SP1P1P1SP0SP1P1SP1P1SP1P1SP1P1P1P0]B[P0F0P1SP1P1IP0]B[P0SP1P1P1P1P1P1P0P1P1P1SP1P1SP1P1P1P1P1P1]B[R]B[P1G]B[P1G]B[P1G]",
                "s2" : "B[P1I]B[]B[P1R]B[P1IP1]B[P1P1P1P1]B[P1G]",
                "s3" : "B[P1P0]B[P0SP1P0F0P1SP1P1IP1]B[P1IP1]B[P1F0P1P0SP1P1P1SP1P1SP1P1P1P1P0SP1P1I]B[]B[R]B[P1G]B[G]B[P1G]"
            }

MPSM_SIGNATURES = {
        "s1" : "he",
        "s2" : "she",
        "s3" : "his",
        "s4" : "hers",
        "s5" : "4243",
}

def check_elem(v, u, _type, _s) :
    l = []
    r = RESULTCHECK_T()
    ret = u.check_elem( v, _type, cast( _s, c_void_p) , len(_s), addressof( r ) )
    
    if ret == 0 :
        while True :
            l.append( (r.id, r.start, r.end, r.value ) )

            try : 
                r = r.next[0]
            except ValueError :
                break
    return ret, l

if __name__ == "__main__" :
    u = cdll.LoadLibrary( "./libsign.so")
    u.add_sign.restype = c_int
    
    new_sign = u.init()
   
    n = 0
    for s in NCD_SIGNATURES :
        print "ADD NCD_SIGNATURE -->", u.add_sign( new_sign, n, 0, cast( NCD_SIGNATURES[s], c_void_p ), len( NCD_SIGNATURES[s] ) )
        n += 1

    for s in MPSM_SIGNATURES :
        print "ADD MPSM_SIGNATURE -->", u.add_sign( new_sign, n, 1, cast( MPSM_SIGNATURES[s], c_void_p ), len( MPSM_SIGNATURES[s] ) )
        n += 1

    u.fix( new_sign )

    r = RESULTCHECK_T()
    print "NCD"
    print "CHECK -->", check_elem( new_sign, u, 0, NCD_SIGNATURES["s1"] )
    print "CHECK -->", check_elem( new_sign, u, 0, NCD_SIGNATURES["s1"] + "B" )
    print "CHECK -->", check_elem( new_sign, u, 0, "HELLO WORLD" )
    print "CHECK -->", check_elem( new_sign, u, 1, "this here is history" )
    print "CHECK -->", check_elem( new_sign, u, 1, "BLAAAA" )
    print "CHECK -->", check_elem( new_sign, u, 1, "414243" )
