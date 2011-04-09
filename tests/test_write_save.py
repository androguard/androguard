#!/usr/bin/env python

import hashlib

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard

def test(got, expected):
   if got == expected:
      prefix = ' OK '
   else:
      prefix = '  X '
   print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected)),
   return (got == expected)

def hexdump(src, length=8, off=0):
   result = []   
   digits = 4 if isinstance(src, unicode) else 2
   for i in xrange(0, len(src), length):   
      s = src[i:i+length]
      hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])      
      text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
      result.append( b"%04X   %-*s   %s" % (i+off, length*(digits + 1), hexa, text) )      
   return b'\n'.join(result)

TEST_TYPE = 0
TYPE_JVM = 1
TYPE_DVM = 2

if len(sys.argv) == 1 :
   TEST_TYPE = TYPE_JVM + TYPE_DVM
elif len(sys.argv) == 2 :
   if sys.argv[1] == "JVM" :
      TEST_TYPE = TYPE_JVM
   elif sys.argv[1] == "DVM" :
      TEST_TYPE = TYPE_DVM

TEST = []

### JAVA TEST ###
FILES_JVM = [ 
          "examples/java/Demo1/orig/BaseCipher.class",
          "examples/java/Demo1/orig/DES.class",
          "examples/java/Demo1/orig/DES$Context.class",
          "examples/java/Demo1/orig/IBlockCipher.class",
          "examples/java/Demo1/orig/IBlockCipherSpi.class",
          "examples/java/Demo1/orig/Properties$1.class",
          "examples/java/Demo1/orig/Properties.class",
          "examples/java/Demo1/orig/Registry.class",
          "examples/java/Demo1/orig/Util.class",
          "examples/java/Demo1/orig/WeakKeyException.class", 
          "examples/java/Demo1/orig_main/Demo1Main.class",
        ]

if TEST_TYPE & TYPE_JVM :
   for i in FILES_JVM :
      TEST.append( i )
   #TEST.append( "./examples/java/test/orig/Test1.class" )

   #for i in FILES :
   #   if i[1] == 0 :
   #      TEST.append( BASE_TEST + i[0] )
   #else :
   #      TEST.append( BASE_MAIN_TEST + i[0] )

### DALVIK TEST ###
FILES_DVM = [ 
            "examples/android/Demo1/bin/classes.dex",
            "examples/dalvik/test/bin/classes.dex"
        ]

if TEST_TYPE & TYPE_DVM :
   for i in FILES_DVM :
      TEST.append( i )

a = androguard.Androguard( TEST )

i = 0
while i < len(TEST) :
   b1 = open(TEST[i]).read()
   _a = a.get("file", TEST[i])
   b2 = _a.save()

   ret = test( hashlib.md5( b1 ).hexdigest(), hashlib.md5( b2 ).hexdigest() )
   print TEST[i]
   if ret :
      j = 0 
      end = max(len(b1), len(b2))
      while j < end :
         if j >= len(b1) :
            print "OUT OF B1 @ OFFSET 0x%x(%d)" % (j,j)
            break
         
         if j >= len(b2) :
            print "OUT OF B2 @ OFFSET 0x%x(%d)" % (j,j)
            break

         if b1[j] != b2[j] :
            print "BEGIN @ OFFSET 0x%x" % j
            print "ORIG : "
            print hexdump(b1[j - 2: j + 10], off=j-2) + "\n"
            print "NEW : "
            print hexdump(b2[j - 2: j + 10], off=j-2) + "\n"

         j += 1
   i += 1

