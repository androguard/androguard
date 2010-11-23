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

class Stack :
   def __init__(self) :
      self.__elems = []

   def push(self, elem) :
      self.__elems.append( elem )

   def pop(self) :
      return self.__elems.pop(-1)

   def show(self) :
      nb = 0

      if len(self.__elems) == 0 :
         print "\t--> nil"

      for i in self.__elems :
         print "\t-->", nb, ": ", i
         nb += 1


TEST = { 
         "aload_0" : [ { "push_objectref" : 0 } ],
         
         "bipush" :  [ { "push_integer_i" : None } ],
         "sipush" :  [ { "push_integer_i" : None } ],
         
         "iconst_0" : [ { "push_integer_d" : 0 } ], 
         
         "iload_1" : [ { "push_integer_l" : 1 } ], 
         "iload_2" : [ { "push_integer_l" : 2 } ], 
         "iload_3" : [ { "push_integer_l" : 3 } ], 
         
         "istore_2" : [ { "pop_objectref" : None }, { "set_objectref" : 2 } ],
         "istore_3" : [ { "pop_objectref" : None }, { "set_objectref" : 3 } ],
         
         "invokespecial" : [ { "pop_callstack" : None }, { "pop_objectref" : None } ],
         
         "putfield" : [ { "putfield" : None }, { "pop_objectref" : None } ],
         "getfield" : [ { "getfield" : None } ],

         "if_icmpge" : [],
         "iadd" : [],
         "invokevirtual" : [],
       }

class ExternalMethod :
   def __init__(self, class_name, name, descriptor) :
      self.__class_name = class_name
      self.__name = name
      self.__descriptor = descriptor

   def get_name(self) :
      return "M@[%s][%s]-[%s]" % (self.__class_name, self.__name, self.__descriptor)

   def set_fathers(self, f) :
      pass

class JVMBasicBlock :
   def __init__(self, start, _vm, _context) :
      self.__vm = _vm
      self.__context = _context

      self.__stack = Stack()

      self.__break = []
      self.__ins = []

      self.__fathers = []
      self.__childs = []

      self.__start = start
      self.__end = self.__start

      self.__name = "BB@0x%x" % self.__start

   def get_name(self) :
      return self.__name

   def get_start(self) :
      return self.__start

   def get_end(self) :
      return self.__end

   def push(self, i) :
      self.__ins.append( i )
      self.__end += i.get_length()

   def push_break_block(self, b):
      self.__break.append( b )

   def set_fathers(self, f) :
      self.__fathers.append( f )

   def set_childs(self) :
      i = self.__ins[-1]
      
      if "invoke" in i.get_name() :
         self.__childs.append( ExternalMethod( i.get_operands()[0], i.get_operands()[1], i.get_operands()[2] ) )
         self.__childs.append( self.__context.get_basic_block( self.__end + 1 ) )
      elif "return" in i.get_name() :
         pass
      elif "goto" in i.get_name() :
         self.__childs.append( self.__context.get_basic_block( self.__end + 1 ) )
         self.__childs.append( self.__context.get_basic_block( i.get_operands() + (self.__end - i.get_length()) ) )
      elif "if" in i.get_name() :
         self.__childs.append( self.__context.get_basic_block( self.__end + 1 ) )
         self.__childs.append( self.__context.get_basic_block( i.get_operands() + (self.__end - i.get_length()) ) )
      else :
         raise("oops")

      for c in self.__childs :
         c.set_fathers( self )

   def analyze(self) :
      for i in self.__ins :
         if i.get_name() in FIELDS :
            o = i.get_operands()
            desc = getattr(self.__vm, "get_field_descriptor")(o[0], o[1], o[2])

            # It's an external 
            if desc == None :
               desc = ExternalFM( o[0], o[1], o[2] )

#               print "RES", res, "-->", desc.get_name()
            self.__context.get_tainted_fields().push_info( desc, (FIELDS[ i.get_name() ][0], self.get_name()) )

   def analyze2(self) :
      for i in self.__ins :
         res = []
         if i.get_name() in TEST :
            for action in TEST[i.get_name()] :
               for k in action :
                  if k == "push_objectref" :
                     value = "obj%d" % action[k] 
                     stack.push( value )
                  elif k == "push_integer_i" :
                     value = i.get_operands()
                     stack.push( value )
                  elif k == "push_integer_d" :
                     stack.push( action[k] )
                  elif k == "push_integer_l" :
                     stack.push( "VL%d" % action[k] )
                  elif k == "pop_callstack" :
                     pass #res.append( stack.pop() )
                  elif k == "pop_objectref" :
                     res.append( stack.pop() )
                  elif k == "putfield" :
                     res.append( stack.pop() )
                  elif k == "getfield" :
                     res.append( stack.pop() )
                     stack.push( "F" )
      #            elif k == "set_value" : 
      #               print "SET VALUE ", action[k], " --> ", res
      #               stack.pop()
      #               stack.pop()
                  elif k == "set_objectref" :
                     print "SET OBJECT REF ", action[k], " --> ", res
                  else : 
                     raise("iiips")
        
                  stack.show()
         else :
            raise("ooops")

   def show(self) :
      print "\t@", self.__name
      nb = 0
      for i in self.__ins :
         print nb,
         i.show(nb)
         nb += 1

      print "\t\tF --->", ', '.join( i.get_name() for i in self.__fathers )
      print "\t\tC --->", ', '.join( i.get_name() for i in self.__childs )

