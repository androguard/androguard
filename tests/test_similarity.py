#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
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

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.similarity.similarity import *

TESTS_RANDOM_SIGN = [   "B[F1]",
                        "B[G]",
                        "B[I]B[RF1]B[F0S]B[IF1]B[]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP1]",
                        "B[R]B[F1]",
                        "B[]B[]B[IR]",
                        "B[G]B[SGIGF0]B[RP1G]B[SP1I]B[SG]B[SSGP0]B[F1]B[P0SSGR]B[F1]B[SSSI]B[RF1P0R]B[GSP0RP0P0]B[GI]B[P1]B[I]B[GP1S]",
                        "B[P0SP1G]B[S]B[SGP0R]B[RI]B[GRS]B[P0]B[GRI]B[I]B[RP0I]B[SGRF0P0]B[I]B[]B[GGSP0]B[P1RSS]B[]B[S]B[IF1GP0]B[IP0P0GP0P1]B[P0RRRF0]B[R]B[R]B[RRF1S]B[F0P1R]",
                        "B[SP0IP0F0P1]B[GS]B[F1]B[RP0]B[IF0P1S]B[P1]",
                        "B[P0GSGP1]B[R]B[RP1P0]B[F1SIIGF1]B[G]B[F0SP1IF0I]B[RF1F0SIP1SG]B[P1GF1]B[P1G]B[F1P1GIIIGF1]B[F0F1P1RG]B[F1SF1]B[F1SRSS]B[GP0]B[SP1]B[IIF1]B[GIRGR]B[IP1]B[GG]B[RIP1RF1GS]B[SS]B[SSIP0GSP1]B[GGIGSP1G]B[P1GIGSGGI]B[P0P1IGRSRR]B[P1P0GP1]B[P1F1GGGS]B[RR]B[SIF1]B[SR]B[RSI]B[IIRGF1]",
             ]

TESTS_CLOSED_SIGN = [
               [ "B[I]B[RF1]B[F0S]B[IF1]B[]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP1]", "B[I]B[RF1]B[F0S]B[IF1]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP1]" ],
               [ "B[I]B[RF1]B[F0S]B[IF1]B[]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP1]", "B[I]B[RF1]B[F0S]B[IF1]B[]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP0]" ],
             ]

TESTS_DIFFERENT_SIGN = [
               [ "B[F0P1P1P1P0F0P1P1P1P1P1P0F0P1F0P1P1P0P1P1P1P1R]", "B[F0P1F0P1P1]B[SP1P1F0F0F0I]B[F0F0P1G]" ],
            ]

TESTS_SMALL_SIGN = [ 
    [ "TOTO TOTO", "TOTO TOTO" ],
    [ "TITO TOTO", "TOTO TOTO" ],
    [ "TOTO TATO", "TOTO TOTO" ],
    [ "B[]B[]B[IR]", "B[]B[]B[IR]"],
    [ "B[]B[]B[IR]", "B[]B[]B[IR]B"],
    [ "HELLO WORLD", "TOTO TOTO" ],
]

CONVERT_RESULT_TEST = { " OK " : 1,
                        "  X " : 0,
                      }
DEBUG = 0

def test(got, expected, fcmp):
    if fcmp(got, expected) :
        prefix = ' OK '
    else:
        prefix = '  X '

    if DEBUG :
        print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected))

    return CONVERT_RESULT_TEST[ prefix ]

# C(xx) = C(x)
def test_Idempotency(n, x) :
    s1 = n.compress(x + x)
    s2 = n.compress(x)

    return test( s1, s2, lambda x, y : x == y), s1, s2

# C(x) <= C(xy)
def test_Monotonicity(n, x, y) :
    s1 = n.compress( x )
    s2 = n.compress( x + y )

    return test( s1, s2, lambda x, y : x <= y ), s1, s2

# C(xy) = C(yx)
def test_Symetry(n, x, y) :
    s1 = n.compress( x + y )
    s2 = n.compress( y + x )

    return test( s1, s2, lambda x, y : x == y), s1, s2

# C(xy) + C(z) <=  C(xz) + C(yz)
def test_Distributivity(n, x, y, z) :
    s1 = n.compress( x + y ) + n.compress( z )
    s2 = n.compress( x + z ) + n.compress( y + z )

    return test( s1, s2, lambda x, y : x <= y ), s1, s2

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '-> %0.8f s' % ((t2-t1))
        return res
    return wrapper

@print_timing
def Idempotency( n, TESTS_TEXT ) :
    print "Idempotency ",
    j = 0
    res = 0
    cc = 0

    for i in itertools.permutations( TESTS_TEXT, 1 ) :
        r, c1, c2 = test_Idempotency( n, i[0] )
        cc += c1
        cc += c2
        res += r
        j += 1
    print res, "/", j, cc, 

@print_timing
def Monotonicity( n, TESTS_TEXT ) :
    print "Monotonicity ",
    j = 0
    res = 0
    cc = 0

    for i in itertools.permutations( TESTS_TEXT, 2 ) :
        r, c1, c2 = test_Monotonicity( n, i[0], i[1] )
        cc += c1
        cc += c2
        res += r
        j += 1

    print res, "/", j, cc, 


@print_timing
def Symetry( n, TESTS_TEXT ) :
    print "Symetry ",
    j = 0
    res = 0
    cc = 0

    for i in itertools.permutations( TESTS_TEXT, 2 ) :
        r, c1, c2 = test_Symetry( n, i[0], i[1] )
        cc += c1
        cc += c2
        res += r
        j += 1

    print res, "/", j, cc, 

