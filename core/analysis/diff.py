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

import hashlib

from androconf import error, warning, debug, set_debug, get_debug
from similarity import *
from analysis import *

import bytecode

######################### DIFF ###############################

def clean_name_instruction( instruction ) :
    op_value = instruction.get_op_value()
    
    # goto range
    if op_value >= 0x28 and op_value <= 0x2a :
        return "goto"

    return instruction.get_name()

def static_operand_instruction( instruction ) :
    buff = ""
    for op in instruction.get_operands() :
        if instruction.type_ins_tag == 0 :
            if "#" in op[0] :
                buff += "%s" % op
    
    if instruction.get_name() == "const-string" :
        buff += instruction.get_operands()[1][-1]
    #print instruction.get_operands()

    return buff

def filter_skip_meth_basic( m ) :
    return False

class CheckSumMeth :
    def __init__(self, m1, sim) :
        self.buff = ""
        self.entropy = 0.0
        
        code = m1.get_code()
        if code != None :
            bc = code.get_bc()

            for i in bc.get() :
                self.buff += clean_name_instruction( i )
                self.buff += static_operand_instruction( i )

            self.entropy = sim.entropy( self.buff )

    def get_entropy(self) :
        return self.entropy

    def get_buff(self) :
        return self.buff

def filter_checksum_meth_basic( m1, sim ) :
    return CheckSumMeth( m1, sim )

def filter_sim_meth_old( m1, m2, sim ) :
    a1 = m1.checksum
    a2 = m2.checksum

    e1 = a1.get_entropy()
    e2 = a2.get_entropy()

    return (max(e1, e2) - min(e1, e2)) 

def filter_sim_meth_basic( m1, m2, sim ) :
    s1 = m1.vmx.get_method_signature( m1.m, predef_sign = SIGNATURE_L0_0 ).get_string()
    s2 = m2.vmx.get_method_signature( m2.m, predef_sign = SIGNATURE_L0_0 ).get_string()

    ncd1, _ = sim.ncd( s1, s2 )

    a1 = m1.checksum
    a2 = m2.checksum

    ncd2, _ = sim.ncd( a1.get_buff(), a2.get_buff() )

    return (ncd1 + ncd2) / 2.0

def filter_sort_meth_basic( x, value ) :
    z = sorted(x.iteritems(), key=lambda (k,v): (v,k))

    if get_debug() :
        for i in z :
            debug("\t %s %s %s %d %f" %(i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), i[0].m.get_length(), i[1]))
 
    if z[:1][0][1] > value :
        return []

    return z[:1]

def filter_sim_bb_basic( bb1, bb2, sim ) :
    ncd, _ = sim.ncd( bb1.get_buff(), bb2.get_buff() )
    return ncd

class CheckSumBB :
    def __init__(self, basic_block) :
        self.basic_block = basic_block
        self.buff = ""
        for i in self.basic_block.ins :
            self.buff += clean_name_instruction( i )
            self.buff += static_operand_instruction( i )

        #self.hash = hashlib.sha256( self.buff + "%d%d" % (len(basic_block.childs), len(basic_block.fathers)) ).hexdigest()
        self.hash = hashlib.sha256( self.buff ).hexdigest()

    def get_buff(self) :
        return self.buff

    def get_hash(self) :
        return self.hash

def filter_checksum_bb_basic( basic_block ) :
    return CheckSumBB( basic_block )

