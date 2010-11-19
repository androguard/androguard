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

import re

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

class ToString :
   def __init__(self, tab) :
      self.__tab = tab
      self.__re_tab = {}

      for i in self.__tab :
         self.__re_tab[i] = []
         for j in self.__tab[i] :
            self.__re_tab[i].append( re.compile( j ) )

      self.__string = ""

   def push(self, name) :
      for i in self.__tab :
         for j in self.__re_tab[i] :
            if j.match(name) != None :
               if len(self.__string) > 0 :
                  if i == 'O' and self.__string[-1] == 'O' :
                     continue
               self.__string += i

   def get_string(self) :
      return self.__string

class BreakBlock(object) :
   def __init__(self, _vm) :
      self._ins = []
      self._vm = _vm

      self._ops = []

      self._fields = {}
      self._methods = {}

   def get_ops(self) :
      return self._ops

   def get_fields(self) :
      return self._fields
   
   def get_methods(self) :
      return self._methods

   def push(self, ins) :
      self._ins.append(ins)

   def show(self) :
      for i in self._ins :
         print "\t\t",
         i.show(0)

##### DVM ######

MATH_DVM_RE = []
for i in dvm.MATH_DVM_OPCODES :
   MATH_DVM_RE.append( (re.compile( i ), dvm.MATH_DVM_OPCODES[i]) )

DVM_TOSTRING = { "O" : dvm.MATH_DVM_OPCODES.keys(),
                 "I" : dvm.INVOKE_DVM_OPCODES,
                 "G" : dvm.FIELD_READ_DVM_OPCODES,
                 "P" : dvm.FIELD_WRITE_DVM_OPCODES,
               }

class DVMBreakBlock(BreakBlock) : 
   def __init__(self, _vm) :
      super(DVMBreakBlock, self).__init__(_vm)

   def analyze(self) :

      for i in self._ins :
         for mre in MATH_DVM_RE :
            if mre[0].match( i.get_name() ) :
               self._ops.append( mre[1] )
               break

##### JVM ######
FIELDS = {
            "getfield" : "R",
            "getstatic" : "R",
            "putfield" : "W",
            "putstatic" : "W",
         }

METHODS = [ "invokestatic", "invokevirtual", "invokespecial" ]

MATH_JVM_RE = []
for i in jvm.MATH_JVM_OPCODES :
   MATH_JVM_RE.append( (re.compile( i ), jvm.MATH_JVM_OPCODES[i]) )

JVM_TOSTRING = { "O" : jvm.MATH_JVM_OPCODES.keys(),
                 "I" : jvm.INVOKE_JVM_OPCODES,
                 "G" : jvm.FIELD_READ_JVM_OPCODES,
                 "P" : jvm.FIELD_WRITE_JVM_OPCODES,
               }

class JVMBreakBlock(BreakBlock) : 
   def __init__(self, _vm) :
      super(JVMBreakBlock, self).__init__(_vm)

      self.__info = { 
                        "F" : [ "get_field_descriptor", self._fields, ContextField ],
                        "M" : [ "get_method_descriptor", self._methods, ContextMethod ],
                    }

   def analyze(self) :
      ctt = []

      for i in self._ins :
         v = self.trans(i)
         if v != None :
            ctt.append( v )

         t = ""

         for mre in MATH_JVM_RE :
            if mre[0].match( i.get_name() ) :
               self._ops.append( mre[1] )
               break

         # Woot it's a field !
         if i.get_name() in FIELDS :
            t = "F" 
         elif i.get_name() in METHODS :
            t = "M"

         if t != "" :
            o = i.get_operands()
            desc = getattr(self._vm, self.__info[t][0])( o[0], o[1], o[2] )

            # It's an external 
            if desc == None :
               desc = ExternalFM( o[0], o[1], o[2] )

            if desc not in self.__info[t][1] :
               self.__info[t][1][desc] = []

            if t == "F" :
               self.__info[t][1][desc].append( self.__info[t][2]( FIELDS[ i.get_name() ][0] ) )
            elif t == "M" :
               self.__info[t][1][desc].append( self.__info[t][2]() )

      for i in self._fields :
         for k in self._fields[i] :
            k.set_details( ctt )

      for i in self._methods : 
         for k in self._methods[i] :
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

class GVM_BCA :
   def __init__(self, _vm, _method) :
      self.__vm = _vm
      self.__method = _method

      
      BO = { "B_O" : jvm.BREAK_JVM_OPCODES, "B_O_C" : JVMBreakBlock, "TS" : JVM_TOSTRING }
      if self.__vm.get_type() == "DVM" :
         BO = { "B_O" : dvm.BREAK_DVM_OPCODES, "B_O_C" : DVMBreakBlock, "TS" : DVM_TOSTRING }

      self.__TS = ToString( BO[ "TS" ] )

      code = self.__method.get_code()

      current_bb = BO["B_O_C"]( self.__vm )
      self.__bb = [ current_bb ]

      BO_RE = []
      for i in BO["B_O"] :
         BO_RE.append( re.compile( i ) )

      bc = code.get_bc()
      for i in bc.get() :
         name = i.get_name()

         match = False
         for j in BO_RE :
            if j.match(name) != None :
               match = True
               break

         # String construction
         self.__TS.push( name )
         
         current_bb.push( i )
         if match == True :
            current_bb.analyze()
   
            current_bb = BO["B_O_C"]( self.__vm )
            self.__bb.append( current_bb ) 
     
      if len( self.__bb ) > 1 :
         self.__bb.pop(-1)

      self.show()

   def get_bb(self) :
      return self.__bb

   def get_ts(self) :
      return self.__TS.get_string()

   def get_method(self) :
      return self.__method

   def get_op(self, op) :
      return []

   def get_ops(self) :
      l = []
      for i in self.__bb :
         for j in i.get_ops() :
            l.append( j )
      return l

   def show(self) :
      print "METHOD", self.__method.get_class_name(), self.__method.get_name(), self.__method.get_descriptor()
      print "\tTOSTRING = ", self.__TS.get_string()
      
      for i in self.__bb :
         print "\t", i, i.get_ops()
         i.show()
      
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
      self.__methods = []
      self.__hmethods = {}
      for i in _vm.get_methods() :
         x = GVM_BCA( _vm, i )
         self.__methods.append( x )
         self.__hmethods[ i ] = x

   def show(self) :
      for i in self.__methods :
         i.show()

   def get(self, method) :
      return self.__hmethods[ method ]

   def get_op(self, op) :
      return [ (i.get_method(), i.get_op(op)) for i in self.l ]

   def get_ops(self, method) :
      return [ (i.get_method(), i.get_ops()) for i in self.l ]
