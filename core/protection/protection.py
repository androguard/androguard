from error import log_loading, warning
from subprocess import Popen, PIPE, STDOUT

import misc

class GenerateMainCode :
   def __init__(self) :
      self.__gc = {}
      self.__functions = {}

      self.__name = "GMC"# + misc.random_string()

   def add(self, _vm, _analysis) :
      r = misc.random_string()
      self.__gc[ r ] = GenerateCode( self, r, _vm, _analysis )

   def addFunction(self, ident, name, desc) :
      if ident not in self.__functions :
         self.__functions[ ident ] = []

      self.__functions[ident].append( (name, desc) )

   def do(self) :
      fd = open(self.__name + ".java", "w")
      fd.write("class %s {\n" % self.__name)

      for i in self.__functions :
         for j in self.__functions[i] :
            print j

      fd.write("}\n")
      fd.close()

   def compile(self) :
      compile = Popen([ "/usr/bin/javac", "%s.java" % self.__name ], stdout=PIPE, stderr=STDOUT)
      stdout, stderr = compile.communicate()
      print "COMPILATION RESULTS", stdout, stderr
      if stdout != "":
         raise("ooo")

   def save(self, path) :
      pass

class GenerateCode :
   def __init__(self, _gmc, _ident, _vm, _analysis) :
      self.gmc = _gmc
      self.ident = _ident
      self.vm = _vm
      self.analysis = _analysis

      self.idx_init = self.analysis.random_free_block_offset( "^\<init\>" )
      self.gmc.addFunction( self.ident, misc.random_string(), "()V" )

#      self.gmc.patchInstruction( "^\<init\>", self.idx_init, [ "aload_0" ] )



class ProtectCode :
   def __init__(self, vms, libs_output) :
      print vms, libs_output

      gmc = GenerateMainCode()

      for i in vms :
         print i.get_vm(), i.get_analysis()

         gmc.add( i.get_vm(), i.get_analysis() )

      gmc.do()
      gmc.compile()
      gmc.save( libs_output )

#         for inte, _ in i.get_analysis().tainted_integers.get_integers() :
#            print "integer : ", repr(inte.get_info())

