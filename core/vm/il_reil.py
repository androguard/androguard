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

import random, string
import opaque

REIL_TYPE_REGISTER = 0
REIL_TYPE_LITERAL = 1
REIL_TYPE_OFFSET = 2

class REIL_REGISTER :
   def __init__(self, name, size=4, value=0) :
      self.__name = name
      self.__size = size
      self.__type = REIL_TYPE_REGISTER
      self.__value = value

   def get_name(self) :
      return self.__name

   def get_size(self) :
      return self.__size

   def get_type(self) :
      return self.__type

   def get_value(self) :
      return self.__value

   def get_str(self) :
      return "%s (%d)" % (self.__name, self.__size)

class REIL_LITERAL :
   def __init__(self, value, size=4) :
      self.__value = value
      self.__size = size
      self.__type = REIL_TYPE_LITERAL

   def get_value(self) :
      return self.__value

   def get_size(self) :
      return self.__size

   def get_type(self) :
      return self.__type

   def get_str(self) :
      return "0x%x (%d)" % (self.__value, self.__size)

class REIL_OFFSET :
   def __init__(self, value, size=4) :
      self.__value = value
      self.__size = size
      self.__type = REIL_TYPE_OFFSET

   def get_value(self) :
      return self.__value

   def get_size(self) :
      return self.__size

   def get_type(self) :
      return self.__type

   def get_str(self) :
      return "0x%x (%d)" % (self.__value, self.__size)

class REIL_BASE(object) :
   def get_registers(self) :
      l = []

      if isinstance( self.rcv0, REIL_REGISTER ) :
         l.append( self.rcv0 )


      if isinstance( self.rcv1, REIL_REGISTER ) :
         l.append( self.rcv1 )

      if isinstance( self.rcvout, REIL_REGISTER ) :
         l.append( self.rcvout )

      return l

   def get_size(self) :
      return 1

   def get_name(self) :
      return self.name

   def view(self) :
      if self.rcv0 == None and self.rcv1 == None and self.rcvout == None :
         print "%s ( , , , )" % (self.name)
      elif self.rcv1 == None :
         print "%s ( %s, , %s )" % (self.name, self.rcv0.get_str(), self.rcvout.get_str())
      else :
         print "%s ( %s, %s, %s )" % (self.name, self.rcv0.get_str(), self.rcv1.get_str(), self.rcvout.get_str())

