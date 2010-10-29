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

import sys, re, types, string
from collections import namedtuple
from struct import pack, unpack, calcsize


HEADER = [ '<QL20sLLLLLLLLLLLLLLLLLLLL', namedtuple( "HEADER", "magic checksum signature file_size header_size endian_tag link_size link_off " \
                                                               "map_off string_ids_size string_ids_off type_ids_size type_ids_off proto_ids_size " \
                                                               "proto_ids_off field_ids_size field_ids_off method_ids_size method_ids_off "\
                                                               "class_defs_size class_defs_off data_size data_off" ) ]

MAP_ITEM = [ '<HHLL', namedtuple("MAP_ITEM", "type unused size offset") ]

PROTO_ID_ITEM = [ '<LLL', namedtuple("PROTO_ID_ITEM", "shorty_idx return_type_idx parameters_off" ) ]
METHOD_ID_ITEM = [ '<HHL', namedtuple("METHOD_ID_ITEM", "class_idx proto_idx name_idx" ) ]
FIELD_ID_ITEM = [ '<HHL', namedtuple("FILED_ID_ITEM", "class_idx type_idx name_idx") ]

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
      
      format = self.general_format.get_value()
      self.data = buff[ calcsize(FILL_ARRAY_DATA[0]) : calcsize(FILL_ARRAY_DATA[0]) + (general_format.size * general_format.element_width ) ]

   def show(self) :
      print self.format.get_value(), self.data

   def get_size(self) :
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
        
   def show(self) :
     print self.format.get_value(), self.keys, self.targets

   def get_size(self) :
     return calcsize(SPARSE_SWITCH[0]) + (self.format.get_value().size * calcsize('<L')) * 2

class PackedSwitch :
   def __init__(self, buff) :
      self.format = SVs( PACKED_SWITCH[0], PACKED_SWITCH[1], buff[ 0 : calcsize(PACKED_SWITCH[0]) ] )
      self.targets = []

      idx = calcsize(PACKED_SWITCH[0])
      for i in range(0, self.format.get_value().size) :
         self.targets.append( unpack('<L', buff[idx:idx+4]) )
         idx += 4
        
   def show(self) :
     print self.format.get_value(), self.targets

   def get_size(self) :
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
                  0x16 : [ "21s", "const-wide/16",              "vAA, #+BBBB", "AA|op BBBB", "AA|op BBBB" ], 
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
   def __init__(self, size, buff) :
      self.__offset = buff.get_idx()
      self.format = SVs( HEADER[0], HEADER[1], buff.read( calcsize(HEADER[0]) ) ) 

   def reload(self) :
      pass

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, self.format.get_value_buff() ) ]

   def get_value(self) :
      return self.format.get_value()

   def show(self) :
      bytecode._Print("HEADER", self.format)

   def get_off(self) :
      return self.__offset

class AnnotationOffItem :
   def __init__(self,  buff, cm) :
      self.__offset = buff.get_idx()
      self.annotation_off = SV( '<L', buff.read( 4 ) )

   def show(self) :
     print self.annotation_off.get_value()

   def get_raw(self) :
     return bytecode.Buff( self.__offset, self.annotation_off.get_value_buff() )

class AnnotationSetItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__annotation_off_item = []

      self.__size = SV( '<L', buff.read( 4 ) )
      for i in range(0, self.__size) :
         self.__annotation_off_item.append( AnnotationOffItem(buff, cm) )

   def get_annotation_off_item(self) :
      return self.__annotation_off_item

   def reload(self) :
      pass

   def show(self) :
      nb = 0
      for i in self.__annotation_off_item :
         print nb, i,
         i.show()
         nb = nb + 1

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset, self.__size.get_value_buff()) ] + [ i.get_raw() for i in self.__annotation_off_item ]

   def get_off(self) :
      return self.__offset

class FieldAnnotation :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.field_idx = SV('<L', buff.read( 4 ) )
      self.annotations_off = SV('<L', buff.read( 4 ) )

   def get_raw(self) :
      return bytecode.Buff(self.__offset, self.field_idx.get_value_buff() + self.annotations_off.get_value_buff())

class MethodAnnotation :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.method_idx = SV('<L', buff.read( 4 ) )
      self.annotations_off = SV('<L', buff.read( 4 ) )

   def get_raw(self) :
      return bytecode.Buff(self.__offset, self.method_idx.get_value_buff() + self.annotations_off.get_value_buff())

class ParameterAnnotation :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.method_idx = SV('<L', buff.read( 4 ) )
      self.annotations_off = SV('<L', buff.read( 4 ) )

   def get_raw(self) :
      return bytecode.Buff(self.__offset, self.method_idx.get_value_buff() + self.annotations_off.get_value_buff())

class AnnotationsDirectoryItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.format = SVs( ANNOTATIONS_DIRECTORY_ITEM[0], ANNOTATIONS_DIRECTORY_ITEM[1], buff.read( calcsize(ANNOTATIONS_DIRECTORY_ITEM[0]) ) )

      self.__field_annotations = []
      for i in range(0, self.format.get_value().fields_size) :
         self.__field_annotations.append( FieldAnnotation( buff, cm ) )

      self.__method_annotations = []
      for i in range(0, self.format.get_value().annotated_methods_size) :
         self.__method_annotations.append( MethodAnnotation( buff, cm ) )

      self.__parameter_annotations = []
      for i in range(0, self.format.get_value().annotated_parameters_size) :
         self.__parameter_annotations.append( ParameterAnnotation( buff, cm ) )

   def reload(self) :
      pass

   def show(self) :
      print self.format.get_value()

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, self.format.get_value_buff() ) ] + \
             [ i.get_raw() for i in self.__field_annotations ] + \
             [ i.get_raw() for i in self.__method_annotations ] + \
             [ i.get_raw() for i in self.__parameter_annotations ]

   def get_off(self) :
      return self.__offset

class TypeLItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.type_idx = SV( '<H', buff.read( 2 ) )

   def show(self) :
      print self.type_idx.get_value_buff()

   def get_raw(self) :
      return bytecode.Buff(self.__offset, self.type_idx.get_value_buff())

class TypeList :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()

      self.pad = ""
      if self.__offset % 4 != 0 :
         self.pad = buff.read( self.__offset % 4 )

      self.size = SV( '<L', buff.read( 4 ) )

      self.__list = []
      for i in range(0, self.size) :
         self.__list.append( TypeLItem( buff, cm ) )

   def reload(self) :
      pass

   def show(self) :
      nb = 0
      for i in self.__list :
         print nb, i,
         i.show()
         nb = nb + 1

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, self.pad + self.size.get_value_buff() ) ] + [ i.get_raw() for i in self.__list ]

   def get_off(self) :
      return self.__offset

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
   
   def get_raw(self) :
      buff = self.__op_value.get_value_buff()
      for i in self.__format :
         if i[1] == "u" :
            buff += writeuleb128( i[0] )
         elif i[1] == "s" :
            buff += writesleb128( i[0] )
      return buff

   def show(self) :
      return [ i[0] for i in self.__format ]

class DebugInfoItem2 :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__buff = buff
      self.__CM = cm
      self.__raw = ""

   def reload(self) :
      n = self.__CM.get_next_offset_item( self.__offset )

      s_idx = self.__buff.get_idx()
      self.__buff.set_idx( self.__offset )
      self.__raw = self.__buff.read( n - self.__offset )
      self.__buff.set_idx( s_idx )

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset, self.__raw) ]

   def get_off(self) :
      return self.__offset

   def show(self) :
      pass

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
      self.size = readuleb128( buff )

      self.__values = []
      for i in range(0, self.size) :
         self.__values.append( EncodedValue(buff, cm) )

   def get_raw(self) :
      return writeuleb128( self.size ) + ''.join(i.get_raw() for i in self.__values)

   def get_values(self) :
      return self.__values

class EncodedValue :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()

      self.val = SV('<B', buff.read( 1 ) )
      self.__value_arg = self.val.get_value() >> 5
      self.__value_type = self.val.get_value() & 0x1f

     
      self.__value = ""

      if self.__value_type >= VALUE_SHORT and self.__value_type < VALUE_ARRAY :
         self.__value = buff.read( self.__value_arg + 1 )
      elif self.__value_type == VALUE_ARRAY :
         self.__value = EncodedArray( buff, cm )
      elif self.__value_type == VALUE_BYTE :
         self.__value = buff.read( 1 )
      elif self.__value_type == VALUE_NULL :
         pass
      elif self.__value_type == VALUE_BOOLEAN :
         pass
      else :
         raise( "oops" )

   def get_raw(self) :
      if isinstance(self.__value, str) :
         return self.val.get_value_buff() + self.__value
      else :
         return self.val.get_value_buff() + self.__value.get_raw()

   def show(self) :
      print self.val, self.__value_arg, self.__value_type, self.__value

class AnnotationElement :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.name_idx = readuleb128( buff )
      
      self.value = EncodedValue( buff, cm )

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset, writeuleb128(self.name_idx) + self.value.get_raw()) ]

   def show(self) :
      print self.name_idx
      self.value.show()

class EncodedAnnotation :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()

      self.type_idx = readuleb128( buff )
      self.size = readuleb128( buff )
      
      self.__elements = []
      for i in range(0, self.size) :
         self.__elements.append( AnnotationElement( buff, cm ) )

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, writeuleb128(self.type_idx) + writeuleb128(self.size) ) ] + \
             [ i.get_raw() for i in self.__elements ]

   def show(self) :
      print self.type_idx, self.size
      for i in self.__elements :
         i.show()

class AnnotationItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.visibility = SV( '<B', buff.read( 1 ) )  
      self.annotation = EncodedAnnotation(buff, cm)

   def reload(self) :
      pass
   
   def show(self) :
      print self.visibility.get_value()
      self.annotation.show()

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset, self.visibility.get_value_buff()) ] + self.annotation.get_raw()

   def get_off(self) :
      return self.__offset

class EncodedArrayItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__value = EncodedArray( buff, cm )
  
   def reload(self) :
     pass

   def show(self) :
      pass

   def get_raw(self) :
      return bytecode.Buff( self.__offset, self.__value.get_raw() )

   def get_off(self) :
      return self.__offset

class StringDataItem :
   def __init__(self, buff) :
      self.__offset = buff.get_idx()
      self.__utf16_size = readuleb128( buff ) 
      self.__data = buff.read( self.__utf16_size + 1 )

   def reload(self) :
      pass

   def get(self) :
      return self.__data[:-1]

   def show(self) :
      print "%d %s" % ( self.__utf16_size, repr( self.__data ) )

   def get_off(self) :
      return self.__offset

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, writeuleb128( self.__utf16_size ) + self.__data ) ]

class StringIdItem :
   def __init__(self, buff) :
      self.__offset = buff.get_idx()      
      self.__string_data_off = SV( '<L', buff.read( 4 ) )

   def reload(self) :
      pass

   def get_data_off(self) :
      return self.__string_data_off.get_value()

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, self.__string_data_off.get_value_buff() ) ]

   def show(self) :
      print self.__string_data_off.get_value()

   def get_off(self) :
      return self.__offset

class IdItem(object) :
   def __init__(self, size, buff, cm, TClass) :
      self.__elem = []
      for i in range(0, size) :
         self.__elem.append( TClass(buff, cm) )

   def get(self, idx) :
      return self.__elem[ idx ]

   def reload(self) :
      for i in self.__elem :
         i.reload()

   def show(self) :
      nb = 0
      for i in self.__elem :
         print nb, i,
         i.show()
         nb = nb + 1

   def get_raw(self) :
      return [ i.get_raw() for i in self.__elem ]

class TypeItem :
   def __init__(self, buff, cm) :
      self.__cm = cm
      self.__offset = buff.get_idx()
      self.__general_format = SV( '<L', buff.read( 4 ) )
      self.__name = None

   def reload(self) :
      self.__name = self.__cm.get_string( self.__general_format.get_value() )

   def show(self) :
      print self.__general_format.get_value(), self.__name

   def get_value(self) :
      return self.__general_format.get_value()

   def get_raw(self) :
      return bytecode.Buff( self.__offset, self.__general_format.get_value_buff() )

class TypeIdItem :
   def __init__(self, size, buff, cm) :
      self.__offset = buff.get_idx()
      self.__type = []
      self.__cm = cm

      for i in range(0, size) :
         self.__type.append( TypeItem( buff, cm ) )

   def reload(self) :
      for i in self.__type :
         i.reload()

   def get(self, idx) :
      return self.__type[ idx ].get_value()

   def get_raw(self) :
      return [ i.get_raw() for i in self.__type ]

   def show(self) :
      nb = 0
      for i in self.__type :
         print nb, 
         i.show()
         nb = nb + 1

   def get_off(self) :
      return self.__offset

class ProtoItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__general_format = SVs( PROTO_ID_ITEM[0], PROTO_ID_ITEM[1], buff.read( calcsize(PROTO_ID_ITEM[0]) ) )
      self.__shorty = None
      self.__return = None
      
      self.__cm = cm

   def reload(self) :
      self.__shorty = self.__cm.get_string( self.__general_format.get_value().shorty_idx )
      self.__return = self.__cm.get_type( self.__general_format.get_value().return_type_idx )

   def get_shorty(self) :
      return self.__shorty

   def get_return_type(self) :
      return self.__return

   def show(self) :
      print self.__shorty, self.__return, self.__general_format.get_value()

   def get_raw(self) :
      return bytecode.Buff( self.__offset, self.__general_format.get_value_buff() )

class ProtoIdItem :
   def __init__(self, size, buff, cm) :
      self.__offset = buff.get_idx()
      self.__proto = []

      for i in range(0, size) :
         self.__proto.append( ProtoItem(buff, cm) )

   def get(self, idx) :
      return self.__proto[ idx ]

   def reload(self) :
      for i in self.__proto :
         i.reload()

   def show(self) :
      nb = 0
      for i in self.__proto :
         print nb, i,
         i.show()
         nb = nb + 1

   def get_raw(self) :
      return [ i.get_raw() for i in self.__proto ]

   def get_off(self) :
      return self.__offset

class FieldItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__general_format = SVs( FIELD_ID_ITEM[0], FIELD_ID_ITEM[1], buff.read( calcsize(FIELD_ID_ITEM[0]) ) )
      self.__class = None
      self.__type = None
      self.__name = None

      self.__cm = cm

   def reload(self) :
      general_format = self.__general_format.get_value()
      self.__class = self.__cm.get_type( general_format.class_idx )
      self.__type = self.__cm.get_type( general_format.type_idx )
      self.__name = self.__cm.get_string( general_format.name_idx )

   def get_class(self) :
      return self.__class

   def get_type(self) :
      return self.__type

   def get_name(self) :
      return self.__name

   def show(self) :
      print self.__class, self.__type, self.__name, self.__general_format.get_value()

   def get_raw(self) :
      return bytecode.Buff( self.__offset, self.__general_format.get_value_buff() )

   def get_off(self) :
      return self.__offset

