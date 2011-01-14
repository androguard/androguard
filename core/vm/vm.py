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
from subprocess import Popen, PIPE, STDOUT                                      

import opaque, jvm 

from il_reil import MTR, BPTR, MetaPolyREIL, REIL_TO_JAVA, REIL_TYPE_REGISTER, REIL_TYPE_LITERAL

class IL_REIL_TO_JAVA :
   def __init__(self, orig_class_name, il_reil) :
      self.__bytecodes = []

      self.__orig_class_name = orig_class_name
      self.__vm_name = random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ] )

      self.__vm_format = None

      self.__RR = {}
      self.__ORR = {}
      self.__OP = {}
      self.__BT = {}

      self.__call_code = []

      self.__debug = False 

      self._analyze( il_reil )

      print self.__RR
      print self.__ORR
      print self.__OP
      print self.__BT

      print self.__bytecodes

      self._create_methods()
      self._create_call_code()

   def _create_methods(self) :
      fd = open("./VM.java", "w")

      fd.write("class VM {\n")

      fd.write("public ")

      if self.__type_return == "" :
         fd.write("void ")
      else :
         fd.write("%s " % self.__type_return)

      fd.write("%s() {\n" % self.__vm_name)
     
      self.__VAR_REG = "REG"
      self.__VAR_IREG = "IREG"
      self.__VAR_IDX = "idx"
      self.__VAR_C_IDX = "c_idx"
      self.__VAR_BC = "BC"

      fd.write("int[] %s = new int[%d];\n" % ( self.__VAR_REG, len(self.__RR) ) )

      fd.write("int[] %s = {" % self.__VAR_IREG)
      buff = ""
      for i in self.__RR :
         buff += "%d,%s," % (self.__RR[i], self.__ORR[ self.__RR[i] ]) 
      fd.write(buff[:-1])
      fd.write("};\n")

      buff = ""
      fd.write("int[][] %s = {" % self.__VAR_BC)
      for i in self.__bytecodes :
         buff += "{%s}," % str(i)[1:-1]
      fd.write(buff[:-1])
      fd.write("};\n")

      fd.write("int %s = 0;\n" % self.__VAR_IDX);
      fd.write("int %s = -1;\n" % self.__VAR_C_IDX);

      if self.__debug :
         fd.write("System.out.println(\"================START VM===============\");\n")
      
      fd.write("while(idx < BC.length) {\n")

      self.__VAR_T = "T"
      self.__VAR_S = "S"

      fd.write("int[] %s = new int[3];\n" % self.__VAR_T);
      fd.write("int[] %s = new int[3];\n" % self.__VAR_S);

      fd.write("T[0] = (BC[idx][0] & 0x00FF0000) >> 16;\n")
      fd.write("T[1] = (BC[idx][0] & 0x0000FF00) >> 8;\n")
      fd.write("T[2] = (BC[idx][0] & 0x000000FF);\n")

      fd.write("S[0] = (BC[idx][1] & 0x00FF0000) >> 16;\n")
      fd.write("S[1] = (BC[idx][1] & 0x0000FF00) >> 8;\n")
      fd.write("S[2] = (BC[idx][1] & 0x000000FF);\n")
      
      if self.__debug :
         fd.write("System.out.println( \"IDX \" + idx );\n")
         fd.write("System.out.println( \"TYPE \" + T[0] + \" \" + T[1] + \" \" + T[2] );\n")
         fd.write("System.out.println( \"SIZE \" + S[0] + \" \" + S[1] + \" \" + S[2] );\n")
         fd.write("System.out.println( \"BC \" + BC[idx][3] + \" \" + BC[idx][4] + \" \" + BC[idx][5] );\n")

      #FIXME
      for i in self.__OP :
         fd.write("if (BC[idx][2] == %d) {\n" % self.__OP[i])
         fd.write( REIL_TO_JAVA( i, self, self.__debug ).get_raw() )
         fd.write("}\n")

      if self.__debug :
         fd.write("System.out.printf(\"REG = \");\n")
         fd.write("for(int j=0; j < REG.length; j++) {\n")
         fd.write("System.out.printf(\"%d \", REG[j]);\n")
         fd.write("}\n")
         fd.write("System.out.println(\"\");\n")

      fd.write("if (%s != -1) {\n" % self.__VAR_C_IDX)
      fd.write("%s = %s;\n" % (self.__VAR_IDX, self.__VAR_C_IDX))
      fd.write("%s = -1;\n" % (self.__VAR_C_IDX))
      fd.write("}\n")

      fd.write("else {\n")
      fd.write("idx = idx + 1;\n")
      fd.write("}\n")

      fd.write("}\n")

      if self.__debug :
         fd.write("System.out.println(\"================STOP VM================\\n\");\n")

      fd.write("return REG[%s];\n" % self.__ORR[ self.__RR[ self.__register_return.get_name() ] ] )

      fd.write("}\n")

      fd.write("}\n") 
      fd.close()

      compile = Popen([ "/usr/bin/javac", "VM.java" ], stdout=PIPE, stderr=STDOUT)
      stdout, stderr = compile.communicate()
      print "COMPILATION RESULTS", stdout, stderr
      if stdout != "":
         raise("oops")

