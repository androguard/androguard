#!/usr/bin/env python2.6

import sys, os
from xml.dom import minidom
from optparse import OptionParser

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./core/")
sys.path.append(PATH_INSTALL + "./core/bytecodes/")

import apk, dvm, androconf 

option_0 = { 'name' : ('-i', '--input'), 'help' : 'input directory', 'nargs' : 1 }
options = [option_0]

def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected)),
    return (got == expected)

def main(options, arguments) :
    for root, dirs, files in os.walk( options.input ) :
        if files != [] :
            for f in files :
                real_filename = root
                if real_filename[-1] != "/" :
                    real_filename += "/"
                real_filename += f

                
                file_type = androconf.is_android( real_filename )

                
                if file_type != None : 
                    try : 
                        if file_type == "APK" :
                            a = apk.APK( real_filename )

                            if a.is_valid_APK() == False :
                                print "FAILED", real_filename, file_type
                                continue

                            raw = a.get_dex()
                        elif file_type == "DEX" :
                            raw = open(real_filename, "rb").read()

                        d = dvm.DalvikVMFormat( raw )
                        print "PASSED", real_filename, file_type
                    except Exception, e :
                        print "FAILED", real_filename, file_type
                        import traceback
                        traceback.print_exc()
                else :
                    print "BAD FILE FORMAT", real_filename


if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

                          
    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)   