def LCS(X, Y):
    m = len(X)
    n = len(Y)
    # An (m+1) times (n+1) matrix
    C = [[0] * (n+1) for i in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if X[i-1] == Y[j-1]:
                C[i][j] = C[i-1][j-1] + 1
            else:
                C[i][j] = max(C[i][j-1], C[i-1][j])
    return C

def getDiff(C, X, Y, i, j, a, r):
    if i > 0 and j > 0 and X[i-1] == Y[j-1]:
        getDiff(C, X, Y, i-1, j-1, a, r)
        debug(" " + "%02X" % ord(X[i-1]))
    else:
        if j > 0 and (i == 0 or C[i][j-1] >= C[i-1][j]):
            getDiff(C, X, Y, i, j-1, a, r)
            a.append( (j-1, Y[j-1]) )
            debug(" + " + "%02X" % ord(Y[j-1]))
        elif i > 0 and (j == 0 or C[i][j-1] < C[i-1][j]):
            getDiff(C, X, Y, i-1, j, a, r)
            r.append( (i-1, X[i-1]) )
            debug(" - " + "%02X" % ord(X[i-1]))

def toString( bb, hS, rS ) :
    S = ""

    for i in bb.ins :
        ident = clean_name_instruction( i )
        ident += static_operand_instruction( i )

#       print i.get_name(), i.get_operands()
        if ident not in hS :
            hS[ ident ] = len(hS)
            rS[ chr( hS[ ident ] ) ] = ident

        S += chr( hS[ ident ] )

    return S

DIFF_INS_TAG = {
                        "ORIG" : 0,
                        "ADD" : 1,
                        "REMOVE" : 2
                    }

class DiffBB :
    def __init__(self, bb1, bb2, info) :
        self.bb1 = bb1
        self.bb2 = bb2
        self.info = info

        self.start = self.bb1.start
        self.end = self.bb1.end
        self.name = self.bb1.name

        self.di = None
        self.ins = []

    def diff_ins(self, di) :
        self.di = di

        off_add = {}
        off_rm = {}
        for i in self.di.add_ins :
            off_add[ i[0] ] = i

        for i in self.di.remove_ins :
            off_rm[ i[0] ] = i

        nb = 0
        for i in self.bb1.ins :
            ok = False
            if nb in off_add :
                debug("%d ADD %s %s" % (nb, off_add[ nb ][2].get_name(), off_add[ nb ][2].get_operands()))
                self.ins.append( off_add[ nb ][2] )
                setattr( off_add[ nb ][2], "diff_tag", DIFF_INS_TAG["ADD"] )
                del off_add[ nb ]

            if nb in off_rm :
                debug("%d RM %s %s" % (nb, off_rm[ nb ][2].get_name(), off_rm[ nb ][2].get_operands()))
                self.ins.append( off_rm[ nb ][2] )
                setattr( off_rm[ nb ][2], "diff_tag", DIFF_INS_TAG["REMOVE"] )
                del off_rm[ nb ]
                ok = True

            if ok == False :
                self.ins.append( i )
                debug("%d %s %s" % (nb, i.get_name(), i.get_operands()))
                setattr( i, "diff_tag", DIFF_INS_TAG["ORIG"] )

            nb += 1

        #print nb, off_add, off_rm

        nbmax = nb
        if off_add != {} :
            nbmax = sorted(off_add)[-1]
        if off_rm != {} :
            nbmax = max(nbmax, sorted(off_rm)[-1])

        while nb <= nbmax :
            if nb in off_add :
                debug("%d ADD %s %s" % (nb, off_add[ nb ][2].get_name(), off_add[ nb ][2].get_operands()))
                self.ins.append( off_add[ nb ][2] )
                setattr( off_add[ nb ][2], "diff_tag", DIFF_INS_TAG["ADD"] )
                del off_add[ nb ]

            if nb in off_rm :
                debug("%d RM %s %s" % (nb, off_rm[ nb ][2].get_name(), off_rm[ nb ][2].get_operands()))
                self.ins.append( off_rm[ nb ][2] )
                setattr( off_rm[ nb ][2], "diff_tag", DIFF_INS_TAG["REMOVE"] )
                del off_rm[ nb ]

            nb += 1

        #print off_add, off_rm

    def set_childs(self, abb) :
        self.childs = self.bb1.childs

        for i in self.ins :
            if i == self.bb2.ins[-1] :

                childs = []
                for c in self.bb2.childs :
                    if c[2].name in abb :
                        debug("SET %s %s" % (c[2], abb[ c[2].name ]))
                        childs.append( (c[0], c[1], abb[ c[2].name ]) )
                    else :
                        debug("SET ORIG %s" % str(c))
                        childs.append( c )

                i.childs = childs

    def show(self) :
        print "\tADD INSTRUCTIONS :"
        for i in self.di.add_ins :
            print "\t\t", i[0], i[1], i[2].get_name(), i[2].get_operands()

        print "\tREMOVE INSTRUCTIONS :"
        for i in self.di.remove_ins :
            print "\t\t", i[0], i[1], i[2].get_name(), i[2].get_operands()

class NewBB :
    def __init__(self, bb) :
        self.bb = bb

        self.start = self.bb.start
        self.end = self.bb.end
        self.name = self.bb.name
        self.ins = self.bb.ins

    def set_childs(self, abb) :
        childs = []
        for c in self.bb.childs :
            if c[2].name in abb :
                debug("SET %s %s " % (c[2], abb[ c[2].name ]))
                childs.append( (c[0], c[1], abb[ c[2].name ]) )
            else :
                debug("SET ORIG %s" % str(c))
                childs.append( c )

        self.childs = childs

class DiffINS :
    def __init__(self, add_ins, remove_ins) :
        self.add_ins = add_ins
        self.remove_ins = remove_ins

def filter_diff_ins_basic( dbb, sim ) :
    final_add = []
    final_rm = []

    hS = {}
    rS = {}

    X = toString( dbb.bb1, hS, rS )
    Y = toString( dbb.bb2, hS, rS )


    debug("%s %d" % (repr(X), len(X)))
    debug("%s %d" % (repr(Y), len(Y)))

    m = len(X)
    n = len(Y)

    C = LCS( X, Y )
    a = []
    r = []

    getDiff(C, X, Y, m, n, a, r)
    debug(a)
    debug(r)

    debug("DEBUG ADD")
    for i in a :
        debug(" \t %s %s %s" % (i[0], dbb.bb2.ins[ i[0] ].get_name(), dbb.bb2.ins[ i[0] ].get_operands()))
        final_add.append( (i[0], 0, dbb.bb2.ins[ i[0] ]) )

    debug("DEBUG REMOVE")
    for i in r :
        debug(" \t %s %s %s" % (i[0], dbb.bb1.ins[ i[0] ].get_name(), dbb.bb1.ins[ i[0] ].get_operands()))
        final_rm.append( (i[0], 0, dbb.bb1.ins[ i[0] ]) )

    dbb.diff_ins( DiffINS( final_add, final_rm ) )


DIFF_BB_TAG = {
                        "ORIG" : 0,
                        "DIFF" : 1,
                        "NEW"  : 2
                  }

class Method :
    def __init__(self, vm, vmx, m, sim) :
        self.m = m
        self.vm = vm
        self.vmx = vmx
        self.mx = vmx.get_method( m )

        self.sort_h = []

        self.sim = sim
        self.hash = {}

    def add_attribute(self, func_meth, func_checksum_bb) :
        bb = {}
        bbhash = {}

        fm = func_meth( self.m, self.sim )

        for i in self.mx.basic_blocks.get() :
            bb[ i.name ] = func_checksum_bb( i )

            try :
                bbhash[ bb[ i.name ].get_hash() ].append( bb[ i.name ] )
            except KeyError :
                bbhash[ bb[ i.name ].get_hash() ] = []
                bbhash[ bb[ i.name ].get_hash() ].append( bb[ i.name ] )

        self.checksum = fm

        self.bb = bb
        self.bb_sha256 = bbhash
        self.sha256 = hashlib.sha256( fm.get_buff() ).hexdigest()

    def quick_similarity(self, new_method, func_sim) :
        return func_sim( self, new_method, self.sim )
    
    def similarity(self, new_method, func_sim) :
        self.hash[ new_method ] = func_sim( self, new_method, self.sim )

    def sort(self, func_sort, value) :
        self.sort_h = func_sort( self.hash, value )

        if self.sort_h == [] :
            return False
        return True

    def checksort(self, method) :
        for i in self.sort_h :
            if method == i[0] :
                return True
        return False

    def get_meth_first_sort(self) :
        if self.sort_h == [] :
            return 1.0

        return self.sort_h[0][0]

    def get_value_first_sort(self) :
        if self.sort_h == [] :
            return 1.0

        return self.sort_h[0][1]

    def diff(self, func_sim_bb, func_diff_ins):
        if self.sort_h == [] :
            self.dbb = {}
            self.nbb = {}
            return

        bb1 = self.bb

        ### Dict for diff basic blocks
            ### vm1 basic block : vm2 basic blocks -> value (0.0 to 1.0)
        diff_bb = {}

        ### List to get directly all diff basic blocks
        direct_diff_bb = []

        ### Dict for new basic blocks
        new_bb = {}

        ### Reverse Dict with matches diff basic blocks
        associated_bb = {}

        for b1 in bb1 :
            diff_bb[ bb1[ b1 ] ] = {}

            debug("%s 0x%x" % (b1, bb1[ b1 ].basic_block.end))
            for i in self.sort_h :
                bb2 = i[0].bb
                b_z = diff_bb[ bb1[ b1 ] ]

                bb2hash = i[0].bb_sha256

                # If b1 is in bb2 :
                    # we can have one or more identical basic blocks to b1, we must add them
                if bb1[ b1 ].get_hash() in bb2hash :
                    for equal_bb in bb2hash[ bb1[ b1 ].get_hash() ] :
                        b_z[ equal_bb.basic_block.name ] = 0.0

                # If b1 is not in bb2 :
                    # we must check similarities between all bb2
                else :
                    for b2 in bb2 :
                        b_z[ b2 ] = func_sim_bb( bb1[ b1 ], bb2[ b2 ], self.sim )

                sorted_bb = sorted(b_z.iteritems(), key=lambda (k,v): (v,k))

                debug("\t\t%s" %  sorted_bb[:2])

                for new_diff in sorted_bb :
                    associated_bb[ new_diff[0] ] = bb1[ b1 ].basic_block

                    if new_diff[1] == 0.0 :
                        direct_diff_bb.append( new_diff[0] )

                if sorted_bb[0][1] != 0.0 :
                    diff_bb[ bb1[ b1 ] ] = (bb2[ sorted_bb[0][0] ], sorted_bb[0][1])
                    direct_diff_bb.append( sorted_bb[0][0] )
                else :
                    del diff_bb[ bb1[ b1 ] ]

        for i in self.sort_h :
            bb2 = i[0].bb
            for b2 in bb2 :
                if b2 not in direct_diff_bb :
                    new_bb[ b2 ] = bb2[ b2 ]

        dbb = {}
        nbb = {}
        # Add all different basic blocks
        for d in diff_bb :
            dbb[ d.basic_block.name ] = DiffBB( d.basic_block, diff_bb[ d ][0].basic_block, diff_bb[ d ] )

        # Add all new basic blocks
        for n in new_bb :
            nbb[ new_bb[ n ].basic_block ] = NewBB( new_bb[ n ].basic_block )
            if n in associated_bb :
                del associated_bb[ n ]

        self.dbb = dbb
        self.nbb = nbb

        # Found diff instructions
        for d in dbb :
            func_diff_ins( dbb[d], self.sim )

        # Set new childs for diff basic blocks
            # The instructions will be tag with a new flag "childs"
        for d in dbb :
            dbb[ d ].set_childs( associated_bb )

        # Set new childs for new basic blocks
        for d in nbb :
            nbb[ d ].set_childs( associated_bb )

        # Create and tag all (orig/diff/new) basic blocks
        self.create_bbs()

    def create_bbs(self) :
        dbb = self.dbb
        nbb = self.nbb

        # For same block :
            # tag = 0
        # For diff block :
            # tag = 1
        # For new block :
            # tag = 2
        l = []
        for bb in self.mx.basic_blocks.get() :
            if bb.name not in dbb :
                # add the original basic block
                bb.bb_tag = DIFF_BB_TAG["ORIG"] 
                l.append( bb )
            else :
                # add the diff basic block
                dbb[ bb.name ].bb_tag = DIFF_BB_TAG["DIFF"]
                l.append( dbb[ bb.name ] )

        for i in nbb :
            # add the new basic block
            nbb[ i ].bb_tag = DIFF_BB_TAG["NEW"] 
            l.append( nbb[ i ] )

        # Sorted basic blocks by addr (orig, new, diff)
        l = sorted(l, key = lambda x : x.start)
        self.bbs = l

    def getsha256(self) :
        return self.sha256

    def show(self, details=False, exclude=[]) :
        print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(),
        print "with",

        for i in self.sort_h :
            print i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), i[1]

        print "\tDIFF BASIC BLOCKS :"
        for d in self.dbb :
            print "\t\t", self.dbb[d].bb1.name, " --->", self.dbb[d].bb2.name, ":", self.dbb[d].info[1]
            if details :
                self.dbb[d].show()

        print "\tNEW BASIC BLOCKS :"
        for b in self.nbb :
            print "\t\t", self.nbb[b].name

        # show diff !
        if details :
            bytecode.PrettyShow2( self.bbs, exclude )

    def show2(self, details=False) :
        print self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(),
        if self.m.get_code() == None :
            print 0
        else :
            print self.m.get_code().get_length()

        for i in self.sort_h :
            print "\t", i[0].m.get_class_name(), i[0].m.get_name(), i[0].m.get_descriptor(), i[1]

        if details :
            bytecode.PrettyShow1( self.mx.basic_blocks.get() )