class FieldIdItem(IdItem) :
   def __init__(self, size, buff, cm) :
      self.__offset = buff.get_idx()
      super(FieldIdItem, self).__init__(size, buff, cm, FieldItem)

   def get_off(self) :
      return self.__offset

class MethodItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__general_format = SVs( METHOD_ID_ITEM[0], METHOD_ID_ITEM[1], buff.read( calcsize(METHOD_ID_ITEM[0]) ) )
      self.__class = None
      self.__proto = None
      self.__name = None

      self.__cm = cm

   def reload(self) :
      general_format = self.__general_format.get_value()
      self.__class = self.__cm.get_type( general_format.class_idx )
      self.__proto = self.__cm.get_proto( general_format.proto_idx )
      self.__name = self.__cm.get_string( general_format.name_idx )

   def get_class(self) :
      return self.__class

   def get_proto(self) :
      return self.__proto

   def get_name(self) :
      return self.__name

   def show(self) :
      print self.__name, self.__proto, self.__class, self.__general_format.get_value()

   def get_raw(self) :
      return bytecode.Buff( self.__offset, self.__general_format.get_value_buff() )

class MethodIdItem :
   def __init__(self, size, buff, cm) :
      self.__offset = buff.get_idx()
      self.methods = []
      for i in range(0, size) :
         self.methods.append( MethodItem(buff, cm) )

   def get(self, idx) :
      return self.methods[ idx ]

   def reload(self) :
      for i in self.methods :
         i.reload()

   def show(self) :
      nb = 0
      for i in self.methods :
         print nb, i,
         i.show()
         nb = nb + 1

   def get_raw(self) :
      return [ i.get_raw() for i in self.methods ]

   def get_off(self) :
      return self.__offset

class EncodedField :
   def __init__(self, buff, cm) :
      self.__field_idx_diff = readuleb128( buff )
      self.__access_flags = readuleb128( buff )
      
      self.__field_idx = 0

      self.__name = None

      self.__cm = cm

   def get_access(self) :
      return self.__access_flags

   def get_descriptor(self) :
      return self.__name[1]

   def get_name(self) :
      return self.__name[2]

   def adjust_idx(self, val) :
      self.__field_idx = self.__field_idx_diff + val

   def get_idx(self) :
      return self.__field_idx

   def reload(self) :
      self.__name = self.__cm.get_field( self.__field_idx )

   def get_raw(self) :
      return writeuleb128( self.__field_idx_diff ) + writeuleb128( self.__access_flags )

   def show(self) :
      print "\tfield_idx_diff=%d %s access_flags=%d" % (self.__field_idx_diff, self.__name, self.__access_flags)

class EncodedMethod :
   def __init__(self, buff, cm) :
      self.method_idx_diff = readuleb128( buff )
      self.access_flags = readuleb128( buff )
      self.code_off = readuleb128( buff )

      self.__method_idx = 0

      self.__name = None
      self.__code = None

      self.__cm = cm

   def get_access(self) :
      return self.access_flags

   def get_code(self) :
      return self.__code

   def get_descriptor(self) :
      return self.proto

   def get_name(self) :
      return self.__name

   def adjust_idx(self, val) :
      self.__method_idx = self.method_idx_diff + val

   def get_idx(self) :
      return self.__method_idx

   def reload(self) :
      v = self.__cm.get_method( self.__method_idx )
      self.__class_name = v[0]
      self.proto = v[1]
      self.__name = v[2]

      self.__code = self.__cm.get_code( self.code_off )

   def get_raw(self) :
      return writeuleb128( self.method_idx_diff ) + writeuleb128( self.access_flags ) + writeuleb128( self.code_off )

   def show(self) :
      print "\tmethod_idx_diff=%d %s access_flags=%d code_off=%d" % (self.method_idx_diff, self.__name, self.access_flags, self.code_off)
      self.__code.show()

class ClassDataItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()

      self.__static_fields_size = readuleb128( buff )
      self.__instance_fields_size = readuleb128( buff )
      self.__direct_methods_size = readuleb128( buff )
      self.__virtual_methods_size = readuleb128( buff ) 

      self.__static_fields = []
      self.__instance_fields = []
      self.__direct_methods = []
      self.__virtual_methods = []


      self.load_field( self.__static_fields_size, self.__static_fields, EncodedField, buff, cm )
      self.load_field( self.__instance_fields_size, self.__instance_fields, EncodedField, buff, cm )
      self.load_field( self.__direct_methods_size, self.__direct_methods, EncodedMethod, buff, cm )
      self.load_field( self.__virtual_methods_size, self.__virtual_methods, EncodedMethod, buff, cm )

   def load_field(self, size, l, Type, buff, cm) :
      prev = 0
      for i in range(0, size) :
         el = Type(buff, cm)
         el.adjust_idx( prev )
         prev = el.get_idx()

         l.append( el )

   def reload(self) :
      for i in self.__static_fields :
         i.reload()

      for i in self.__instance_fields :
         i.reload()

      for i in self.__direct_methods :
         i.reload()

      for i in self.__virtual_methods :
         i.reload()

   def get_off(self) :
      return self.__offset

   def get_methods(self) :
      return [ x for x in self.__direct_methods ] + [ x for x in self.__virtual_methods ]

   def get_fields(self) :
      return [ x for x in self.__static_fields ] + [ x for x in self.__instance_fields ]

   def show(self) :
      print "static_fields_size=%d instance_fields_size=%d direct_methods_size=%d virtual_methods_size=%d" % (self.__static_fields_size, self.__instance_fields_size, self.__direct_methods_size, self.__virtual_methods_size)

      print "SF"
      for i in self.__static_fields :
         i.show()

      print "IF"
      for i in self.__instance_fields :
         i.show()

      print "DM"
      for i in self.__direct_methods :
         i.show()

      print "VM"
      for i in self.__virtual_methods :
         i.show()

   def get_raw(self) :

      buff = writeuleb128( self.__static_fields_size ) + \
             writeuleb128( self.__instance_fields_size ) + \
             writeuleb128( self.__direct_methods_size ) + \
             writeuleb128( self.__virtual_methods_size ) + \
             ''.join(i.get_raw() for i in self.__static_fields) + \
             ''.join(i.get_raw() for i in self.__instance_fields) + \
             ''.join(i.get_raw() for i in self.__direct_methods) + \
             ''.join(i.get_raw() for i in self.__virtual_methods)

      return [ bytecode.Buff(self.__offset, buff) ]

class ClassItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()
      self.__general_format = SVs( CLASS_DEF_ITEM[0], CLASS_DEF_ITEM[1], buff.read( calcsize(CLASS_DEF_ITEM[0]) ) )
      self.__name = None
      self.__sname = None

      self.__CM = cm

   def reload(self) :
      general_format = self.__general_format.get_value()
      self.__name = self.__CM.get_type( general_format.class_idx )
      self.__sname = self.__CM.get_type( general_format.superclass_idx )

      self.__class_data_item = self.__CM.get_class_data_item( self.__general_format.get_value().class_data_off )

      self.__class_data_item.reload()

   def get_name(self) :
      return self.__name

   def get_info(self) :
      return "%s:%s" % (self.__name, self.__sname)

   def get_methods(self) :
      return self.__class_data_item.get_methods()

   def get_fields(self) :
      return self.__class_data_item.get_fields()

   def show(self) :
      print self.__name, self.__sname, self.__general_format.get_value()
      self.__class_data_item.show()

   def get_raw(self) :
      return [ bytecode.Buff( self.__offset, self.__general_format.get_value_buff() ) ]

class ClassDefItem :
   def __init__(self, size, buff, cm) :
      self.__offset = buff.get_idx()
      self.class_def = []

      for i in range(0, size) :
         idx = buff.get_idx()
   
         class_def = ClassItem( buff, cm )
         self.class_def.append( class_def )
         
         buff.set_idx( idx + calcsize(CLASS_DEF_ITEM[0]) )

   def export(self) :
      pass

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
      nb = 0
      for i in self.class_def :
         print nb,
         i.show()
         nb = nb + 1

   def get_raw(self) :
      return [ i.get_raw() for i in self.class_def ]

   def get_off(self) :
      return self.__offset

class EncodedTypeAddrPair :
   def __init__(self, buff) :
      self.__type_idx = readuleb128( buff )
      self.__addr = readuleb128( buff )

   def get_raw(self) :
      return writeuleb128( self.__type_idx ) + writeuleb128( self.__addr )

class EncodedCatchHandler :
   def __init__(self, buff) :
      self.__size = readsleb128( buff )

      self.__handlers = []
      
      for i in range(0, abs(self.__size)) :
         self.__handlers.append( EncodedTypeAddrPair(buff) )

      if self.__size <= 0 :
         self.__catch_all_addr = readuleb128( buff )

   def show(self) :
      bytecode._Print("ENCODED_CATCH_HANDLER SIZE", self.__size)

   def get_raw(self) :
      buff = writesleb128( self.__size ) + ''.join(i.get_raw() for i in self.__handlers)
      
      if self.__size <= 0 :
         buff += writeuleb128( self.__catch_all_addr )

      return buff

class EncodedCatchHandlerList :
   def __init__(self, buff) :
      self.__size = readuleb128( buff )
      self.__list = []

      for i in range(0, self.__size) :
         self.__list.append( EncodedCatchHandler(buff) )

   def show(self) :
      bytecode._Print("ENCODED_CATCH_HANDLER_LIST SIZE", self.__size)
      for i in self.__list :
         i.show()
      
   def get_raw(self) :
      return writeuleb128( self.__size ) + ''.join(i.get_raw() for i in self.__list)

class DalvikCode : 
   def __init__(self, buff) :
      off = buff.get_idx()
      while off % 4 != 0 :
         off += 1

      self.__offset = off 
      buff.set_idx( off )
