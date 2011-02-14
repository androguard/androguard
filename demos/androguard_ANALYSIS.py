#!/usr/bin/env python

import sys, hashlib

PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

OUTPUT = "./output/"
#TEST  = 'examples/java/test/orig/Test1.class'
#TEST  = 'examples/java/Demo1/orig/DES.class'
#TEST  = 'examples/java/Demo1/orig/Util.class'
TEST = 'examples/android/Test/bin/classes.dex'
#TEST = 'examples/android/Hello_Kitty/classes.dex'

a = androguard.AndroguardS( TEST )
x = analysis.VM_BCA( a.get_vm() )

#x.show()

# CFG
for method in a.get_methods() :
   g = x.hmethods[ method ]
   
#   g.basic_blocks.export_dot( OUTPUT + "%s-%s" % (method.get_name(), hashlib.md5( "%s-%s" % (method.get_class_name(), method.get_descriptor())).hexdigest()) + ".dot" )
   print method.get_class_name(), method.get_name(), method.get_descriptor(), method.get_code().get_length()
   for i in g.basic_blocks.get() :
      print "\t %s %x %x" % (i.name, i.start, i.end), i.ins[-1].get_name(), '[ CHILDS = ', ', '.join( "%x-%x-%s" % (j[0], j[1], j[2].get_name()) for j in i.childs ), ']', '[ FATHERS = ', ', '.join( j[2].get_name() for j in i.fathers ), ']', i.free_blocks_offsets

      #print "\t\t", x.tainted_variables.get_fields_by_bb( i )
      #print x.tainted_packages.get_packages_by_bb( i )

#   print x.get_method_signature(method, analysis.GRAMMAR_TYPE_CLEAR)
   print x.get_method_signature(method, analysis.GRAMMAR_TYPE_ANONYMOUS)

print ""
# Strings
print "STRINGS"
for s, _ in x.tainted_variables.get_strings() :
   print "String : ", repr(s.get_info())
   for path in s.get_paths() :
      print "\t\t =>", path.get_access_flag(), path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), path.get_bb().get_name(), "%x" % (path.get_bb().start + path.get_idx() )

print ""
# Fields
print "FIELDS"
for f, _ in x.tainted_variables.get_fields() :
   print "field : ", repr(f.get_info())
   for path in f.get_paths() :
      print "\t\t =>", path.get_access_flag(), path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), path.get_bb().get_name(), "%x" % (path.get_bb().start + path.get_idx() )

print ""
# Packages
print "PACKAGES"
for m, _ in x.tainted_packages.get_packages() :
   print "package : ", repr(m.get_info())
   for path in m.get_paths() :
      if path.get_access_flag() == analysis.TAINTED_PACKAGE_CREATE :
         print "\t\t =>", path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), path.get_bb().get_name(), "%x" % (path.get_bb().start + path.get_idx() )
      else :
         print "\t\t =>", path.get_name(), path.get_descriptor(), "from --->", path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), path.get_bb().get_name(), "%x" % (path.get_bb().start + path.get_idx() )
