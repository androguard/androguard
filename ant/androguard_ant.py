#!/usr/bin/env python

import sys, os

# CHANGE THE PATH BY THE DIRECTORY WHERE YOU HAVE INSTALL Androguard
PATH_ANDROGUARD_INSTALL = "/home/desnos/androguard/"

sys.path.append( PATH_ANDROGUARD_INSTALL )
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core")
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core/bytecodes")
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core/predicates")
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core/analysis")
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core/vm")
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core/wm")
sys.path.append( PATH_ANDROGUARD_INSTALL + "/core/protection")

import traceback

import androguard
from error import warning

def get_classes(path) :
   g_files = []
   for root, dirs, files in os.walk( path ) :
      if files != [] :
         for file in files :
            if ".class" in file :
               g_files.append(root + "/" + file)
   return g_files

def __main__() :
   print sys.argv
   if len( sys.argv ) > 1 :
      files = []
      for p in sys.argv[1].split(":") :
         files.extend( get_classes( p ) )

      a = androguard.Androguard( files )
      try :
         a.do( sys.argv[2] )
      except Exception, e:
         warning("!!!! Androguard failed !!!!")
         traceback.print_exc()

__main__()
