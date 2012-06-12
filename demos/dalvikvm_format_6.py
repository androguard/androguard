#!/usr/bin/env python

import sys

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core.bytecodes import dvm
from androguard.core.bytecodes import apk
from androguard.core.analysis import analysis

def hexdump(src, length=8, off=0):
    result = []
    digits = 4 if isinstance(src, unicode) else 2
    for i in xrange(0, len(src), length):
        s = src[i:i+length]
        hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
        result.append( b"%04X   %-*s   %s" % (i+off, length*(digits + 1), hexa, text) )
    return b'\n'.join(result)

class MDalvikVMFormat:
    def __init__(self, vm, vmx) :
        self.vm = vm
        self.vmx = vmx

    def fix_checksums(self) :
      pass

    def modify_instruction(self, class_name, method_name, descriptor, offset, instructions) :
        pass

    def test_save(self) :
        original_buff = self.vm.get_buff()

        import hashlib
        b1 = original_buff

        method = self.vm.get_method_descriptor( "Ltests/androguard/TestActivity;", "pouet2", "()I" )
        ins = method.get_instruction( 17 )
        print ins

#        ins.BBBB = 11

        b2 = self.vm.save()

        if hashlib.md5( b1 ).hexdigest() != hashlib.md5( b2 ).hexdigest() :
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
                    print hexdump(b1[j - 10: j + 10], off=j-10) + "\n"
                    print "NEW : "
                    print hexdump(b2[j - 10: j + 10], off=j-10) + "\n"
                    raise("ooo")

                j += 1


        print "OK"

        return b2

TEST = "examples/android/TestsAndroguard/bin/TestsAndroguard.apk"
#TEST = "examples/android/TestsAndroguard/bin/classes.dex"

FILENAME = "./toto.apk"

a = apk.APK( TEST )
j = dvm.DalvikVMFormat( a.get_dex() )
x = analysis.VMAnalysis( j )

m = MDalvikVMFormat(j, x)
print j, x, m

new_dex = m.test_save()

a.new_zip(  filename=FILENAME,
            deleted_files="(META-INF/.)", new_files = {
            "classes.dex" : new_dex } )
apk.sign_apk( FILENAME, "/home/desnos/androguard/tmp/androguard.androtrace", "tototo" )
