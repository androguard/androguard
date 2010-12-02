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

import re, random, string

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
   def __init__(self, _vm, idx) :
      self._vm = _vm
      self._start = idx
      self._end = self._start 

      self._ins = []
      
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
      self._end += ins.get_length()

   def get_start(self) :
      return self._start

   def get_end(self) :
      return self._end

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

BREAK_JVM_OPCODES_RE = []
for i in jvm.BREAK_JVM_OPCODES :
   BREAK_JVM_OPCODES_RE.append( re.compile( i ) )
     
class Stack :
   def __init__(self) :
      self.__elems = []

   def push(self, elem) :
      self.__elems.append( elem )

   def get(self) :
      return self.__elems[-1]

   def pop(self) :
      return self.__elems.pop(-1)

   def nil(self) :
      return len(self.__elems) == 0

   def show(self) :
      nb = 0

      if len(self.__elems) == 0 :
         print "\t--> nil"

      for i in self.__elems :
         print "\t-->", nb, ": ", i
         nb += 1


def push_objectref(_vm, ins, special, stack) :
   value = "OBJ_REF_@_%d" % special
   stack.push( value )

   return []

def push_integer_i(_vm, ins, special, stack) :
   value = ins.get_operands()
   stack.push( value )

   return []

def push_integer_d(_vm, ins, special, stack) :
   stack.push( special )

   return []

def push_integer_l(_vm, ins, special, stack) :
   stack.push( "VARIABLE_LOCAL_@_%d" % special )
   return []

def push_integer_l_i(_vm, ins, special, stack) :
   stack.push( "VARIABLE_LOCAL_@_%d" % ins.get_operands() )

   return []

def pop_objectref(_vm, ins, special, stack) :
   return [ stack.pop() ]

def putfield(_vm, ins, special, stack) :
   return [ stack.pop() ]

def getfield(_vm, ins, special, stack) :
   l = [ stack.pop() ]
   stack.push( "FIELD" )

   return l

def getstatic(_vm, ins, special, stack) :
   stack.push( "FIELD_STATIC" )

   return []

def new(_vm, ins, special, stack) :
   stack.push( "NEW_OBJ" )
   return []

def dup(_vm, ins, special, stack) :
   stack.push( stack.get() )
   return []

def ldc(_vm, ins, special, stack) :
   stack.push( "STRING" )
   return []

def invokespecial(_vm, ins, special, stack) :
   desc = ins.get_operands()[-1]
   param = desc[1:desc.find(")")]
   ret = desc[desc.find(")")+1:]

   print "DESC --->", param, calc_nb( param ), ret, calc_nb( ret )

   for i in range(0, calc_nb( param )) :
      stack.pop()

   stack.pop()
                     
   for i in range(0, calc_nb( ret )):
      stack.push( "E" )

   return []

def set_objectref(_vm, ins, special, stack) :
   print "SET OBJECT REF ", special, " --> ", stack.pop() 
   return []

def set_objectref_i(_vm, ins, special, stack) :
   print "SET OBJECT REF ", ins.get_operands(), " --> ", stack.pop()
   return []

def calc_nb(info) :
   if info == "" or info == "V" :
      return 0

   if ";" in info :
      n = 0
      for i in info.split(";") :
         if i != "" :
            n += 1
      return n 
   else :
      return len(info)

