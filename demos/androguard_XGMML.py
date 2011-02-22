#!/usr/bin/env python

from xml.sax.saxutils import escape, unescape
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
#TEST = 'apks/TAT-LWP-Mod-Dandelion.apk'

a = androguard.AndroguardS( TEST )
x = analysis.VM_BCA( a.get_vm() )

#x.show()
NODES_ID = {}
EDGES_ID = {}

def export_xgmml(g, output) :
   method = g.get_method()
   class_name = method.get_class_name()

   for i in g.basic_blocks.get() :
      fd.write("<node id=\"%d\" label=\"%s-%s\">\n" % (len(NODES_ID), class_name, escape(i.name)))
      
      fd.write("</node>\n")

      NODES_ID[ class_name + i.name ] = len(NODES_ID)

   for i in g.basic_blocks.get() :
      for j in i.childs :
         label = "%s-%s (pp) %s-%s" % (class_name, escape(i.name), class_name, escape(j[-1].name))
         fd.write( "<edge id=\"%d\" label=\"%s\" source=\"%d\" target=\"%d\">\n" % (len(EDGES_ID), label, NODES_ID[ class_name + i.name ], NODES_ID[ class_name + j[-1].name ]) )
         
         fd.write("</edge>\n")

         EDGES_ID[ label ] = len(EDGES_ID)

fd = open("test.xgmml", "w")
fd.write("<?xml version='1.0'?>\n")
fd.write("<graph id=\"1\" label=\"Androguard\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:ns1=\"http://www.w3.org/1999/xlink\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" xmlns=\"http://www.cs.rpi.edu/XGMML\">\n")
   
# CFG
for method in a.get_methods() :
   g = x.hmethods[ method ]
   export_xgmml(g, fd)

fd.write("</graph>")
fd.close()
