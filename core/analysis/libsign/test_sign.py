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

import sys, itertools, time, os, random
from ctypes import cdll, c_float, c_int, c_uint, c_void_p, Structure, addressof, create_string_buffer, cast, POINTER, pointer

PATH_INSTALL = "../../../"
sys.path.append(PATH_INSTALL + "./")
sys.path.append(PATH_INSTALL + "./core")
sys.path.append(PATH_INSTALL + "./core/bytecodes")
sys.path.append(PATH_INSTALL + "./core/analysis")

import apk, dvm, analysis, msign

NCD_SIGNATURES = {
    "s1" : ("Lcom/android/root/Setting;", "postUrl", "(Ljava/lang/String; Landroid/content/Context;)V"),
}

MPSM_SIGNATURES = {
        "s1" : "he",
        "s2" : "she",
        "s3" : "his",
        "s4" : "hers",
        "s5" : "4243",
}

def create_entropies(vmx, m, u) :
    l = [ vmx.get_method_signature(m, predef_sign = analysis.SIGNATURE_L0_0 ).get_string(),
          vmx.get_method_signature(m, "L4", { "L4" : { "arguments" : ["Landroid"] } } ).get_string(),
          vmx.get_method_signature(m, "L4", { "arguments" : ["Ljava"] } ).get_string(),
          vmx.get_method_signature(m, "hex" ).get_string(),
          vmx.get_method_signature(m, "L3" ).get_string(),
        ]
    
    e = msign.ENTROPIES_T()
    e1 = e
    i = 0

    while i < len(l) :
        e1.value = u.entropy( cast( l[i], c_void_p ), len( l[i] ) )

        if i == len(l) - 1 :
            e1.next = None 
        else :
            e1.next = pointer( msign.ENTROPIES_T() )
            e1 = e1.next[0]
        
        i += 1
    return e

def add_elem(v, u, n, _s, ets) :
    l = [] 
    ret = u.add_elem( v, n, cast(_s, c_void_p) , len(_s), addressof( ets ) )
    return ret
   
def check(v, u) :
    r = msign.RESULTCHECK_T()
    l = []
    ret = u.check( v, addressof( r ) )
    if ret == 0 :
        while True :
            l.append( (r.id, r.start, r.end, r.value ) )

            try : 
                r = r.next[0]
            except ValueError :
                break
    print ret, l

if __name__ == "__main__" :
    u = cdll.LoadLibrary( "./libsign.so")
    u.add_sign.restype = c_int
    u.entropy.restype = c_float

    new_sign = u.init()


    a = apk.APK( PATH_INSTALL + "apks/DroidDream/Magic Hypnotic Spiral.apk" )
    vm = dvm.DalvikVMFormat( a.get_dex() )
    vmx = analysis.VMAnalysis( vm )


    n = 0
    for s in NCD_SIGNATURES :
        v = NCD_SIGNATURES[ s ]
        m = vm.get_method_descriptor( v[0], v[1], v[2] )

        entropies = create_entropies( vmx, m, u ) 
        print m, entropies
        
        value = vmx.get_method_signature(m, predef_sign = analysis.SIGNATURE_L0_0 ).get_string()

        print "ADD NCD_SIGNATURE -->", u.add_sign( new_sign, n, 0, cast( value, c_void_p ), len( value ), addressof ( entropies ) )
        
        n += 1

    #for s in MPSM_SIGNATURES :
    #    print "ADD MPSM_SIGNATURE -->", u.add_sign( new_sign, n, 1, cast( MPSM_SIGNATURES[s], c_void_p ), len( MPSM_SIGNATURES[s] ) )
    #    n += 1

    m_save = m
    print "ADD ELEM"
    for m in vm.get_methods() :
        entropies = create_entropies( vmx, m, u )

        if m_save == m :
            print "N =", n

        value = vmx.get_method_signature(m, predef_sign = analysis.SIGNATURE_L0_0 ).get_string()
        add_elem( new_sign, u, n, value, entropies )

        n += 1

    print "CHECK"
    check( new_sign, u )

    #r = RESULTCHECK_T()
    #print "NCD"
    #print "CHECK -->", n, add_elem( new_sign, u, 0, n, NCD_SIGNATURES["s2"] )
    #n += 1
    #print "CHECK -->", n, add_elem( new_sign, u, 0, n, NCD_SIGNATURES["s3"] )
    #u.fix( new_sign )


    #print "CHECK -->", check_elem( new_sign, u, 0, "HELLO WORLD" )
    #print "CHECK -->", check_elem( new_sign, u, 1, "this here is history" )
    #print "CHECK -->", check_elem( new_sign, u, 1, "BLAAAA" )
    #print "CHECK -->", check_elem( new_sign, u, 1, "414243" )