@print_timing
def Distributivity( n, TESTS_TEXT ) :
    print "Distributivity ",
    j = 0
    cc = 0
    res = 0

    for i in itertools.permutations( TESTS_TEXT, 3 ) :
        r, c1, c2 = test_Distributivity( n, i[0], i[1], i[2] )
        cc += c1
        cc += c2
        res += r
        j += 1

    print res, "/", j, cc, 

def TestNCDPermutations(n, ref, threshold) :
    tres, nb, idx, t = benchmark(n.ncd, ref, threshold, lambda x, y : x <= y)
    print "NCD Permutation %f threshold=%f time=%fs for %d/%d" % ( tres, threshold, t, nb, idx )

def TestNCSPermutations(n, ref, threshold) :
    tres, nb, idx, t = benchmark(n.ncs, ref, threshold, lambda x, y : x >= y)
    print "NCS Permutation %f threshold=%f time=%fs for %d/%d" % ( tres, threshold, t, nb, idx )

def TestCMIDPermutations(n, ref, threshold) :
    tres, nb, idx, t = benchmark(n.cmid, ref, threshold, lambda x, y : x >= y)
    print "CMID Permutation %f threshold=%f time=%fs for %d/%d" % ( tres, threshold, t, nb, idx )

def TestNCD( n, tests, type_test ) :
    TestSim("NCD", tests, type_test, n.ncd)

def TestNCS( n, tests, type_test ) :
    TestSim("NCS", tests, type_test, n.ncs)

def TestCMID( n, tests, type_test ) :
    TestSim("CMID", tests, type_test, n.cmid)

def TestCMID2( n ) :
    x = "HI WORLD"
    y = "B[I]B[RF1]B[F0S]B[IF1]B[]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP1]B[SP0IP0F0P1]B[GS]B[F1]B[RP0]B[IF0P1S]B[P1]"
    print n.cmid( x, y )

def TestSim(type_sim, tests, type_test, func) :
    print type_sim, type_test
    nb = 0

    print "\t",
    t1 = time.clock()
    for i in tests :
        val, _ = func( i[0], i[1] )
        print "%d:%f" % (nb, val),
        nb += 1
    t2 = time.clock()
    print "%fs" % (t2 - t1)

def benchmark(func, ref, threshold, fcmp) :
    nb = 0
    idx = 0
    tres = 0.0
    t1 = time.clock()
    for i in itertools.permutations(ref) :
        perm = ''.join(j for j in i)
        res = func(ref, perm)
        tres += res
        if fcmp(res, threshold) :
            nb += 1
        idx += 1
    t2 = time.clock()

    return tres/idx, nb, idx, t2 - t1

def TestEntropy(n, tests, diff) :
    nb = 0
    t1 = time.clock()
    for i in tests :
        nb += test( n.entropy(i[0])[0], n.entropy(i[1])[0], lambda x, y : (max(x,y) - min(x,y)) <= diff )
    t2 = time.clock()
    print "* Entropy %fs %d/%d" % (t2 - t1, nb, len(tests))

def TestProperties(n, data) :
    # Properties
    Idempotency( n, data )
    Monotonicity( n, data )
    Symetry( n, data )
    Distributivity( n, data )

def TestSmallString(n, data) :
    for i in data :
        print i, n.ncd( i[0], i[1] )

def RandomData() :
    l = []
    for i in range(0,9) :
        l.append( os.urandom( random.randint(0, 100) ) )
    return l

TESTS = { "ZLIB"        : ZLIB_COMPRESS,
          "BZ2"         : BZ2_COMPRESS,
          "LZMA"        : LZMA_COMPRESS,
          "XZ"          : XZ_COMPRESS,
          "SNAPPY"      : SNAPPY_COMPRESS,
          "VCBLOCKSORT" : VCBLOCKSORT_COMPRESS,
   #       "SMAZ"         : SMAZ_COMPRESS,
        }

if __name__ == "__main__" :
    try :
        import psyco
        psyco.full()
    except ImportError:
        pass

    n = SIMILARITY( "androguard/core/similarity/libsimilarity/libsimilarity.so" )

    TestEntropy( n, TESTS_CLOSED_SIGN, 0.04 )
    TestEntropy( n, TESTS_DIFFERENT_SIGN, 0.8 )

    for i in TESTS :
        n.set_compress_type( TESTS[i] )
        print "* ", i

        #TestProperties( n, TESTS_RANDOM_SIGN )
        TestSmallString( n, TESTS_SMALL_SIGN )
        
        #TestProperties( n, RandomData() )


        # Closed signature
        #TestNCD( n, TESTS_CLOSED_SIGN, "closed" )
        #TestNCS( n, TESTS_CLOSED_SIGN, "closed" )
        #TestCMID( n, TESTS_CLOSED_SIGN, "closed" )

        # Different signature
        #TestNCD( n, TESTS_DIFFERENT_SIGN, "different" )
        
        
        
        # Permutations
        #TestNCDPermutations( n, "Android", 0.2 )
        #n.clear_caches()

        #TestNCSPermutations( n, "Androgu", 0.8 )
        #n.clear_caches()

        #TestCMIDPermutations( n, "Androgu", 0.8 )
        #n.clear_caches()

        print
#      for j in range(1, 10) :
#         n.set_level( j )
#         print "level", j,

#         print "\t -->", n.ncd("F1M2M2M4F1", "F2M3M3M1F2"),
#         print "\t -->", n.ncd("FMMMF", "MMFF"),
#         print "\t -->", n.ncd("FMMMF", "FMMMF")

            # print "\t bench -->", benchmark(n, "androgu")
