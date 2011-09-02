# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
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

from ctypes import cdll, c_char, c_float, c_int, c_uint, c_ulong, c_double, c_void_p, Structure, addressof, create_string_buffer, cast, POINTER, pointer
from array import array
import json, sys, base64, hashlib

import dvm, apk, androconf
from analysis import *

import libsign

NCD_SIGNATURE   = 0
MPSM_SIGNATURE  = 1

DEFAULT_SIGNATURE = SIGNATURE_L0_2

############### 
#from scikits.learn.decomposition import PCA
#import pylab as pl
##############

METHSIM = 0
CLASSSIM = 1
METHHASH = 2
CLASSHASH = 3

class SignSim :
    def __init__(self, sim_type) :
        self.sign = libsign.Msign()
        self.sim_type = sim_type

        self.debug = False
        self.minimum_signature = None

        #self.sign.set_debug_log( 1 )

    def set_debug(self) :
        self.debug = True

    def load_config(self, buff) :
        self.sign.set_threshold_low( buff["THRESHOLD_LOW"] )
        self.sign.set_threshold_high( buff["THRESHOLD_HIGH"] )

        self.sign.set_dist( str(buff["DISTANCE"]) )
        self.sign.set_method( str(buff["METHOD"]) )
        # L0_2, Android, Java, Hex, Exception
        self.sign.set_weight( buff["WEIGHTS"] )

    def load_sign(self, unique_id, unique_idlink, i, ssign, j , nb) :
        if self.minimum_signature == None :
            self.minimum_signature = len(ssign[1])

        if self.minimum_signature > len(ssign[1]) :
            self.minimum_signature = len(ssign[1])
        
        self.sign.add_sign_sim( unique_id, 
                                unique_idlink,
                                j,
                                str(base64.b64decode(ssign[1])), 
                                ssign[ 2 : ] )
        
        if self.debug :
            print "L:%d I:%d N:%d J:%d" % (unique_idlink, unique_id, nb, j),
            print ssign[ 2 : ], 
    
    def load_sign_string(self, unique_id, unique_idlink, i, ssign, j , nb) :
        self.sign.add_sign_string( unique_id, 
                                   ssign[1] );

        if self.debug :
            print "L:%d I:%d N:%d J:%d" % (unique_idlink, unique_id, nb, j),
            print ssign[ 1 : ], 

    def fix(self) :
        if self.minimum_signature != None :
            self.minimum_signature = (self.minimum_signature - self.minimum_signature * 0.3)

    def add_elem_sim(self, uniqueid, s1, entropies) :
        if self.minimum_signature < len(s1) :
            return self.sign.add_elem_sim( uniqueid, s1, entropies )

    def add_elem_string(self, uniqueid, s1) :
        return self.sign.add_elem_string( uniqueid, s1 )

    def set_npass(self, npass) :
        self.sign.set_npass( npass )

    def get_debug(self) :
        return self.sign.get_debug()

    def check_sim(self) :
        return self.sign.check_sim()

    def check_string(self) :
        return self.sign.check_string()

    def raz(self) :
        self.sign.raz()

