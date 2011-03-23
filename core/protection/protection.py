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

from struct import pack, unpack
from subprocess import Popen, PIPE, STDOUT
import os

from error import log_loading, warning
from analysis import TAINTED_PACKAGE_CREATE
import jvm, misc

class GenerateMainCode :
   def __init__(self) :
      self.__gc = {}
      self.__hi = {}
      self.__info_gc = {}
      self.__functions = {}
      
      self.__name = "GMC"# + misc.random_string()

   def getClass(self) :
      return self.__name

   def addVM(self, _vm, _analysis, objects_create) :
      r = misc.random_string()
      self.__info_gc[ r ] = ( _vm, _analysis )

      gc = GenerateCode( self, r, _vm, _analysis, objects_create )
      self.__gc[ r ] = gc
      self.__hi[ r ] = HandleINT( gc )

   def addFunction(self, ident, name, desc) :
      if ident not in self.__functions :
         self.__functions[ ident ] = {}

      self.__functions[ident][ name ] = {}
      self.__functions[ident][ name ][ desc ] = []

   def addInFunction(self, ident, name, desc, ins) :
      self.__functions[ident][ name ][ desc ].append( ins )

   def addLibraryDependencies(self, ident) :
      _vm = self.__info_gc[ ident ][0]

      class_name = _vm.get_classes_names()[0]

      cm = _vm.get_class_manager()
      id_class = cm.create_class( self.__name )

      for func in self.__functions[ident] :
         for desc in self.__functions[ident][ func ] :
            id_name_and_type = cm.create_name_and_type( func, desc )
            cm.create_method_ref( id_class, id_name_and_type )

      id_name_and_type = cm.create_name_and_type( "<init>", "()V" )
      cm.create_method_ref( id_class, id_name_and_type )

   def addNewField(self, ident, _access, _type) :
      _vm = self.__info_gc[ ident ][0]
      class_name = _vm.get_classes_names()[0]
      
      name = misc.random_string()
      _vm.insert_field( class_name, name, [ _access, _type ] )

      return [ name, _access, _type ]

   def createObject(self, ident, _type, _field ) :
      l = []

      l.append( [ "aload_0" ] )
      l.append( [ "new", _type ] )
      l.append( [ "dup" ] )
      l.append( [ "invokespecial", _type, '<init>', '()V' ] )
      l.append( [ "putfield", _field[0], _field[2] ] )
      
      return l

   def insertAt(self, ident, method, idx, ins) :
      _vm = self.__info_gc[ ident ][0]
      class_name = _vm.get_classes_names()[0]

      code = method.get_code()
      
      print method, ins, idx, code.get_relative_idx( idx )
     
      code.inserts_at( code.get_relative_idx( idx ), ins )

   def do(self) :
      fd = open(self.__name + ".c", "w")
      fd.write("#include <jni.h>\n")
      
      fd.write("JNIEXPORT void JNICALL Java_%s_GMCInit(JNIEnv *env, jclass cls) {\n" % self.__name)
      fd.write("printf(\"[GMC][native] init !!!!\\n\");\n")
      fd.write("}\n")

      fd.close()

      fd = open(self.__name + ".java", "w")
      fd.write("class %s {\n" % self.__name)

      fd.write("private native void GMCInit();\n");

      fd.write("static { System.loadLibrary(\"%s\"); }" % self.__name)

      fd.write("public %s(){\n" % self.__name)
      fd.write("GMCInit();\n")
      fd.write("System.out.println(\"[GMC] init\");\n")
      fd.write("Throwable t = new Throwable();\n" )
      fd.write("for ( StackTraceElement s : t.getStackTrace()) {\n" )
      fd.write("System.out.println( \"s : \" + s.getMethodName() );\n" )
      fd.write("}\n")

      fd.write("}")

      for i in self.__gc :
         self.__gc[ i ].do()

      self.insertINT()
      
      self.patch()

      for i in self.__functions :
         for name in self.__functions[i] :
            for desc in self.__functions[i][name] :
               # split the descriptor and build params and ret
               x = desc.split(")")
               params = self._build_params( x[0][1:] )
               ret = self._build_ret( x[1] )

               fd.write("public %s %s(%s) {\n" % ( ret, name, params ))

               for ins in self.__functions[i][name][desc] :
                  fd.write( ins )

               fd.write("}\n")

      fd.write("}\n")
      fd.close()

      self.compile()

   def insertINT(self) :
      for i in self.__gc :
         for (integer, idx, method) in self.__hi[ i ].gets() :
            code = method.get_code()
           
            print "[GMC] insertINT", method, integer, idx, code.get_relative_idx( idx )

            #code.inserts_at( code.get_relative_idx( idx ), ins )

   def patch(self) :
      pass

   def _build_params(self, v) :
      l = jvm.formatFD(v)
      z = []

      for i in l :
         if isinstance(i, list) :
            z.append( "%s %s%s" % (i[0], misc.random_string(), ''.join(j for j in i[1])) )
         else :
            z.append( "%s %s" % (i, misc.random_string()) )

      return ', '.join(i for i in z)

   def _build_ret(self, v) :
      l = jvm.formatFD( v )
      if isinstance(l[0], list) :
         return "%s%s" % (l[0][0], ' '.join(j for j in l[0][1]))
      return l[0]
      
   def compile(self) :
      print "[GMC] CREATING NATIVE OBJECTS ...."

      JAVA_INCLUDE = "/usr/lib/jvm/java-6-sun/include"
      compile = Popen([ "gcc", "-c", "%s.c" % self.__name, "-I"+JAVA_INCLUDE, "-I"+JAVA_INCLUDE+"/linux"], stdout=PIPE, stderr=STDOUT)
      stdout, stderr = compile.communicate()
      print "[GMC] COMPILATION RESULTS", stdout, stderr
      if stdout != "" :
         raise("ooo")

      print "[GMC] CREATING CLASS ...."
      compile = Popen([ "/usr/bin/javac", "%s.java" % self.__name ], stdout=PIPE, stderr=STDOUT)
      stdout, stderr = compile.communicate()
      print "[GMC] COMPILATION RESULTS", stdout, stderr
      if stdout != "":
         raise("ooo")


   def save(self, path) :
      print "[GMC] CREATING SHARED LIBRARY ...."
      compile = Popen([ "gcc", "-o", "%s/lib%s.so" % (path, self.__name), "%s.o" % self.__name, "-shared" ], stdout=PIPE, stderr=STDOUT)
      stdout, stderr = compile.communicate()
      print "[GMC] COMPILATION RESULTS", stdout, stderr
      if stdout != "" :
         raise("ooo")
      
      print "[GMC] CREATING JAR ...."
      compile = Popen([ "/usr/bin/jar", "-fc", "%s/%s.jar" % (path, self.__name) , "%s.class" % (self.__name)  ],  stdout=PIPE, stderr=STDOUT)
      stdout, stderr = compile.communicate()
      print "[GMC] COMPILATION RESULTS", stdout, stderr
      if stdout != "":
         raise("ooo")

