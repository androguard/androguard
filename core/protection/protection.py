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

from error import log_loading, warning
from subprocess import Popen, PIPE, STDOUT
import os

from networkx import DiGraph, all_pairs_dijkstra_path, simple_cycles, single_source_dijkstra_path, predecessor

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

class HandleINT :
   def __init__(self, gc) :
      self.gc = gc

   def gets(self) :
      for i in self.gc.vm.get_methods() :
         for j in self.gc.analysis.tainted_integers.get_method( i ) :
            p = j.get()
            #print p.get_value(), p.get_idx(), p.get_bb(), p.get_method() 
            yield (p.get_value(), p.get_idx() + p.get_bb().start, p.get_method())

   def length(self) :
      nb = 0
      for i in self.gc.vm.get_methods() :
         nb += len( self.gc.analysis.tainted_integers.get_method( i ) )

      return nb

class ObjectPaths :
   def __init__(self, vms) :
      g = DiGraph()
      
      classes = [ i.get_vm().get_classes_names()[0] for i in vms ]

      objects_create = {}
      methods_call = {}
      for i in vms :
         objects_create[ i.get_vm() ] = []

         for m, _ in i.get_analysis().tainted_packages.get_packages() :
            paths = m.get_paths()
            for j in paths :
               if j.get_method().get_class_name() in classes and m.get_info() in classes :
                  node1 = "%s %s %s" % (j.get_method().get_class_name(), j.get_method().get_name(), j.get_method().get_descriptor())

                  if j.get_access_flag() == TAINTED_PACKAGE_CREATE :
                     node2 = "%s-0x%x" % (m.get_info(), j.get_bb().start + j.get_idx())
                     print node1, "(create ---->)", node2
                    
                     ### An object of a specific type is created, we must add it
                     objects_create[ i.get_vm() ].append( (j, m) )
                     
                     g.add_edge(node2, node1)
                  else :
                     node2 = "%s %s %s" % (m.get_info(), j.get_name(), j.get_descriptor())
                     print node1, "(call ---->)", node2


      # Get all paths of created objects
      for i in g.node :
         #print i, "---->", g.successors( i )
         print i, "---->"
         sources = predecessor( g, i )
         for j in sources :
            if sources[j] != [] :
               print "\t\t", j, "-->", sources[j]

      #for i in g.node :
      #   print i, "---->"
      #   sources = single_source_dijkstra_path(g, i)
      #   for j in sources :
      #      print "\t\t", j, "-->", sources[j]


#############################################
class VMsModiciation :
   def __init__(self, vms) :
      pass

class VMModification :
   def __init__(self, vm) :
      pass
#############################################


#############################################
class Protection(object) :
   def __init__(self) :
      pass

class ProtectionClear(Protection) :
   def __init__(self) :
      pass

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
class Modification :
   def __init__(self) :
      pass

#############################################


#############################################
"""
   Save information about added code
      - useful to show the overhead of the protection
"""
class OverHead :
   def __init__(self) :
      pass
#############################################

class ProtectCode :
   def __init__(self, vms, libs_output) :
      mo = Modification( vms )
      vmsmo = VMsModiciation( vms, mo )

      # S1
      ########################################################
      # Get all created objects paths
      op = ObjectPaths( vms )
      
      # S2
      ########################################################
      # Get data to be protect and remove original bytecodes


      # S3
      ########################################################
      # Generate keys 

      # Protect data

      # S4
      ########################################################
      # Add new bytecodes to generate keys
      
      # Add new bytecodes to get protected data

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