class REIL_ADD(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "ADD"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_AND(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "AND"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_BISZ(REIL_BASE) :
   def __init__(self, rcv0, rcvout) :
      self.name = "BISZ"
      
      self.rcv0 = rcv0
      self.rcv1 = None
      self.rcvout = rcvout

class REIL_BRSH(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "BRSH"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_BLSH(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "BLSH"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_DIV(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "DIV"
      
      raise("OOPS")

class REIL_JCC(REIL_BASE) :
   def __init__(self, rcv0, rcvout) :
      self.name = "JCC"
      
      self.rcv0 = rcv0
      self.rcv1 = None
      self.rcvout = rcvout

class REIL_LDM(REIL_BASE) :
   def __init__(self, rcv0, rcvout) :
      self.name = "LDM"
      
      self.rcv0 = rcv0
      self.rcv1 = None
      self.rcvout = rcvout

class REIL_MOD(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "MOD"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_MUL(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "MUL"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_NOP(REIL_BASE) :
   def __init__(self) :
      self.name = "NOP"
      
      self.rcv0 = None 
      self.rcv1 = None
      self.rcvout = None

class REIL_OR(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "OR"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_STM(REIL_BASE) :
   def __init__(self, rcv0, rcvout) :
      self.name = "STM"

      self.rcv0 = rcv0
      self.rcv1 = None
      self.rcvout = rcvout

class REIL_STR(REIL_BASE) :
   def __init__(self, rcv0, rcvout) :
      self.name = "STR"
      
      self.rcv0 = rcv0
      self.rcv1 = None
      self.rcvout = rcvout

class REIL_SUB(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "SUB"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

class REIL_UNDEF(REIL_BASE) :
   def __init__(self) :
      self.name = "UNDEF"

      self.rcv0 = None
      self.rcv1 = None
      self.rcvout = None

class REIL_UNKN(REIL_BASE) :
   def __init__(self) :
      self.name = "UNKN"

      self.rcv0 = None
      self.rcv1 = None
      self.rcvout = None

class REIL_XOR(REIL_BASE) :
   def __init__(self, rcv0, rcv1, rcvout) :
      self.name = "XOR"
      
      self.rcv0 = rcv0
      self.rcv1 = rcv1
      self.rcvout = rcvout

def INIT_VAR(l) :
   return [ REIL_STR( REIL_LITERAL(i.get_value(), i.get_size()), i) for i in l ]

class BPTR :
   def __init__(self, prng) :
      self.__RI = []
      
      var_j = REIL_REGISTER( "j", 4, 0 )
      var_germe = REIL_REGISTER( "GERME", 4, prng["GERME"] )
      var_a = REIL_REGISTER( "A", 4, prng["A"] )
      var_c = REIL_REGISTER( "C", 4, prng["C"] )
      var_m =  REIL_REGISTER( "M", 4, prng["M"] )
      var_iter = REIL_REGISTER( "ITER", 4, prng["ITER"] )
      var_tmp = REIL_REGISTER( "TMP", 4 )

      for i in INIT_VAR( [ var_j, var_germe, var_a, var_c, var_m, var_iter ] ) :
         self.__RI.append( i )


      self.__RI.append( REIL_SUB(var_j, var_iter, var_tmp) )
      self.__RI.append( REIL_BISZ(var_tmp, var_tmp) )
      branch_1 = [ REIL_JCC(var_tmp, REIL_LITERAL(0)), len(self.__RI) - 2 ]

      self.__RI.append( branch_1[0] )

      # GERME = (A * GERME + C) % M
      self.__RI.append( REIL_MUL(var_a, var_germe, var_germe) )
      self.__RI.append( REIL_ADD(var_germe, var_c, var_germe) )
      self.__RI.append( REIL_MOD(var_germe, var_m, var_germe) )

      self.__RI.append( REIL_ADD(var_j, REIL_LITERAL(1), var_j) )
      branch_2 = [ REIL_JCC(REIL_LITERAL(1), REIL_OFFSET( branch_1[1] ) ) ]

      self.__RI.append( branch_2[0] )

      branch_1[0].rcvout = REIL_OFFSET( len(self.__RI) )

      nb = 0
      for i in self.__RI :
         print "0x%x" % nb, 
         i.view()
         nb += 1

      self.__result = var_germe

   def get(self) :
      return [ "int", "", self.__RI, self.__result ]

class MTR :
   def __init__(self, math) : 
      self.__math = math
      self.__RI = []
      self.__RR = {}
      self.__result = ""

      self.__b_op = { '+' : REIL_ADD,
                      '-' : REIL_SUB
                    }
   
      self.run()

   def run(self) :
      for i in self.__math :
         if i[0] not in self.__RR :
            self.__RR[ i[0] ] = REIL_REGISTER( i[0], 4 )

         if len(i) == 3 :
            r = REIL_STR( REIL_LITERAL( i[2], 4 ), self.__RR[ i[0] ] )
         elif len(i) == 5 :
            r = self.__b_op[i[3]]( self.__RR[ i[2] ], REIL_LITERAL( i[4], 4 ), self.__RR[ i[0] ] )
         else :
            raise('ooops')

         self.__RI.append( r )

      for i in self.__RI :
         if i.rcvout.get_name() == self.__math[-1][0] :
            self.__result = i.rcvout
            break

   def get(self) :
      return [ "int", "", self.__RI, self.__result ]

# STR LX, , RX --> BASIC MATH RX
class MetaREIL :
   def __init__(self, ori) :
      self.__ORI = ori
      self.__RI = []
      self.__NEW_RI = []

      if self.__ORI[2][0].get_name() == "STR" :
         if self.__ORI[2][0].rcv0.get_type() == REIL_TYPE_LITERAL :
            oint = opaque.INT( self.__ORI[2][0].rcv0.get_value(), \
                               prefix=random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ] ),\
                               size=2 ).run()
            print oint
            mtir = MTR( oint )
            print mtir.get()
            
            _, _, ins, ret = mtir.get()
            for i in ins :
               self.__NEW_RI.append( i )

            self.__NEW_RI.append( REIL_STR( ret, self.__ORI[2][0].rcvout ) )

      self.__RI = self.__NEW_RI + self.__ORI[2]

      for i in self.__RI :
         i.view()

   def get(self) :
      return [ self.__ORI[0], self.__ORI[1], self.__RI, self.__ORI[3] ] 

class STR_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value = 0;\n"

      self.__buff += VM.get_pos_reg( 3, "x" )
      self.__buff += VM.get_value( 1, "value" )
      self.__buff += VM.set_reg( "x", "value" )

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- STR\\n\");\n"

class ADD_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value1 = 0, value2 = 0;\n"
     
      self.__buff += VM.get_pos_reg( 3, "x" )

      self.__buff += VM.get_value( 1, "value1")
      self.__buff += VM.get_value( 2, "value2")

      self.__buff += "value1 = value1 + value2;\n"
      self.__buff += VM.set_reg( "x", "value1" )

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- ADD\\n\");\n"

class SUB_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value1 = 0, value2 = 0;\n"
   
      self.__buff += VM.get_pos_reg( 3, "x" )
      
      self.__buff += VM.get_value( 1, "value1")
      self.__buff += VM.get_value( 2, "value2")

      self.__buff += "value1 = value1 - value2;\n"
      self.__buff += VM.set_reg( "x", "value1" )

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- SUB\\n\");\n"

class BISZ_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value = 0;\n"
   
      self.__buff += VM.get_pos_reg( 3, "x" )
      
      self.__buff += VM.get_value( 1, "value")

      self.__buff += "if (value != 0) { " + VM.set_reg( "x", "0" ) + "}"
      self.__buff += "else {" + VM.set_reg( "x", "1" ) + "}"

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- BISZ\\n\");\n"

class JCC_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value = 0;\n"

      self.__buff += VM.get_value( 1, "value")


      self.__buff += "if (value != 0) {" + VM.set_idx( 3 ) + "}"

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- JCC\\n\");\n"

class MUL_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value1 = 0, value2 = 0;\n"
   
      self.__buff += VM.get_pos_reg( 3, "x" )
      
      self.__buff += VM.get_value( 1, "value1")
      self.__buff += VM.get_value( 2, "value2")

      self.__buff += "value1 = value1 * value2;\n"
      self.__buff += VM.set_reg( "x", "value1" ) 

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- MUL\\n\");\n" 

class MOD_TO_JAVA :
   def __init__(self, VM) :
      self.__buff = "int x = 0;\n"
      self.__buff += "int value1 = 0, value2 = 0;\n"
   
      self.__buff += VM.get_pos_reg( 3, "x" )
      
      self.__buff += VM.get_value( 1, "value1")
      self.__buff += VM.get_value( 2, "value2")

      self.__buff += "value1 = value1 % value2;\n"
      self.__buff += VM.set_reg( "x", "value1" )

   def get_raw(self) :
      return self.__buff + "\n" + "System.out.println(\"---- MOD\\n\");\n"

class REIL_TO_JAVA :
   def __init__(self, op, VM) : 
      self.__OP = { "STR" : STR_TO_JAVA,
                    "ADD" : ADD_TO_JAVA,
                    "SUB" : SUB_TO_JAVA,
                    "BISZ" : BISZ_TO_JAVA,
                    "JCC" : JCC_TO_JAVA,
                    "MUL" : MUL_TO_JAVA,
                    "MOD" : MOD_TO_JAVA,
                  }

      if op in self.__OP :
         self.__buff = self.__OP[op]( VM ).get_raw()
      else :
         print op
         raise("oops")

   def get_raw(self) :
      return self.__buff + "\n"