FILTER_CHECKSUM_METH    =           "FILTER_CHECKSUM_METH"      # function to checksum a method
FILTER_SIM_METH         =           "FILTER_SIM_METH"           # function to calculate the similarity between two methods
FILTER_SORT_METH        =           "FILTER_SORT_METH"          # function to sort all diffing methods
FILTER_SORT_VALUE       =           "FILTER_SORT_VALUE"         # value which used in the sort method to eliminate not interesting comparisons
FILTER_SKIP_METH        =           "FILTER_SKIP_METH"          # function to skip methods
FILTER_MARK_METH        =           "FILTER_MARK_METH"          # function to mark all diffing methods
FILTER_MARK_VM          =           "FILTER_MARK_VM"            # function to mark vms
FILTER_CHECKSUM_BB      =           "FILTER_CHECKSUM_BB"        # function to checksum a basic block
FILTER_SIM_BB           =           "FILTER_SIM_BB"             # function to calculate the similarity between two basic blocks
FILTER_DIFF_INS         =           "FILTER_DIFF_INS"           # function to diff two basic blocks
FILTER_CHECKSUM_VM      =           "FILTER_CHECKSUM_VM"        # function to checksum a vm
FILTER_SIM_VM           =           "FILTER_SIM_VM"             # function to calculate the similarity between two vms 