class GenerateCode :
   def __init__(self, _gmc, _ident, _vm, _analysis, objects_create) :
      self.gmc = _gmc
      self.ident = _ident
      self.vm = _vm
      self.analysis = _analysis
      self.objects_create = objects_create

#      method_init = self.vm.get_method( "<init>" )[0]
#      idx_init = self.analysis.hmethods[ method_init ].random_free_block_offset()

#      f_name = misc.random_string()
#      f_desc = "()V"

#      self.gmc.addFunction( self.ident, f_name, f_desc )
#      self.gmc.addInFunction( self.ident, f_name, f_desc, "System.out.println(\"ANDROGUARD\\n\");\n" )
#      self.gmc.addInFunction( self.ident, f_name, f_desc, "Throwable t = new Throwable();\n" )
#      self.gmc.addInFunction( self.ident, f_name, f_desc, "for ( StackTraceElement s : t.getStackTrace()) {\n" )
#      self.gmc.addInFunction( self.ident, f_name, f_desc, "System.out.println( \"s : \" + s.getMethodName() );\n" )
#      self.gmc.addInFunction( self.ident, f_name, f_desc, "}\n")

#      self.gmc.addLibraryDependencies( self.ident )
#      field = self.gmc.addNewField( self.ident, "ACC_PUBLIC", jvm.classToJclass( self.gmc.getClass() ) )

#      co = self.gmc.createObject( self.ident, self.gmc.getClass(), field )
#      self.gmc.insertAt( self.ident, method_init, idx_init, co )

#      for i in self.vm.get_methods() :
#         print i.get_name(), i.get_descriptor()