class JVMBreakBlock(BreakBlock) : 
   def __init__(self, _vm) :
      super(JVMBreakBlock, self).__init__(_vm)
      
      self.__info = { 
                        "F" : [ "get_field_descriptor", self._fields, ContextField ],
                        "M" : [ "get_method_descriptor", self._methods, ContextMethod ],
                    }

   
   def analyze(self) :
      ctt = []

      stack = Stack()
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
            desc = getattr(self._vm, self.__info[t][0])(o[0], o[1], o[2])

            # It's an external 
            if desc == None :
               desc = ExternalFM( o[0], o[1], o[2] )

            if desc not in self.__info[t][1] :
               self.__info[t][1][desc] = []

            if t == "F" :
               self.__info[t][1][desc].append( self.__info[t][2]( FIELDS[ i.get_name() ][0] ) )
 
#               print "RES", res, "-->", desc.get_name()
#               self.__tf.push_info( desc, [ FIELDS[ i.get_name() ][0], res ] )
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


class TaintedField :
   def __init__(self, field) :
      self.__field = field

      self.__paths = []

   def get_info(self) :
      return [ self.__field.get_class_name(), self.__field.get_name(), self.__field.get_descriptor() ]

   def push(self, info) :
      self.__paths.append( info )

   def get_paths(self) :
      return self.__paths

class TaintedFields :
   def __init__(self, _vm) :
      self.__vm = _vm
      self.__fields = {}

   def add(self, field) :
      self.__fields[ field ] = TaintedField( field )

   def push_info(self, field, info) :
      try :
         self.__fields[ field ].push( info ) 
      except KeyError :
         pass

   def show(self) :
      print "TAINTED FIELDS :"

      for k in self.__fields :
         print "\t -->", self.__fields[k].get_info()
         for path in self.__fields[k].get_paths() :
            print "\t\t =>", path

class BasicBlocks :
   def __init__(self, _vm) :
      self.__vm = _vm
      self.__bb = []

      self.__tainted_fields = TaintedFields( self.__vm ) 
      for i in self.__vm.get_fields() :
         self.__tainted_fields.add( i )

   def push(self, bb):
      self.__bb.append( bb )

   def get_basic_block(self, idx) :
      for i in self.__bb :
         if idx >= i.get_start() and idx <= i.get_end() :
            return i
      return None

   def get_tainted_fields(self) :
      return self.__tainted_fields

   def get(self) :
      for i in self.__bb :
         yield i

class GVM_BCA :
   def __init__(self, _vm, _method) :
      self.__vm = _vm
      self.__method = _method


      BO = { "BreakOPCODES" : jvm.BREAK_JVM_OPCODES, "BreakClass" : JVMBreakBlock, 
             "BasicOPCODES" : jvm.BRANCH2_JVM_OPCODES, "BasicClass" : JVMBasicBlock, 
             "TS" : JVM_TOSTRING }
      if self.__vm.get_type() == "DVM" :
         BO = { "BreakOPCODES" : dvm.BREAK_DVM_OPCODES, "BreakClass" : DVMBreakBlock, "TS" : DVM_TOSTRING }

      self.__TS = ToString( BO[ "TS" ] )
      
      BO["BreakOPCODES_H"] = []
      for i in BO["BreakOPCODES"] :
         BO["BreakOPCODES_H"].append( re.compile( i ) )
     
      BO["BasicOPCODES_H"] = []
      for i in BO["BasicOPCODES"] :
         BO["BasicOPCODES_H"].append( re.compile( i ) )

      code = self.__method.get_code()

      self.__basic_blocks = BasicBlocks( self.__vm )
      current_basic = BO["BasicClass"]( 0, self.__vm, self.__basic_blocks )
      self.__basic_blocks.push( current_basic )
      
      self.__break_blocks = []
      current_break = BO["BreakClass"]( self.__vm )
      self.__break_blocks.append(current_break)

      bc = code.get_bc()
      for i in bc.get() :
         name = i.get_name()

         ################## String construction ###################
         self.__TS.push( name )
        
         ##################### Basic Block ########################
         match = False
         for j in BO["BasicOPCODES_H"] :
            if j.match(name) != None :
               match = True
               break
         
         current_basic.push( i )
         if match == True :
            current_basic = BO["BasicClass"]( current_basic.get_end() + 1, self.__vm, self.__basic_blocks )
            self.__basic_blocks.push( current_basic )

         ##################### Break Block ########################
         match = False
         for j in BO["BreakOPCODES_H"] :
            if j.match(name) != None :
               match = True
               break

         current_break.push( i )
         if match == True :
            current_break.analyze()
            current_break = BO["BreakClass"]( self.__vm )

            self.__break_blocks.append( current_break )
         #########################################################

      for i in self.__basic_blocks.get() :
         i.set_childs()

      for i in self.__basic_blocks.get() :
         i.analyze()

   def get_bb(self) :
      return self.__break_blocks

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
    
      for i in self.__basic_blocks.get() :
         print "\t", i
         i.show()
         print ""
   
      self.__basic_blocks.get_tainted_fields().show()
      #for i in self.__break_blocks :
      #   print "\t", i
      #   i.show()

      #self.__tainted_fields.show()

      #self.show_fields()
      #self.show_methods()

      print "\n"

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