FILTERS_DIFF_BASIC = {
    FILTER_CHECKSUM_METH    : filter_checksum_meth_basic,
    FILTER_SIM_METH         : filter_sim_meth_basic,
    FILTER_SORT_METH        : filter_sort_meth_basic,
    FILTER_SORT_VALUE       : 0.6,
    FILTER_SKIP_METH        : filter_skip_meth_basic,

    FILTER_CHECKSUM_BB      : filter_checksum_bb_basic,
    FILTER_SIM_BB           : filter_sim_bb_basic,
                                        
    FILTER_DIFF_INS         : filter_diff_ins_basic,    
}

BASE            =       "base"
METHODS         =       "methods"
HASHSUM         =       "hashsum"
DIFFMETHODS     =       "diffmethods"
NEWMETHODS      =       "newmethods"
DELETEMETHODS   =       "deletemethods"
MATCHMETHODS    =       "matchmethods"
DIFFVMS         =       "diffvms"
class Diff(object) :
    def __init__(self, vm1, vm2, F=FILTERS_DIFF_BASIC) :
        #set_debug()
        
        self.vms = [ vm1, vm2 ]
        self.vm1 = vm1
        self.vm2 = vm2

        self.sim = SIMILARITY( "classification/libsimilarity/libsimilarity.so" )
        self.sim.set_compress_type( SNAPPY_COMPRESS )

        self.nb_methods = 0

        self.F = F
        self.filters = {}


        self._init_filters()
        self._init_index_methods()
        self._init_similarity()
        self._init_sort_methods()
        self._init_diff_methods()
        self._init_new_methods()


    def _init_filters(self) :
        self.filters = {}
        self.filters[ BASE ] = {}
        self.filters[ BASE ].update( self.F )
        self.filters[ METHODS ] = {}
        self.filters[ HASHSUM ] = {}
        self.filters[ DIFFMETHODS ] = []
        self.filters[ NEWMETHODS ] = []
        self.filters[ DELETEMETHODS ] = []
        self.filters[ MATCHMETHODS ] = []

        for j in self.vms :
            self.filters[METHODS][ j[0] ] = []
            self.filters[HASHSUM][ j[0] ] = []

    def _init_index_methods(self) :
        for i in self.vms :
            for method in i[0].get_methods() :
                self.nb_methods += 1
                m = Method( i[0], i[1], method, self.sim )

                # Skip the method ?
                if self.filters[BASE][FILTER_SKIP_METH]( method ) :
                    continue
                    
                self.filters[METHODS][ i[0] ].append( m )
                m.add_attribute( self.filters[BASE][FILTER_CHECKSUM_METH], self.filters[BASE][FILTER_CHECKSUM_BB] )
                self.filters[HASHSUM][i[0]].append( m.getsha256() )

    def _init_similarity(self) :
        # Add a cache to available method in BB2
        available_vm2_methods = []
        for k in self.filters[METHODS][self.vm2[0]] :
            # B2 not at 0.0 in BB1
            if k.getsha256() not in self.filters[HASHSUM][self.vm1[0]] :
                available_vm2_methods.append( k )
            # B2 matched perfectly in BB1
            else :
                if k not in self.filters[MATCHMETHODS] :
                    self.filters[MATCHMETHODS].append( k )

        # Check if some methods in the first file has been modified
        for j in self.filters[METHODS][self.vm1[0]] :
            debug("SIM FOR %s %s %s" % (j.m.get_class_name(), j.m.get_name(), j.m.get_descriptor()))
            # B1 not at 0.0 in BB2
            if j.getsha256() not in self.filters[HASHSUM][self.vm2[0]] :
                for k in available_vm2_methods :        
                    j.similarity( k, self.filters[BASE][FILTER_SIM_METH] )
                    if j not in self.filters[DIFFMETHODS] :
                        self.filters[DIFFMETHODS].append(j)
            # B1 matched perfectly in BB2
            else :
                if j not in self.filters[MATCHMETHODS] :
                    self.filters[MATCHMETHODS].append( j )

    def _init_sort_methods(self) :
