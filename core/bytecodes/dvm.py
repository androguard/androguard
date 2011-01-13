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

import bytecode


import misc
from bytecode import SV, SVs

import sys, re, types, string, zipfile, StringIO
from collections import namedtuple
from struct import pack, unpack, calcsize

from subprocess import Popen, PIPE, STDOUT

######################################################## APK FORMAT ########################################################
AAPT_PATH = "./externals/android/8/aapt"
class APK :
   def __init__(self, filename, raw=False) :
      self.filename = filename

      self.permissions = {}
      self.permissions_global = []

      if raw == True :
         self.__raw = filename
      else :
         fd = open( filename, "r" )
         self.__raw = fd.read()
         fd.close()

      self.zip = zipfile.ZipFile( StringIO.StringIO( self.__raw ) )

      for i in self.zip.namelist() :
         if ".xml" in i :
            compile = Popen([AAPT_PATH , "d", "permissions", self.filename, i], stdout=PIPE, stderr=STDOUT)
            stdout, stderr = compile.communicate()
            x = ""
            for j in stdout.split("\n") :
               if "package:" in j :
                  x = i + j.split(":")[1]
                  self.permissions[ x ] = []
               else :
                  if j != "" :
                     self.permissions[ x ].append( j )
                     if j not in self.permissions_global :
                        self.permissions_global.append( j )

   def get_dex(self) :
      return self.zip.read("classes.dex")

   def get_permissions(self) :
      return self.permissions, self.permissions_global

   def show(self) :
      print self.zip.namelist()
      print self.permissions_global

######################################################## DEX FORMAT ########################################################
DEX_FILE_MAGIC = 'dex\n035\x00'

HEADER = [ '<QL20sLLLLLLLLLLLLLLLLLLLL', namedtuple( "HEADER", "magic checksum signature file_size header_size endian_tag link_size link_off " \
                                                               "map_off string_ids_size string_ids_off type_ids_size type_ids_off proto_ids_size " \
                                                               "proto_ids_off field_ids_size field_ids_off method_ids_size method_ids_off "\
                                                               "class_defs_size class_defs_off data_size data_off" ) ]

MAP_ITEM = [ '<HHLL', namedtuple("MAP_ITEM", "type unused size offset") ]

PROTO_ID_ITEM = [ '<LLL', namedtuple("PROTO_ID_ITEM", "shorty_idx return_type_idx parameters_off" ) ]
METHOD_ID_ITEM = [ '<HHL', namedtuple("METHOD_ID_ITEM", "class_idx proto_idx name_idx" ) ]
FIELD_ID_ITEM = [ '<HHL', namedtuple("FIELD_ID_ITEM", "class_idx type_idx name_idx") ]

CLASS_DEF_ITEM = [ '<LLLLLLLL', namedtuple("CLASS_DEF_ITEM", "class_idx access_flags superclass_idx interfaces_off source_file_idx annotations_off class_data_off static_values_off") ]

TRY_ITEM = [ '<LHH', namedtuple("TRY_ITEM", "start_addr insn_count handler_off" ) ]
ANNOTATIONS_DIRECTORY_ITEM = [ '<LLLL', namedtuple("ANNOTATIONS_DIRECTORY_ITEM", "class_annotations_off fields_size annotated_methods_size annotated_parameters_size") ]

TYPE_MAP_ITEM = {
                  0x0    : "TYPE_HEADER_ITEM",
                  0x1    : "TYPE_STRING_ID_ITEM",
                  0x2    : "TYPE_TYPE_ID_ITEM",
                  0x3    : "TYPE_PROTO_ID_ITEM",
                  0x4    : "TYPE_FIELD_ID_ITEM",
                  0x5    : "TYPE_METHOD_ID_ITEM",
                  0x6    : "TYPE_CLASS_DEF_ITEM",
                  0x1000 : "TYPE_MAP_LIST",
                  0x1001 : "TYPE_TYPE_LIST",
                  0x1002 : "TYPE_ANNOTATION_SET_REF_LIST",
                  0x1003 : "TYPE_ANNOTATION_SET_ITEM",
                  0x2000 : "TYPE_CLASS_DATA_ITEM",
                  0x2001 : "TYPE_CODE_ITEM",
                  0x2002 : "TYPE_STRING_DATA_ITEM",
                  0x2003 : "TYPE_DEBUG_INFO_ITEM",
                  0x2004 : "TYPE_ANNOTATION_ITEM",
                  0x2005 : "TYPE_ENCODED_ARRAY_ITEM",
                  0x2006 : "TYPE_ANNOTATIONS_DIRECTORY_ITEM",
                }

SPARSE_SWITCH = [ '<HH', namedtuple("SPARSE_SWITCH", "ident size") ]
PACKED_SWITCH = [ '<HHL', namedtuple("PACKED_SWITCH", "ident size first_key") ]
FILL_ARRAY_DATA = [ '<HHL', namedtuple("FILL_ARRAY_DATA", "ident element_width size") ]

class FillArrayData :
   def __init__(self, buff) :
      self.format = SVs( FILL_ARRAY_DATA[0], FILL_ARRAY_DATA[1], buff[ 0 : calcsize(FILL_ARRAY_DATA[0]) ] )
      
      general_format = self.format.get_value()
      self.data = buff[ calcsize(FILL_ARRAY_DATA[0]) : calcsize(FILL_ARRAY_DATA[0]) + (general_format.size * general_format.element_width ) ]

   def get_name(self) :
      return "FILL-ARRAY-DATA"

   def show(self, pos) :
      print pos, self.format.get_value(), repr(self.data),
      buff = ""
      for i in range(0, len(self.data)) :
         buff += "\\x%02x" % ord( self.data[i] )
      print buff[:-1]

   def get_length(self) :
      general_format = self.format.get_value()
      return calcsize(FILL_ARRAY_DATA[0]) + ( general_format.size * general_format.element_width )

class SparseSwitch :
   def __init__(self, buff) :
      self.format = SVs( SPARSE_SWITCH[0], SPARSE_SWITCH[1], buff[ 0 : calcsize(SPARSE_SWITCH[0]) ] )
      self.keys = []
      self.targets = []

      idx = calcsize(SPARSE_SWITCH[0])
      for i in range(0, self.format.get_value().size) :
         self.keys.append( unpack('<L', buff[idx:idx+4]) )
         idx += 4

      for i in range(0, self.format.get_value().size) :
         self.targets.append( unpack('<L', buff[idx:idx+4]) )
         idx += 4
        
   def get_operands(self) :
      return self.targets

   def get_name(self) :
      return "SPARSE-SWITCH"

   def show(self, pos) :
     print pos, self.format.get_value(), self.keys, self.targets,

   def get_length(self) :
     return calcsize(SPARSE_SWITCH[0]) + (self.format.get_value().size * calcsize('<L')) * 2

class PackedSwitch :
   def __init__(self, buff) :
      self.format = SVs( PACKED_SWITCH[0], PACKED_SWITCH[1], buff[ 0 : calcsize(PACKED_SWITCH[0]) ] )
      self.targets = []

      idx = calcsize(PACKED_SWITCH[0])
      for i in range(0, self.format.get_value().size) :
         self.targets.append( unpack('<L', buff[idx:idx+4]) )
         idx += 4

   def get_operands(self) :
      return self.targets

   def get_name(self) :
      return "PACKED-SWITCH"

   def show(self, pos) :
      print pos, self.format.get_value(), self.targets,

   def get_length(self) :
      return calcsize(PACKED_SWITCH[0]) + (self.format.get_value().size * calcsize('<L'))