class MSignature :
    def __init__(self, dbname = "./signatures/dbandroguard", dbconfig = "./signatures/dbconfig") :
        self.__signs = {}
        self.__rsigns = {}
        self.__ids = {}
        self.__lids = {}
        
        self.meth_sim = SignSim("METHSIM") 
        self.class_sim = SignSim("CLASSSIM")
        #self.class_hash = SignSim("CLASSHASH")

        #self.pca = PCA(n_components=2)
        #self.X = []
       
        self.dbname = dbname
        self.dbconfig = dbconfig
        self.debug = False
       
    def load(self) :
        self.load_config( open(self.dbconfig, "r").read() )
        self.load_sign( open(self.dbname, "r").read() )

        self.meth_sim.fix()
        self.class_sim.fix()

    def set_debug(self) :
        self.debug = True
        self.meth_sim.set_debug()
        self.class_sim.set_debug()
        
    def load_config(self, buff) :
        buff = json.loads( buff )

        self.meth_sim.load_config( buff["METHSIM"] )
        self.class_sim.load_config( buff["CLASSSIM"] )

    def _create_id(self, i) :
        v = len(self.__ids)
        self.__ids[ v ] = i
        return v
    
    def _create_id_link(self) :
        v = len(self.__lids)
        self.__lids[ v ] = 1
        return v
    
    def load_sign(self, buff) :
        buff = json.loads( buff )

        nb_meth_sim = 0
        nb_class_sim = 0
        for i in buff :
            if self.debug :
                print "%s (%s)" % (i, buff[i][1])

            j = buff[i][0]

            current_sign = [ i ]
            self.__signs[ len(self.__signs) ] = current_sign
            unique_idlink = self._create_id_link()

            nb = 0
            ccurrent_sign = {}

            c_nb_meth_sim = 0
            c_nb_class_sim = 0
            for ssign in j :
                if ssign[0] == METHSIM :
                    c_nb_meth_sim += 1
                elif ssign[0] == CLASSSIM :
                    c_nb_class_sim += 1

            for ssign in j :
                if self.debug :
                    print "\t--->",
                # METHSIM
                if ssign[0] == METHSIM :
                    if self.debug :
                        print "METHSIM",
                    uniqueid = self._create_id( "%s-%d" % (i, nb) )
                    self.meth_sim.load_sign( uniqueid, unique_idlink, i, ssign, c_nb_meth_sim, nb )

                    ccurrent_sign[ uniqueid ] = nb
                    self.__rsigns[ uniqueid ] = len(self.__signs) - 1
                    nb += 1 
                    nb_meth_sim += 1
                    if self.debug :
                        print
                elif ssign[0] == CLASSSIM : 
                    if self.debug :
                        print "CLASSSIM",
                    uniqueid = self._create_id( "%s-%d" % (i, nb) )
                    self.class_sim.load_sign( uniqueid, unique_idlink, i, ssign, c_nb_class_sim, nb )

                    ccurrent_sign[ uniqueid ] = nb
                    self.__rsigns[ uniqueid ] = len(self.__signs) - 1
                    nb += 1 
                    nb_class_sim += 1
                    if self.debug :
                        print
                #elif ssign[0] == CLASSHASH :
                #    print "CLASSHASH",
                #
                #    uniqueid = self._create_id( "%s-%d" % (i, nb) )
                #    self.class_hash.load_sign_string( uniqueid, unique_idlink, i, ssign, c_nb_class_sim, nb )
                #    ccurrent_sign[ uniqueid ] = nb
                #    self.__rsigns[ uniqueid ] = len(self.__signs) - 1
                #    nb += 1
                #    print

            current_sign.append( ccurrent_sign )
            current_sign.append( buff[i][-1] )

        if self.debug :
            print
        self.meth_sim.set_npass( nb_meth_sim )
        self.class_sim.set_npass( nb_class_sim )

    def check_apk(self, apk) :
        if self.debug :
            print "loading apk..",
            sys.stdout.flush()
        
        classes_dex = apk.get_dex()
        return self._check( classes_dex )
    
    def check_dex(self, buff) :
        return self._check( buff )

    def __check(self) :
        l_meth = self.meth_sim.check_sim() 
        #l_classhash = self.class_hash.check_string()

        l = []
        l.extend( l_meth[1:] )

        ret = l_meth[0]
        if l_meth[0] == -1 :
            l_class = self.class_sim.check_sim()
            l.extend( l_class[1:] )
            ret = ret and l_class[0]

        return ret, l

    def _check(self, buff) :
        if self.debug :
            print "loading dex..",
            sys.stdout.flush()
        
        vm = dvm.DalvikVMFormat( buff )
        vmx = VMAnalysis( vm )

        if self.debug :
            print "check 1 ",
            sys.stdout.flush()
       
        # Add methods for METHSIM
        for method in vm.get_methods() :
            uniqueid = self._create_id( method.get_class_name() + method.get_name() + method.get_descriptor() )
            entropies = create_entropies(vmx, method)
            #print method.get_class_name(), method.get_name(), method.get_descriptor(), uniqueid

            ret = self.meth_sim.add_elem_sim( uniqueid, entropies[0], entropies[1:] )
            
        for c in vm.get_classes() :
            value = ""
            value_entropy = 0.0
            android_entropy = 0.0
            java_entropy = 0.0
            hex_entropy = 0.0
            exception_entropy = 0.0
            nb_methods = 0
            
            class_data = c.get_class_data()
            if class_data == None :
                continue

            #buff += "%d%d%d%d%d" % ( c.get_access_flags(), class_data.static_fields_size, class_data.instance_fields_size, class_data.direct_methods_size, class_data.virtual_methods_size )
            
            for m in c.get_methods() :
                z_tmp = create_entropies( vmx, m )
                            
                value += z_tmp[0]
                value_entropy += z_tmp[1]
                android_entropy += z_tmp[2]
                java_entropy += z_tmp[3]
                hex_entropy += z_tmp[4]
                exception_entropy += z_tmp[5]

                nb_methods += 1
                
            #buff += "%d%s" % (m.get_access_flags(), m.get_descriptor())

            #for f in c.get_fields() :
            #    buff += "%d%s" % (f.get_access_flags(), f.get_descriptor())

            if nb_methods != 0 :
                uniqueid = self._create_id( m.get_class_name() )
                ret = self.class_sim.add_elem_sim( uniqueid, value, [ value_entropy/nb_methods, 
                                                                  android_entropy/nb_methods, 
                                                                  java_entropy/nb_methods, 
                                                                  hex_entropy/nb_methods,
                                                                  exception_entropy/nb_methods ] )
       
            #uniqueid = self._create_id( buff )
            #ret = self.class_hash.add_elem_string( uniqueid, hashlib.sha256( buff ).hexdigest() )

        #X_r = self.pca.fit(self.X).transform(self.X)
        #sys.argv = [ "toto.py" ]
        #pl.figure()
        #for i in X_r :
        #    pl.scatter( i[0], i[1] )
        #for c, i, target_name in zip("rgb", [0, 1, 2], target_names):
        #    pl.scatter(X_r[y == i, 0], X_r[y == i, 1], c=c, label=target_name)
        #pl.legend()
        #pl.title('PCA of dataset')
        #pl.savefig('totocluster')
        #pl.show()
        
        if self.debug :
            print "2",
            sys.stdout.flush()
       

        ret, l = self.__check()

        if self.debug :
            dt = self.meth_sim.get_debug()
            dt1 = self.class_sim.get_debug()
            print "C:%d CC:%d CMP:%d EL:%d" % (dt[2], dt[3], dt[0], dt[1]),
            print "C:%d CC:%d CMP:%d EL:%d" % (dt1[2], dt1[3], dt1[0], dt1[1]),
        
            #print ret, l, "---->",
        
        ret = self.__eval( l )

        #print "---->", self.__eval( l )

        self.meth_sim.raz()
        self.class_sim.raz()

        return ret, l

    def __eval(self, l) :
        current_sign = {} 
        ret = [] 

        for i in l :
            m_sign = self.__signs[ self.__rsigns[ i[0] ] ]

            try :
                ev = current_sign[ self.__rsigns[ i[0] ] ]
            except KeyError :
                current_sign[ self.__rsigns[ i[0] ] ] = m_sign[-1]
                ev = current_sign[ self.__rsigns[ i[0] ] ]
           
            current_sign[ self.__rsigns[ i[0] ] ] = ev.replace( str( m_sign[1][i[0]] ), "True" )

        
        for i in l :
            ev = current_sign[ self.__rsigns[ i[0] ] ]
            ev = ev.replace("1", "False")

            if (eval(ev) == True) :
                return self.__signs[ self.__rsigns[ i[0] ] ][0]
        
        return None