#       print "DEBUG DIFF METHODS"
        delete_methods = []
        for j in self.filters[DIFFMETHODS] :
            debug("%s %s %s %d" % (j.m.get_class_name(), j.m.get_name(), j.m.get_descriptor(), j.m.get_length()))
            ret = j.sort( self.filters[BASE][FILTER_SORT_METH], self.filters[BASE][FILTER_SORT_VALUE] )
            if ret == False :
                delete_methods.append( j )

        for j in delete_methods :
            self.filters[ DELETEMETHODS ].append( j )
            pos = self.filters[ DIFFMETHODS ].index( j )
            self.filters[ DIFFMETHODS ].remove( j )

    def _init_diff_methods(self) :
#       print "DEBUG DIFF METHODS"
        for j in self.filters[DIFFMETHODS] :
#           print "DEBUG", j, j.m.get_class_name(), j.m.get_name(), j.m.get_descriptor()
            j.diff( self.filters[BASE][FILTER_SIM_BB], self.filters[BASE][FILTER_DIFF_INS] )

    def _init_new_methods(self) :
        # Check if some methods in the second file are totally new !
        for j in self.filters[METHODS][self.vm2[0]] :

            # new methods can't be in diff methods
            if j not in self.filters[DIFFMETHODS] :
                # new methods hashs can't be in first file
                if j.getsha256() not in self.filters[HASHSUM][self.vm1[0]] :
                    ok = True
                    # new methods can't be compared to another one
                    for diff_method in self.filters[DIFFMETHODS] :
                        #print diff_method, "--->", j
                        if diff_method.checksort( j ) :
                            ok = False
                            break

                    if ok :
                        self.filters[NEWMETHODS].append( j )

    def get_diff_methods(self) :
        return self.get_elem( DIFFMETHODS )

    def get_new_methods(self) :
        return self.get_elem( NEWMETHODS )
    
    def get_delete_methods(self) :
        return self.get_elem( DELETEMETHODS )

    def get_match_methods(self) :
        return self.get_elem( MATCHMETHODS )

    def get_elem(self, attr) :
        return [ x for x in self.filters[attr] ]

