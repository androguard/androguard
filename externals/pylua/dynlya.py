#!/usr/bin/env python

import random, base64, os, sys

LUAPATH = "./lua-5.1.4/src/"

class OpCodes :
   def __init__(self, nmax, nb) :
      self.nmax = nmax
      self.nb = nb

   def Generate(self) :
      l = []
     
      while len(l) < self.nb :
         i = random.randint(0, self.nmax)
         if i not in l :     
            l.append(i) 
      return l

class DynPyLua :
   def __init__(self) :
      self.lua_opcodes = "tabopcodes.h"

      o = OpCodes(0x3f - 1, 38)

      self.l = o.Generate()

   def CreateLuaOpcodes(self) :
      fd = open(self.lua_opcodes, "w")
      fd.write("const int TabOpCodesVM[] = { ")

      buff = ""
      for i in self.l  :
         buff += hex(i) + ", "

      buff = buff[:-2]
      fd.write("%s };\n" % buff)
      fd.close()

d = DynPyLua()
d.CreateLuaOpcodes()
