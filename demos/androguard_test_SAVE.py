#!/usr/bin/env python

import hashlib

import sys
PATH_INSTALL = "./"                                                                                                                                                                                                               
sys.path.append(PATH_INSTALL + "./")

import androguard

def hexdump(src, length=8, off=0):
   result = []   
   digits = 4 if isinstance(src, unicode) else 2
   for i in xrange(0, len(src), length):   
      s = src[i:i+length]
      hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])      
      text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
      result.append( b"%04X   %-*s   %s" % (i+off, length*(digits + 1), hexa, text) )      
   return b'\n'.join(result)

### JAVA TEST ###
BASE_TEST = "./examples/java/Demo1/orig/"
BASE_MAIN_TEST = "./examples/java/Demo1/orig_main/"
TEST = [ './examples/java/test/orig/Test1.class' ]
FILES = [ 
          ("BaseCipher.class", 0),
          ("DES.class", 0), 
          ("DES$Context.class", 0), 
          ("IBlockCipher.class", 0), 
          ("IBlockCipherSpi.class", 0), 
          ("Properties$1.class", 0), 
          ("Properties.class", 0), 
          ("Registry.class", 0), 
          ("Util.class", 0), 
          ("WeakKeyException.class", 0), 
          ("Demo1Main.class", 1)
        ]

for i in FILES :
   if i[1] == 0 :
      TEST.append( BASE_TEST + i[0] )
   else :
      TEST.append( BASE_MAIN_TEST + i[0] )

### DALVIK TEST ###
FILES = [ 
        #    "examples/android/Demo1/bin/classes.dex",
            "examples/dalvik/test/bin/classes.dex"
        ]

for i in FILES :
   TEST.append( i )

### ALL ###

a = androguard.Androguard( TEST )

i = 0
while i < len(TEST) :
   b1 = open(TEST[i]).read()
   _a = a.get("file", TEST[i])
   b2 = _a.save()

   if hashlib.md5( b1 ).hexdigest() != hashlib.md5( b2 ).hexdigest() :
      print "HASH %s NO GO" % TEST[i]

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

   else :
      print "HASH %s GO" % TEST[i]
  
   i += 1

