import os, sys, hashlib, random, types, itertools, hashlib, cPickle, base64, string, threading
from xml.sax.saxutils import escape, unescape

from error import log_loading, warning
import misc

WM_CLASS = 0
WM_METHOD = 1

import bm_a0

WM_BIND = {}

for i in bm_a0.INIT() :
   WM_BIND[ i.NAME ] = ( i, i.TYPE )

class WM :
   def __init__(self, vm, class_name, wm_type, analysis) :
      self.__class_name = class_name

      self.__wms = { "CLASS" : [],
                     "METHODS" : {},

                     "SSS_CLASS" : None,
                     "SSS_METHODS" : {},
                   }
   
      self.__a = analysis
   
      ######### WM in class ############
      list_x = []
      for i in wm_type :
         if WM_BIND[ i ][1] == WM_CLASS :
            wb = WM_BIND[ i ][0](vm, self.__a)
            
            print "CREATING %s ... %s" % (class_name, wb.NAME)
            wb.run()

            l_x = wb.get()

            for z in l_x :
               list_x.append( z )

            self.__wms[ "CLASS" ].append( (i, wb) )
     
      # Create the secret sharing for class
      if list_x != [] :
         self.__wms[ "SSS_CLASS" ] = DWBO( "TOTO", list_x )

      ######### WM in methods ##########
      for method in vm.get_methods() :
         list_x = []
     
         print "CREATING %s %s %s ..." % (method.get_class_name(), method.get_name(), method.get_descriptor()),
         for i in wm_type :
            if WM_BIND[ i ][1] == WM_METHOD :
               wb = WM_BIND[ i ][0]( vm, method, self.__a )
            
               print wb.NAME,
               wb.run()

               l_x = wb.get()
         
               for z in l_x :
                  list_x.append( z )

               if method not in self.__wms[ "METHODS" ] :
                  self.__wms[ "METHODS" ][ method ] = []

               self.__wms[ "METHODS" ][ method ].append( (i, wb) )
         print ""

         # Create the secret sharing for methods
         if list_x != [] :
            self.__wms[ "SSS_METHODS" ][ method ] = DWBO( "TOTO", list_x )

   def save(self) :
      buffer = ""

      # Save class watermarks
      if self.__wms[ "SSS_CLASS" ] != None :
         sss = self.__wms[ "SSS_CLASS" ]

         buffer += "<class name=\"%s\">\n" % self.__class_name
         buffer += "<threshold>%d</threshold>\n" %  ( sss.get_threshold() )
         buffer += "<sss>%s</sss>\n" %  ( base64.b64encode( cPickle.dumps( sss.get_y() ) ) )

         for j in self.__wms[ "CLASS" ] :
            buffer += "<wm type=\"%s\">%s</wm>\n" % ( j[0], base64.b64encode( cPickle.dumps( j[1].get_export_context() ) ) )

         buffer += "</class>\n"

      # Save methods watermarks
      for i in self.__wms[ "SSS_METHODS" ] :
         sss = self.__wms[ "SSS_METHODS" ][ i ]
         buffer += "<method class=\"%s\" name=\"%s\" descriptor=\"%s\">\n" % ( i.get_class_name(), escape( i.get_name() ), i.get_descriptor() )
         buffer += "<threshold>%d</threshold>\n" %  ( sss.get_threshold() )
         buffer += "<sss>%s</sss>\n" %  ( base64.b64encode( cPickle.dumps( sss.get_y() ) ) )

         for j in self.__wms[ "METHODS" ][i] :
            buffer += "<wm type=\"%s\">%s</wm>\n" % ( j[0], base64.b64encode( cPickle.dumps( j[1].get_export_context() ) ) )

         buffer += "</method>\n"

      return buffer

class WMMLoad :
   def __init__(self, item) :
      # Load a specific watermark method from a xml file

      # get class name, method name and method descriptor
      self.__class_name = item.getAttribute('class')
      self.__name = unescape( item.getAttribute('name') )
      self.__descriptor = item.getAttribute('descriptor')

      self.__wms = []

      # get the threshold
      th = int( item.getElementsByTagName( 'threshold' )[0].firstChild.data )

      # load the y
      x = base64.b64decode( item.getElementsByTagName( 'sss' )[0].firstChild.data )
      self.__dwbo = DWBOCheck( cPickle.loads( x ), th )


      for s_item in item.getElementsByTagName( 'wm' ) :
         _type = str( s_item.getAttribute('type') )

         # load the context of the original watermark
         if WM_BIND[ _type ][1] == WM_CLASS :
            wb = WM_BIND[ _type ][0]( None, None )
         else :
            wb = WM_BIND[ _type ][0]( None, None, None )
        
         x = cPickle.loads( base64.b64decode( s_item.firstChild.data ) )
         wb.set_context( x )

         self.__wms.append( (_type, wb) )
   
   def get_wms(self) :
      return self.__wms

   def get_name(self) :
      return self.__name

   def get_dwbo(self) :
      return self.__dwbo