######################### SIM ###############################

def filter_sim_meth_sim( m1, m2, sim ) :
    # CFG + API
    mysign = SIGNATURE_L0_4
    s1 = m1.vmx.get_method_signature( m1.m, predef_sign=mysign ).get_string()
    s2 = m2.vmx.get_method_signature( m2.m, predef_sign=mysign ).get_string()

    ncd1, ret = sim.ncd( s1, s2 )

    # Exception
    mysign_exception = SIGNATURE_L0_0_L2
    s1 = m1.vmx.get_method_signature( m1.m, predef_sign=mysign_exception ).get_level( 2 )
    s2 = m2.vmx.get_method_signature( m2.m, predef_sign=mysign_exception ).get_level( 2 )

    ncd2, ret = sim.ncd( s1, s2 )

    if ret == -1 :
        return ncd1

    return (ncd1 + ncd2) / 2

class CheckSumVM :
    def __init__(self, vm) :
        self.vm = vm

def filter_checksum_vm_sim( vm ):
    return CheckSumVM( vm )

COEFF_SIM_VM = {
        "STRING" : 1,
        "CONSTANT_FLOAT" : 1,
        "CLINIT" : 1
}

def filter_sim_vm_sim( vm1, vm2, sim ):
    svm1 = ''.join( vm1.vm[0].get_strings() )
    svm2 = ''.join( vm2.vm[0].get_strings() )

    return { "STRING" : sim.ncd( svm1, svm2 )[0] }

