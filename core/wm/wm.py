import os, sys, hashlib, random, types, itertools, hashlib, cPickle, base64

from xml.sax.saxutils import escape, unescape

import misc

import wm_l1, wm_l3, wm_l4

WM_L1 = 0
WM_L3 = 1
WM_L4 = 2

WM_BIND = {
            WM_L1 : wm_l1.INIT(),
            WM_L3 : wm_l3.INIT(),
            WM_L4 : wm_l4.INIT(),
         }

class WM :
   def __init__(self, vm, method, wm_type, analysis) :
      self.__method = method
      self.__wms = []
   
      self.__a = analysis
   
      list_x = []
      
      for i in wm_type :
         wb = WM_BIND[ i ]( vm, method, self.__a )
         wb.run()

         l_x = wb.get()
         
         for z in l_x :
            list_x.append( z )

         self.__wms.append( (i, wb) )

      print list_x
      if list_x == [] :
         raise("list is empty")

      self.__ob = DWBO( hashlib.sha512( method.get_raw() ).hexdigest(), list_x )

      #for i in self.__a.get_bb() :
      #   print i
      #   i.show()
      #   print ""

#      ob = DWBO( "55f3f36e2c93ea69e1871102d3f8653f38ab7b36", [ 12345668, 90877676, 878978, 87987673 ] )
#      ob.show()

#      print self.__a.get_freq()
#      self.__ob.show()

#      print self.__ob.verify_with_X( self.__a.get_freq() )
#      print ob.verify_with_X( [ 12345668, 90877676, 878978, 87987673, 788789 ] )
#   print ob.verify_with_X( [ 12345668, 90877676, 878978, 4, 87987673 ] )
#      print ob.verify_with_X( [ 1, 2, 3, 4, 5, 6 ] )

   def save(self) :
      buffer = "<method class=\"%s\" name=\"%s\" descriptor=\"%s\">\n" % ( self.__method.get_class_name(), escape( self.__method.get_name() ), self.__method.get_descriptor() )
      buffer += "<sss>%s</sss>\n" %  ( base64.b64encode( cPickle.dumps( self.__ob.get_y() ) ) )


      for i in self.__wms :
         buffer += "<wm type=\"%d\">%s</wm>\n" % ( i[0], base64.b64encode( cPickle.dumps( i[1].get_export_context() ) ) )

      buffer += "</method>\n"

      return buffer

class WMMLoad :
   def __init__(self, item) :
      self.__class_name = item.getAttribute('class')
      self.__name = unescape( item.getAttribute('name') )
      self.__descriptor = item.getAttribute('descriptor')
      
      self.__wms = []

      x = base64.b64decode( item.getElementsByTagName( 'sss' )[0].firstChild.data )
#      print cPickle.loads( x )


      for s_item in item.getElementsByTagName( 'wm' ) :
         _type = int( s_item.getAttribute('type') )

         wb = WM_BIND[ _type ]( None, None, None )
        
         x = cPickle.loads( base64.b64decode( s_item.firstChild.data ) )
         wb.set_context( x )


         self.__wms.append( (_type, wb) )

   def get_wms(self) :
      return self.__wms

   def get_name(self) :
      return self.__name

class WMLoad :
   def __init__(self, document) :
      self.__methods = []

      for item in document.getElementsByTagName('method') :
         self.__methods.append( WMMLoad( item ) )

   def get_methods(self) :
      return self.__methods

class WMCheck :
   def __init__(self, wm_orig, vm, method, analysis) :

      print method.get_name()

      for _method in wm_orig.get_methods() :
         list_x = []
         print "\t --->", _method.get_name()
         for _type, _wm in _method.get_wms() :
            wb = WM_BIND[ _type ]( vm, method, analysis )

            wb.set_context( _wm.get_import_context() )
            wb.run()

            l_x = _wm.challenge( wb )

            for i in l_x :
               list_x.append( i )

         print "\t\t X :", list_x
         #print wm_orig.get_dwbo().verify_with_X( list_x )
      print ""

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

   def get_y(self) :
      return [ self.__points[k] for k in self.__points ]

   def get_points(self) :
      return self.__points

   def get_hash(self) :
      return self.__hash

   def show(self) :
      print self.__hash
      for i in self.__points :
         print i, self.__points[i]