INSTRUCTIONS_ACTIONS = { 
         "aload_0" : [ { push_objectref : 0 } ],
         
         "bipush" :  [ { push_integer_i : None } ],
         "sipush" :  [ { push_integer_i : None } ],
         
         "iconst_0" : [ { push_integer_d : 0 } ], 
         "iconst_3" : [ { push_integer_d : 3 } ],

         "iload" : [ { push_integer_l_i : None } ],
         "iload_1" : [ { push_integer_l : 1 } ], 
         "iload_2" : [ { push_integer_l : 2 } ], 
         "iload_3" : [ { push_integer_l : 3 } ], 
         
         "istore" : [ { set_objectref_i : None } ],

         "istore_2" : [ { set_objectref : 2 } ],
         "istore_3" : [ { set_objectref : 3 } ],
         
         "invokespecial" : [ { invokespecial : None } ], 
         "invokevirtual": [ { invokespecial : None } ], 
         
         "putfield" : [ { putfield : None }, { pop_objectref : None } ],
         "getfield" : [ { getfield : None } ],
         
         "getstatic" : [ { getstatic : None } ],

         "new" : [ { new : None } ],
         
         "dup" : [ { dup : None } ],

         "ldc" : [ { ldc : None } ],
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
   def __init__(self, start, _vm, _method, _context) :
      self.__vm = _vm
      self.__method = _method
      self.__context = _context

      self.__stack = Stack()

      self.__break = []
      self.__ins = []

      self.__fathers = []
      self.__childs = []

      self.__start = start
      self.__end = self.__start

      self.__break_blocks = []

      self.__free_blocks_offsets = []

      self.__name = "%s-BB@0x%x" % (self.__method.get_name(), self.__start)

   def get_method(self) :
      return self.__method

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

   def next_free_block_offset(self, idx=0) :
      print idx, self.__free_blocks_offsets
      for i in self.__free_blocks_offsets :
         if i > idx :
            return i
      return -1

   def get_random_free_block_offset(self) :
      return self.__free_blocks_offsets[ random.randint(0, len(self.__free_blocks_offsets) - 1) ]

   def get_random_free_break_block(self) :
      for i in self.__break_blocks :
         if i.get_free() == True :
            return i
      return None

   def get_random_break_block(self) :
      return self.__break_blocks[ random.randint(0, len(self.__break_blocks) - 1) ]

   def get_break_block(self, idx) :
      for i in self.__break_blocks :
         if idx >= i.get_start() and idx <= i.get_end() :
            return i
      return None

   def analyze_break_blocks(self) :
      idx = self.get_start()

      current_break = JVMBreakBlock( self.__vm, idx )
      self.__break_blocks.append(current_break)
      for i in self.__ins :
         name = i.get_name()

         ##################### Break Block ########################
         match = False
         for j in BREAK_JVM_OPCODES_RE :
            if j.match(name) != None :
               match = True
               break

         current_break.push( i )
         if match == True :
            current_break.analyze()
            current_break = JVMBreakBlock( self.__vm, current_break.get_end() )

            self.__break_blocks.append( current_break )
         #########################################################

         idx += i.get_length()

   def analyze(self) :
      idx = 0
      for i in self.__ins :
         if "load" in i.get_name() or "store" in i.get_name() :
            action = i.get_name()

            access_flag = [ "R", "load" ]
            if "store" in action : 
               access_flag = [ "W", "store" ]

            if "_" in action :
               name = i.get_name().split(access_flag[1])
               value = name[1][-1]
            else :
               value = i.get_operands()

            variable_name = "%s-%s" % (i.get_name()[0], value)
            
            self.__context.get_tainted_variables().add( variable_name, TAINTED_LOCAL_VARIABLE, self.__method )
            self.__context.get_tainted_variables().push_info( TAINTED_LOCAL_VARIABLE, variable_name, (access_flag[0], idx, self, self.__method) ) 
         if i.get_name() in FIELDS :
            o = i.get_operands()
            desc = getattr(self.__vm, "get_field_descriptor")(o[0], o[1], o[2])

            # It's an external 
            if desc == None :
               desc = ExternalFM( o[0], o[1], o[2] )

#               print "RES", res, "-->", desc.get_name()
            self.__context.get_tainted_variables().push_info( TAINTED_FIELD, desc, (FIELDS[ i.get_name() ][0], idx, self, self.__method) )
         
         idx += i.get_length()

   def analyze_code(self) :
      stack = Stack()

      self.__free_blocks_offsets.append( self.get_start() )

      idx = 0
      for i in self.__ins :
         res = []

         try : 
            print i.get_name(), i.get_name() in INSTRUCTIONS_ACTIONS
            for actions in INSTRUCTIONS_ACTIONS[ i.get_name() ] :
               for action in actions :
                  x = action( self.__vm, i, actions[action], stack )
                  for val in x :
                     res.append( val )

            stack.show()
         except KeyError :
            print "[[[[ %s is not in INSTRUCTIONS_ACTIONS ]]]]" % i.get_name()

         idx += i.get_length()

         if stack.nil() == True and i != self.__ins[-1] :
            self.__free_blocks_offsets.append( idx + self.get_start() )

   def show(self) :
      print "\t@", self.__name
      
      idx = 0
      nb = 0
      for i in self.__ins :
         print "\t\t", nb, idx,
         i.show(nb)
         nb += 1
         idx += i.get_length()

      print ""
      print "\t\tFree blocks offsets --->", self.__free_blocks_offsets
      print "\t\tBreakBlocks --->", len(self.__break_blocks)

      print "\t\tF --->", ', '.join( i.get_name() for i in self.__fathers )
      print "\t\tC --->", ', '.join( i.get_name() for i in self.__childs )

class JVMBreakBlock(BreakBlock) : 
   def __init__(self, _vm, idx) :
      super(JVMBreakBlock, self).__init__(_vm, idx)
      
      self.__info = { 
                        "F" : [ "get_field_descriptor", self._fields, ContextField ],
                        "M" : [ "get_method_descriptor", self._methods, ContextMethod ],
                    }

   
   def get_free(self) :
      if self._ins == [] :
         return False

      if "store" in self._ins[-1].get_name() :
         return True
      elif "putfield" in self._ins[-1].get_name() :
         return True

      return False

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


TAINTED_LOCAL_VARIABLE = 0
TAINTED_FIELD = 1
class Path :
   def __init__(self, info) :
      self.__access_flag = info[0]
      self.__idx = info[1]
      self.__bb = info[2]
      self.__method = info[3]

   def get_access_flag(self) :
      return self.__access_flag

   def get_idx(self) :
      return self.__idx

   def get_bb(self) :
      return self.__bb

   def get_method(self) :
      return self.__method

class TaintedVariable :
   def __init__(self, var, _type) :
      self.__var = var
      self.__type = _type

      self.__paths = []

   def get_type(self) :
      return self.__type

   def get_info(self) :
      if self.__type == TAINTED_FIELD :
         return [ self.__var.get_class_name(), self.__var.get_name(), self.__var.get_descriptor() ]

   def push(self, info) :
      self.__paths.append( Path( info ) )

   def get_paths(self) :
      for i in self.__paths :
         yield i

class TaintedVariables :
   def __init__(self, _vm) :
      self.__vm = _vm
      self.__vars = {}

   def get_local_variables(self, _method) :
      return self.__vars[ _method ]

   def get_field(self, class_name, name, descriptor) :
      for i in self.__vars :
         if isinstance( self.__vars[i], dict ) == False :
            if i.get_class_name() == class_name and i.get_name() == name and i.get_descriptor() == descriptor :
               return self.__vars[i]
      return None

   def add(self, var, _type, _method=None) :
      if _type == TAINTED_FIELD :
         self.__vars[ var ] = TaintedVariable( var, _type )
      elif _type == TAINTED_LOCAL_VARIABLE :
         if _method not in self.__vars :
            self.__vars[ _method ] = {}

         if var not in self.__vars[ _method ] : 
            self.__vars[ _method ][ var ] = TaintedVariable( var, _type )
      else :
         raise("ooop")

   def push_info(self, _type, var, info, _method=None) :
      try :
         if _type == TAINTED_FIELD : 
            self.__vars[ var ].push( info ) 
         elif _type == TAINTED_LOCAL_VARIABLE :
            self.__vars[ info[-1] ][ var ].push( info )
         else :
            raise("ooop")
      except KeyError :
         pass

   def show(self) :
      print "TAINTED FIELDS :"

      for k in self.__vars :
         if isinstance( self.__vars[k], dict ) == False :
            print "\t -->", self.__vars[k].get_info()
            for path in self.__vars[k].get_paths() :
               print "\t\t =>", path.get_access_flag(), path.get_bb().get_name(), path.get_idx()


      print "TAINTED LOCAL VARIABLES :"
      for k in self.__vars :
         if isinstance( self.__vars[k], dict ) == True :
            print "\t -->", k.get_class_name(), k.get_name(), k.get_descriptor()
            for var in self.__vars[k] :
               print "\t\t ", var
               for path in self.__vars[k][var].get_paths() :
                  print "\t\t\t =>", path.get_access_flag(), path.get_bb().get_name(), path.get_idx()

class BasicBlocks :
   def __init__(self, _vm, _tv) :
      self.__vm = _vm
      self.__tainted_variables = _tv

      self.__bb = []

   def push(self, bb):
      self.__bb.append( bb )

   def get_basic_block(self, idx) :
      for i in self.__bb :
         if idx >= i.get_start() and idx <= i.get_end() :
            return i
      return None

   def get_tainted_variables(self) :
      return self.__tainted_variables

   def get(self) :
      for i in self.__bb :
         yield i

class GVM_BCA :
   def __init__(self, _vm, _method, tv) :
      self.__vm = _vm
      self.__method = _method

      self.__tainted_variables = tv

      BO = { "BasicOPCODES" : jvm.BRANCH2_JVM_OPCODES, "BasicClass" : JVMBasicBlock, 
             "TS" : JVM_TOSTRING }
      if self.__vm.get_type() == "DVM" :
         BO = { "TS" : DVM_TOSTRING }

      self.__TS = ToString( BO[ "TS" ] )
      
      BO["BasicOPCODES_H"] = []
      for i in BO["BasicOPCODES"] :
         BO["BasicOPCODES_H"].append( re.compile( i ) )

      code = self.__method.get_code()

      self.__basic_blocks = BasicBlocks( self.__vm, self.__tainted_variables )
      current_basic = BO["BasicClass"]( 0, self.__vm, self.__method, self.__basic_blocks )
      self.__basic_blocks.push( current_basic )
      
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
            current_basic.analyze_break_blocks()
            current_basic.analyze_code()

            current_basic = BO["BasicClass"]( current_basic.get_end(), self.__vm, self.__method, self.__basic_blocks )
            self.__basic_blocks.push( current_basic )
      
      current_basic.analyze_break_blocks()
      current_basic.analyze_code()

      for i in self.__basic_blocks.get() :
         i.set_childs()

      for i in self.__basic_blocks.get() :
         i.analyze()

   def get_free_before_offset(self, idx=0) :
      for i in self.__basic_blocks.get() :
         if i.get_end() <= idx :
            x = i.get_random_free_break_block()
            if x != None :
               return x.get_end()
      return -1


   def get_free_block_offset(self, idx=0) :
      for i in self.__basic_blocks.get() :
         if i.get_start() >= idx :
            x = i.get_random_free_block_offset()
            return x
      return -1

   def next_free_block_offset(self, idx=0) :
      for i in self.__basic_blocks.get() : 
         if i.get_start() >= idx :
            x = i.next_free_block_offset( idx )
            print x, idx
            if x != -1 :
               return x
      return -1

   def get_break_block(self, idx) :
      for i in self.__basic_blocks.get() :
         if idx >= i.get_start() and idx <= i.get_end() :
            return i.get_break_block( idx )
      return None

   def get_bb(self) :
      return self.__break_blocks

   def get_ts(self) :
      return self.__TS.get_string()

   def get_method(self) :
      return self.__method

   def get_op(self, op) :
      return []

   def get_local_variables(self) :
      return self.__tainted_variables.get_local_variables( self.__method )

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
   
      self.__basic_blocks.get_tainted_variables().show()
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
      self.__vm = _vm

      self.__tainted_variables = TaintedVariables( self.__vm ) 
      for i in self.__vm.get_fields() :
         self.__tainted_variables.add( i, TAINTED_FIELD )
      
      self.__methods = []
      self.__hmethods = {}
      self.__nmethods = {}

      for i in self.__vm.get_methods() :
         x = GVM_BCA( self.__vm, i, self.__tainted_variables )
         self.__methods.append( x )
         self.__hmethods[ i ] = x
         self.__nmethods[ i.get_name() ] = x

   def get_like_field(self) :
      return [ random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ]),
               "ACC_PUBLIC",
               "I"
             ]

   def get_init_method(self) :
      m = self.__vm.get_method("<init>")
      return m[0]

   def get_random_integer_value(self, method, descriptor) :
      return 0

   def get_free_end_offset(self, method, idx=0) :
      # We would like a specific free offset in a method
      try :
         return self.__hmethods[ method ].get_free_end_offset( idx )
      except KeyError :
         # We haven't found the method ...
         return -1

   def get_free_before_offset(self, method, idx=0) :
      # We would like a specific free offset in a method
      try :
         return self.__hmethods[ method ].get_free_before_offset( idx )
      except KeyError :
         # We haven't found the method ...
         return -1

   def next_free_block_offset(self, method, idx=0) :
      # We would like a specific free offset in a method
      try :
         return self.__hmethods[ method ].next_free_block_offset( idx )
      except KeyError :
         # We haven't found the method ...
         return -1

   def get_free_block_offset(self, method, idx=0) :
      # Random method "." to get a free offset
      if method == "." :
         for i in self.__hmethods :
            if random.randint(0, 1) == 1 :
               return self.__hmethods[i].get_free_block_offset(idx)
         return self.__methods[0].get_free_block_offset(idx)

      # We would like a specific free offset in a method
      try :
         return self.__hmethods[ method ].get_free_block_offset( idx )
      except KeyError :
         # We haven't found the method ...
         return -1

   def get_free_relative_offset(self, method, idx=0) :
      value = self.get_free_offset( method, idx )

      code = method.get_code()
      return code.get_relative_idx( value )

   def get_tainted_field(self, class_name, name, descriptor) :
      return self.__tainted_variables.get_field( class_name, name, descriptor )

   def show(self) :
      for i in self.__methods :
         i.show()

   def get(self, method) :
      return self.__hmethods[ method ]

   def get_op(self, op) :
      return [ (i.get_method(), i.get_op(op)) for i in self.l ]

   def get_ops(self, method) :
      return [ (i.get_method(), i.get_ops()) for i in self.l ]
