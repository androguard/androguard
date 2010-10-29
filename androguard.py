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

import sys, xml.dom.minidom 

PATH_INSTALL = "./"

sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/predicates")
sys.path.append(PATH_INSTALL + "/core/analysis")
sys.path.append(PATH_INSTALL + "/core/vm")

import bytecode, jvm, dvm, misc, analysis, opaque, vm

VM_INT_AUTO = 0
VM_INT_BASIC_MATH_FORMULA = 1
VM_INT_BASIC_PRNG = 2
INVERT_VM_INT_TYPE = { "VM_INT_AUTO" : VM_INT_AUTO,
                       "VM_INT_BASIC_MATH_FORMULA" : VM_INT_BASIC_MATH_FORMULA,
                       "VM_INT_BASIC_PRNG" : VM_INT_BASIC_PRNG
                     }


class VM_int :
   """VM_int is the main high level Virtual Machine object to protect a method by remplacing all integer contants

      @param andro : an L{Androguard} / L{AndroguardS} object to have full access to the desired information
      @param class_name : the class of the method
      @param method_name : the name of the method to protect
      @param descriptor : the descriptor of the method
      @param vm_int_type : the type of the Virtual Machine
   """
   def __init__(self, andro, class_name, method_name, descriptor, vm_int_type) :
      method, _vm = andro.get_method_descriptor(class_name, method_name, descriptor)
      code = method.get_code()

      class_manager = _vm.get_class_manager()

      # LOOP until integers constant !
      iip = True
      while iip == True : 
         idx = 0
         end_iip = True
         for bc in code.get_bc().get() :
            if bc.get_name() in _vm.get_INTEGER_INSTRUCTIONS() :
               if vm_int_type == VM_INT_BASIC_MATH_FORMULA :
                  vi = vm.VM_int_basic_math_formula( class_manager.get_this_class_name(), code, idx )
               elif vm_int_type == VM_INT_BASIC_PRNG :
                  vi = vm.VM_int_basic_prng( class_manager.get_this_class_name(), code, idx )
               else :
                  raise("oops")

               for new_method in vi.get_methods() : 
                  _vm.insert_direct_method( new_method.get_name(), new_method )
               method.show()
               vi.patch_code()

               end_iip = False
               
               break
            idx += 1
         
         # We have patch zero integers, it's the end my friend !
         if end_iip == True :
            iip = False

class BC :
   def __init__(self, bc) :
      self.__bc = bc

   def get_vm(self) :
      return self.__bc

   def _get(self, val, name) :
      l = []
      r = getattr(self.__bc, val)(name)
      for i in r :
         l.append( i )
      return l

   def _gets(self, val) :
      l = []
      r = getattr(self.__bc, val)()
      for i in r :
         l.append( i )
      return l

   def gets(self, name) :
      return self._gets("get_" + name)

   def get(self, val, name) :
      return self._get("get_" + val, name)

   def insert_direct_method(self, name, method) :
      return self.__bc.insert_direct_method(name, method)
  
   def insert_craft_method(self, name, proto, codes) :
      return self.__bc.insert_craft_method( name, proto, codes) 

   def show(self) :
      self.__bc.show()

   def save(self) :
      return self.__bc.save()

   def __getattr__(self, value) :          
      return getattr(self.__bc, value)

PROTECT_VM_AUTO = "protect_vm_auto"
PROTECT_VM_INTEGER = "protect_vm_integer"
PROTECT_VM_INTEGER_TYPE = "protect_vm_integer_type"

class Androguard :
   """Androguard is the main object to abstract and manage differents formats
   
      @param files : a list of filenames (filename must be terminated by .class or .dex)   
   """
   def __init__(self, files, config=None) :
      self.__files = files
      self.__bc = []
      self._analyze()

   def _iterFlatten(self, root):
      if isinstance(root, (list, tuple)):      
         for element in root :
            for e in self._iterFlatten(element) :      
               yield e                         
      else:                      
         yield root

   def _analyze(self) :
      for i in self.__files :
         if ".class" in i :
            bc = jvm.JVMFormat( open(i).read() )
         elif ".dex" in i :
            bc = dvm.DalvikVMFormat( open(i).read() )
         else :
            raise( "Unknown bytecode" )

         self.__bc.append( (i, BC( bc )) )

   def get_raw(self) :
      """Return raw format of all file"""
      l = []
      for _, bc in self.__bc :
         l.append( bc._get_raw() )
      return l

   def get_method_descriptor(self, class_name, method_name, descriptor) :
      for file_name, bc in self.__bc :
         x = bc.get_method_descriptor( class_name, method_name, descriptor )
         if x != None :
            return x, bc
      return None

   def get(self, name, val) :
      if name == "file" :
         for file_name, bc in self.__bc :
            if file_name == val :
               return bc

         return None
      else :
         l = []
         for file_name, bc in self.__bc :
            l.append( bc.get( name, val ) )

         return list( self._iterFlatten(l) )

   def gets(self, name) :
      l = []
      for file_name, bc in self.__bc :
         l.append( bc.gets( name ) )

      return l

   def show(self) :
      for _, bc in self.__bc :
         bc.show()

   def protect(self, fileconf) :
      fd = open(fileconf, "r")
      buffxml = fd.read()
      fd.close()

      document = xml.dom.minidom.parseString(buffxml)
      for item in document.getElementsByTagName('method') :
         if item.getElementsByTagName( PROTECT_VM_INTEGER )[0].firstChild != None :
            if item.getElementsByTagName( PROTECT_VM_INTEGER )[0].firstChild.data == "1" :
               vm_type = INVERT_VM_INT_TYPE[ item.getElementsByTagName( PROTECT_VM_INTEGER_TYPE )[0].firstChild.data ]
               VM_int( self, item.getAttribute('class'), item.getAttribute('name'), item.getAttribute('descriptor'), vm_type )

class AndroguardS :
   """AndroguardS is the main object to abstract and manage differents formats but only per filename. In fact this class is just a wrapper to the main class Androguard

      @param filename : the filename to use (filename must be terminated by .class or .dex)   
   """
   def __init__(self, filename) :
      self.__filename = filename
      self.__orig_a = Androguard( [ filename ] )
      self.__a = self.__orig_a.get( "file", filename )
      
   def get_vm(self) :
      return self.__a.get_vm()

   def save(self) :
      return self.__a.save()

   def __getattr__(self, value) :
      try :
         return getattr(self.__orig_a, value)
      except AttributeError :
         return getattr(self.__a, value)
