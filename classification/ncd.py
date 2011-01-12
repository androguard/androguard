from ctypes import cdll, c_float

ZLIB_COMPRESS =         0
BZ2_COMPRESS =          1
SMAZ_COMPRESS =         2
class NCD :
   def __init__(self) :
      self._u = cdll.LoadLibrary( "./libncd/libncd.so" )
      self._u.ncd.restype = c_float
      self._threads = []
      self._level = 9

   def set_level(self, level) :
      self._level = level

   def get(self, s1, s2) :
      return self._u.ncd( self._level, s1, len(s1), s2, len(s2) )

   def set_compress_type(self, t):
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

         print "\t bench -->", benchmark(n, "androg")
