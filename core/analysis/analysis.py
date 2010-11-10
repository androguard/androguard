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

import jvm, dvm

class ContextField :
   def __init__(self, mode) :
      self.mode = mode
      self.details = []

   def set_details(self, details) :
      for i in details :
         self.details.append( i )

class ContextMethod :
   def __init__(self) :
      self.details = []

   def set_details(self, details) :
      for i in details :
         self.details.append( i )

class ExternalFM :
   def __init__(self, class_name, name, descriptor) :
      self.class_name = class_name
      self.name = name
      self.descriptor = descriptor

   def get_class_name(self) :
      return self.class_name

   def get_name(self) :
      return self.name

   def get_descriptor(self) :
      return self.descriptor

##### JVM ######
FIELDS = {
            "getfield" : "R",
            "getstatic" : "R",
            "putfield" : "W",
            "putstatic" : "W",
         }

METHODS = [ "invokestatic", "invokevirtual", "invokespecial" ]

class JVMBreakBlock : 
   def __init__(self, _vm) :
      self.__ins = []
      self.__vm = _vm

      self.__fields = {}
      self.__methods = {}

      self.__info = { 
                        "F" : [ "get_field_descriptor", self.__fields, ContextField ],
                        "M" : [ "get_method_descriptor", self.__methods, ContextMethod ],
                    }

   def get_fields(self) :
      return self.__fields
   
   def get_methods(self) :
      return self.__methods

   def push(self, ins) :
      self.__ins.append(ins)
   
   def analyze(self) :
      ctt = []

      for i in self.__ins :
         v = self.trans(i)
         if v != None :
            ctt.append( v )

         t = ""
         # Woot it's a field !
         if i.get_name() in FIELDS :
            t = "F" 
         elif i.get_name() in METHODS :
            t = "M"

         if t != "" :
            o = i.get_operands()
            desc, _ = getattr(self.__vm, self.__info[t][0])( o[0], o[1], o[2] )

            # It's an external 
            if desc == None :
               desc = ExternalFM( o[0], o[1], o[2] )

            if desc not in self.__info[t][1] :
               self.__info[t][1][desc] = []

            if t == "F" :
               self.__info[t][1][desc].append( self.__info[t][2]( FIELDS[ i.get_name() ][0] ) )
            elif t == "M" :
               self.__info[t][1][desc].append( self.__info[t][2]() )

      for i in self.__fields :
         for k in self.__fields[i] :
            k.set_details( ctt )

      for i in self.__methods : 
         for k in self.__methods[i] :
            k.set_details( ctt )

   def trans(self, i) :
      v = i.get_name()[0:2]
      if v == "il" or v == "ic" or v == "ia" or v == "si" or v == "bi" :
         return "I"
     
      if v == "ba" :
         return "B"

      if v == "if" :
         return "IF"
     
      if v == "ir" :
         return "RET"

      if "and" in i.get_name() :
         return "&"
      
      if "add" in i.get_name() :
         return "+"

      if "sub" in i.get_name() :
         return "-"

      if "xor" in i.get_name() :
         return "^"

      if "ldc" in i.get_name() :
         return "I"

      if "invokevirtual" in i.get_name() :
         return "M" + i.get_operands()[2]

      if "getfield" in i.get_name() :
         return "F" + i.get_operands()[2]

   def show(self) :
      print self.__fields

class GVM_BCA :
   def __init__(self, _vm, _method) :
      self.__vm = _vm
      self.__method = _method

      BO = [ jvm.BREAK_JVM_OPCODES, JVMBreakBlock ]
      if self.__vm.get_type() == "DVM" :
         BO = [ jvm.BREAK_DVM_OPCODES, DVMBreakBlock ]

      code = self.__method.get_code()

      current_bb = BO[1]( self.__vm )
      self.__bb = [ current_bb ]

      bc = code.get_bc()
      for i in bc.get() :
         name = i.get_name()
         m_name = name.split("_")[0]

         current_bb.push( i )
         if name in BO[0] or m_name in BO[0] :
            current_bb.analyze()
   
            current_bb = BO[1]( self.__vm )
            self.__bb.append( current_bb ) 
     
      if len( self.__bb ) > 1 :
         self.__bb.pop(-1)

   def show(self) :
      print "METHOD", self.__method.get_class_name(), self.__method.get_name(), self.__method.get_descriptor()
      #self.__method.show()
      self.show_fields()
      self.show_methods()

   def _iterFlatten(self, root):
      if isinstance(root, (list, tuple)):      
         for element in root :
            for e in self._iterFlatten(element) :      
               yield e               
      else:                      
         yield root
   
   def show_fields(self) :
      print "\t #FIELDS :"
      l = []
      for i in self.__bb :
         fields = i.get_fields()
         for field in fields :
            print "\t\t-->", field.get_class_name(), field.get_name(), field.get_descriptor()
            for context in fields[field] :
               print "\t\t\t |---|",  context.mode, context.details

   def show_methods(self) :
      print "\t #METHODS :"
      l = []
      for i in self.__bb :
         methods = i.get_methods()
         for method in methods :
            print "\t\t-->", method.get_class_name(), method.get_name(), method.get_descriptor()
            for context in methods[method] :
               print "\t\t\t |---|", context.details

class VMBCA :
   def __init__(self, _vm) :
      self.l = []
      for i in _vm.get_methods() :
         self.l.append( GVM_BCA( _vm, i ) )

   def show(self) :
      for i in self.l :
         i.show()