#print "OFF = 0x%x %x ################################################" % (buff.get_idx(), buff.get_idx() % 4) 

      self.__off = buff.get_idx()

      self.__registers_size = SV( '<H', buff.read( 2 ) )   
      self.__ins_size = SV( '<H', buff.read( 2 ) )
      self.__outs_size = SV( '<H', buff.read( 2 ) )
      self.__tries_size = SV( '<H', buff.read( 2 ) )
      self.__debug_info_off = SV( '<L', buff.read( 4 ) )
      self.__insns_size = SV( '<L', buff.read( 4 ) )


      self.__insn = buff.read( self.__insns_size.get_value() * 2 )

      self.__h_special_bytecodes = {}
      self.__bytecodes = []
#print repr( self.__insn )

      ushort = calcsize( '<H' )

      real_j = 0
      j = 0 
      while j < (self.__insns_size.get_value() * ushort) :

         if real_j in self.__h_special_bytecodes :
            special_e = self.__h_special_bytecodes[ real_j ]( self.__insn[j : ] )
            self.__bytecodes.append( special_e )

#print "EXIT special bytecodes", special_e

            del self.__h_special_bytecodes[ real_j ]
            j += special_e.get_size()
         else :
            op_value = unpack( '<B', self.__insn[j] )[0]
            
            if op_value in DALVIK_OPCODES :
#print real_j, "ENTER into", DALVIK_OPCODES[ op_value ][1], repr( self.__insn[j : j + int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort ] )

               operands = []
               special = None

               if len(DALVIK_OPCODES[ op_value ]) >= 4 :
                  if len( DALVIK_OPCODES[ op_value ][3] ) == 0 :
                     bytecode.Exit( "opcode [ 0x%x:%s ] not yet supported" % (op_value ,DALVIK_OPCODES[ op_value ][1]) )

                  operands, special = self._analyze_mnemonic( self.__insn[ j : j + int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort ], DALVIK_OPCODES[ op_value ])

                  if special != None :
                     self.__h_special_bytecodes[ special[0] + real_j ] = special[1] 

#               if DALVIK_OPCODES[ op_value ][1] == "packed-switch" :
#                  print DALVIK_OPCODES[ op_value ][1], repr( self.__insn[j : j + int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort ] ), operands, special
#   bytecode.Exit( "test" )

#print "EXIT classic bytecodes", operands, special
               self.__bytecodes.append( [ DALVIK_OPCODES[ op_value ][1], repr( self.__insn[j : j + int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort ] ), operands ] )

               j += ( int( DALVIK_OPCODES[ op_value ][0][0] ) * ushort)
            else :
               bytecode.Exit( "invalid opcode [ 0x%x ]" % op_value )

         real_j = j / 2

#print "PAD", self.__tries_size.value, self.__insns_size.value, "0x%x" % buff.get_idx()
#if (self.__tries_size.value > 0) :
#         self.__padding = SV( '<H', buff.read( 2 ) )
      if (self.__insns_size.get_value() % 2 == 1) :
         self.__padding = SV( '<H', buff.read( 2 ) )

      self.__tries = []
      self.__handlers = []
      if self.__tries_size.get_value() > 0 :
         for i in range(0, self.__tries_size.get_value()) :
            try_item = SVs( TRY_ITEM[0], TRY_ITEM[1], buff.read( calcsize(TRY_ITEM[0]) ) )
            self.__tries.append( try_item )
#print try_item
         
         self.__handlers.append( EncodedCatchHandlerList( buff ) )

   def _analyze_mnemonic(self, buff_operands, mnemonic) :
      operands = []
      
      t_ops = mnemonic[3].split(' ')
#      print t_ops, mnemonic[2]

      l = []
      for i in buff_operands :
         l.append( (ord(i) & 0b11110000) >> 4 )
         l.append( (ord(i) & 0b00001111) )
              
#      print l 
      for i in t_ops :
         sub_ops = i.split('|')         
#         print "SOP", sub_ops,
                  
         if len(sub_ops[-1]) == 2 :
            sub_ops = [ sub_ops[-1] ] + sub_ops[0:-1]
         else :
            sub_ops = sub_ops[2:] + sub_ops[0:2]

#         print sub_ops

         for sub_op in sub_ops :
            zero_count = string.count(sub_op, '0')
                     
            if zero_count == len(sub_op) :
               continue

            size = ((len(sub_op) - zero_count)  * 4)
            signed = 0

            pos_op = string.find(mnemonic[2], sub_op)
            if pos_op != -1 and mnemonic[2][pos_op - 1] == '+' : 
                  signed = 1

            ttype = "op@"
            if pos_op != -1 :            
#               print pos_op
               t_pos_op = pos_op
               while pos_op > 0 and mnemonic[2][pos_op] != ' ' :
                  pos_op = pos_op - 1

               ttype = mnemonic[2][pos_op : t_pos_op].replace(' ', '')

            val = self._extract( signed, l, size ) << (zero_count * 4)
