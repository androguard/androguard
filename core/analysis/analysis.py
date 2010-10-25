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

class Analysis(object) :
   def __init__(self) :
      pass

class DBCA(Analysis) :
   def __init__(self) :
      pass

EMPTY = 0
STACK = 1

PUSH = 0
POP  = 1

LOCAL_VARIABLE = 0
NULL = 1
UNKNOWN = 2

JAVA_OPCODES_ACTIONS = { 
            "aconst_null" :             [ STACK, PUSH, NULL ],
            "aload_0" :                 [ STACK, PUSH, LOCAL_VARIABLE, 0 ],
            "aload_1" :                 [ STACK, PUSH, LOCAL_VARIABLE, 1 ],
            "aload_2" :                 [ STACK, PUSH, LOCAL_VARIABLE, 2 ],
            "areturn" :                 [ STACK, POP ],
            "astore_2" :                [ STACK, POP, LOCAL_VARIABLE, 2 ],
            "ifnonnull" :               [ EMPTY ],
            "invokevirtual" :           [ STACK, PUSH, UNKNOWN ] ,
      }

class Elem(object) :
   def __init__(self) :
      pass

class NullElem(Elem) :
   def __init__(self) :
      super(NullElem, self).__init__()

class UnknownElem(Elem) :
   def __init__(self) :
      super(UnknownElem, self).__init__()

class Memory :
   def __init__(self, nb) :
      self.__elem = []
      for i in range(0, nb) :
         self.__elem.append( Elem() )

   def get(self, idx) :
      return self.__elem[ idx ]

   def put(self, elem, idx) :
      self.__elem[idx] = elem

   def show(self) :
      print self.__elem

class JStack :
   def __init__(self, code) :
      self.__elems = []

      self.__max_stack = code.get_max_stack()
      self.__max_locals = code.get_max_locals()

      self.__locals = Memory( self.__max_locals )

   def get(self, elem_type, idx=-1) :
      if elem_type == LOCAL_VARIABLE :
         return self.__locals.get( idx )
      elif elem_type == NULL : 
         return NullElem() 
      elif elem_type == UNKNOWN :
         return UnknownElem()
      else :
         raise("error")

   def put(self, elem, elem_type, idx) :
      if elem_type == LOCAL_VARIABLE :
         self.__locals.put(elem, idx)
      else :
         raise("error")

   def push(self, elem) :
      self.__elems.insert(0, elem)

   def pop(self) :
      return self.__elems.pop(0)

   def show(self) :
      print "CURRENT_STACK", self.__elems
      print "CURRENT_LOCALS",
      self.__locals.show()

class JBCA2(Analysis) :
   def __init__(self, _class, _method) :
      super(JBCA2, self).__init__()

      self.__class = _class
      self.__method = _method

#   self.__method.show_info()


      code = self.__method.get_code()
      code.show_info()

      self.__stack = JStack(code)

      bc = code.get_bc()
      for i in bc.get() :
         name, operands = i.get_name(), i.get_operands()
         print name, operands

         if name not in JAVA_OPCODES_ACTIONS :
            raise("ooops")

         if JAVA_OPCODES_ACTIONS[name][0] == STACK :
            self._stack_handle( JAVA_OPCODES_ACTIONS[name][1:] )     
         
         self._show_stack()
         print ""

   def _show_stack(self) :
      self.__stack.show()

   def _stack_handle(self, action) :
      print "ACTION", action
      if action[0] == PUSH :
         self.__stack.push( self.__stack.get( *action[1:] ) ) #, action[2]) )
      elif action[0] == POP :
         elem = self.__stack.pop()
         if len(action) > 1 :
            self.__stack.put( elem,  action[1], action[2] )
      else :
         raise("error")


JAVA_BYTECODES_BREAK = [ "areturn", "astore", "bastore", "goto", "if", "iinc", "istore", "pop", "putfield" ]

class BreakBlock : 
   def __init__(self) :
      self.__ins = []

   def push(self, ins) :
      self.__ins.append(ins)

   def show(self) :
      for i in self.__ins : 
         print "\t", i.get_name(), i.get_operands()

class JBCA(Analysis) :
   def __init__(self, _class, _method) :
      super(JBCA, self).__init__()

      self.__class = _class
      self.__method = _method

      code = self.__method.get_code()
      code.show_info()

      current_bb = BreakBlock()
      self.__bb = [ current_bb ]

      bc = code.get_bc()
      for i in bc.get() :
         name = i.get_name()

         n_name = name
         if "_" in name :
            n_name = name.split("_")[0]

         current_bb.push( i )
         if n_name in JAVA_BYTECODES_BREAK :
            current_bb = BreakBlock()
            self.__bb.append( current_bb ) 
     
      if len( self.__bb ) > 1 :
         self.__bb.pop(-1)

      for i in self.__bb :
         print i 
         i.show()
         print ""
