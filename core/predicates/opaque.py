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

import random

class PRNG :
   def __init__(self, value, prefix="x") :
      self.__value = value

   def run(self) :
      elements = self._find_cong( self.__value )
      print "ELEMENTS ", elements

      print self._cong( elements[0], elements[1], elements[2], elements[3], elements[4], self.__value, elements[4] )

      values= { "GERME" : elements[0], 
               "A" : elements[1],
               "C" : elements[2],
               "M" : elements[3],
               "ITER" : elements[4]
              }

      print values
      return values

   def _find_cong(self, value) :
      elements = self.__find_cong( value )
      while elements == None :
         elements = self.__find_cong( value )
      return elements

   def __find_cong(self, value) :
      germe = random.randint(0, value * 2)
      a = 1 % 4 
      m = random.randint(value, value * 2)
      c = random.randint(0, 255)
      n = random.randint(value, value * 2)
      iter = random.randint(5, 30)

      res = self._cong(germe, a, c, m, n, value, iter)
      return res

   def _cong(self, germe, a, c, m, n, value, iter) :
      map = {}
      y = 0
      for i in range(0, n) :
         y = (a * germe + c) % m         
         germe = y             
         map[i] = germe
         if y == value :
            print "%d FIND !!!" % y                                                                                                            
            if i >= iter :            
               return [map[i - iter], a, c, m, iter]
         print y,
      print ""
      return None
      

class INT :
   def __init__(self, value, size=2, prefix="x") :
      self.__value = value
      self.__prefix = prefix
      self.__size = size

      self.__ops = [ ("+", lambda x,y : x + y) , 
                     ("-", lambda x,y : x - y), 
#                     ("*", lambda x,y : x * y),
#                     ("<<", lambda x,y : x << y ),
#                     (">>", lambda x,y : x >> y),
#          ("&", lambda x,y : x & y),
#                     ("|", lambda x,y : x | y) 
                   ]

      self.__rops = { "+" : "-",
                      "-" : "+",
                      "<<" : ">>",
                      ">>" : "<<",
      }

   def run(self) :
      h = {}
      l = []

      cvalue = self.__value
     
      order = [] 
      for i in range(0, self.__size) :
         operation = self.__ops[ random.randint( 0, len(self.__ops) - 1 ) ]
         rvalue = random.randint(0, abs( self.__value ) * 100)
         nvalue = operation[1]( cvalue, rvalue )
         order.append( [ cvalue, rvalue, nvalue, operation ] )
         cvalue = nvalue

      order.reverse()
#      print order


      idx = 0
      l = []
      current_var = self.__prefix + str(idx)
      current = [ current_var, "=", order[0][2] ]
      l.append( current )
      for i in order :
         op = self.__rops[ i[3][0] ]         
         lvalue = i[1]

         idx += 1
         o_current_var = current_var
         current_var = self.__prefix + str(idx)    

         current = [ current_var, "=", o_current_var, op, lvalue ]

         l.append( current )

      return l 