#      print "COMPILATION RESULTS", "SWAP ...."

      self.__vm_format = jvm.JVMFormat( open( "VM.class" ).read() )

   def _create_call_code(self) :
      self.__call_code.append( [ "aload_0" ] )

      method_vm = self.__vm_format.get_method(self.__vm_name)[0]
      self.__call_code.append( [ "invokevirtual", self.__orig_class_name, self.__vm_name, method_vm.get_descriptor() ] )

   def _analyze(self, il_reil) :
      self.__type_return = il_reil[0]
      self.__type_param = il_reil[1]
      self.__register_return = il_reil[3]

      nb = 0
      for i in il_reil[2] :
         print nb,
         i.view()
         nb += 1

         information_type = 0
         information_size = 0

         if i.get_name() not in self.__OP :
            self.__OP[ i.get_name() ] = self._unique_value( self.__OP )

         for r in i.get_registers() :
            if r.get_name() not in self.__RR :
               self.__RR[ r.get_name() ] = self._unique_value( self.__RR )
               self.__ORR[ self.__RR[ r.get_name() ] ] = len( self.__ORR )

         v0, v0_size, v0_type = self._get_val( i.rcv0 )
         v1, v1_size, v1_type = self._get_val( i.rcv1 )
         v2, v2_size, v2_type = self._get_val( i.rcvout )

         information_type = (self._get_type( v0_type ) << 16) + (self._get_type( v1_type ) << 8) + self._get_type( v2_type )
         information_size = (v0_size << 16) + (v1_size << 8) + v2_size
         
         self.__bytecodes.append( [ information_type, information_size, self.__OP[ i.get_name() ], v0, v1, v2 ] )

   def _get_type(self, v) :
      if v not in self.__BT :
         n_v = self._unique_value( self.__BT )
         self.__BT[ v ] = n_v

      return self.__BT[ v ]

   def _get_val(self, r) :
      if r == None :
         return 0x0, 0x0, 0x0

      if r.get_type() == REIL_TYPE_REGISTER :
         return self.__RR[ r.get_name() ], r.get_size(), r.get_type()

      return r.get_value(), r.get_size(), r.get_type()

   def _random_int(self) :
      return random.randint( 0, 0xFF )

   def _unique_value(self, h) :
      v = self._random_int()
      for k in h :
         if k == v :
            self._unique_value( h )
      return v

   def call_code(self) :
      return self.__call_code

   def get_methods(self) :
      return self.__vm_format.get_method(self.__vm_name)

   def get_operand(self, pos) :
      return self.__VAR_BC + "[" + self.__VAR_IDX + "]" + "[" + str(3 + pos - 1) + "]"

   def get_pos_reg(self, operand, variable) :
      buff = "for(int j=0; j < %s.length; j+=2) {\n" % self.__VAR_IREG
      buff +=   "if (%s[j] == %s){\n" % (self.__VAR_IREG, self.get_operand(operand))
      buff +=           "%s = %s[j + 1];\n" % (variable, self.__VAR_IREG)
      buff +=           "break;\n"
      buff +=   "}\n"
      buff += "}\n"

      return buff

   def get_value(self, operand, variable) :
      buff = "if (%s[%s] == %d) {\n" % (self.__VAR_T, operand - 1, self.__BT[REIL_TYPE_REGISTER])
      buff +=   "for(int j=0; j < %s.length; j+=2) {\n" % self.__VAR_IREG

      buff +=           "if (%s[j] == %s){\n" % (self.__VAR_IREG, self.get_operand(operand))
      buff +=                   "%s = %s[ %s[j + 1] ];\n" % (variable, self.__VAR_REG, self.__VAR_IREG)
      buff +=                           "break;\n"
      buff +=           "}\n"

      buff +=   "}\n"
      buff += "}\n"

      buff += "else {\n"
      buff += "%s = %s;\n" % (variable, self.get_operand(operand))
      buff += "}\n"

      return buff

   def set_reg(self, pos, variable) :
      return "%s[%s] = %s;\n" % (self.__VAR_REG, pos, variable)

   def set_idx(self, operand) :
      return "%s = %s;\n" % (self.__VAR_C_IDX, self.get_operand(operand))

class VM_int(object) :
   def patch_code(self) :
      code = self._code
      idx = self._idx 

      code.remove_at( idx )
      
      for new_code in self._irtj.call_code() :
         code.insert_at( idx, new_code )
         idx += 1

   def get_methods(self) :
     return self._irtj.get_methods()

class VM_int_basic_math_formula(VM_int) :
   def __init__(self, orig_class_name, code, idx) :
      self._code = code
      self._idx = idx

      i = code.get_at( idx )
      print i, i.get_name(), i.get_operands()
     
      oint = opaque.INT( i.get_operands() ).run()
      mtir = MTR( oint )
     
      mtir = MetaPolyREIL( mtir.get() )

      self._irtj = IL_REIL_TO_JAVA( orig_class_name, mtir.get() )

class VM_int_basic_prng(VM_int) :
   def __init__(self, orig_class_name, code, idx) :
      self._code = code
      self._idx = idx

      i = code.get_at( idx )
#      print i, i.get_name(), i.get_operands()
      oint = opaque.PRNG( i.get_operands() ).run()
      atoil = BPTR( oint )

      atoil = MetaPolyREIL( atoil.get() )
      
      self._irtj = IL_REIL_TO_JAVA( orig_class_name, atoil.get() )