#            print sub_op, val, l

            operands.append( [ttype, val] )

            if len(l) == 0 :
               break

      if len(mnemonic) == 5 :
         return operands, (operands[2][1], mnemonic[4])

      return operands, None

   def _extract(self, signed, l, size) :
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

   def get_bc(self) :
      return self.__bytecodes

   def get_off(self) :
      return self.__off

   def show(self) :
      print "*" * 80 
      print "DALVIK_CODE :"
      bytecode._Print("\tREGISTERS_SIZE", self.__registers_size)
      bytecode._Print("\tINS_SIZE", self.__ins_size)
      bytecode._Print("\tOUTS_SIZE", self.__outs_size)
      bytecode._Print("\tTRIES_SIZE", self.__tries_size)
      bytecode._Print("\tDEBUG_INFO_OFF", self.__debug_info_off)
      bytecode._Print("\tINSNS_SIZE", self.__insns_size)

      for i in self.__handlers :
         i.show()

      print ""

      nb = 0
      for i in self.__bytecodes :
         if type(i).__name__ == 'list' :
            print "\t", nb, i[0], ' '.join("%s%x" % (n[0], n[1]) for n in i[-1])
         else :
            print "\t", nb, i.show()
         nb += 1


      print "*" * 80

   def get_raw(self) :
      buff =  self.__registers_size.get_value_buff() + \
              self.__ins_size.get_value_buff() + \
              self.__outs_size.get_value_buff() + \
              self.__tries_size.get_value_buff() + \
              self.__debug_info_off.get_value_buff() + \
              self.__insns_size.get_value_buff() + \
              self.__insn

      if (self.__insns_size.get_value() % 2 == 1) :
         buff += self.__padding.get_value_buff()

      if self.__tries_size.get_value() > 0 :
         buff += ''.join(i.get_value_buff() for i in self.__tries)
         buff += self.__handlers.get_raw()

      return bytecode.Buff( self.__offset,
                            buff )

class CodeItem :
   def __init__(self, size, buff) :
      self.__offset = buff.get_idx()
      self.__code = []

      for i in range(0, size) :
         self.__code.append( DalvikCode( buff ) )

   def get_code(self, off) :
      for i in self.__code :
         if i.get_off() == off :
            return i

   def reload(self) :
      pass

   def show(self) :
      for i in self.__code :
         i.show()

   def get_raw(self) :
      return [ i.get_raw() for i in self.__code ]

   def get_off(self) :
      return self.__offset
      
class MapItem :
   def __init__(self, buff, cm) :
      self.__offset = buff.get_idx()

      self.format = SVs( MAP_ITEM[0], MAP_ITEM[1], buff.read( calcsize( MAP_ITEM[0] ) ) )

      self.__item = None

      general_format = self.format.get_value()
      buff.set_idx( general_format.offset )

