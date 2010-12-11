#!/usr/bin/env python

DOT = "/usr/bin/dot"

import dircache

from subprocess import Popen, PIPE, STDOUT  

a = dircache.listdir('./')
for i in a :
   if ".dot" in i :
      compile = Popen([ DOT, i, "-Tpng" ], stdout=PIPE, stderr=STDOUT)                                                                                                                                                
      stdout, stderr = compile.communicate()
      #print "COMPILATION RESULTS", stdout, stderr
      fd = open(i[:-4] + ".png", "w")
      fd.write( stdout )
      fd.close()
   