DALVIK_OPCODES = {
                  0x00 : [ "10x", "nop"                         ],
                  0x01 : [ "12x", "move",                       "vA, vB", "B|A|op" ],
                  0x02 : [ "22x", "move/from16",                "vAA, vBBBB", "AA|op BBBB" ],
                  0x03 : [ "32x", "move/16",                    "vAAAA, vBBBB", "00|op AAAA BBBB" ],
                  0x04 : [ "12x", "move-wide",                  "vA, vB", "B|A|op" ],
                  0x05 : [ "22x", "move-wide/from16",           "vAA, vBBBB", "AA|op BBBB" ],
                  0x06 : [ "32x", "move-wide/16",               "vAAAA, vBBBB", "00|op AAAA BBBB" ],
                  0x07 : [ "12x", "move-object",                "vA, vB", "B|A|op" ],
                  0x08 : [ "22x", "move-object/from16",         "vAA, vBBBB", "AA|op BBBB" ],
                  0x09 : [ "32x", "move-object/16",             "vAAAA, vBBBB", "00|op AAAA BBBB" ],
                  0x0a : [ "11x", "move-result",                "vAA", "AA|op" ],
                  0x0b : [ "11x", "move-result-wide",           "vAA", "AA|op" ],
                  0x0c : [ "11x", "move-result-object",         "vAA", "AA|op" ],
                  0x0d : [ "11x", "move-exception",             "vAA", "AA|op" ],
                  0x0e : [ "10x", "return-void"                  ],
                  0x0f : [ "11x", "return",                     "vAA", "AA|op" ],
                  0x10 : [ "11x", "return-wide",                "vAA", "AA|op" ],
                  0x11 : [ "11x", "return-object",              "vAA", "AA|op" ],
                  0x12 : [ "11n", "const/4",                    "vA, #+B", "B|A|op" ],
                  0x13 : [ "21s", "const/16",                   "vAA, #+BBBB", "AA|op BBBB" ],
                  0x14 : [ "31i", "const",                      "vAA, #+BBBBBBBB", "AA|op BBBB BBBB" ],
                  0x15 : [ "21h", "const/high16",               "vAA, #+BBBB0000", "AA|op BBBB0000" ],
                  0x16 : [ "21s", "const-wide/16",              "vAA, #+BBBB", "AA|op BBBB" ], 
                  0x17 : [ "31i", "const-wide/32",              "vAA, #+BBBBBBBB", "AA|op BBBB BBBB" ],
                  0x18 : [ "51l", "const-wide",                 "vAA, #+BBBBBBBBBBBBBBBB", "AA|op BBBB BBBB BBBB BBBB" ],
                  0x19 : [ "21h", "const-wide/high16",          "vAA, #+BBBB000000000000", "AA|op BBBB000000000000" ],
                  0x1a : [ "21c", "const-string",               "vAA, string@BBBB", "AA|op BBBB" ],
                  0x1b : [ "31c", "const-string/jumbo",         "vAA, string@BBBBBBBB", "AA|op BBBB BBBB" ],
                  0x1c : [ "21c", "const-class",                "vAA, type@BBBB", "AA|op BBBB" ],
                  0x1d : [ "11x", "monitor-enter",              "vAA", "AA|op" ],
                  0x1e : [ "11x", "monitor-exit",               "vAA", "AA|op" ],
                  0x1f : [ "21c", "check-cast",                 "vAA, type@BBBB", "AA|op BBBB" ],
                  0x20 : [ "22c", "instance-of",                "vA, vB, type@CCCC", "B|A|op CCCC" ],
                  0x21 : [ "12x", "array-length",               "vA, vB", "B|A|op" ],
                  0x22 : [ "21c", "new-instance",               "vAA, type@BBBB", "AA|op BBBB" ],
                  0x23 : [ "22c", "new-array",                  "vA, vB, type@CCCC", "B|A|op CCCC" ],
                  0x24 : [ "35c", "filled-new-array",           "vD, vE, vF, vG, vA, type@CCCC", "B|A|op CCCC G|F|E|D" ], 
                  0x25 : [ "3rc", "filled-new-array/range",     "", ""      ],
                  0x26 : [ "31t", "fill-array-data",            "vAA, +BBBBBBBB ", "AA|op BBBBBBBB", FillArrayData ],
                  0x27 : [ "11x", "throw",                      "vAA", "B|A|op" ],
                  0x28 : [ "10t", "goto",                       "+AA", "AA|op"],
                  0x29 : [ "20t", "goto/16",                    "+AAAA", "00|op AAAA" ],
                  0x2a : [ "30t", "goto/32",                    "+AAAAAAAA", "00|op AAAA AAAA" ],
                  0x2b : [ "31t", "packed-switch",              "vAA, +BBBBBBBB ", "AA|op BBBBBBBB", PackedSwitch ],
                  0x2c : [ "31t", "sparse-switch",              "vAA +BBBBBBBB", "AA|op BBBBBBBB", SparseSwitch ],
                  0x2d : [ "23x", "cmpl-float",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x2e : [ "23x", "cmpg-float",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x2f : [ "23x", "cmpl-double",                "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x30 : [ "23x", "cmpg-double",                "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x31 : [ "23x", "cmp-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x32 : [ "22t", "if-eq",                      "vA, vB, +CCCC", "B|A|op CCCC" ],
                  0x33 : [ "22t", "if-ne",                      "vA, vB, +CCCC", "B|A|op CCCC" ],
                  0x34 : [ "22t", "if-lt",                      "vA, vB, +CCCC", "B|A|op CCCC" ],
                  0x35 : [ "22t", "if-ge",                      "vA, vB, +CCCC", "B|A|op CCCC" ],
                  0x36 : [ "22t", "if-gt",                      "vA, vB, +CCCC", "B|A|op CCCC" ],
                  0x37 : [ "22t", "if-le",                      "vA, vB, +CCCC", "B|A|op CCCC" ],
                  0x38 : [ "21t", "if-eqz",                     "vAA, +BBBB", "AA|op BBBB" ],
                  0x39 : [ "21t", "if-nez",                     "vAA, +BBBB", "AA|op BBBB" ],
                  0x3a : [ "21t", "if-ltz",                     "vAA, +BBBB", "AA|op BBBB" ],
                  0x3b : [ "21t", "if-gez",                     "vAA, +BBBB", "AA|op BBBB" ],
                  0x3c : [ "21t", "if-gtz",                     "vAA, +BBBB", "AA|op BBBB" ],
                  0x3d : [ "21t", "if-lez",                     "vAA, +BBBB", "AA|op BBBB" ],
                  0x44 : [ "23x", "aget",                       "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x45 : [ "23x", "aget-wide",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x46 : [ "23x", "aget-object",                "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x47 : [ "23x", "aget-boolean",               "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x48 : [ "23x", "aget-byte",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x49 : [ "23x", "aget-char",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x4a : [ "23x", "aget-short",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x4b : [ "23x", "aput",                       "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x4c : [ "23x", "aput-wide",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x4d : [ "23x", "aput-object",                "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x4e : [ "23x", "aput-boolean",               "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x4f : [ "23x", "aput-byte",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x50 : [ "23x", "aput-char",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x51 : [ "23x", "aput-short",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x52 : [ "22c", "iget",                       "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x53 : [ "22c", "iget-wide",                  "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x54 : [ "22c", "iget-object",                "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x55 : [ "22c", "iget-boolean",               "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x56 : [ "22c", "iget-byte",                  "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x57 : [ "22c", "iget-char",                  "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x58 : [ "22c", "iget-short",                 "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x59 : [ "22c", "iput",                       "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x5a : [ "22c", "iput-wide",                  "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x5b : [ "22c", "iput-object",                "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x5c : [ "22c", "iput-boolean",               "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x5d : [ "22c", "iput-byte",                  "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x5e : [ "22c", "iput-char",                  "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x5f : [ "22c", "iput-short",                 "vA, vB, field@CCCC", "B|A|op CCCC" ],
                  0x60 : [ "21c", "sget",                       "vAA, field@BBBB", "AA|op BBBB" ],
                  0x61 : [ "21c", "sget-wide",                  "vAA, field@BBBB", "AA|op BBBB" ],
                  0x62 : [ "21c", "sget-object",                "vAA, field@BBBB", "AA|op BBBB" ],
                  0x63 : [ "21c", "sget-boolean",               "vAA, field@BBBB", "AA|op BBBB" ],
                  0x64 : [ "21c", "sget-byte",                  "vAA, field@BBBB", "AA|op BBBB" ],
                  0x65 : [ "21c", "sget-char",                  "vAA, field@BBBB", "AA|op BBBB" ],
                  0x66 : [ "21c", "sget-short",                 "vAA, field@BBBB", "AA|op BBBB" ],
                  0x67 : [ "21c", "sput",                       "vAA, field@BBBB", "AA|op BBBB" ],
                  0x68 : [ "21c", "sput-wide",                  "vAA, field@BBBB", "AA|op BBBB" ],
                  0x69 : [ "21c", "sput-object",                "vAA, field@BBBB", "AA|op BBBB" ],
                  0x6a : [ "21c", "sput-boolean",               "vAA, field@BBBB", "AA|op BBBB" ],
                  0x6b : [ "21c", "sput-byte",                  "vAA, field@BBBB", "AA|op BBBB" ],
                  0x6c : [ "21c", "sput-char",                  "vAA, field@BBBB", "AA|op BBBB" ],
                  0x6d : [ "21c", "sput-short",                 "vAA, field@BBBB", "AA|op BBBB" ],
                  0x6e : [ "35c", "invoke-virtual",             "vB{vD, vE, vF, vG, vA}, meth@CCCC", "B|A|op CCCC G|F|E|D" ],
                  0x6f : [ "35c", "invoke-super",               "vB{vD, vE, vF, vG, vA}, meth@CCCC", "B|A|op CCCC G|F|E|D" ],
                  0x70 : [ "35c", "invoke-direct",              "vB{vD, vE, vF, vG, vA}, meth@CCCC", "B|A|op CCCC G|F|E|D" ], 
                  0x71 : [ "35c", "invoke-static",              "vB{vD, vE, vF, vG, vA}, meth@CCCC", "B|A|op CCCC G|F|E|D" ],
                  0x72 : [ "35c", "invoke-interface",           "vB{vD, vE, vF, vG, vA}, meth@CCCC", "B|A|op CCCC G|F|E|D" ],
                  0x74 : [ "3rc", "invoke-virtual/range",       "vB{vCCCC .. vNNNN}, meth@BBBB", "AA|op BBBB CCCC" ],
                  0x75 : [ "3rc", "invoke-super/range",         "vB{vCCCC .. vNNNN}, meth@BBBB", "AA|op BBBB CCCC" ],
                  0x76 : [ "3rc", "invoke-direct/range",        "vB{vCCCC .. vNNNN}, meth@BBBB", "AA|op BBBB CCCC" ],
                  0x77 : [ "3rc", "invoke-static/range",        "vB{vCCCC .. vNNNN}, meth@BBBB", "AA|op BBBB CCCC" ],
                  0x78 : [ "3rc", "invoke-interface/range",     "vB{vCCCC .. vNNNN}, meth@BBBB", "AA|op BBBB CCCC" ],
                  0x7b : [ "12x", "neg-int",                    "vA, vB", "B|A|op" ],
                  0x7c : [ "12x", "not-int",                    "vA, vB", "B|A|op" ],
                  0x7d : [ "12x", "neg-long",                   "vA, vB", "B|A|op" ],
                  0x7e : [ "12x", "not-long",                   "vA, vB", "B|A|op" ],
                  0x7f : [ "12x", "neg-float",                  "vA, vB", "B|A|op" ],
                  0x80 : [ "12x", "neg-double",                 "vA, vB", "B|A|op" ],
                  0x81 : [ "12x", "int-to-long",                "vA, vB", "B|A|op" ],
                  0x82 : [ "12x", "int-to-float",               "vA, vB", "B|A|op" ],
                  0x83 : [ "12x", "int-to-double",              "vA, vB", "B|A|op" ],
                  0x84 : [ "12x", "long-to-int",                "vA, vB", "B|A|op" ],
                  0x85 : [ "12x", "long-to-float",              "vA, vB", "B|A|op" ],
                  0x86 : [ "12x", "long-to-double",             "vA, vB", "B|A|op" ],
                  0x87 : [ "12x", "float-to-int",               "vA, vB", "B|A|op" ],
                  0x88 : [ "12x", "float-to-long",              "vA, vB", "B|A|op" ],
                  0x89 : [ "12x", "float-to-double",            "vA, vB", "B|A|op" ],
                  0x8a : [ "12x", "double-to-int",              "vA, vB", "B|A|op" ],
                  0x8b : [ "12x", "double-to-long",             "vA, vB", "B|A|op" ],
                  0x8c : [ "12x", "double-to-float",            "vA, vB", "B|A|op" ],
                  0x8d : [ "12x", "int-to-byte",                "vA, vB", "B|A|op" ],
                  0x8e : [ "12x", "int-to-char",                "vA, vB", "B|A|op" ],
                  0x8f : [ "12x", "int-to-short",               "vA, vB", "B|A|op" ],
                  0x90 : [ "23x", "add-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x91 : [ "23x", "sub-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x92 : [ "23x", "mul-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x93 : [ "23x", "div-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x94 : [ "23x", "rem-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x95 : [ "23x", "and-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x96 : [ "23x", "or-int",                     "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x97 : [ "23x", "xor-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x98 : [ "23x", "shl-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x99 : [ "23x", "shr-int",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x9a : [ "23x", "ushr-int",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x9b : [ "23x", "add-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x9c : [ "23x", "sub-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x9d : [ "23x", "mul-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x9e : [ "23x", "div-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0x9f : [ "23x", "rem-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa0 : [ "23x", "and-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa1 : [ "23x", "or-long",                    "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa2 : [ "23x", "xor-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa3 : [ "23x", "shl-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],         
                  0xa4 : [ "23x", "shr-long",                   "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa5 : [ "23x", "ushr-long",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa6 : [ "23x", "add-float",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa7 : [ "23x", "sub-float",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa8 : [ "23x", "mul-float",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xa9 : [ "23x", "div-float",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xaa : [ "23x", "rem-float",                  "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xab : [ "23x", "add-double",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xac : [ "23x", "sub-double",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xad : [ "23x", "mul-double",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xae : [ "23x", "div-double",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xaf : [ "23x", "rem-double",                 "vAA, vBB, vCC", "AA|op CC|BB" ],
                  0xb0 : [ "12x", "add-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb1 : [ "12x", "sub-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb2 : [ "12x", "mul-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb3 : [ "12x", "div-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb4 : [ "12x", "rem-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb5 : [ "12x", "and-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb6 : [ "12x", "or-int/2addr",               "vA, vB", "B|A|op" ],
                  0xb7 : [ "12x", "xor-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb8 : [ "12x", "shl-int/2addr",              "vA, vB", "B|A|op" ],
                  0xb9 : [ "12x", "shr-int/2addr",              "vA, vB", "B|A|op" ],
                  0xba : [ "12x", "ushr-int/2addr",             "vA, vB", "B|A|op" ],
                  0xbb : [ "12x", "add-long/2addr",             "vA, vB", "B|A|op" ],
                  0xbc : [ "12x", "sub-long/2addr",             "vA, vB", "B|A|op" ],
                  0xbd : [ "12x", "mul-long/2addr",             "vA, vB", "B|A|op" ],
                  0xbe : [ "12x", "div-long/2addr",             "vA, vB", "B|A|op" ],
                  0xbf : [ "12x", "rem-long/2addr",             "vA, vB", "B|A|op" ],
                  0xc0 : [ "12x", "and-long/2addr",             "vA, vB", "B|A|op" ],
                  0xc1 : [ "12x", "or-long/2addr",              "vA, vB", "B|A|op" ],
                  0xc2 : [ "12x", "xor-long/2addr",             "vA, vB", "B|A|op" ],
                  0xc3 : [ "12x", "shl-long/2addr",             "vA, vB", "B|A|op" ],
                  0xc4 : [ "12x", "shr-long/2addr",             "vA, vB", "B|A|op" ],
                  0xc5 : [ "12x", "ushr-long/2addr",            "vA, vB", "B|A|op" ],
                  0xc6 : [ "12x", "add-float/2addr",            "vA, vB", "B|A|op" ],
                  0xc7 : [ "12x", "sub-float/2addr",            "vA, vB", "B|A|op" ],
                  0xc8 : [ "12x", "mul-float/2addr",            "vA, vB", "B|A|op" ],
                  0xc9 : [ "12x", "div-float/2addr",            "vA, vB", "B|A|op" ],
                  0xca : [ "12x", "rem-float/2addr",            "vA, vB", "B|A|op" ],
                  0xcb : [ "12x", "add-double/2addr",           "vA, vB", "B|A|op" ],
                  0xcc : [ "12x", "sub-double/2addr",           "vA, vB", "B|A|op" ],
                  0xcd : [ "12x", "mul-double/2addr",           "vA, vB", "B|A|op" ],
                  0xce : [ "12x", "div-double/2addr",           "vA, vB", "B|A|op" ],
                  0xcf : [ "12x", "rem-double/2addr",           "vA, vB", "B|A|op" ],
                  0xd0 : [ "22s", "add-int/lit16",              "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd1 : [ "22s", "rsub-int",                   "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd2 : [ "22s", "mul-int/lit16",              "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd3 : [ "22s", "div-int/lit16",              "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd4 : [ "22s", "rem-int/lit16",              "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd5 : [ "22s", "and-int/lit16",              "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd6 : [ "22s", "or-int/lit16",               "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd7 : [ "22s", "xor-int/lit16",              "vA, vB, #+CCCC", "B|A|op CCCC" ],
                  0xd8 : [ "22b", "add-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xd9 : [ "22s", "rsub-int/lit8",              "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xda : [ "22s", "mul-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xdb : [ "22s", "div-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xdc : [ "22s", "rem-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xdd : [ "22s", "and-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xde : [ "22s", "or-int/lit8",                "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xdf : [ "22s", "xor-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xe0 : [ "22s", "shl-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xe1 : [ "22s", "shr-int/lit8",               "vAA, vBB, #+CC", "AA|op CC|BB" ],
                  0xe2 : [ "22s", "ushr-int/lit8",              "vAA, vBB, #+CC", "AA|op CC|BB" ],
                 }

MATH_DVM_OPCODES = { "add." : '+',
                     "div." : '/',
                     "mul." : '*',
                     "or." : '|',
                     "sub." : '-',
                     "and." : '&',
                     "xor." : '^',
                     "shl." : "<<",
                     "shr." : ">>",
                   }

INVOKE_DVM_OPCODES = [ "invoke." ]

FIELD_READ_DVM_OPCODES = [ ".get" ]
FIELD_WRITE_DVM_OPCODES = [ ".put" ]
                              
BREAK_DVM_OPCODES = [ "invoke.", "move.", ".put", "if." ]

BRANCH_DVM_OPCODES = [ "if.", "goto", "goto.", "return", "return.", "packed." ] #, "sparse." ]

def readuleb128(buff) :
   result = ord( buff.read(1) )
   if result > 0x7f :
      cur = ord( buff.read(1) )
      result = (result & 0x7f) | ((cur & 0x7f) << 7)
      if cur > 0x7f :
         cur = ord( buff.read(1) )
         result |= (cur & 0x7f) << 14
         if cur > 0x7f :
            cur = ord( buff.read(1) )
            result |= (cur & 0x7f) << 21
            if cur > 0x7f :
               cur = ord( buff.read(1) )
               result |= cur << 28

   return result

def readsleb128(buff) :
   result = unpack( '<b', buff.read(1) )[0]

   if result <= 0x7f :
      result = (result << 25) 
      if result > 0x7fffffff :
         result = (0x7fffffff & result) - 0x80000000
      result = result >> 25 
   else :
      cur = unpack( '<b', buff.read(1) )[0]
      result = (result & 0x7f) | ((cur & 0x7f) << 7)
      if cur <= 0x7f :
         result = (result << 18) >> 18
      else :
         cur = unpack( '<b', buff.read(1) )[0]
         result |= (cur & 0x7f) << 14
         if cur <= 0x7f :   
            result = (result << 11) >> 11
         else :
            cur = unpack( '<b', buff.read(1) )[0]
            result |= (cur & 0x7f) << 21
            if cur <= 0x7f :
               result = (result << 4) >> 4
            else :
               cur = unpack( '<b', buff.read(1) )[0]
               result |= cur << 28

   return result

def writeuleb128(value) :
   remaining = value >> 7

   buff = ""
   while remaining > 0 :
      buff += pack( "<B", ((value & 0x7f) | 0x80) )

      value = remaining
      remaining >>= 7

   buff += pack( "<B", value & 0x7f )
   return buff

def writesleb128(value) :
   remaining = value >> 7
   hasMore = True
   end = 0 
   buff = ""

   if (value & (-sys.maxint - 1)) == 0 :   
      end = 0
   else :
      end = -1

   while hasMore :
      hasMore = (remaining != end) or ((remaining & 1) != ((value >> 6) & 1))
      tmp = 0
      if hasMore :
         tmp = 0x80

      buff += pack( "<B", (value & 0x7f) | (tmp) )
      value = remaining
      remaining >>= 7

   return buff

class HeaderItem :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.format = SVs( HEADER[0], HEADER[1], buff.read( calcsize(HEADER[0]) ) ) 

   def reload(self) :
      pass

   def get_obj(self) :
      return []

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, self.format.get_value_buff() ) ]

   def get_value(self) :
      return self.format.get_value()

   def show(self) :
      bytecode._Print("HEADER", self.format)

   def get_off(self) :
      return self.__offset.off

class AnnotationOffItem :
   def __init__(self,  buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.annotation_off = SV( '<L', buff.read( 4 ) )

   def show(self) :
     print "ANNOTATION_OFF_ITEM annotation_off=0x%x" % self.annotation_off.get_value()

   def get_obj(self) :
      return []

   def get_raw(self) :
     return bytecode.Buff( self.__offset.off, self.annotation_off.get_value_buff() )

class AnnotationSetItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.annotation_off_item = []

      self.size = SV( '<L', buff.read( 4 ) )
      for i in range(0, self.size) :
         self.annotation_off_item.append( AnnotationOffItem(buff, cm) )

   def reload(self) :
      pass

   def get_annotation_off_item(self) :
      return self.annotation_off_item

   def show(self) :
      print "ANNOTATION_SET_ITEM"
      nb = 0
      for i in self.annotation_off_item :
         print nb, 
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.annotation_off_item ]

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset.off, self.size.get_value_buff()) ] + [ i.get_raw() for i in self.annotation_off_item ]

   def get_off(self) :
      return self.__offset.off

class FieldAnnotation :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.field_idx = SV('<L', buff.read( 4 ) )
      self.annotations_off = SV('<L', buff.read( 4 ) )

   def show(self) :
      print "FIELD_ANNOTATION field_idx=0x%x annotations_off=0x%x" % (self.field_idx.get_value(), self.annotations_off.get_value())

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff(self.__offset.off, self.field_idx.get_value_buff() + self.annotations_off.get_value_buff())

class MethodAnnotation :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.method_idx = SV('<L', buff.read( 4 ) )
      self.annotations_off = SV('<L', buff.read( 4 ) )

   def show(self) :
      print "METHOD_ANNOTATION method_idx=0x%x annotations_off=0x%x" % ( self.method_idx.get_value(), self.annotations_off.get_value())

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff(self.__offset.off, self.method_idx.get_value_buff() + self.annotations_off.get_value_buff())

class ParameterAnnotation :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.method_idx = SV('<L', buff.read( 4 ) )
      self.annotations_off = SV('<L', buff.read( 4 ) )

   def show(self) :
      print "PARAMETER_ANNOTATION method_idx=0x%x annotations_off=0x%x" % (self.method_idx.get_value(), self.annotations_off.get_value())

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff(self.__offset.off, self.method_idx.get_value_buff() + self.annotations_off.get_value_buff())

class AnnotationsDirectoryItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.format = SVs( ANNOTATIONS_DIRECTORY_ITEM[0], ANNOTATIONS_DIRECTORY_ITEM[1], buff.read( calcsize(ANNOTATIONS_DIRECTORY_ITEM[0]) ) )

      self.field_annotations = []
      for i in range(0, self.format.get_value().fields_size) :
         self.field_annotations.append( FieldAnnotation( buff, cm ) )

      self.method_annotations = []
      for i in range(0, self.format.get_value().annotated_methods_size) :
         self.method_annotations.append( MethodAnnotation( buff, cm ) )

      self.parameter_annotations = []
      for i in range(0, self.format.get_value().annotated_parameters_size) :
         self.parameter_annotations.append( ParameterAnnotation( buff, cm ) )

   def reload(self) :
      pass

   def show(self) :
      print "ANNOTATIONS_DIRECTORY_ITEM", self.format.get_value()
      for i in self.field_annotations :
         i.show()

      for i in self.method_annotations :
         i.show()

      for i in self.parameter_annotations :
         i.show()

   def get_obj(self) :
      return [ i for i in self.field_annotations ] + \
             [ i for i in self.method_annotations ] + \
             [ i for i in self.parameter_annotations ]

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, self.format.get_value_buff() ) ] + \
             [ i.get_raw() for i in self.field_annotations ] + \
             [ i.get_raw() for i in self.method_annotations ] + \
             [ i.get_raw() for i in self.parameter_annotations ]

   def get_off(self) :
      return self.__offset.off

class TypeLItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      self.type_idx = SV( '<H', buff.read( 2 ) )

   def show(self) :
      print "TYPE_LITEM", self.type_idx.get_value()

   def get_string(self) :
      return self.__CM.get_type( self.type_idx.get_value() )

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff(self.__offset.off, self.type_idx.get_value_buff())

class TypeList :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      offset = buff.get_idx()

      self.pad = ""
      if offset % 4 != 0 :
         self.pad = buff.read( offset % 4 )

      self.size = SV( '<L', buff.read( 4 ) )

      self.list = []
      for i in range(0, self.size) :
         self.list.append( TypeLItem( buff, cm ) )

   def reload(self) :
      pass

   def get_type_list_off(self) :
      return self.__offset.off + len(self.pad)

   def get_string(self) :
      return ' '.join(i.get_string() for i in self.list)

   def show(self) :
      print "TYPE_LIST"
      nb = 0
      for i in self.list :
         print nb, self.__offset.off + len(self.pad),
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.list ]

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, self.pad + self.size.get_value_buff() ) ] + [ i.get_raw() for i in self.list ]

   def get_off(self) :
      return self.__offset.off

DBG_END_SEQUENCE                = 0x00 #    (none)  terminates a debug info sequence for a code_item
DBG_ADVANCE_PC                  = 0x01 #    uleb128 addr_diff       addr_diff: amount to add to address register    advances the address register without emitting a positions entry
DBG_ADVANCE_LINE                = 0x02 #    sleb128 line_diff       line_diff: amount to change line register by    advances the line register without emitting a positions entry
DBG_START_LOCAL                 = 0x03 #    uleb128 register_num 
                                       #    uleb128p1 name_idx 
                                       #    uleb128p1 type_idx      
                                       #        register_num: register that will contain local name_idx: string index of the name 
                                       #        type_idx: type index of the type  introduces a local variable at the current address. Either name_idx or type_idx may be NO_INDEX to indicate that that value is unknown.
DBG_START_LOCAL_EXTENDED        = 0x04 #    uleb128 register_num uleb128p1 name_idx uleb128p1 type_idx uleb128p1 sig_idx       
                                       #        register_num: register that will contain local 
                                       #        name_idx: string index of the name 
                                       #        type_idx: type index of the type
                                       #        sig_idx: string index of the type signature     
                                       # introduces a local with a type signature at the current address. Any of name_idx, type_idx, or sig_idx may be NO_INDEX to indicate that that value is unknown. (
                                       # If sig_idx is -1, though, the same data could be represented more efficiently using the opcode DBG_START_LOCAL.)
                                       # Note: See the discussion under "dalvik.annotation.Signature" below for caveats about handling signatures.
DBG_END_LOCAL                   = 0x05 #    uleb128 register_num    
                                       #         register_num: register that contained local     
                                       #         marks a currently-live local variable as out of scope at the current address
DBG_RESTART_LOCAL               = 0x06 #    uleb128 register_num    
                                       #         register_num: register to restart re-introduces a local variable at the current address. 
                                       #         The name and type are the same as the last local that was live in the specified register.
DBG_SET_PROLOGUE_END            = 0x07 #    (none)  sets the prologue_end state machine register, indicating that the next position entry that is added should be considered the end of a 
                                       #            method prologue (an appropriate place for a method breakpoint). The prologue_end register is cleared by any special (>= 0x0a) opcode.
DBG_SET_EPILOGUE_BEGIN          = 0x08 #    (none)  sets the epilogue_begin state machine register, indicating that the next position entry that is added should be considered the beginning 
                                       #            of a method epilogue (an appropriate place to suspend execution before method exit). The epilogue_begin register is cleared by any special (>= 0x0a) opcode.
DBG_SET_FILE                    = 0x09 #    uleb128p1 name_idx      
                                       #         name_idx: string index of source file name; NO_INDEX if unknown indicates that all subsequent line number entries make reference to this source file name, 
                                       #         instead of the default name specified in code_item
DBG_Special_Opcodes_BEGIN       = 0x0a #    (none)  advances the line and address registers, emits a position entry, and clears prologue_end and epilogue_begin. See below for description.
DBG_Special_Opcodes_END         = 0xff

class DBGBytecode :
   def __init__(self, op_value) :
      self.__op_value = op_value
      self.__format = []

   def get_op_value(self) :
      return self.__op_value

   def add(self, value, ttype) :
      self.__format.append( (value, ttype) )
   
   def show(self) :
      return [ i[0] for i in self.__format ]

   def get_obj(self) :
      return []

   def get_raw(self) :
      buff = self.__op_value.get_value_buff()
      for i in self.__format :
         if i[1] == "u" :
            buff += writeuleb128( i[0] )
         elif i[1] == "s" :
            buff += writesleb128( i[0] )
      return buff

class DebugInfoItem2 :
   def __init__(self, buff, cm) :
      self.__CM = cm 
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )

      self.__buff = buff
      self.__raw = ""

   def reload(self) :
      offset = self.__offset.off

      n = self.__CM.get_next_offset_item( offset )

      s_idx = self.__buff.get_idx()
      self.__buff.set_idx( offset )
      self.__raw = self.__buff.read( n - offset )
      self.__buff.set_idx( s_idx )

   def show(self) :
      pass

   def get_obj(self) :
      return []

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset.off, self.__raw) ]

   def get_off(self) :
      return self.__offset.off

class DebugInfoItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__line_start = readuleb128( buff )
      self.__parameters_size = readuleb128( buff ) 

      self.__parameter_names = []
      for i in range(0, self.__parameters_size) :
         self.__parameter_names.append( readuleb128( buff ) )

      self.__bytecodes = []
      bcode = DBGBytecode( SV( '<B', buff.read(1) ) )
      self.__bytecodes.append( bcode )

      while bcode.get_op_value().get_value() != DBG_END_SEQUENCE :
         bcode_value = bcode.get_op_value().get_value()
#         print "0x%x" % bcode_value

         if bcode_value == DBG_SET_PROLOGUE_END : 
            pass
         elif bcode_value >= DBG_Special_Opcodes_BEGIN and bcode_value <= DBG_Special_Opcodes_END :
            pass 
         elif bcode_value == DBG_ADVANCE_PC :
            bcode.add( readuleb128( buff ), "u" )
         elif bcode_value == DBG_ADVANCE_LINE :
            bcode.add( readsleb128( buff ), "s" )
         elif bcode_value == DBG_START_LOCAL :
            bcode.add( readuleb128( buff ), "u" )
            bcode.add( readuleb128( buff ), "u" )
            bcode.add( readuleb128( buff ), "u" )
         elif bcode_value == DBG_START_LOCAL_EXTENDED :
            bcode.add( readuleb128( buff ), "u" )
            bcode.add( readuleb128( buff ), "u" )
            bcode.add( readuleb128( buff ), "u" )
            bcode.add( readuleb128( buff ), "u" )
         elif bcode_value == DBG_END_LOCAL :
            bcode.add( readuleb128( buff ), "u" )
         elif bcode_value == DBG_RESTART_LOCAL :
            bcode.add( readuleb128( buff ), "u" )
         else :
            bytecode.Exit( "unknown or not yet supported DBG bytecode 0x%x" % bcode_value ) 
   
         bcode = DBGBytecode( SV( '<B', buff.read(1) ) )
         self.__bytecodes.append( bcode )

   def reload(self) :
      pass

   def show(self) :
      print self.__line_start
      print self.__parameters_size
      print self.__parameter_names

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, writeuleb128( self.__line_start ) + \
                                             writeuleb128( self.__parameters_size ) + \
                                             ''.join(writeuleb128(i) for i in self.__parameter_names) + \
                                             ''.join(i.get_raw() for i in self.__bytecodes) ) ]


VALUE_BYTE     = 0x00   # (none; must be 0)       ubyte[1]        signed one-byte integer value
VALUE_SHORT    = 0x02   # size - 1 (0..1)  ubyte[size]     signed two-byte integer value, sign-extended
VALUE_CHAR     = 0x03   # size - 1 (0..1)  ubyte[size]     unsigned two-byte integer value, zero-extended
VALUE_INT      = 0x04   # size - 1 (0..3)  ubyte[size]     signed four-byte integer value, sign-extended
VALUE_LONG     = 0x06   # size - 1 (0..7)  ubyte[size]     signed eight-byte integer value, sign-extended
VALUE_FLOAT    = 0x10   # size - 1 (0..3)  ubyte[size]     four-byte bit pattern, zero-extended to the right, and interpreted as an IEEE754 32-bit floating point value
VALUE_DOUBLE   = 0x11   # size - 1 (0..7)  ubyte[size]     eight-byte bit pattern, zero-extended to the right, and interpreted as an IEEE754 64-bit floating point value
VALUE_STRING   = 0x17   # size - 1 (0..3)  ubyte[size]     unsigned (zero-extended) four-byte integer value, interpreted as an index into the string_ids section and representing a string value
VALUE_TYPE     = 0x18   # size - 1 (0..3)  ubyte[size]     unsigned (zero-extended) four-byte integer value, interpreted as an index into the type_ids section and representing a reflective type/class value
VALUE_FIELD    = 0x19   # size - 1 (0..3)  ubyte[size]     unsigned (zero-extended) four-byte integer value, interpreted as an index into the field_ids section and representing a reflective field value
VALUE_METHOD   = 0x1a   # size - 1 (0..3)  ubyte[size]     unsigned (zero-extended) four-byte integer value, interpreted as an index into the method_ids section and representing a reflective method value
VALUE_ENUM     = 0x1b   # size - 1 (0..3)  ubyte[size]     unsigned (zero-extended) four-byte integer value, interpreted as an index into the field_ids section and representing the value of an enumerated type constant
VALUE_ARRAY    = 0x1c   # (none; must be 0)       encoded_array   an array of values, in the format specified by "encoded_array Format" below. The size of the value is implicit in the encoding.
VALUE_ANNOTATION       = 0x1d   # (none; must be 0)       encoded_annotation      a sub-annotation, in the format specified by "encoded_annotation Format" below. The size of the value is implicit in the encoding.
VALUE_NULL     = 0x1e   # (none; must be 0)       (none)  null reference value
VALUE_BOOLEAN  = 0x1f   # boolean (0..1) (none)  one-bit value; 0 for false and 1 for true. The bit is represented in the value_arg.


class EncodedArray :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.size = readuleb128( buff )

      self.values = []
      for i in range(0, self.size) :
         self.values.append( EncodedValue(buff, cm) )

   def show(self) :
      print "ENCODED_ARRAY"
      for i in self.values :
         i.show()

   def get_values(self) :
      return self.values

   def get_obj(self) :
      return [ i for i in self.values ]

   def get_raw(self) :
      return writeuleb128( self.size ) + ''.join(i.get_raw() for i in self.values)

class EncodedValue :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )

      self.val = SV('<B', buff.read( 1 ) )
      self.__value_arg = self.val.get_value() >> 5
      self.__value_type = self.val.get_value() & 0x1f

     
      self.value = ""

      if self.__value_type >= VALUE_SHORT and self.__value_type < VALUE_ARRAY :
         self.value = buff.read( self.__value_arg + 1 )
      elif self.__value_type == VALUE_ARRAY :
         self.value = EncodedArray( buff, cm )
      elif self.__value_type == VALUE_ANNOTATION :
         self.value = EncodedAnnotation( buff, cm ) 
      elif self.__value_type == VALUE_BYTE :
         self.value = buff.read( 1 )
      elif self.__value_type == VALUE_NULL :
         pass
      elif self.__value_type == VALUE_BOOLEAN :
         pass
      else :
         bytecode.Exit( "Unknown value 0x%x" % self.__value_type )

   def show(self) :
      print "ENCODED_VALUE", self.val, self.__value_arg, self.__value_type, repr(self.value)

   def get_obj(self) :
      if isinstance(self.value, str) == False :
         return [ self.value ]
      return []

   def get_raw(self) :
      if isinstance(self.value, str) :
         return self.val.get_value_buff() + self.value
      else :
         return self.val.get_value_buff() + self.value.get_raw()

class AnnotationElement :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.name_idx = readuleb128( buff )
      self.value = EncodedValue( buff, cm )

   def show(self) :
      print "ANNOTATION_ELEMENT", self.name_idx
      self.value.show()
   
   def get_obj(self) :
      return [ self.value ]

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset.off, writeuleb128(self.name_idx) + self.value.get_raw()) ]


class EncodedAnnotation :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )

      self.type_idx = readuleb128( buff )
      self.size = readuleb128( buff )
      
      self.elements = []
      for i in range(0, self.size) :
         self.elements.append( AnnotationElement( buff, cm ) )

   def show(self) :
      print "ENCODED_ANNOTATION", self.type_idx, self.size
      for i in self.elements :
         i.show()
   
   def get_obj(self) :
      return [ i for i in self.elements ]

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, writeuleb128(self.type_idx) + writeuleb128(self.size) ) ] + \
             [ i.get_raw() for i in self.elements ]

class AnnotationItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )

      self.visibility = SV( '<B', buff.read( 1 ) )  
      self.annotation = EncodedAnnotation(buff, cm)

   def reload(self) :
      pass
   
   def show(self) :
      print "ANNOATATION_ITEM", self.visibility.get_value()
      self.annotation.show()

   def get_obj(self) :
      return [ self.annotation ]

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset.off, self.visibility.get_value_buff()) ] + self.annotation.get_raw()

   def get_off(self) :
      return self.__offset.off

class EncodedArrayItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )

      self.value = EncodedArray( buff, cm )
  
   def reload(self) :
     pass

   def show(self) :
      print "ENCODED_ARRAY_ITEM"
      self.value.show()

   def get_obj(self) :
      return [ self.value ]

   def get_raw(self) :
      return bytecode.Buff( self.__offset.off, self.value.get_raw() )

   def get_off(self) :
      return self.__offset.off

class StringDataItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )

      self.utf16_size = readuleb128( buff ) 
      self.data = buff.read( self.utf16_size + 1 )

      if self.data[-1] != '\x00' :
         i = buff.read( 1 )
         self.utf16_size += 1
         self.data += i
         while i != '\x00' :
            i = buff.read( 1 )
            self.utf16_size += 1
            self.data += i
                  
   def reload(self) :
      pass

   def get(self) :
      return self.data[:-1]

   def show(self) :
      print "STRING_DATA_ITEM", "%d %s" % ( self.utf16_size, repr( self.data ) )

   def get_obj(self) :
      return []

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, writeuleb128( self.utf16_size ) + self.data ) ]
   
   def get_off(self) :
      return self.__offset.off

class StringIdItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
     
      self.string_data_off = SV( '<L', buff.read( 4 ) )

   def reload(self) :
      pass

   def get_data_off(self) :
      return self.string_data_off.get_value()

   def get_obj(self) :
      return [] 

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, self.string_data_off.get_value_buff() ) ]

   def show(self) :
      print "STRING_ID_ITEM", self.string_data_off.get_value()

   def get_off(self) :
      return self.__offset.off

class IdItem(object) :
   def __init__(self, size, buff, cm, TClass) :
      self.elem = []
      for i in range(0, size) :
         self.elem.append( TClass(buff, cm) )

   def gets(self) :
      return self.elem

   def get(self, idx) :
      return self.elem[ idx ]

   def reload(self) :
      for i in self.elem :
         i.reload()

   def show(self) :
      nb = 0
      for i in self.elem :
         print nb,
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.elem ]

   def get_raw(self) :
      return [ i.get_raw() for i in self.elem ]

class TypeItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.format = SV( '<L', buff.read( 4 ) )
      self._name = None

   def reload(self) :
      self._name = self.__CM.get_string( self.format.get_value() )

   def show(self) :
      print "TYPE_ITEM", self.format.get_value(), self._name

   def get_value(self) :
      return self.format.get_value()

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff( self.__offset.off, self.format.get_value_buff() )

class TypeIdItem :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.type = []

      for i in range(0, size) :
         self.type.append( TypeItem( buff, cm ) )

   def reload(self) :
      for i in self.type :
         i.reload()

   def get(self, idx) :
      return self.type[ idx ].get_value()

   def show(self) :
      print "TYPE_ID_ITEM"
      nb = 0
      for i in self.type :
         print nb, 
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.type ]

   def get_raw(self) :
      return [ i.get_raw() for i in self.type ]

   def get_off(self) :
      return self.__offset.off

class ProtoItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.format = SVs( PROTO_ID_ITEM[0], PROTO_ID_ITEM[1], buff.read( calcsize(PROTO_ID_ITEM[0]) ) )
      self._shorty = None
      self._return = None
      self._params = None

   def reload(self) :
      self._shorty = self.__CM.get_string( self.format.get_value().shorty_idx )
      self._return = self.__CM.get_type( self.format.get_value().return_type_idx )
      self._params = self.__CM.get_type_list( self.format.get_value().parameters_off )

   def get_params(self) :
      return self._params

   def get_shorty(self) :
      return self._shorty

   def get_return_type(self) :
      return self._return

   def show(self) :
      print "PROTO_ITEM", self._shorty, self._return, self.format.get_value()

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff( self.__offset.off, self.format.get_value_buff() )

class ProtoIdItem :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.proto = []

      for i in range(0, size) :
         self.proto.append( ProtoItem(buff, cm) )

   def get(self, idx) :
      return self.proto[ idx ]

   def reload(self) :
      for i in self.proto :
         i.reload()

   def show(self) :
      print "PROTO_ID_ITEM"
      nb = 0
      for i in self.proto :
         print nb,
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.proto ]

   def get_raw(self) :
      return [ i.get_raw() for i in self.proto ]

   def get_off(self) :
      return self.__offset.off

class FieldItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.format = SVs( FIELD_ID_ITEM[0], FIELD_ID_ITEM[1], buff.read( calcsize(FIELD_ID_ITEM[0]) ) )
      self._class = None
      self._type = None
      self._name = None

   def reload(self) :
      general_format = self.format.get_value()
      self._class = self.__CM.get_type( general_format.class_idx )
      self._type = self.__CM.get_type( general_format.type_idx )
      self._name = self.__CM.get_string( general_format.name_idx )

   def get_class_name(self) :
      return self._class

   def get_class(self) :
      return self._class

   def get_type(self) :
      return self._type

   def get_descriptor(self) :
      return self._type
   
   def get_name(self) :
      return self._name

   def show(self) :
      print "FIELD_ITEM", self._class, self._type, self._name, self.format.get_value()

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff( self.__offset.off, self.format.get_value_buff() )

   def get_off(self) :
      return self.__offset.off

class FieldIdItem(IdItem) :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      super(FieldIdItem, self).__init__(size, buff, cm, FieldItem)

   def get_off(self) :
      return self.__offset.off

class MethodItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.format = SVs( METHOD_ID_ITEM[0], METHOD_ID_ITEM[1], buff.read( calcsize(METHOD_ID_ITEM[0]) ) )
      self._class = None
      self._proto = None
      self._name = None

   def reload(self) :
      general_format = self.format.get_value()
      self._class = self.__CM.get_type( general_format.class_idx )
      self._proto = self.__CM.get_proto( general_format.proto_idx )
      self._name = self.__CM.get_string( general_format.name_idx )

   def get_type(self) :
      return self.format.get_value().proto_idx

   def show(self) :
      print "METHOD_ITEM", self._name, self._proto, self._class, self.format.get_value()
   
   def get_class(self) :
      return self._class

   def get_proto(self) :
      return self._proto

   def get_name(self) :
      return self._name

   def get_obj(self) :
      return []

   def get_raw(self) :
      return bytecode.Buff( self.__offset.off, self.format.get_value_buff() )

class MethodIdItem :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.methods = []
      for i in range(0, size) :
         self.methods.append( MethodItem(buff, cm) )

   def get(self, idx) :
      return self.methods[ idx ]

   def reload(self) :
      for i in self.methods :
         i.reload()

   def show(self) :
      print "METHOD_ID_ITEM"
      nb = 0
      for i in self.methods :
         print nb,
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.methods ]

   def get_raw(self) :
      return [ i.get_raw() for i in self.methods ]

   def get_off(self) :
      return self.__offset.off

class EncodedField :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.field_idx_diff = readuleb128( buff )
      self.access_flags = readuleb128( buff )
      
      self.__field_idx = 0

      self._name = None
      self._proto = None
      self._class_name = None

   def reload(self) :
      name = self.__CM.get_field( self.__field_idx )
      self._class_name = name[0]
      self._name = name[2]
      self._proto = ''.join(i for i in name[1])

   def get_access(self) :
      return self.access_flags

   def get_class_name(self) :
      return self._class_name

   def get_descriptor(self) :
      return self._proto

   def get_name(self) :
      return self._name

   def adjust_idx(self, val) :
      self.__field_idx = self.field_idx_diff + val

   def get_idx(self) :
      return self.__field_idx

   def get_obj(self) :
      return []

   def get_raw(self) :
      return writeuleb128( self.field_idx_diff ) + writeuleb128( self.access_flags )

   def show(self) :
      print "\tENCODED_FIELD field_idx_diff=%d access_flags=%d (%s,%s,%s)" % (self.field_idx_diff, self.access_flags, self._class_name, self._proto, self._name)

class EncodedMethod :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.method_idx_diff = readuleb128( buff )
      self.access_flags = readuleb128( buff )
      self.code_off = readuleb128( buff )

      self.__method_idx = 0

      self._name = None
      self._proto = None
      self._class_name = None

      self._code = None

   def reload(self) :
      v = self.__CM.get_method( self.__method_idx )
      self._class_name = v[0]
      self._proto = ''.join(i for i in v[1])
      self._name = v[2]

      self._code = self.__CM.get_code( self.code_off )

   def show(self) :
      print "\tENCODED_METHOD method_idx_diff=%d access_flags=%d code_off=0x%x (%s %s,%s)" % (self.method_idx_diff, self.access_flags, self.code_off, self._class_name, self._proto, self._name)
      if self._code != None :
         self._code.show()

   def pretty_show(self, vm_a) :
      print "\tENCODED_METHOD method_idx_diff=%d access_flags=%d code_off=0x%x (%s %s,%s)" % (self.method_idx_diff, self.access_flags, self.code_off, self._class_name, self._proto, self._name)
      if self._code != None :
         self._code.pretty_show( vm_a.hmethods[ self ] )

   def get_access(self) :
      return self.access_flags

   def get_code(self) :
      return self._code

   def get_descriptor(self) :
      return self._proto

   def get_class_name(self) :
      return self._class_name

   def get_name(self) :
      return self._name

   def adjust_idx(self, val) :
      self.__method_idx = self.method_idx_diff + val

   def get_idx(self) :
      return self.__method_idx

   def get_obj(self) :
      return []

   def get_raw(self) :
      return writeuleb128( self.method_idx_diff ) + writeuleb128( self.access_flags ) + writeuleb128( self.code_off )


class ClassDataItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.static_fields_size = readuleb128( buff )
      self.instance_fields_size = readuleb128( buff )
      self.direct_methods_size = readuleb128( buff )
      self.virtual_methods_size = readuleb128( buff ) 

      self.static_fields = []
      self.instance_fields = []
      self.direct_methods = []
      self.virtual_methods = []

      self.load_field( self.static_fields_size, self.static_fields, EncodedField, buff, cm )
      self.load_field( self.instance_fields_size, self.instance_fields, EncodedField, buff, cm )
      self.load_field( self.direct_methods_size, self.direct_methods, EncodedMethod, buff, cm )
      self.load_field( self.virtual_methods_size, self.virtual_methods, EncodedMethod, buff, cm )

   def load_field(self, size, l, Type, buff, cm) :
      prev = 0
      for i in range(0, size) :
         el = Type(buff, cm)
         el.adjust_idx( prev )
         prev = el.get_idx()

         l.append( el )

   def reload(self) :
      for i in self.static_fields :
         i.reload()

      for i in self.instance_fields :
         i.reload()

      for i in self.direct_methods :
         i.reload()

      for i in self.virtual_methods :
         i.reload()

   def show(self) :
      print "CLASS_DATA_ITEM static_fields_size=%d instance_fields_size=%d direct_methods_size=%d virtual_methods_size=%d" % \
            (self.static_fields_size, self.instance_fields_size, self.direct_methods_size, self.virtual_methods_size)

      print "SF"
      for i in self.static_fields :
         i.show()

      print "IF"
      for i in self.instance_fields :
         i.show()

      print "DM"
      for i in self.direct_methods :
         i.show()

      print "VM"
      for i in self.virtual_methods :
         i.show()

   def pretty_show(self, vm_a) :
      print "CLASS_DATA_ITEM static_fields_size=%d instance_fields_size=%d direct_methods_size=%d virtual_methods_size=%d" % \
            (self.static_fields_size, self.instance_fields_size, self.direct_methods_size, self.virtual_methods_size)

      print "SF"
      for i in self.static_fields :
         i.show()

      print "IF"
      for i in self.instance_fields :
         i.show()

      print "DM"
      for i in self.direct_methods :
         i.pretty_show( vm_a )

      print "VM"
      for i in self.virtual_methods :
         i.pretty_show( vm_a )

   def get_methods(self) :
      return [ x for x in self.direct_methods ] + [ x for x in self.virtual_methods ]

   def get_fields(self) :
      return [ x for x in self.static_fields ] + [ x for x in self.instance_fields ]

   def get_off(self) :
      return self.__offset.off

   def get_obj(self) :
      return [ i for i in self.static_fields ] + \
             [ i for i in self.instance_fields ] + \
             [ i for i in self.direct_methods ] + \
             [ i for i in self.virtual_methods ]

   def get_raw(self) :
      buff = writeuleb128( self.static_fields_size ) + \
             writeuleb128( self.instance_fields_size ) + \
             writeuleb128( self.direct_methods_size ) + \
             writeuleb128( self.virtual_methods_size ) + \
             ''.join(i.get_raw() for i in self.static_fields) + \
             ''.join(i.get_raw() for i in self.instance_fields) + \
             ''.join(i.get_raw() for i in self.direct_methods) + \
             ''.join(i.get_raw() for i in self.virtual_methods)

      return [ bytecode.Buff(self.__offset.off, buff) ]

class ClassItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.format = SVs( CLASS_DEF_ITEM[0], CLASS_DEF_ITEM[1], buff.read( calcsize(CLASS_DEF_ITEM[0]) ) )
      self._class_data_item = None

      self._name = None
      self._sname = None

   def reload(self) :
      general_format = self.format.get_value()
      self._name = self.__CM.get_type( general_format.class_idx )
      self._sname = self.__CM.get_type( general_format.superclass_idx )

      if general_format.class_data_off != 0 :
         self._class_data_item = self.__CM.get_class_data_item( general_format.class_data_off )
         self._class_data_item.reload()

   def show(self) :
      print "CLASS_ITEM", self._name, self._sname, self.format.get_value()
  
   def get_name(self) :
      return self._name

   def get_info(self) :
      return "%s:%s" % (self._name, self._sname)

   def get_methods(self) :
      if self._class_data_item != None :
         return self._class_data_item.get_methods()
      return []

   def get_fields(self) :
      if self._class_data_item != None :
         return self._class_data_item.get_fields()
      return []

   def get_obj(self) :
      return []

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, self.format.get_value_buff() ) ]

class ClassDefItem :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.class_def = []

      for i in range(0, size) :
         idx = buff.get_idx()
   
         class_def = ClassItem( buff, cm )
         self.class_def.append( class_def )
         
         buff.set_idx( idx + calcsize(CLASS_DEF_ITEM[0]) )

   def get_method(self, name_class, name_method) :
      l = []

      for i in self.class_def :
         if i.get_name() == name_class :
            for j in i.get_methods() :
               if j.get_name() == name_method :
                  l.append(j)

      return l

   def get_names(self) :
      return [ x.get_name() for x in self.class_def ]

   def reload(self) :
      for i in self.class_def :
         i.reload()

   def show(self) :
      print "CLASS_DEF_ITEM"
      nb = 0
      for i in self.class_def :
         print nb,
         i.show()
         nb = nb + 1

   def get_obj(self) :
      return [ i for i in self.class_def ]

   def get_raw(self) :
      return [ i.get_raw() for i in self.class_def ]

   def get_off(self) :
      return self.__offset.off

class EncodedTypeAddrPair :
   def __init__(self, buff) :
      self.type_idx = readuleb128( buff )
      self.addr = readuleb128( buff )

   def get_obj(self) :
      return []

   def show(self) :
      print "ENCODED_TYPE_ADDR_PAIR", self.type_idx, self.addr

   def get_raw(self) :
      return writeuleb128( self.type_idx ) + writeuleb128( self.addr )

class EncodedCatchHandler :
   def __init__(self, buff) :
      self.size = readsleb128( buff )

      self.handlers = []
      
      for i in range(0, abs(self.size)) :
         self.handlers.append( EncodedTypeAddrPair(buff) )

      if self.size <= 0 :
         self.catch_all_addr = readuleb128( buff )

   def show(self) :
      print "ENCODED_CATCH_HANDLER size=0x%x" % self.size
      for i in self.handlers :
         i.show()

   def get_obj(self) :
      return [ i for i in self.handlers ]

   def get_raw(self) :
      buff = writesleb128( self.size ) + ''.join(i.get_raw() for i in self.handlers)
      
      if self.size <= 0 :
         buff += writeuleb128( self.catch_all_addr )

      return buff

class EncodedCatchHandlerList :
   def __init__(self, buff) :
      self.size = readuleb128( buff )
      self.list = []

      for i in range(0, self.size) :
         self.list.append( EncodedCatchHandler(buff) )

   def show(self) :
      print "ENCODED_CATCH_HANDLER_LIST size=0x%x" % self.size
      for i in self.list :
         i.show()
   
   def get_obj(self) :
      return [ i for i in self.list ]

   def get_raw(self) :
      return writeuleb128( self.size ) + ''.join(i.get_raw() for i in self.list)

class DBCSpe :
   def __init__(self, cm, op) :
      self.__CM = cm
      self.op = op

   def get_name(self) :
      return self.op.get_name()
   
   def get_operands(self) :
      return  self.op.get_operands()

   def get_length(self) :
      return self.op.get_length()

   def show(self, pos) :
      self.op.show( pos )

class DBC :
   def __init__(self, class_manager, op_name, operands, raw_buff) :
      self.__CM = class_manager

      self.op_name = op_name
      self.operands = operands
      self.raw_buff = raw_buff

   def get_length(self) :
      return len(self.raw_buff)

   def get_name(self) :
      """Return the name of the bytecode"""
      return self.op_name

   def get_operands(self) :
      return self.operands

   def show(self, pos) :
      print self.op_name,

      v = []
      r = []
      for i in self.operands[1:] :
         if i[0] == "v" :
            v.append( i )
         else :
            r.append( i )

      if "invoke" in self.op_name :
         off = v[0][1]
         x = v[2:4]
         x.reverse()
         t = v[4:]
         t.reverse()
         x.extend( t )
         print ', '.join(self._more_info(n[0], n[1]) for n in x[:off]), ' '.join(self._more_info(n[0], n[1]) for n in r),
      else :
         v.reverse()
         print ', '.join(self._more_info(n[0], n[1]) for n in v), ' '.join(self._more_info(n[0], n[1]) for n in r),

   def _more_info(self, c, v) :
      if "string" in c :
         return "%s%x{%s}" % (c, v, self.__CM.get_string(v))
      elif "meth" in c :
         m = self.__CM.get_method(v)
         return "%s%x{%s %s%s,%s}" % (c, v, m[0], m[1][0], m[1][1], m[2])
      elif "field" in c :
         f = self.__CM.get_field(v)
         return "%s%x{%s %s,%s}" % (c, v, f[0], f[1], f[2])
      elif "type" in c :
         return "%s%x{%s}" % (c, v, self.__CM.get_type(v))
      return "%s%x" % (c, v)

class DCode :
   def __init__(self, class_manager, size, buff) :
      self.__CM = class_manager
      self.__insn = buff

      self.__h_special_bytecodes = {}
      self.__bytecodes = []

      ushort = calcsize( '<H' )
      
      real_j = 0
      j = 0 
      while j < (size * ushort) :
         # handle special instructions
         if real_j in self.__h_special_bytecodes :
            special_e = self.__h_special_bytecodes[ real_j ]( self.__insn[j : ] )

            self.__bytecodes.append( DBCSpe( self.__CM, special_e ) )

            del self.__h_special_bytecodes[ real_j ]
            j += special_e.get_length()
         else :
            op_value = unpack( '<B', self.__insn[j] )[0]
            
            if op_value in DALVIK_OPCODES :
               operands = []
               special = None

               if len(DALVIK_OPCODES[ op_value ]) >= 4 :
                  if len( DALVIK_OPCODES[ op_value ][3] ) == 0 :
                     bytecode.Exit( "opcode [ 0x%x:%s ] not yet supported" % (op_value ,DALVIK_OPCODES[ op_value ][1]) )

                  operands, special = self._analyze_mnemonic( self.__insn[ j : j + int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort ], DALVIK_OPCODES[ op_value ])

                  if special != None :
                     self.__h_special_bytecodes[ special[0] + real_j ] = special[1] 

               self.__bytecodes.append( DBC( self.__CM, DALVIK_OPCODES[ op_value ][1], operands, self.__insn[j : j + int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort ] ) )

               j += ( int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort)
            else :
               bytecode.Exit( "invalid opcode [ 0x%x ]" % op_value )

         real_j = j / 2

   def _analyze_mnemonic(self, buff_operands, mnemonic) :
      operands = []
      t_ops = mnemonic[3].split(' ')

#      print "la", mnemonic
      l = []
      for i in buff_operands :
         l.append( (ord(i) & 0b11110000) >> 4 )
         l.append( (ord(i) & 0b00001111) )
              
      for i in t_ops :
         sub_ops = i.split('|')         
                  
         if len(sub_ops[-1]) == 2 :
            sub_ops = [ sub_ops[-1] ] + sub_ops[0:-1]
         else :
            sub_ops = sub_ops[2:] + sub_ops[0:2]

#         print sub_ops
         for sub_op in sub_ops :
            zero_count = string.count(sub_op, '0')
                     
            #print sub_op, "ZERO", zero_count
            if zero_count == len(sub_op) :
               for zero in range(0, zero_count) :
                  l.pop(0)
               continue

            size = ((len(sub_op) - zero_count)  * 4)
            signed = 0

            pos_op = string.find(mnemonic[2], sub_op)
            if pos_op != -1 and mnemonic[2][pos_op - 1] == '+' : 
               signed = 1
            
            #print mnemonic, repr(sub_op), signed
            ttype = "op@"

            truc = False
            if pos_op != -1 :
               t_pos_op = pos_op 

               while pos_op > 0 and mnemonic[2][pos_op] != ' ' :
                  pos_op = pos_op - 1

               ttype = mnemonic[2][pos_op : t_pos_op].replace(' ', '')
               if "{" in ttype :
                  ttype = ttype[ string.find(ttype, "{") + 1 : ]
            else :
               if sub_op != "op" :
                  ttype = "v"

#            print "SIZE", size
            val = self._extract( signed, l, size ) << (zero_count * 4)
   
            operands.append( [ttype, val] )

            if len(l) == 0 :
               break

#      if mnemonic[1] == "invoke-direct" :
#         print "ID", operands

      if len(mnemonic) == 5 :
         return operands, (operands[2][1], mnemonic[4])
      
      return operands, None

   def _extract(self, signed, l, size) :
      #print signed, l, size
      #if size == 16 :
      #   print repr(chr( (l[0] << 4) + (l[1]) ) + chr( (l[2] << 4) + (l[3]) ))

      func = string.capitalize

      if signed == 1 :
         func = string.lower
         
      if size == 4 :
         return l.pop(0)
      elif size == 8 :
         return unpack('<%s' % func('B'), chr( (l.pop(0) << 4) + l.pop(0) ) )[0]
      elif size == 16 :
         return unpack('<%s' % func('H'), chr( (l.pop(0) << 4) + (l.pop(0)) ) + chr( (l.pop(0) << 4) + (l.pop(0)) ) )[0]
      elif size == 32 :
         return unpack('<%s' % func('L'), chr( (l.pop(0) << 4) + (l.pop(0)) ) + chr( (l.pop(0) << 4) + (l.pop(0)) ) + chr( (l.pop(0) << 4) + (l.pop(0)) ) + chr( (l.pop(0) << 4) + (l.pop(0)) ) )[0]
      else :      
         bytecode.Exit( "invalid size [ 0x%x ]" % size )                                                                                                                                                                 

   def get(self) :
      return self.__bytecodes

   def get_raw(self) :
      return self.__insn

   def get_ins_off(self, off) :
      idx = 0

      for i in self.__bytecodes :
         if idx == off :
            return i
         idx += i.get_length()

      return None

   def show(self) :
      nb = 0
      idx = 0
      for i in self.__bytecodes :
         print nb, "0x%x" % idx,   
         i.show(nb)
         print

         idx += i.get_length()
         nb += 1
   
   def pretty_show(self, m_a) :
      paths = []
      for i in m_a.basic_blocks.get() :
         for j in i.childs :
            paths.append( ( j[0], j[1] ) )

      nb = 0
      idx = 0
      for i in self.__bytecodes :
         bytecode.PrettyShow( idx, paths, nb, i )
         idx += ( i.get_length() )
         nb += 1

class DalvikCode : 
   def __init__(self, buff, cm) :
      self.__CM = cm
      
      off = buff.get_idx()
      while off % 4 != 0 :
         off += 1

      buff.set_idx( off )

      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.__off = buff.get_idx()

      self.registers_size = SV( '<H', buff.read( 2 ) )   
      self.ins_size = SV( '<H', buff.read( 2 ) )
      self.outs_size = SV( '<H', buff.read( 2 ) )
      self.tries_size = SV( '<H', buff.read( 2 ) )
      self.debug_info_off = SV( '<L', buff.read( 4 ) )
      self.insns_size = SV( '<L', buff.read( 4 ) )

      ushort = calcsize( '<H' )

      self._code = DCode( self.__CM, self.insns_size.get_value(), buff.read( self.insns_size.get_value() * ushort ) )

      if (self.insns_size.get_value() % 2 == 1) :
         self.__padding = SV( '<H', buff.read( 2 ) )

      self.__tries = []
      self.__handlers = []
      if self.tries_size.get_value() > 0 :
         for i in range(0, self.tries_size.get_value()) :
            try_item = SVs( TRY_ITEM[0], TRY_ITEM[1], buff.read( calcsize(TRY_ITEM[0]) ) )
            self.__tries.append( try_item )
         
         self.__handlers.append( EncodedCatchHandlerList( buff ) )

   def get_length(self) :
      return self.insns_size.get_value()

   def get_bc(self) :
      return self._code

   def get_off(self) :
      return self.__off

   def _begin_show(self) :
      print "*" * 80 
      print "DALVIK_CODE :"
      bytecode._Print("\tREGISTERS_SIZE", self.registers_size)
      bytecode._Print("\tINS_SIZE", self.ins_size)
      bytecode._Print("\tOUTS_SIZE", self.outs_size)
      bytecode._Print("\tTRIES_SIZE", self.tries_size)
      bytecode._Print("\tDEBUG_INFO_OFF", self.debug_info_off)
      bytecode._Print("\tINSNS_SIZE", self.insns_size)

      for i in self.__handlers :
         i.show()

      print ""

   def show(self) :
      self._begin_show()
      self._code.show()
      self._end_show()

   def _end_show(self) :
      print "*" * 80

   def pretty_show(self, vm_a) :
      self._begin_show()
      self._code.pretty_show(vm_a)
      self._end_show()

   def get_obj(self) :
      return [ i for i in self.__handlers ]

   def get_raw(self) :
      buff =  self.registers_size.get_value_buff() + \
              self.ins_size.get_value_buff() + \
              self.outs_size.get_value_buff() + \
              self.tries_size.get_value_buff() + \
              self.debug_info_off.get_value_buff() + \
              self.insns_size.get_value_buff() + \
              self._code.get_raw()

      if (self.insns_size.get_value() % 2 == 1) :
         buff += self.__padding.get_value_buff()

      if self.tries_size.get_value() > 0 :
         buff += ''.join(i.get_value_buff() for i in self.__tries)
         for i in self.__handlers :
            buff += i.get_raw()

      return bytecode.Buff( self.__offset.off,
                            buff )

class CodeItem :
   def __init__(self, size, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.code = []
      self.__code_off = {}

      for i in range(0, size) :
         x = DalvikCode( buff, cm )
         self.code.append( x )
         self.__code_off[ x.get_off() ] = x

   def get_code(self, off) :
      try : 
         return self.__code_off[off]
      except KeyError :
         return None

   def reload(self) :
      pass

   def show(self) :
      print "CODE_ITEM"
      for i in self.code :
         i.show()

   def get_obj(self) :
      return [ i for i in self.code ]

   def get_raw(self) :
      return [ i.get_raw() for i in self.code ]

   def get_off(self) :
      return self.__offset.off
      
class MapItem :
   def __init__(self, buff, cm) :
      self.__CM = cm
      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.format = SVs( MAP_ITEM[0], MAP_ITEM[1], buff.read( calcsize( MAP_ITEM[0] ) ) )

      self.item = None

      general_format = self.format.get_value()
      buff.set_idx( general_format.offset )

#      print TYPE_MAP_ITEM[ general_format.type ], "@ 0x%x(%d) %d" % (buff.get_idx(), buff.get_idx(), general_format.size)

      if TYPE_MAP_ITEM[ general_format.type ] == "TYPE_STRING_ID_ITEM" :
         self.item = [ StringIdItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_CODE_ITEM" :
         self.item = CodeItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_TYPE_ID_ITEM" :
         self.item = TypeIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_PROTO_ID_ITEM" :
         self.item = ProtoIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_FIELD_ID_ITEM" :
         self.item = FieldIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_METHOD_ID_ITEM" :
         self.item = MethodIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_CLASS_DEF_ITEM" :
         self.item = ClassDefItem( general_format.size, buff, cm )
      
      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_HEADER_ITEM" :
         self.item = HeaderItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ANNOTATION_ITEM" :
         self.item = [ AnnotationItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ANNOTATION_SET_ITEM" :
         self.item = [ AnnotationSetItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ANNOTATIONS_DIRECTORY_ITEM" :
         self.item = [ AnnotationsDirectoryItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_TYPE_LIST" :
         self.item = [ TypeList( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_STRING_DATA_ITEM" :
         self.item = [ StringDataItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_DEBUG_INFO_ITEM" :
      # FIXME : strange bug with sleb128 ....
#       self.item = [ DebugInfoItem( buff, cm ) for i in range(0, general_format.size) ]
         self.item = DebugInfoItem2( buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ENCODED_ARRAY_ITEM" :
         self.item = [ EncodedArrayItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_CLASS_DATA_ITEM" :
         self.item = [ ClassDataItem(buff, cm) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_MAP_LIST" :
         pass # It's me I think !!!
      
      else :
         bytecode.Exit( "Map item @ 0x%x(%d) is unknown" % (buff.get_idx(), buff.get_idx()) )

   def reload(self) :
      if self.item != None :
         if isinstance( self.item, list ):
            for i in self.item :
               i.reload()
         else :
            self.item.reload()

   def show(self) :
      bytecode._Print( "MAP_ITEM", self.format )
      bytecode._Print( "\tTYPE_ITEM", TYPE_MAP_ITEM[ self.format.get_value().type ])

      if self.item != None :
         if isinstance( self.item, list ):
            for i in self.item :
               i.show()
         else :   
            if isinstance(self.item, CodeItem) == False :
               self.item.show()

   def pretty_show(self, vm_a) :
      bytecode._Print( "MAP_ITEM", self.format )
      bytecode._Print( "\tTYPE_ITEM", TYPE_MAP_ITEM[ self.format.get_value().type ])

      if self.item != None :
         if isinstance( self.item, list ):
            for i in self.item :
               if isinstance(i, ClassDataItem) :
                  i.pretty_show(vm_a)
               elif isinstance(self.item, CodeItem) == False :
                  i.show()
         else :
            if isinstance(self.item, ClassDataItem) :
               self.item.pretty_show(vm_a)
            elif isinstance(self.item, CodeItem) == False :
               self.item.show()

   def get_obj(self) :
      if self.item == None :
         return []

      if isinstance( self.item, list ) :
         return [ i for i in self.item ]

      return [ self.item ]

   def get_raw(self) :
      if self.item == None :
         return [ bytecode.Buff( self.__offset.off, self.format.get_value_buff() ) ]
      else :
         if isinstance( self.item, list ) :
            return [ bytecode.Buff( self.__offset.off, self.format.get_value_buff() ) ] + [ i.get_raw() for i in self.item ]
         else :
            return [ bytecode.Buff( self.__offset.off, self.format.get_value_buff() ) ] + self.item.get_raw()

   def get_length(self) :
      return calcsize( MAP_ITEM[0] )

   def get_type(self) :
      return self.format.get_value().type

   def get_item(self) :
      return self.item

class OffObj :
   def __init__(self, o) :
      self.off = o

class ClassManager :
   def __init__(self) :
      self.__manage_item = {}
      self.__manage_item_off = []
      self.__offsets = {}

      self.__strings_off = {}

   def add_offset(self, off, obj) :
      x = OffObj( off )
      self.__offsets[ obj ] = x
      return x

   def add_type_item(self, type_item, item) :
      self.__manage_item[ type_item ] = item
   
      sdi = False
      if type_item == "TYPE_STRING_DATA_ITEM" :
         sdi = True

      if item != None : 
         if isinstance(item, list) :
            for i in item :
               goff = i.get_off()
               self.__manage_item_off.append( goff )
               if sdi == True :
                  self.__strings_off[ goff ] = i
         else :
            self.__manage_item_off.append( item.get_off() )

   def get_code(self, idx) :
      return self.__manage_item[ "TYPE_CODE_ITEM" ].get_code( idx )

   def get_class_data_item(self, off) :
      for i in self.__manage_item[ "TYPE_CLASS_DATA_ITEM" ] :
         if i.get_off() == off :
            return i

      bytecode.Exit( "unknown class data item @ 0x%x" % off )

   def get_string(self, idx) :
      off = self.__manage_item[ "TYPE_STRING_ID_ITEM" ][idx].get_data_off() 
      try :
         return self.__strings_off[off].get()
      except KeyError :
         bytecode.Exit( "unknown string item @ 0x%x(%d)" % (off,idx) )

   def get_type_list(self, off) :
      if off == 0 :
         return "()"

      for i in self.__manage_item[ "TYPE_TYPE_LIST" ] :
         if i.get_type_list_off() == off :
            return "(" + i.get_string() + ")"
      
      return None

   def get_type(self, idx) :
      type = self.__manage_item[ "TYPE_TYPE_ID_ITEM" ].get( idx )
      return self.get_string( type )

   def get_proto(self, idx) :
      proto = self.__manage_item[ "TYPE_PROTO_ID_ITEM" ].get( idx )
      return [ proto.get_params(), proto.get_return_type() ]

   def get_field(self, idx, ref=False) :
      field = self.__manage_item[ "TYPE_FIELD_ID_ITEM"].get( idx )

      if ref == True :
         return field

      return [ field.get_class(), field.get_type(), field.get_name() ]

   def get_method(self, idx) :
      method = self.__manage_item[ "TYPE_METHOD_ID_ITEM" ].get( idx )
      return [ method.get_class(), method.get_proto(), method.get_name() ]

   def get_next_offset_item(self, idx) :
      for i in self.__manage_item_off :
         if i > idx :
            return i
      return idx

class MapList :
   def __init__(self, off, buff) :
      self.__CM = ClassManager()
      buff.set_idx( off )

      self.__offset = self.__CM.add_offset( buff.get_idx(), self )
      
      self.size = SV( '<L', buff.read( 4 ) )

      self.map_item = []
      for i in range(0, self.size) :
         idx = buff.get_idx()

         mi = MapItem( buff, self.__CM )
         self.map_item.append( mi )

         buff.set_idx( idx + mi.get_length() )

         self.__CM.add_type_item( TYPE_MAP_ITEM[ mi.get_type() ], mi.get_item() )

      for i in self.map_item :
         i.reload()

   def get_item_type(self, ttype) :
      for i in self.map_item :
         if TYPE_MAP_ITEM[ i.get_type() ] == ttype :
            return i.get_item()

   def show(self) :
      bytecode._Print("MAP_LIST SIZE", self.size.get_value())
      for i in self.map_item :
         i.show()

   def pretty_show(self, vm_a) :
      bytecode._Print("MAP_LIST SIZE", self.size.get_value())
      for i in self.map_item :
         i.pretty_show(vm_a)

   def get_obj(self) :
      return [ x for x in self.map_item ]

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset.off, self.size.get_value_buff()) ] + \
             [ x.get_raw() for x in self.map_item ]

   def get_class_manager(self) :
      return self.__CM

class Data :
   def __init__(self, buff) :
      pass

class DalvikVMFormat(bytecode._Bytecode) :
   def __init__(self, buff) :
      super(DalvikVMFormat, self).__init__( buff )
      super(DalvikVMFormat, self).register( bytecode.SHOW, self.show )

      self.load_class()

   def load_class(self) :
      self.__header = HeaderItem( 0, self, ClassManager() )

      self.map_list = MapList( self.__header.get_value().map_off, self )

      self.classes = self.map_list.get_item_type( "TYPE_CLASS_DEF_ITEM" )
      self.methods = self.map_list.get_item_type( "TYPE_METHOD_ID_ITEM" )
      self.fields = self.map_list.get_item_type( "TYPE_FIELD_ID_ITEM" )
      self.codes = self.map_list.get_item_type( "TYPE_CODE_ITEM" )
      self.strings = self.map_list.get_item_type( "TYPE_STRING_DATA_ITEM" )

   def show(self) :
      """Show the .class format into a human readable format"""
      self.map_list.show()

   def save(self) :
      """
         Return the dex (with the modifications) into raw format
      
         @rtype: string
      """
      return self._get_raw()

   def pretty_show(self, vm_a) :
      self.map_list.pretty_show(vm_a)

   def _iterFlatten(self, root):
      if isinstance(root, (list, tuple)):      
         for element in root :
            for e in self._iterFlatten(element) :      
               yield e               
      else:                      
         yield root
   
   def _Exp(self, x) :
      l = []
      for i in x :
         l.append(i)
         l.append( self._Exp( i.get_obj() ) )
      return l

   def _get_raw(self) :
#      print len( list(self._iterFlatten( self._Exp( self.map_list.get_obj() ) ) ) )
      # Due to the specific format of dalvik virtual machine,
      # we will get a list of raw object described by a buffer, a size and an offset
      # where to insert the specific buffer into the file 
      l = self.map_list.get_raw()

      result = list(self._iterFlatten( l ))
      result = sorted(result, key=lambda x: x.offset)

      idx = 0
      buff = ""
      for i in result :
#         print idx, i.offset, "--->", i.offset + i.size
         if idx == i.offset :
            buff += i.buff
         else :
#            print "PATCH @ 0x%x" % idx
            self.set_idx( idx )
            buff += '\x00' * (i.offset - idx)
            buff += i.buff
            idx += (i.offset - idx) 
#            raise( "oops" )

         idx += i.size 

      return buff

   def get_method(self, name) :
      """Return into a list all methods which corresponds to the regexp

         @param name : the name of the method (a regexp)
      """
      prog = re.compile(name)
      l = []
      for i in self.classes.class_def :
         for j in i.get_methods() : 
            if prog.match( j.get_name() ) :
               l.append( j )
      return l

   def get_field(self, name) :
      """Return into a list all fields which corresponds to the regexp

         @param name : the name of the field (a regexp)
      """
      prog = re.compile(name)
      l = []
      for i in self.classes.class_def :
         for j in i.get_fields() :
            if prog.match( j.get_name() ) :
               l.append( j )
      return l

   def get_all_fields(self) :
      return self.fields.gets()

   def get_fields(self) :
      """Return all objects fields"""
      l = []
      for i in self.classes.class_def :
         for j in i.get_fields() :
            l.append( j )
      return l

   def get_methods(self) :
      """Return all objects methods"""
      l = []
      for i in self.classes.class_def :
         for j in i.get_methods() :
            l.append( j )
      return l

   def get_method_descriptor(self, class_name, method_name, descriptor) :
      """
         Return the specific method

         @param class_name : the class name of the method
         @param method_name : the name of the method
         @param descriptor : the descriptor of the method

      """
      for i in self.classes.class_def :
         for j in i.get_methods() :
            if class_name == j.get_class_name() and method_name == j.get_name() and descriptor == j.get_descriptor() :
               return j
      return None

   def get_field_descriptor(self, class_name, field_name, descriptor) :
      """
         Return the specific field

         @param class_name : the class name of the field
         @param field_name : the name of the field
         @param descriptor : the descriptor of the field

      """
      for i in self.classes.class_def :
         if class_name == i.get_name() : 
            for j in i.get_fields() :
               if field_name == j.get_name() and descriptor == j.get_descriptor() :
                  return i
      return None
   
   def get_class_manager(self) :
      """
         Return directly the class manager
      
         @rtype : L{ClassManager}
      """
      return self.map_list.get_class_manager()

   def get_strings(self) :
      """
         Return all strings
      """
      return [i.get() for i in self.strings]

   def get_type(self) :
      return "DVM"