#####################
#      #self.gmc.createCall( self.ident, "", field, [] )
#
#      self.gmc.addFunction( self.ident, misc.random_string(), "(IDLjava/lang/Thread;)Ljava/lang/Object;" )
#      self.gmc.patchInstruction( "^\<init\>", self.idx_init, [ "aload_0" ] )
#####################

   def do(self) :
      print self.vm.get_name(), "Objects create", self.objects_create

class Node :
   def __init__(self, name) :
      self.name = name
      self.child = []
      self.father = []

   def add(self, node, idx) :
      self.child.append( [node, idx] )

   def add_p(self, node) :
      self.father.append( node )

class Nodes :
   def __init__(self, paths) :
      self.nodes = {}
      self.paths = paths

   def add(self, name) :
      if name not in self.nodes :
         self.nodes[ name ] = Node( name )

   def add_edge(self, n1, idx, n2) :
      self.nodes[ n1 ].add( n2, idx )
      self.nodes[ n2 ].add_p( n1 )

   def get_all_paths(self) :
      for i in self.nodes :
         if self.nodes[i].father == [] and self.nodes[i].child != [] :
            self.get_all_paths2( [i, None], [] )
      return self.paths.get()

   def get_all_paths2(self, n, l) :
      l.append( n )

      for j in self.nodes[ n[0] ].child :
         self.get_all_paths2( j, list(l) ) 

      if self.nodes[ l[-1][0] ].child == [] :
         self.paths.add( l )
      else :
         del l

   def get_nodes(self) :
      for i in self.nodes :
         yield self.nodes[ i ]

   def show(self) :
      for i in self.nodes :
         print "N ", i
         print "\t", self.nodes[ i ].child

class Paths :
   def __init__(self) :
      self.paths = []

   def add(self, p) :
      self.paths.append( [ list(i) for i in p ] )

   def get(self) :
      for i in self.paths :
         z = i[0]

         i[0].pop(-1)
         j = 0 
         while j < len(i) - 1 :
            i[j].append( i[j+1].pop(-1) )
            j += 1

         i[j].append( None )

      return self.paths

class InformationPaths :
   def __init__(self, vmsmo) :
      P = Paths()
      N = Nodes( P )
      
      classes = [ i.get_vm().get_classes_names()[0] for i in vmsmo.gets() ]

      for i in vmsmo.gets() :
         for m, _ in i.get_vm_analysis().tainted_packages.get_packages() :
            paths = m.get_paths()
            for j in paths :
               if j.get_method().get_class_name() in classes and m.get_info() in classes :
                  node1 = "%s" % (j.get_method().get_class_name())
                  
                  N.add( node1 )
                  if j.get_access_flag() == TAINTED_PACKAGE_CREATE :
                     node2 = "%s" % (j.get_class_name())
                     N.add( node2 )
                     N.add_edge( node1, j, node2 )

      self.objects_paths = N.get_all_paths()
      self.N = N

   def get_objects_paths(self) :
      return self.objects_paths

   def get_classes_with_no_father(self) :
      l = []
      for i in self.N.get_nodes() :
         if i.father == [] and i.child != [] :
            l.append( i.name )
      return l

   def show(self) :
      print "ALL OBJECTS PATHS", len(self.objects_paths), self.objects_paths

      for i in self.objects_paths :
         print i

         for j in i :
            print "\t--->", j[0],
            if j[1] != None :
               print " : ", j[1].get_method().get_class_name(), j[1].get_method().get_name(), j[1].get_method().get_descriptor(), "0x%x" % (j[1].get_bb().start + j[1].get_idx()), " ->", j[1].get_class_name(),
            print

#############################################
class VMsModiciation :
   def __init__(self, vms, mo) :
      self.vms = vms
      self.mo = mo

      self._vms = {}

      for i in self.vms :
         self._vms[ i ] = VMModification( i, mo )

   def gets(self) :
      for i in self._vms :
         yield self._vms[ i ]

class VMModification :
   def __init__(self, vm, mo) :
      self.vm = vm
      self.mo = mo

   def remove(self, class_name, method_name, descriptor, idx, insn_nb) :
      return self.mo.remove( self.vm, class_name, method_name, descriptor, idx, insn_nb )

   def get_vm(self) :
      return self.vm.get_vm()

   def get_vm_analysis(self) :
      return self.vm.get_analysis()
      
#############################################


#############################################
"""
   Create the new library (native and java)
      - 
      -
"""
class Protection(object) :
   def __init__(self, vmsmo, ip) :
      self.vmsmo = vmsmo
      self.ip = ip

   def generate_keys(self) :
      print self.ip.get_objects_paths()

      raise("ooo")

   def patch(self) :
      pass