class WMLoad :
   def __init__(self, document) :
      self.__methods = []
      self.__classes = []

      # load each watermark class 
      for item in document.getElementsByTagName('class') :
         self.__classes.append( WMMLoad( item ) )

      # load each watermark method
      for item in document.getElementsByTagName('method') :
         self.__methods.append( WMMLoad( item ) )

   def get_classes(self) :
      return self.__classes

   def get_methods(self) :
      return self.__methods

class WMCheck :
   def __init__(self, wm_orig, andro, analysis) :
      for _class in wm_orig.get_classes() :
         print _class


      raise("ooo")

      # check if a watermark is present on the compared method
      for _method in wm_orig.get_methods() :
         list_x = []
         for _type, _wm in _method.get_wms() :
            wb = WM_BIND[ _type ][0]( vm, method, analysis )

            wb.set_context( _wm.get_import_context() )
            wb.run()

            l_x = _wm.challenge( wb )

            for i in l_x :
               list_x.append( i )

         #print "\t\t X :", list_x
         sols =  _method.get_dwbo().verify_with_X( list_x )
         if len(sols) > 0 :
            print "\t --->", _method.get_name(), 
            print "\t\t SOL :", len(sols), "--->",  
            for sol in sols :
               if sol > 0 :
                  print repr( misc.long2str(long(sol)) ),

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
     
    def get_secret(self) :
       return self.__secret

    def get_threshold(self) :
       return self.__threshold

    def split(self) :
        points = {} 
        for i in self.__pieces :
            points[i] = self.poly.get_n_point( i )

        return points

class AlgoWM :
   def __init__(self, th) :
      self.__threshold = th
   
   def interpolate(self, x0, y0, x1, y1, x) :
      return (y0*(x-x1) - y1*(x-x0)) / (x0 - x1);

   def NevilleAlgorithm(self, xs, ys):
      for i in range(1, len(xs)) :
         for k in range(0, len(xs) - i) :
            ys[k] = self.interpolate(xs[k], ys[k], xs[k+i], ys[k+1], 0)
      return ys[0]

   def run(self, coord_x, coord_y) :
      try :
         import gmpy
         coord_x = [ gmpy.mpz(i) for i in coord_x ]
         coord_y = [ gmpy.mpz(i) for i in coord_y ]
      except ImportError :
         warning("module gmpy not found")

      try :
         import psyco
      
         psyco.bind(self._run)
         psyco.bind(self.NevilleAlgorithm)
         psyco.bind(self.interpolate)
      except ImportError :
         warning("module psyco not found")

      return self._run( coord_x, coord_y )

   def _run(self, coord_x, coord_y) :
      sols = []
      
      res = itertools.combinations( coord_x, self.__threshold + 1)     
      nb = 0
      for i in res :
         nb += 1
         
         res2 = itertools.product( i, coord_y )
         l = []
         for j in res2 :
#            print "\t res2 j", j
            l.append( j )

         res3 = itertools.combinations( l, self.__threshold + 1 )
         for j in res3 :
#            print "\t res3 j", j
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
#               print final_x, final_y
               sol = self.NevilleAlgorithm( final_x, final_y )
               sols.append( sol )
      return sols

class DWBO : 
   def __init__(self, hash, val, max_threshold=-1) :
      self.__hash = hash
      self.__val = val

      if max_threshold == -1 :
         th = (len(self.__val) / 2) + 1

      self.__sss = ShamirSecretScheme(self.__hash, self.__val, (len(self.__val) / 2) + 1)
      self.__points = self.__sss.split()

   def get_secret(self) :
      return self.__sss.get_secret()

   def get_y(self) :
      return [ self.__points[k] for k in self.__points ]

   def get_points(self) :
      return self.__points

   def get_threshold(self) :
      return self.__sss.get_threshold()

   def show(self) :
      print self.__hash
      for i in self.__points :
         print i, self.__points[i]

class DWBOCheck :
   def __init__(self, l_y, th) :
      self.__l_y = l_y
      self.__algo = AlgoWM( th )

   def verify_with_X(self, l_x) :
      return self.__algo.run( l_x, self.__l_y )
