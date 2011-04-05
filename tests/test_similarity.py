#!/usr/bin/env python

import sys

PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")
sys.path.append(PATH_INSTALL + "./classification")

from similarity import *

def test(got, expected):
   if got == expected:
      prefix = ' OK '
   else:
      prefix = '  X '
   print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected))


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

   n = NCD( "classification/libsimilarity/libsimilarity.so" )
  
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
