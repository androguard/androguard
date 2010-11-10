#!/usr/bin/env python

import pylua

HELLO = "print \"hello from LUA\""

OBJECT_HELLO = "Hello = {}\n"                                   \
               "function Hello.new(self)\n"                     \
               "        o = {  }\n"                             \
               "        setmetatable(o, self)\n"                \
               "        self.__index = self\n"                  \
               "        return o\n"                             \
               "end\n"                                          \
               "function Hello.TEST(self)\n"                    \
               "        print \"hello from OBJECT LUA\"\n"      \
               "end\n"                                          \
               "return Asm\n"

p = pylua.PYLUA()
p.call(HELLO)

p.call(OBJECT_HELLO)

p.call("h = Hello:new()")
p.call("h:TEST()")
