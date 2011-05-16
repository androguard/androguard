#!/usr/bin/env python2.6

import sys, os
from xml.dom import minidom
PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./core/")
sys.path.append(PATH_INSTALL + "./core/bytecodes/")

import apk, dvm, misc

def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected)),
    return (got == expected)

TESTS = [ "./debug" ]

for i in TESTS :
    for root, dirs, files in os.walk( i ) :
        if files != [] :
            for f in files :
                real_filename = root
                if real_filename[-1] != "/" :
                    real_filename += "/"
                real_filename += f

                
                file_type = misc.is_android( real_filename )

                if file_type != None : 
                    if file_type == "APK" :
                        try :
                            a = apk.APK( real_filename )
                        except Exception, e :
                            print "FAILED", real_filename, file_type
                            import traceback
                            traceback.print_exc()
                            continue

                        if a.is_valid_APK() == False :
                            continue

                        raw = a.get_dex()
                    elif file_type == "DEX" :
                        raw = open(real_filename, "rb").read()
            

                    try :
                        d = dvm.DalvikVMFormat( raw )
                        print "PASSED", real_filename, file_type
                    except Exception, e :
                        print "FAILED", real_filename, file_type
                        import traceback
                        traceback.print_exc()
                else :
                    print "BAD FILE FORMAT", real_filename
