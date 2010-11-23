import os, sys, hashlib, random, types, itertools, hashlib, cPickle, base64, string, threading

from xml.sax.saxutils import escape, unescape

import misc

import wm_l1, wm_l2, wm_l3, wm_l4

WM_CLASS = 0
WM_METHOD = 1

WM_L1 = 0
WM_L2 = 1
WM_L3 = 2
WM_L4 = 3

WM_BIND = {
            WM_L1 : (wm_l1.INIT(), WM_METHOD),
            WM_L2 : (wm_l2.INIT(), WM_CLASS),
            WM_L3 : (wm_l3.INIT(), WM_METHOD),
            WM_L4 : (wm_l4.INIT(), WM_METHOD),
         }

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
            wb.run()

            l_x = wb.get()

            for z in l_x :
               list_x.append( z )

            self.__wms[ "CLASS" ].append( (i, wb) )
      
      if list_x != [] :
         self.__wms[ "SSS_CLASS" ] = DWBO( "TOTO", list_x )

      ######### WM in methods ##########
      for method in vm.get_methods() :
         list_x = []
      
         for i in wm_type :
            if WM_BIND[ i ][1] == WM_METHOD :
               wb = WM_BIND[ i ][0]( vm, method, self.__a )
               wb.run()

               l_x = wb.get()
         
               for z in l_x :
                  list_x.append( z )

               if method not in self.__wms[ "METHODS" ] :
                  self.__wms[ "METHODS" ][ method ] = []

               self.__wms[ "METHODS" ][ method ].append( (i, wb) )

         if len(list_x) > 4 :
            self.__wms[ "SSS_METHODS" ][ method ] = DWBO( "TOTO", list_x )

               #self.__ob = DWBO( "TOTO", list_x )#hashlib.sha512( method.get_raw() ).hexdigest(), list_x )

      #for i in self.__a.get_bb() :
      #   print i
      #   i.show()
      #   print ""


      # X : [45320332736772208547853609619680203699510933865184698619245616070443536495415L, 386, 1565, 872, 1465, 872, 1179, 872]
      # [45320332736772208547853609619680203699510933865184698619245616070443536495415L, 386, 1565, 872, 1465, 872, 1179, 872]


#      X = [ 45320332736772208547853609619680203699510933865184698619245616070443536495415L, 386, 1565, 872, 1465, 872, 1179, 872] # [45320332736772208547853609619680203699510933865184698619245616070443536495415L, 386, 1565, 872, 1465, 872, 1179, 872]
#      ob = DWBO( "TOTO", [45320332736772208547853609619680203699510933865184698619245616070443536495415L, 386, 1565, 872, 1465, 872, 1179, 872] )
#      print ob.verify_with_X( X )
#      raise("ooops")

#      ob = DWBO( "55f3f36e2c93ea69e1871102d3f8653f38ab7b36", [ 12345668, 90877676, 878978, 87987673 ] )
#      ob.show()

#      print self.__a.get_freq()
#      self.__ob.show()

#      print self.__ob.verify_with_X( self.__a.get_freq() )
#      print ob.verify_with_X( [ 12345668, 90877676, 878978, 87987673, 788789 ] )
#      print ob.verify_with_X( [ 12345668, 90877676, 878978, 4, 87987673 ] )
#      print ob.verify_with_X( [ 1, 2, 3, 4, 5, 6 ] )

#      raise("ooops")

   def save(self) :
      buffer = ""

      if self.__wms[ "SSS_CLASS" ] != None :
         sss = self.__wms[ "SSS_CLASS" ]

         buffer += "<class name=\"%s\">\n" % self.__class_name
         buffer += "<threshold>%d</threshold>\n" %  ( sss.get_threshold() )
         buffer += "<sss>%s</sss>\n" %  ( base64.b64encode( cPickle.dumps( sss.get_y() ) ) )

         for j in self.__wms[ "CLASS" ] :
            buffer += "<wm type=\"%d\">%s</wm>\n" % ( j[0], base64.b64encode( cPickle.dumps( j[1].get_export_context() ) ) )

         buffer += "</class>\n"

      for i in self.__wms[ "SSS_METHODS" ] :
         sss = self.__wms[ "SSS_METHODS" ][ i ]
         buffer += "<method class=\"%s\" name=\"%s\" descriptor=\"%s\">\n" % ( i.get_class_name(), escape( i.get_name() ), i.get_descriptor() )
         buffer += "<threshold>%d</threshold>\n" %  ( sss.get_threshold() )
         buffer += "<sss>%s</sss>\n" %  ( base64.b64encode( cPickle.dumps( sss.get_y() ) ) )

         for j in self.__wms[ "METHODS" ][i] :
            buffer += "<wm type=\"%d\">%s</wm>\n" % ( j[0], base64.b64encode( cPickle.dumps( j[1].get_export_context() ) ) )

         buffer += "</method>\n"

      return buffer

class WMMLoad :
   def __init__(self, item) :
      self.__class_name = item.getAttribute('class')
      self.__name = unescape( item.getAttribute('name') )
      self.__descriptor = item.getAttribute('descriptor')
      
      self.__wms = []

      th = int( item.getElementsByTagName( 'threshold' )[0].firstChild.data )

      x = base64.b64decode( item.getElementsByTagName( 'sss' )[0].firstChild.data )
      self.__dwbo = DWBOCheck( cPickle.loads( x ), th )


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

   def get_dwbo(self) :
      return self.__dwbo

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
         sols =  _method.get_dwbo().verify_with_X( list_x )
         print "\t\t SOL :", len(sols)

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
      sols = []
      
      res = itertools.combinations( coord_x, self.__threshold + 1)     
      nb = 0
      for i in res :
         print nb, "/", len(coord_x) * (self.__threshold + 1)
         nb += 1
#         print "I", i
         
         res2 = itertools.product( i, coord_y )
         l = []
         for j in res2 :
#            print "\t res2 j", j
            l.append( j )
         print ""

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
