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

import sys, xml.dom.minidom, re, random, string, os

PATH_INSTALL = "./"

sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/predicates")
sys.path.append(PATH_INSTALL + "/core/analysis")
sys.path.append(PATH_INSTALL + "/core/vm")
sys.path.append(PATH_INSTALL + "/core/wm")
sys.path.append(PATH_INSTALL + "/core/protection")

import bytecode, jvm, dvm, misc, analysis, opaque
from error import error

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
      import vm

      method, _vm = andro.get_method_descriptor(class_name, method_name, descriptor)
      code = method.get_code()

      # LOOP until integers constant !
      iip = True
      while iip == True : 
         idx = 0
         end_iip = True
         for bc in code.get_bc().get() :
            if bc.get_name() in _vm.get_INTEGER_INSTRUCTIONS() :
               if vm_int_type == VM_INT_BASIC_MATH_FORMULA :
                  vi = vm.VM_int_basic_math_formula( class_name, code, idx )
               elif vm_int_type == VM_INT_BASIC_PRNG :
                  vi = vm.VM_int_basic_prng( class_name, code, idx )
               else :
                  raise("oops")

               for new_method in vi.get_methods() : 
                  _vm.insert_direct_method( new_method.get_name(), new_method )
               vi.patch_code()

               end_iip = False
               
               break
            idx += 1
         
         # We have patched zero integers, it's the end my friend !
         if end_iip == True :
            iip = False

      method.show()

class WM :
   def __init__(self, andro, class_name, wm_type) :
      if wm_type == [] :
         raise("....")
      
      import wm
      self._w = wm.WM( andro.get_vm(), class_name, wm_type, andro.get_analysis() )

   def get(self) :
      return self._w

class WMCheck :
   def __init__(self, andro, class_name, input_file) :
      fd = open(input_file, "rb")
      buffxml = fd.read()
      fd.close()

      document = xml.dom.minidom.parseString(buffxml)

      w_orig = wm.WMLoad( document )
      w_cmp = wm.WMCheck( w_orig, andro, andro.get_analysis() )

def OBFU_NAMES_GEN(prefix="") :
   return prefix + random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ] )

OBFU_NAMES_FIELDS = 0
OBFU_NAMES_METHODS = 1
class OBFU_Names :
   """
      OBFU_Names is the object that change the name of a field or a method by a random string, and resolving
      dependencies into other files

      @param andro : an L{Androguard} object to have full access to the desired information, and represented a pool of files with the same format
      @param class_name : the class of the method/field (a python regexp)
      @param name : the name of the method/field (a python regexp)
      @param descriptor : the descriptor of the method/field (a python regexp)
      @param obfu_type : the type of the obfuscated (field/method) (OBFU_NAMES_FIELDS, OBFU_NAMES_METHODS)
      @param gen_method : a method which generate random string
   """
   def __init__(self, andro, class_name, name, descriptor, obfu_type, gen_method=OBFU_NAMES_GEN) :
      if obfu_type != OBFU_NAMES_FIELDS and obfu_type != OBFU_NAMES_METHODS :
         raise("ooops")

      re_class_name = re.compile(class_name)
      re_name = re.compile(name)
      re_descriptor = re.compile(descriptor)

      if obfu_type == OBFU_NAMES_FIELDS :
         search_in = andro.gets("fields")
      elif obfu_type == OBFU_NAMES_METHODS :
         search_in = andro.gets("methods")

      depends = []

      # Change the name of all fields/methods
      for fm in search_in :
         if re_class_name.match( fm.get_class_name() ) :
            if re_name.match( fm.get_name() ):
               if re_descriptor.match( fm.get_descriptor() ) :
                  _, _vm = andro.get_method_descriptor( fm.get_class_name(), fm.get_name(), fm.get_descriptor() )
                  old_name = fm.get_name()
                  new_name = gen_method()
                  
                  # don't change the constructor for a .class file
                  if obfu_type == OBFU_NAMES_METHODS :
                     _, _vm = andro.get_method_descriptor( fm.get_class_name(), fm.get_name(), fm.get_descriptor() )
                     if _vm.get_type() == "JVM" and old_name != "<init>" :
                        fm.set_name( new_name )
                        depends.append( (fm, old_name) )
                  elif obfu_type == OBFU_NAMES_FIELDS :
                     fm.set_name( new_name )
                     depends.append( (fm, old_name) )

      # Change the name in others files
      for i in depends :
         for _vm in andro.get_vms() :
            if obfu_type == OBFU_NAMES_FIELDS :
               _vm.set_used_field( [ i[0].get_class_name(), i[1], i[0].get_descriptor() ], [ i[0].get_class_name(), i[0].get_name(), i[0].get_descriptor() ] )
            elif obfu_type == OBFU_NAMES_METHODS :
               _vm.set_used_method( [ i[0].get_class_name(), i[1], i[0].get_descriptor() ], [ i[0].get_class_name(), i[0].get_name(), i[0].get_descriptor() ] )

