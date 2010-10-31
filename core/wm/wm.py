import os, sys, hashlib, random, types, itertools, hashlib

import analysis, misc

class WM_R :
   def __init__(self, vm, method) :
      self.__a = analysis.VMBCA( vm, method )
      #for i in self.__a.get_bb() :
      #   print i
      #   i.show()
      #   print ""

#      ob = DWBO( "55f3f36e2c93ea69e1871102d3f8653f38ab7b36", [ 12345668, 90877676, 878978, 87987673 ] )
#      ob.show()

#      print self.__a.get_freq()
      self.__ob = DWBO( hashlib.sha512( method.get_raw() ).hexdigest(), self.__a.get_freq() )
#      self.__ob.show()

#      print self.__ob.verify_with_X( self.__a.get_freq() )
#      print ob.verify_with_X( [ 12345668, 90877676, 878978, 87987673, 788789 ] )
#   print ob.verify_with_X( [ 12345668, 90877676, 878978, 4, 87987673 ] )
#      print ob.verify_with_X( [ 1, 2, 3, 4, 5, 6 ] )
     
   def get_hash(self) :
      return self.__ob.get_hash()

   def get_values(self) :
      l = []
      for k, v in self.__ob.get_points() :
         l.append( v )
      return l

class Polynomial :
    def __init__(self, degree, secret_long, length) :
        self.degree = degree
        self.x0 = secret_long
        self.length = length

        self.coeff = {}
        self.coeff[0] = secret_long

        for i in range(1, self.degree+1) :
            self.coeff[i] = self.get_random_number(length)
            #print "COEFF[%d] = %d" % (i, self.coeff[i])
	    #hashlib.sha256(str(self.coeff[i])).hexdigest()
           
#        print "f(x) = %d " % self.coeff[0],
#	for i in range(1, self.degree+1) :
#		 print "+ %d x^%d" % (self.coeff[i], i),
#	print ""

    def get_n_point(self, x) :
        res = 0
        for i in range(1, len(self.coeff)) :
            res += self.coeff[i] * pow(x, i) 

        res += self.coeff[0]
        return res

    def interpolate(self, x0, y0, x1, y1, x) :
        return (y0*(x-x1) - y1*(x-x0)) / (x0 - x1);

    def neville_algorithm(self, xs, ys):
	for i in range(1, len(xs)) :
            for k in range(0, len(xs) - i) :
                ys[k] = self.interpolate(xs[k], ys[k], xs[k+i], ys[k+1], 0)

        return ys[0]

    def get_random_number(self, randomBytes=128):
        """Return a random long integer."""
        rf = open('/dev/urandom', 'r')
        rl = misc.str2long(rf.read(randomBytes))
        rf.close()
        return rl                  

class ShamirSecretScheme :
    def __init__(self, secret, pieces, threshold) :
      self.__secret = secret
      self.__hash = hashlib.sha256(self.__secret).hexdigest()

      self.__secret_long = misc.str2long(self.__secret)
      self.__hash_long = hashlib.sha256(str(self.__secret_long)).hexdigest()

      self.__pieces = pieces
      self.__threshold = threshold 

#      print "SECRET %s => TO LONG %d" % (self.__secret, self.__secret_long)
#      print "HASH SECRET %s" % self.__hash
#      print "THRESHOLD %d" % self.__threshold

      self.poly = Polynomial(self.__threshold, self.__secret_long, len(self.__secret))
        
    def split(self) :
        points = {} 
        for i in self.__pieces :
            points[i] = self.poly.get_n_point( i )

        return points

    def combi(self, k, l, s, f) :
      if k == 0 :
         f.append( s )
         return 

      if len(l) == 0 :
         return
         
      if len(s) == 0 :
         self.combi( k - 1, l[1:], [ l[0] ], f )
      else :
         self.combi( k - 1, l[1:], s + [ l[0] ], f )

      self.combi(k, l[1:], s, f)

    def join_direct(self) :
      xs = []
      ys = []
     
      points = self.split()

      for i in points :
         xs.append(i) 
         ys.append(points[i])

      print xs, ys

      sol = self.poly.solveSystem2(xs, ys)

      if sol == self.get_secret_long() :
         print True
#
#      try :
#         return [sol, hashlib.sha256(misc.long2str(sol)).hexdigest()]
#      except ValueError :
#         return ["", 0]

    def join(self, coord_x, coord_y) :
# print self.__threshold, len(coord_x)

      res = itertools.combinations( coord_x, self.__threshold + 1 )     
      for i in res :
#         print "I", i
         
         res2 = itertools.product( i, coord_y )
         l = []
         for j in res2 :
#            print "\t", j
            l.append( j )
#         print ""

         res3 = itertools.combinations( l, self.__threshold + 1 )
         for j in res3 :
            print "\t", j
            d = []
            oops = False 
            for v in j :
               if v[0] not in d :
                  d.append(v[0])
               else :
                  oops = True
                  break

               if v[1] not in d :
                  d.append(v[1])
               else :
                  oops = True
                  break

            if oops == False :
#               print oops, j

               final_x = []
               final_y = []
               for v in j : 
                  final_x.append(v[0])
                  final_y.append(v[1])
               sol = self.poly.neville_algorithm(final_x, final_y)
               if sol == self.get_secret_long() :
                  return True, j

      return False, None

    def get_secret_long(self) :
      return self.__secret_long

class DWBO : 
   def __init__(self, hash, val) :
      self.__hash = hash
      self.__val = val

      self.__sss = ShamirSecretScheme(self.__hash, self.__val, (len(self.__val) / 2) + 1)
      self.__points = self.__sss.split()


   def verify_with_X(self, coord_x) :
      result, success = self.__sss.join( coord_x, self.__points.values() )
      return result, success

   def get_points(self) :
      return self.__points

   def get_hash(self) :
      return self.__hash

   def show(self) :
      print self.__hash
      for i in self.__points :
         print i, self.__points[i]