def filter_skip_meth_sim( m ) :
    code = m.get_code()
    if code != None :
        if code.get_length() < 100 :
            return True
        return False
    return True

def filter_mark_vm( values ) :
    return values.values()

def filter_mark_meth( v ) :
    if v >= 0.2 :
        return 1.0

    return v

FILTERS_SIM = {
        FILTER_CHECKSUM_VM      : filter_checksum_vm_sim,
        FILTER_SIM_VM           : filter_sim_vm_sim,
        FILTER_MARK_VM          : filter_mark_vm,
                                            
        FILTER_CHECKSUM_METH    : filter_checksum_meth_basic,
        FILTER_SIM_METH         : filter_sim_meth_sim,
        FILTER_SORT_METH        : filter_sort_meth_basic,
        FILTER_SORT_VALUE       : 0.6,
        FILTER_SKIP_METH        : filter_skip_meth_sim,
        FILTER_MARK_METH        : filter_mark_meth,

        FILTER_CHECKSUM_BB      : filter_checksum_bb_basic,
        
}

### SIM :
    # DATA
        # string                           [OK]
        # constant (int, float ...)
        # clinit
    # CODE
        # CFG / Instructions : module Diff [OK]
        # Exceptions                       [OK]
        # API                              [OK]
        # CFG method
        # Fill array data
        # Format