#      print TYPE_MAP_ITEM[ general_format.type ], "@ 0x%x(%d) %d" % (buff.get_idx(), buff.get_idx(), general_format.size)

      if TYPE_MAP_ITEM[ general_format.type ] == "TYPE_STRING_ID_ITEM" :
         self.__item = [ StringIdItem( buff ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_CODE_ITEM" :
         self.__item = CodeItem( general_format.size, buff )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_TYPE_ID_ITEM" :
         self.__item = TypeIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_PROTO_ID_ITEM" :
         self.__item = ProtoIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_FIELD_ID_ITEM" :
         self.__item = FieldIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_METHOD_ID_ITEM" :
         self.__item = MethodIdItem( general_format.size, buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_CLASS_DEF_ITEM" :
         self.__item = ClassDefItem( general_format.size, buff, cm )
      
      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_HEADER_ITEM" :
         self.__item = HeaderItem( general_format.size, buff )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ANNOTATION_ITEM" :
         self.__item = [ AnnotationItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ANNOTATION_SET_ITEM" :
         self.__item = [ AnnotationSetItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ANNOTATIONS_DIRECTORY_ITEM" :
         self.__item = [ AnnotationsDirectoryItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_TYPE_LIST" :
         self.__item = [ TypeList( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_STRING_DATA_ITEM" :
         self.__item = [ StringDataItem( buff ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_DEBUG_INFO_ITEM" :
      # FIXME : strange bug with sleb128 ....
#       self.__item = [ DebugInfoItem( buff, cm ) for i in range(0, general_format.size) ]
         self.__item = DebugInfoItem2( buff, cm )

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_ENCODED_ARRAY_ITEM" :
         self.__item = [ EncodedArrayItem( buff, cm ) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_CLASS_DATA_ITEM" :
         self.__item = [ ClassDataItem(buff, cm) for i in range(0, general_format.size) ]

      elif TYPE_MAP_ITEM[ general_format.type ] == "TYPE_MAP_LIST" :
         pass # It's me I think !!!

      else :
         bytecode.Exit( "Map item @ 0x%x(%d) is unknown" % (buff.get_idx(), buff.get_idx()) )

   def get_raw(self) :
      if self.__item == None :
         return [ bytecode.Buff( self.__offset, self.format.get_value_buff() ) ]
      else :
         if isinstance( self.__item, list ) :
            return [ bytecode.Buff( self.__offset, self.format.get_value_buff() ) ] + [ i.get_raw() for i in self.__item ]
         else :
            return [ bytecode.Buff( self.__offset, self.format.get_value_buff() ) ] + self.__item.get_raw()

   def get_length(self) :
      return calcsize( MAP_ITEM[0] )

   def get_type(self) :
      return self.format.get_value().type

   def get_item(self) :
      return self.__item

   def reload(self) :
      if self.__item != None :
         if isinstance( self.__item, list ):
            for i in self.__item :
               i.reload()
         else :
            self.__item.reload()

   def show(self) :
      bytecode._Print( "MAP_ITEM", self.format )
      bytecode._Print( "\tTYPE_ITEM", TYPE_MAP_ITEM[ self.format.get_value().type ])

      if self.__item != None :
         if isinstance( self.__item, list ):
            for i in self.__item :
               i.show()
         else :   
            self.__item.show()

class CM :
   def __init__(self) :
      self.__manage_item = {}
      self.__manage_item_off = []

   def add_type_item(self, type_item, item) :
      self.__manage_item[ type_item ] = item
    
      if item != None : 
         if isinstance(item, list) :
            for i in item :
               self.__manage_item_off.append( i.get_off() )
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
      for i in self.__manage_item[ "TYPE_STRING_DATA_ITEM" ] :
         if i.get_off() == off :
            return i.get()

      bytecode.Exit( "unknown string item @ 0x%x(%d)" % (off,idx) )

   def get_type(self, idx) :
      type = self.__manage_item[ "TYPE_TYPE_ID_ITEM" ].get( idx )
      return self.get_string( type )

   def get_proto(self, idx) :
      proto = self.__manage_item[ "TYPE_PROTO_ID_ITEM" ].get( idx )
      return [  proto.get_shorty(), proto.get_return_type() ]

   def get_field(self, idx) :
      field = self.__manage_item[ "TYPE_FIELD_ID_ITEM"].get( idx )
      return [ field.get_class(), field.get_type(), field.get_name() ]

   def get_method(self, idx) :
      method = self.__manage_item[ "TYPE_METHOD_ID_ITEM" ].get( idx )
      return [ method.get_class(), method.get_proto(), method.get_name() ]

   def get_next_offset_item(self, idx) :
      for i in self.__manage_item_off :
         if i > idx :
            return i

class MapList :
   def __init__(self, off, buff) :
      self.__CM = CM()

      buff.set_idx( off )

      self.__offset = buff.get_idx()
      
      self.__size = SV( '<L', buff.read( 4 ) )

      self.__map_item = []
      for i in range(0, self.__size) :
         idx = buff.get_idx()

         mi = MapItem( buff, self.__CM )
         self.__map_item.append( mi )
      
         buff.set_idx( idx + mi.get_length() )

         self.__CM.add_type_item( TYPE_MAP_ITEM[ mi.get_type() ], mi.get_item() )

      for i in self.__map_item :
         i.reload()

   def get_item_type(self, ttype) :
      for i in self.__map_item :
         if TYPE_MAP_ITEM[ i.get_type() ] == ttype :
            return i.get_item()

   def show(self) :
      bytecode._Print("MAP_LIST SIZE", self.__size.get_value())
      for i in self.__map_item :
         i.show()

   def get_raw(self) :
      return [ bytecode.Buff(self.__offset, self.__size.get_value_buff()) ] + \
             [ x.get_raw() for x in self.__map_item ] 

class Data :
   def __init__(self, buff) :
      pass

class DalvikVMFormat(bytecode._Bytecode) :
   def __init__(self, buff) :
      super(DalvikVMFormat, self).__init__( buff )
      super(DalvikVMFormat, self).register( bytecode.SHOW, self.show )

      self.load_class()

   def load_class(self) :
      self.__header = HeaderItem( 0, self )

      self.__map_list = MapList( self.__header.get_value().map_off, self )

      self.classes = self.__map_list.get_item_type( "TYPE_CLASS_DEF_ITEM" )
      self.methods = self.__map_list.get_item_type( "TYPE_METHOD_ID_ITEM" )
      self.codes = self.__map_list.get_item_type( "TYPE_CODE_ITEM" )

   def show(self) :
      """Show the .class format into a human readable format"""
      self.__map_list.show()

   def _iterFlatten(self, root):
      if isinstance(root, (list, tuple)):      
         for element in root :
            for e in self._iterFlatten(element) :      
               yield e               
      else:                      
         yield root

   def _get_raw(self) :
      # Due to the specific format of dalvik virtual machine,
      # we will get a list of raw object described by a buffer, a size and an offset
      # where to insert the specific buffer into the file 
      l = self.__map_list.get_raw()

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

   def save(self) :
      """Return the class (with the modifications) into raw format"""
      return self._get_raw()
   
   def get_type(self) :
      return "DVM"