class ProtectionClear(Protection) :
   def __init__(self, vmsmo, ip, protdata) :
      super(ProtectionClear, self).__init__( vmsmo, ip )
      
      self.generate_keys()

      raise("ooo")

class ProtectionCrypt(Protection) :
   def __init__(self) :
      pass

#############################################


#############################################
"""
   Handle all bytecodes modification in classes
      - save add/remove modifications
      - apply at the end modifcations to have no problems
"""
MODIFICATION_ADD = 0
MODIFICATION_REMOVE = 1
class Modification :
   def __init__(self, vms) :
      self.__vmmo = {}

      for vm in vms :
         self.__vmmo[ vm ] = []

   # Remove insn_nb instructions @ idx
   def remove(self, vm, class_name, method_name, descriptor, idx, insn_nb) :
      method = vm.get_method_descriptor( class_name, method_name, descriptor )
      code = method.get_code()

      self.__vmmo[ vm ].append( [MODIFICATION_REMOVE, method, code.get_relative_idx( idx ), insn_nb] )

   def patch(self) :
      raise("ooo")

#############################################


#############################################
"""
   Save information about added code
      - useful to show the complexity (and the overhead) of the protection
"""
class Complexity :
   def __init__(self) :
      pass
#############################################


#############################################

"""

   - If object creation is used with default constructor :
      - newInstance
   - Else if object creation is used with a particular constructor :
      - <init> of class is renamed
      - newInstance (call the new <init> constructor)
      - call a specific method (which is the original constructor)
"""

class HandleObject :
   def __init__(self, vmsmo, paths) :
      for path in paths :
         for j in path :
            if j[1] != None :
               print j

class HandleInt :
   def __init__(self, vmsmo, classes) :
      self.vmsmo = vmsmo
      self.excluded_classes = classes

      self.data = {}

      for i in self.vmsmo.gets() :
         vm = i.get_vm()
         vm_analysis = i.get_vm_analysis()
         print vm, vm_analysis, vm.get_classes_names()
         
         for method in vm.get_methods() :
            if method.get_class_name() not in self.excluded_classes :
               for j in vm_analysis.tainted_integers.get_method( method ) :
                  p = j.get()
                  print "\t", p.get_value(), p.get_idx(), p.get_bb(), p.get_method(), method.get_class_name(), method.get_name(), method.get_descriptor()

                  if method.get_class_name() not in self.data :
                     self.data[ method.get_class_name() ] = []

                  # Remove data from the class
                  i.remove( method.get_class_name(), method.get_name(), method.get_descriptor(), p.get_bb().start + p.get_idx(), 1 )
                  
                  # Add protected data for next steps
                  self.data[ method.get_class_name() ].append( [ len(self.data[ method.get_class_name() ]), pack('<L', p.get_value()), "INTEGER" ] )

   def get_data(self) :
      return self.data

class ProtectData :
   def __init__(self, data) :
      print data

#############################################

class ProtectCode :
   def __init__(self, vms, libs_output) :
      mo = Modification( vms )
      vmsmo = VMsModiciation( vms, mo )

      # S1
      ########################################################
      # Get all created information paths
      ip = InformationPaths( vmsmo )
      ip.show()

      # S2
      ########################################################
      # Get data to be protected and remove original bytecodes
      #         - integers
      #         - object creation
      #         - ...
#      HandleObject( vmsmo, ip.get_objects_paths() )
      hi = HandleInt( vmsmo, ip.get_classes_with_no_father() )
   
      # Save protected data to be independant of what we are protectecting (int, string ...)
      pd = ProtectData( hi.get_data() )

      # S3
      ########################################################
      # Generate keys 
      # Protect data
      prot = ProtectionClear( vmsmo, ip, pd )
      
      # S4
      ########################################################
      # Add new bytecodes to generate keys
      prot.patch()

      # Add new bytecodes to get protected data
      hi.patch( pd )

      # S5
      ########################################################
      # Apply all modifications
      mo.patch()

      # S6
      ########################################################
      # Save files ...
      mo.save( libs_output )

#      gmc = GenerateMainCode()     
#      for i in vms :
#         gmc.addVM( i.get_vm(), i.get_analysis(), objects_create[i.get_vm()] )

#      gmc.do()
#      gmc.save( libs_output )

#         for inte, _ in i.get_analysis().tainted_integers.get_integers() :
#            print "integer : ", repr(inte.get_info())