class Sim(Diff) :
    def __init__(self, vm1, vm2, F=FILTERS_SIM) :
        #set_debug()
        self.vm_marks = []
        self.diff_methods_marks = [] 
        self.marks = [] 
        self.final_score = 0.0 
        super(Sim, self).__init__(vm1, vm2, F)

        self._init_diff_vms()
        self._init_mark_methods()
       
        self.marks.extend( self.vm_marks )
        self.marks.extend( self.diff_methods_marks )

        s = 0.0
        for i in self.marks :
            s += (1.0 - i)
        self.final_score = (s/len(self.marks)) * 100

    def get_marks(self) :
        return self.marks

    def get_final_score(self) :
        return self.final_score

    def _init_diff_vms(self) :
        x1 = self.filters[BASE][FILTER_CHECKSUM_VM]( self.vm1 ) 
        x2 = self.filters[BASE][FILTER_CHECKSUM_VM]( self.vm2 )

        val = self.filters[BASE][FILTER_SIM_VM]( x1, x2, self.sim )
        self.vm_marks.extend( self.filters[BASE][FILTER_MARK_VM]( val ) )

    def _init_diff_methods(self) :
        # we don't want to diff instructions of basic blocks
        pass

    def _init_mark_methods(self) :
        # Change the compression to have a better result for a one <-> one comparaison in order to have a correct percentage
        self.sim.set_compress_type( XZ_COMPRESS )

        # mark diff methods
        for j in self.filters[DIFFMETHODS] :
            debug("%s %s %s" % (j.m.get_class_name(), j.m.get_name(), j.m.get_descriptor()))
                
            # get the first method which match
            k = j.get_meth_first_sort()
               
            # recalculate the similarity to have better percentage with a better algorithm
            v1 = j.quick_similarity( k, self.filters[BASE][FILTER_SIM_METH] ) 

            # filter the mark to eliminate totaly diff method
            v2 = self.filters[BASE][FILTER_MARK_METH]( v1 )
            self.diff_methods_marks.append( v2 )

        # mark match methods
        for m in self.filters[ MATCHMETHODS ] :
            v = self.filters[BASE][FILTER_MARK_METH]( 0.0 )
            self.diff_methods_marks.append( v )

        # Check if some methods in the second file are totally new !
        #for fil in self.filters :
        #    for j in self.filters[fil][METHODS][vm2[0]] :

                # new methods can't be in diff methods
        #        if j not in self.filters[fil][DIFFMETHODS] :
                    # new methods hashs can't be in first file
        #            if j.getsha256( self.filters[fil][BASE][FILTER_NAME] ) not in self.filters[fil][HASHSUM][vm1[0]] :
        #                ok = True
                        # new methods can't be compared to another one
        #                for diff_method in self.filters[fil][DIFFMETHODS] :
        #                    #print diff_method, "--->", j
        #                    if diff_method.checksort( self.filters[fil][BASE][FILTER_NAME], j ) :
        #                        ok = False
        
        #                        break

                        # It's a new method in VM2, compare them to VM1
        #                if ok :
        #                    for k in self.filters[fil][METHODS][vm1[0]] :
                                # k must have an invalid hash in vm2 to be compare
        #                        if k.getsha256( self.filters[fil][BASE][FILTER_NAME] ) not in self.filters[fil][HASHSUM][vm2[0]] :
        #                            j.similarity( k, self.filters[fil][BASE][FILTER_SIM_METH], self.filters[fil][BASE][FILTER_NAME] )
        #                    self.filters[fil][NEWMETHODS].append( j )

        #print "DEBUG NEW METHODS"
        #for fil in self.filters :
            #print "\tDEBUG", self.filters[fil][NEWMETHODS]
        #    for method in self.filters[fil][NEWMETHODS] :
               #print "DEBUG", method.m.get_class_name(), method.m.get_name(), method.m.get_descriptor()
        #       method.sort( self.filters[fil][BASE][FILTER_NAME] ) 
        #       self.scoring.append( method.getclosesort( self.filters[fil][BASE][FILTER_NAME] ) )

######################### SIM with multiple files : FIXME ###############################

class Si : 
    def __init__(self, name, val) :
        self.name = name
        self.val = val
        self.vectors = []

    def cmp(self, vectors) :
        self.vectors = vectors

def CMP(sim, x, y) :
    return sim.ncd( x.val, y.val )[0]

import analysis
import json

class SimJson :
    def __init__(self, vm1, filename) :
        self.vm1 = vm1

        import scipy.cluster.hierarchy
        
        print "Loading"
        fd = open(filename, "r")
        self.files = json.load( fd )
        fd.close()

        print "Checking ..."

        SIGN = "L0_0"
        L = []
        M = []

        self.sim = SIMILARITY( "classification/libsimilarity/libsimilarity.so" )
        self.sim.set_compress_type( SNAPPY_COMPRESS )                                                                                                                                            

        for i in self.files[1:] :
            for j in i :
                if j != "SourceFilename" :
                    for key in i[j] :
                        if len(i[j][key][SIGN]) > 10 :
                            L.append( Si( j, i[j][key][SIGN] ) )
                        #print i[j][SIGN]

        print len(L) * len(vm1[0].get_methods())
        for m in vm1[0].get_methods() :
            s = vm1[1].get_method_signature( m, predef_sign = analysis.SIGNATURE_L0_0 )

            i = Si( m, s.get_string() )
            i.cmp( [ CMP(self.sim, i, j) for j in L ] )
            M.append( i )

        print M 

        X = [ i.vectors for i in M ]

        fd = open("toto.json", "w")
        json.dump( X, fd )
        fd.close()
        #Z = scipy.cluster.hierarchy.linkage( X )
        #scipy.cluster.hierarchy.dendrogram( Z )