class BC :
   def __init__(self, bc) :
      self.__bc = bc

   def get_vm(self) :
      return self.__bc

   def get_analysis(self) :
      return self.__a

   def analyze(self) :
      self.__a = analysis.VM_BCA( self.__bc, code_analysis=True )

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
      @param raw : specify if the filename is in fact a raw buffer (default : False) #FIXME
   """
   def __init__(self, files, raw=False) :
      self.__files = files
      
      self.__orig_raw = {}
      for i in self.__files :
         self.__orig_raw[ i ] = open(i, "rb").read()

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
         #print "processing ", i
         if ".class" in i :
            bc = jvm.JVMFormat( self.__orig_raw[ i ] )
         elif ".jar" in i :
            x = jvm.JAR( i )
            bc = x.get_classes()
         elif ".dex" in i :
            bc = dvm.DalvikVMFormat( self.__orig_raw[ i ] )
         elif ".apk" in i :
            x = dvm.APK( i )
            bc = dvm.DalvikVMFormat( x.get_dex() )
         else :
            raise( "Unknown bytecode" )

         if isinstance(bc, list) :
            for j in bc :
               self.__bc.append( (j[0], BC( jvm.JVMFormat(j[1]) ) ) )
         else :
            self.__bc.append( (i, BC( bc )) )

   def __analyze(self) :
      for i in self.get_bc() :
         i[1].analyze()

   def get_class(self, class_name) :
      for _, bc in self.__bc :
         if bc.get_class(class_name) == True :
            return bc
      return None

   def get_raw(self) :
      """Return raw format of all file"""
      l = []
      for _, bc in self.__bc :
         l.append( bc._get_raw() )
      return l

   def get_orig_raw(self) :
      return self.__orig_raw

   def get_method_descriptor(self, class_name, method_name, descriptor) :
      """
         Return the specific method 
         
         @param class_name : the class name of the method
         @param method_name : the name of the method
         @param descriptor : the descriptor of the method
      """
      for file_name, bc in self.__bc :
         x = bc.get_method_descriptor( class_name, method_name, descriptor )
         if x != None :
            return x, bc
      return None, None

   def get_field_descriptor(self, class_name, field_name, descriptor) :
      """
         Return the specific field

         @param class_name : the class name of the field
         @param field_name : the name of the field
         @param descriptor : the descriptor of the field
      """
      for file_name, bc in self.__bc :
         x = bc.get_field_descriptor( class_name, field_name, descriptor )
         if x != None :
            return x, bc
      return None, None

   def get(self, name, val) :
      """
         Return the specific value for all files

         @param name :
         @param val : 
      """
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
      """
         Return the specific value for all files

         @param name :
      """
      l = []
      for file_name, bc in self.__bc :
         l.append( bc.gets( name ) )

      return list( self._iterFlatten(l) )
   
   def get_vms(self) :
      return [ i[1].get_vm() for i in self.__bc ]

   def get_bc(self) :
      return self.__bc

   def show(self) :
      """
         Display all files
      """
      for _, bc in self.__bc :
         bc.show()

   def do(self, fileconf) :
      self.__analyze()

      fd = open(fileconf, "rb")
      buffxml = fd.read()
      fd.close()

      document = xml.dom.minidom.parseString(buffxml)

      main_path = document.getElementsByTagName( "main_path" )[0].firstChild.data
      libs_path = document.getElementsByTagName( "libs_path" )[0].firstChild.data
      
      if document.getElementsByTagName( "watermark" ) != [] :
         watermark_item = document.getElementsByTagName( "watermark" )[0]
         watermark_types = []
         for item in watermark_item.getElementsByTagName( "type" ) :
            watermark_types.append( str( item.firstChild.data ) )
         watermark_output = watermark_item.getElementsByTagName( "output" )[0].firstChild.data
         print watermark_types, "--->", watermark_output

         fd = open(watermark_output, "w")

         fd.write("<?xml version=\"1.0\"?>\n") 
         fd.write("<andro id=\"androguard wm\">\n")
         wms = []
         for i in self.get_bc() :
            for class_name in i[1].get_classes_names() :
               wm = WM( i[1], class_name, watermark_types )
               fd.write( wm.get().save() )
         fd.write("</andro>\n")
         fd.close()

      if document.getElementsByTagName( "protect_code" ) != [] :
         import protection

         protect_code_item = document.getElementsByTagName( "protect_code" )[0]
         protection.ProtectCode( [ i[1] for i in self.get_bc() ], main_path + libs_path )
         
#      for item in document.getElementsByTagName('method') :
#         if item.getElementsByTagName( PROTECT_VM_INTEGER )[0].firstChild != None :
#            if item.getElementsByTagName( PROTECT_VM_INTEGER )[0].firstChild.data == "1" :
#               vm_type = INVERT_VM_INT_TYPE[ item.getElementsByTagName( PROTECT_VM_INTEGER_TYPE )[0].firstChild.data ]
#               VM_int( self, item.getAttribute('class'), item.getAttribute('name'), item.getAttribute('descriptor'), vm_type )

      if document.getElementsByTagName( "save_path" ) != [] :
         self.save( main_path + document.getElementsByTagName( "save_path" )[0].firstChild.data )
      else :
         self.save()

   def save(self, output_dir=None) :
      for file_name, bc in self.get_bc() :
         if output_dir == None :
            output_file_name = file_name
         else :
            output_file_name = output_dir + os.path.basename( file_name )

         print "[+] [AG] SAVING ... ", output_file_name
         fd = open(output_file_name, "w")
         fd.write( bc.save() )
         fd.close()

class AndroguardS :
   """AndroguardS is the main object to abstract and manage differents formats but only per filename. In fact this class is just a wrapper to the main class Androguard

      @param filename : the filename to use (filename must be terminated by .class or .dex)   
      @param raw : specify if the filename is a raw buffer (default : False)
   """
   def __init__(self, filename, raw=False) :
      self.__filename = filename
      self.__orig_a = Androguard( [ filename ], raw )
      self.__a = self.__orig_a.get( "file", filename )
      
   def get_orig_raw(self) :
      return self.__orig_a.get_orig_raw()[ self.__filename ]

   def get_vm(self) :
      """
         This method returns the VMFormat which correspond to the file
         
         @rtype: L{jvm.JVMFormat} or L{dvm.DalvikVMFormat}
      """
      return self.__a.get_vm()

   def save(self) :
      """
         Return the original format (with the modifications) into raw format

         @rtype: string
      """
      return self.__a.save()

   def __getattr__(self, value) :
      try :
         return getattr(self.__orig_a, value)
      except AttributeError :
         return getattr(self.__a, value)