def create_entropies(vmx, m) :
    l = [ vmx.get_method_signature(m, predef_sign = DEFAULT_SIGNATURE).get_string(),
          libsign.entropy( vmx.get_method_signature(m, predef_sign = DEFAULT_SIGNATURE ).get_string() ),
          libsign.entropy( vmx.get_method_signature(m, "L4", { "L4" : { "arguments" : ["Landroid"] } } ).get_string() ),
          libsign.entropy( vmx.get_method_signature(m, "L4", { "L4" : { "arguments" : ["Ljava"] } } ).get_string() ),
          libsign.entropy( vmx.get_method_signature(m, "hex" ).get_string() ),
          libsign.entropy( vmx.get_method_signature(m, "L2" ).get_string() ),
        ]

    return l

class CSignature :
    def add_file(self, srules) :
        l = []
        rules = json.loads( srules )

        ret_type = androconf.is_android( rules[0]["SAMPLE"] )
        if ret_type == "APK" :
            a = apk.APK( rules[0]["SAMPLE"] )
            classes_dex = a.get_dex()
        elif ret_type == "DEX" :
            classes_dex = open( rules[0]["SAMPLE"], "rb" ).read()
        else :
            return None

        vm = dvm.DalvikVMFormat( classes_dex )
        vmx = VMAnalysis( vm )

        for i in rules[1:] :
            x = { i["NAME"] : [] }
            n = 0
            
            sign = []
            for j in i["SIGNATURE"] :
                z = []
                if j["TYPE"] == "METHSIM" :
                    z.append( METHSIM )
                    m = vm.get_method_descriptor( j["CN"], j["MN"], j["D"] )
                    if m == None :
                        raise("ooo")
                    
                    #print m.get_length()

                    z_tmp = create_entropies( vmx, m )
                    z_tmp[0] = base64.b64encode( z_tmp[0] )
                    z.extend( z_tmp )
                elif j["TYPE"] == "CLASSHASH" :
                    buff = ""
                    for c in vm.get_classes() :
                        if j["CN"] == c.get_name() :
                            z.append( CLASSHASH )
                            class_data = c.get_class_data()
                            buff += "%d%d%d%d%d" % ( c.get_access_flags(), class_data.static_fields_size, class_data.instance_fields_size, class_data.direct_methods_size, class_data.virtual_methods_size )
                            for m in c.get_methods() :
                                buff += "%d%s" % (m.get_access_flags(), m.get_descriptor())

                            for f in c.get_fields() :
                                buff += "%d%s" % (f.get_access_flags(), f.get_descriptor())

                            z.append( hashlib.sha256( buff ).hexdigest() )
                elif j["TYPE"] == "CLASSSIM" :
                    for c in vm.get_classes() :
                        if j["CN"] == c.get_name() :
                            z.append( CLASSSIM )
                            value = ""
                            value_entropy = 0.0
                            android_entropy = 0.0
                            java_entropy = 0.0
                            hex_entropy = 0.0
                            exception_entropy = 0.0
                            nb_methods = 0
                            for m in c.get_methods() :
                                z_tmp = create_entropies( vmx, m )
                            
                                value += z_tmp[0]
                                value_entropy += z_tmp[1]
                                android_entropy += z_tmp[2]
                                java_entropy += z_tmp[3]
                                hex_entropy += z_tmp[4]
                                exception_entropy += z_tmp[5]

                                nb_methods += 1

                            z.extend( [ base64.b64encode(value), 
                                        value_entropy/nb_methods, 
                                        android_entropy/nb_methods, 
                                        java_entropy/nb_methods, 
                                        hex_entropy/nb_methods, 
                                        exception_entropy/nb_methods ] )
                #elif j["TYPE"] == "MPSM" :
                #    z.append( 1 )
                #    z.append( j["STYPE"] )
                #    z.append( vmx.get_method_signature( vm.get_method_descriptor( j["CN"], j["MN"], j["D"] ), predef_sign = j["STYPE"] ).get_string() )

                sign.append( z )

            x[ i["NAME"] ].append( sign )
            x[ i["NAME"] ].append( i["BF"] )
            l.append( x )
        print l
        return l

    def entropy(self, s) :
        return libsign.entropy( s )

    def list_indb(self, output) :
        fd = open(output, "r")
        buff = json.loads( fd.read() )
        fd.close()

        for i in buff :
            print i, 
            for j in buff[i][0] :
                print j[0], j[2:],
            print

    def add_indb(self, signatures, output) :
        fd = open(output, "a+")
        buff = fd.read() 
        if buff == "" :
            buff = {}
        else :
            buff = json.loads( buff )
        fd.close()

        for i in signatures :
            buff.update( i )

        fd = open(output, "w") 
        fd.write( json.dumps( buff ) )
        fd.close()
