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


from jvm import JVMFormat, BREAK_JAVA_OPCODES, BRANCH_JAVA_OPCODES, MATH_JAVA_OPCODES, INVERT_JAVA_OPCODES

class JavaBreakBlock : 
   def __init__(self) :
      self.__ins = []

   def push(self, ins) :
      self.__ins.append(ins)

   def freq(self) :
      #l = []
      branch = [ 0, 0 ]
      for i in self.__ins :
         if i.get_name() in MATH_JAVA_OPCODES :
            branch[0] = branch[0] + ( INVERT_JAVA_OPCODES[ i.get_name() ] << branch[1] )
            branch[1] += 8

      #l.append( branch )

      return branch[0]

   def show(self) :
      for i in self.__ins : 
         print "\t", i.get_name(), i.get_operands()

class JBCA :
   def __init__(self, _vm, _method) :
      self.__method = _method

      code = self.__method.get_code()

      current_bb = JavaBreakBlock()
      self.__bb = [ current_bb ]

      bc = code.get_bc()
      for i in bc.get() :
         name = i.get_name()
         m_name = name.split("_")[0]

         current_bb.push( i )
         if name in BREAK_JAVA_OPCODES :
            current_bb = JavaBreakBlock()
            self.__bb.append( current_bb ) 
     
         elif m_name in BREAK_JAVA_OPCODES :
            current_bb = JavaBreakBlock()
            self.__bb.append( current_bb )

      if len( self.__bb ) > 1 :
         self.__bb.pop(-1)

   def get_freq(self) :
      l = []
      for i in self.__bb :
         x = i.freq()
         if x != 0 :
            l.append( x )
      return l

   def get_bb(self) :
      return self.__bb

class DBCA :
   def __init__(self) :
      pass

class VMBCA :
   def __init__(self,  _vm, _method) :
      if _vm.get_type() == "JVM" :
         self.__a = JBCA( _vm, _method )

   def __getattr__(self, value) :
      return getattr( self.__a, value )
