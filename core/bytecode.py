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


from struct import unpack, pack

from error import warning

# Handle exit message
def Exit( msg ):
   warning("Error : " + msg)
   raise("oops")

# Print arg into a correct format
def _Print(name, arg) :
   buff = name + " "

   if type(arg).__name__ == 'int' :
      buff += "0x%x" % arg
   elif type(arg).__name__ == 'long' :
      buff += "0x%x" % arg
   elif type(arg).__name__ == 'str' :
      buff += "%s" % arg
   elif isinstance(arg, SV) :
      buff += "0x%x" % arg.get_value()
   elif isinstance(arg, SVs) :
      buff += arg.get_value().__str__()

   print buff

def PrettyShow(idx, paths, nb, ins) :
   p = []
   for j in paths :
      m_in = j[0]
      m_ax = j[1]
      if j[0] > j[1] :
         m_in = j[1]
         m_ax = j[0]

      if idx >= m_in and idx <= m_ax :
         if idx == j[0] :
            p.append( j[1] )
            print "o",
         if idx == j[1] :
            print ">",

         if idx != j[0] and idx != j[1] :
            print "|",
      else :
         print " ",

   print nb, "0x%x" % idx,
   ins.show( idx )

   if p != [] :
      print "[", ' '.join("%x" % i for i in p), "]",
   print

class SV : 
   """SV is used to handle more easily a value"""
   def __init__(self, size, buff) :
      self.__size = size
      self.__value = unpack(self.__size, buff)[0]

   def _get(self) :
      return pack(self.__size, self.__value)

   def __str__(self) :
      return "0x%x" % self.__value

   def __int__(self) :
      return self.__value

   def get_value_buff(self) :
      return self._get()

   def get_value(self) :
      return self.__value

   def set_value(self, attr) :
      self.__value = attr

class SVs :
   """SVs is used to handle more easily a structure of different values"""
   def __init__(self, size, ntuple, buff) :
      self.__size = size

      self.__value = ntuple._make( unpack( self.__size, buff ) )

   def _get(self) :
      l = []
      for i in self.__value._fields :
         l.append( getattr( self.__value, i ) )
      return pack( self.__size, *l)

   def _export(self) :
      return [ x for x in self.__value._fields ]

   def get_value_buff(self) :
      return self._get()

   def get_value(self) :
      return self.__value

   def set_value(self, attr) :
      self.__value = self.__value._replace( **attr )

   def __str__(self) :
      return self.__value.__str__()

class MethodBC(object) :
   def show(self, value) :
      getattr(self, "show_" + value)()

class BuffHandle :
   def __init__(self, buff) :
      self.__buff = buff
      self.__idx = 0

   def read_b(self, size) :
      return self.__buff[ self.__idx : self.__idx + size ]

   def read(self, size) :
      if isinstance(size, SV) :
         size = size.value

      buff = self.__buff[ self.__idx : self.__idx + size ]
      self.__idx += size

      return buff

class Buff :
   def __init__(self, offset, buff) :
      self.offset = offset
      self.buff = buff

      self.size = len(buff)

SHOW = 0
class _Bytecode(object) :
   def __init__(self, buff) :
      try :
         import psyco
         psyco.full()
      except ImportError :
         warning("module psyco not found")

      self.__buff = buff
      
      self.__registers = { SHOW : [] }
      self.__idx = 0


   def read(self, size) :
      if isinstance(size, SV) :
         size = size.value

      buff = self.__buff[ self.__idx : self.__idx + size ]
      self.__idx += size

      return buff

   def readat(self, off) :
      if isinstance(off, SV) :
         off = off.value

      return self.__buff[ off : ]

   def read_b(self, size) :
      return self.__buff[ self.__idx : self.__idx + size ]

   def set_idx(self, idx) :
      if isinstance(idx, SV) :
         self.__idx = idx.value
      else :
         self.__idx = idx

   def get_idx(self) :
      return self.__idx

   def add_idx(self, idx) :
      self.__idx += idx

   def register(self, type_register, fct) :
      self.__registers[ type_register ].append( fct )

   def get_buff(self) :
      return self.__buff

   def length_buff(self) :
      return len( self.__buff )

   def show(self) :
      print self
      for i in self.__registers[ SHOW ] :
         i()

   def save(self, filename) :
      fd = open(filename, "w")
      buff = self._save()
      fd.write( buff )
      fd.close()
