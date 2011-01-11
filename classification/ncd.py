from ctypes import cdll, c_float

ZLIB_COMPRESS = 0
BZ2_COMPRESS = 1
class NCD :
   def __init__(self) :
      self._u = cdll.LoadLibrary( "./libncd/libncd.so" )
      self._u.ncd.restype = c_float
      self._threads = []

   def get(self, s1, s2) :
      return self._u.ncd( s1, len(s1), s2, len(s2) )

   def set_compress_type(self, t):
      self._u.set_compress_type(t)

def benchmark(n, ref) :
   import itertools

   idx = 0
   for i in itertools.permutations(ref) :
      perm = ''.join(j for j in i)
      res = n.get(ref, perm)
      if res < 0.2 :
         print "\t", idx, res, ref, perm
      idx += 1

TESTS = { "ZLIB" : ZLIB_COMPRESS,
         "BZ2" : BZ2_COMPRESS,
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

      print "various tests :"
      print "\t", n.get("F1M2M2M4F1", "F2M3M3M1F2")
      print "\t", n.get("FMMMF", "MMFF")
      print "\t", n.get("FMMMF", "FMMMF")

      print "benchmark with permutations :"
      benchmark(n, "andro")
