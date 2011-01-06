from ctypes import cdll, c_float

class NCD :
   def __init__(self) :
      self._u = cdll.LoadLibrary( "./libncd/libncd.so" )
      self._u.ncd.restype = c_float
      self._threads = []

   def get(self, s1, s2) :
      return self._u.ncd( s1, len(s1), s2, len(s2) )

def benchmark(n, ref) :
   import itertools

   idx = 0
   for i in itertools.permutations(ref) :
      perm = ''.join(j for j in i)
      res = n.get(ref, perm)
      if res < 0.2 :
         print idx, res, ref, perm
      idx += 1

if __name__ == "__main__" :
   try : 
      import psyco
      psyco.full()
   except ImportError:
      pass

   n = NCD()
   benchmark(n, "androgua")
