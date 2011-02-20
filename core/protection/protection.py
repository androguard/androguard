from error import log_loading, warning
from subprocess import Popen, PIPE, STDOUT
import os

import jvm, misc

class GenerateMainCode :
   def __init__(self) :
      self.__gc = {}
      self.__info_gc = {}
      self.__functions = {}
      
      self.__name = "GMC"# + misc.random_string()

   def getClass(self) :
      return self.__name

   def add(self, _vm, _analysis) :
      r = misc.random_string()
      self.__info_gc[ r ] = ( _vm, _analysis )
      self.__gc[ r ] = GenerateCode( self, r, _vm, _analysis )

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
      
      fd.write("JNIEXPORT void JNICALL Java_GMC_GMCInit(JNIEnv *env, jclass cls) {\n")
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

      fd.write("}")

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

      for i in self.__gc :
         self.__gc[ i ].do()

      self.compile()

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
      compile = Popen([ "gcc", "-c", "GMC.c", "-I"+JAVA_INCLUDE, "-I"+JAVA_INCLUDE+"/linux"], stdout=PIPE, stderr=STDOUT)
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
      compile = Popen([ "gcc", "-o", "%s/libGMC.so" % path, "GMC.o", "-shared" ], stdout=PIPE, stderr=STDOUT)
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
   def __init__(self, _gmc, _ident, _vm, _analysis) :
      self.gmc = _gmc
      self.ident = _ident
      self.vm = _vm
      self.analysis = _analysis

      method_init = self.vm.get_method( "<init>" )[0]
      idx_init = self.analysis.hmethods[ method_init ].random_free_block_offset()

      f_name = misc.random_string()
      f_desc = "()V"

      self.gmc.addFunction( self.ident, f_name, f_desc )
      self.gmc.addInFunction( self.ident, f_name, f_desc, "System.out.println(\"ANDROGUARD\\n\");\n" )
      self.gmc.addInFunction( self.ident, f_name, f_desc, "Throwable t = new Throwable();\n" )
      self.gmc.addInFunction( self.ident, f_name, f_desc, "for ( StackTraceElement s : t.getStackTrace()) {\n" )
      self.gmc.addInFunction( self.ident, f_name, f_desc, "System.out.println( \"s : \" + s.getMethodName() );\n" )
      self.gmc.addInFunction( self.ident, f_name, f_desc, "}\n")

      self.gmc.addLibraryDependencies( self.ident )
      field = self.gmc.addNewField( self.ident, "ACC_PUBLIC", jvm.classToJclass( self.gmc.getClass() ) )

      co = self.gmc.createObject( self.ident, self.gmc.getClass(), field )
      self.gmc.insertAt( self.ident, method_init, idx_init, co )

      for i in self.vm.get_methods() :
         print i.get_name(), i.get_descriptor()

      #self.gmc.createCall( self.ident, "", field, [] )

#      self.gmc.addFunction( self.ident, misc.random_string(), "(IDLjava/lang/Thread;)Ljava/lang/Object;" )
#      self.gmc.patchInstruction( "^\<init\>", self.idx_init, [ "aload_0" ] )

   def do(self) :
      pass


class ProtectCode :
   def __init__(self, vms, libs_output) :
      gmc = GenerateMainCode()

      for i in vms :
      #   print i.get_vm(), i.get_analysis()

         gmc.add( i.get_vm(), i.get_analysis() )

      gmc.do()
      gmc.save( libs_output )

#         for inte, _ in i.get_analysis().tainted_integers.get_integers() :
#            print "integer : ", repr(inte.get_info())

