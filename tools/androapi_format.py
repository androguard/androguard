#!/usr/bin/env python

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

import os, sys, re, string

from dvm_permissions_unformatted import PERMISSIONS

BASIC_TYPES = { 
   "byte" : "B",
   "char" : "C",
   "double" : "D",
   "float" : "F",
   "int" : "I",
   "long" : "J",
   "short" : "S",
   "boolean" : "B",
   "void" : "V",
}

ADVANCED_TYPES = {
   "String" : "Ljava/lang/String;",
   "List" : "Ljava/util/List;",
   "AccountManagerFuture" : "Landroid/accounts/AccountManagerFuture;",
   "CellLocation" : "Landroid/telephony/CellLocation;",
   "Uri" : "Landroid/net/Uri;",
   "Cursor" : "Landroid/database/Cursor;",
   "Set" : "Ljava/util/Set;",
   "BluetoothServerSocket" : "Landroid/bluetooth/BluetoothServerSocket;",
   "BluetoothSocket" : "Landroid/bluetooth/BluetoothSocket;",
   "DownloadManager.Request" : "Landroid/app/DownloadManager/Request;",
}

def translateDescParams( desc_params ) :
   desc_params = desc_params.replace(" ", "")
   buff = ""

   for elem in desc_params.split(",") :
      if elem != "" :

         tab = ""
         if "[" in elem : 
            tab = "[" * string.count(elem, "[")

            elem = elem[ : tab.find("[") - 2 ]

         if elem not in BASIC_TYPES :
            buff += tab + "L" + elem.replace(".", "/") + ";"
         else :
            buff += tab + BASIC_TYPES[ elem ]

   return buff

def translateDescReturn( desc_return ) :
   buff = ""
   for elem in desc_return.split(" ") :

      tab = ""
      if "[" in elem :
         tab = "[" * string.count(elem, "[")
         elem = elem[ : tab.find("[") - 2 ]

      if elem in BASIC_TYPES :
         buff += tab + BASIC_TYPES[ elem ]
      else :
         if elem in ADVANCED_TYPES :
            buff += tab + ADVANCED_TYPES[ elem ]
            
   return buff

def translateToCLASS( desc_params, desc_return ) :
   print desc_params, desc_return,

   buff = "(" + translateDescParams( desc_params[ desc_params.find("(") + 1 : -1 ] ) + ")" + translateDescReturn( desc_return )
   print "----->", buff

   return [ desc_params[ : desc_params.find("(") ], buff ]

def translateToCLASS2( constant_name, desc_return ):
   return [ constant_name, translateDescReturn( desc_return ) ]

for perm in PERMISSIONS :
   for package in PERMISSIONS[perm] :
      for element in PERMISSIONS[perm][package] :
         if element[0] == "F" :
            element.extend( translateToCLASS( element[1], element[2] ) )
         elif element[0] == "C" :
            element.extend( translateToCLASS2( element[1], element[2] ) )


fd = open("../core/bytecodes/dvm_permissions.py", "w")

fd.write("DVM_PERMISSIONS = { \n")

for perm in PERMISSIONS : 
   fd.write("\"%s\" = {\n" % perm)

   for package in PERMISSIONS[perm] :
      fd.write("\t\"%s\" : [\n" % package)
      
      for element in PERMISSIONS[perm][package] :
         fd.write("\t\t(\"%s\", \"%s\", \"%s\"),\n" % (element[0], element[-2], element[-1]) )

      fd.write("\t],\n")
   fd.write("},\n")
fd.write("}\n")

fd.close()
