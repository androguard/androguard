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

import re, random, string, cPickle

from error import error, warning
import jvm, dvm
from api_permissions import DVM_PERMISSIONS_BY_PERMISSION, DVM_PERMISSIONS_BY_ELEMENT

class ContextField :
    def __init__(self, mode) :
        self.mode = mode
        self.details = []

    def set_details(self, details) :
        for i in details :
            self.details.append( i )

class ContextMethod :
    def __init__(self) :
        self.details = []

    def set_details(self, details) :
        for i in details :
            self.details.append( i )

class ExternalFM :
    def __init__(self, class_name, name, descriptor) :
        self.class_name = class_name
        self.name = name
        self.descriptor = descriptor

    def get_class_name(self) :
        return self.class_name

    def get_name(self) :
        return self.name

    def get_descriptor(self) :
        return self.descriptor

class ToString :
    def __init__(self, tab) :
        self.__tab = tab
        self.__re_tab = {}

        for i in self.__tab :
            self.__re_tab[i] = []
            for j in self.__tab[i] :
                self.__re_tab[i].append( re.compile( j ) )

        self.__string = ""

    def push(self, name) :
        for i in self.__tab :
            for j in self.__re_tab[i] :
                if j.match(name) != None :
                    if len(self.__string) > 0 :
                        if i == 'O' and self.__string[-1] == 'O' :
                            continue
                    self.__string += i

    def get_string(self) :
        return self.__string

class BreakBlock(object) :
    def __init__(self, _vm, idx) :
        self._vm = _vm
        self._start = idx
        self._end = self._start

        self._ins = []

        self._ops = []

        self._fields = {}
        self._methods = {}


    def get_ops(self) :
        return self._ops

    def get_fields(self) :
        return self._fields

    def get_methods(self) :
        return self._methods

    def push(self, ins) :
        self._ins.append(ins)
        self._end += ins.get_length()

    def get_start(self) :
        return self._start

    def get_end(self) :
        return self._end

    def show(self) :
        for i in self._ins :
            print "\t\t",
            i.show(0)

##### DVM ######

MATH_DVM_RE = []
for i in dvm.MATH_DVM_OPCODES :
    MATH_DVM_RE.append( (re.compile( i ), dvm.MATH_DVM_OPCODES[i]) )

DVM_TOSTRING = { "O" : dvm.MATH_DVM_OPCODES.keys(),
                 "I" : dvm.INVOKE_DVM_OPCODES,
                 "G" : dvm.FIELD_READ_DVM_OPCODES,
                 "P" : dvm.FIELD_WRITE_DVM_OPCODES,
               }

class DVMBreakBlock(BreakBlock) :
    def __init__(self, _vm) :
        super(DVMBreakBlock, self).__init__(_vm)

    def analyze(self) :
        for i in self._ins :
            for mre in MATH_DVM_RE :
                if mre[0].match( i.get_name() ) :
                    self._ops.append( mre[1] )
                    break

##### JVM ######
FIELDS = {
            "getfield" : "R",
            "getstatic" : "R",
            "putfield" : "W",
            "putstatic" : "W",
         }

METHODS = [ "invokestatic", "invokevirtual", "invokespecial" ]

JVM_TOSTRING = { "O" : jvm.MATH_JVM_OPCODES.keys(),
                 "I" : jvm.INVOKE_JVM_OPCODES,
                 "G" : jvm.FIELD_READ_JVM_OPCODES,
                 "P" : jvm.FIELD_WRITE_JVM_OPCODES,
               }

BREAK_JVM_OPCODES_RE = []
for i in jvm.BREAK_JVM_OPCODES :
    BREAK_JVM_OPCODES_RE.append( re.compile( i ) )

class Stack :
    def __init__(self) :
        self.__elems = []

    def gets(self) :
        return self.__elems

    def push(self, elem) :
        self.__elems.append( elem )

    def get(self) :
        return self.__elems[-1]

    def pop(self) :
        return self.__elems.pop(-1)

    def nil(self) :
        return len(self.__elems) == 0

    def insert_stack(self, idx, elems) :
        if elems != self.__elems :
            for i in elems :
                self.__elems.insert(idx, i)
                idx += 1

    def show(self) :
        nb = 0

        if len(self.__elems) == 0 :
            print "\t--> nil"

        for i in self.__elems :
            print "\t-->", nb, ": ", i
            nb += 1

class StackTraces :
    def __init__(self) :
        self.__elems = []

    def save(self, idx, i_idx, ins, stack_pickle, msg_pickle) :
        self.__elems.append( (idx, i_idx, ins, stack_pickle, msg_pickle) )

    def get(self) :
        for i in self.__elems :
            yield (i[0], i[1], i[2], cPickle.loads( i[3] ), cPickle.loads( i[4] ) )

    def show(self) :
        for i in self.__elems :
            print i[0], i[1], i[2].get_name()

            cPickle.loads( i[3] ).show()
            print "\t", cPickle.loads( i[4] )

def push_objectref(_vm, ins, special, stack, res, ret_v) :
    value = "OBJ_REF_@_%s" % str(special)
    stack.push( value )

def push_objectref_l(_vm, ins, special, stack, res, ret_v) :
    stack.push( "VARIABLE_LOCAL_%d" % special )

def push_objectref_l_i(_vm, ins, special, stack, res, ret_v) :
    stack.push( "VARIABLE_LOCAL_%d" % ins.get_operands() )

def pop_objectref(_vm, ins, special, stack, res, ret_v) :
    ret_v.add_return( stack.pop() )

def multi_pop_objectref_i(_vm, ins, special, stack, res, ret_v) :
    for i in range(0, ins.get_operands()[1]) :
        stack.pop()

def push_objectres(_vm, ins, special, stack, res, ret_v) :
    value = ""

    if special[0] == 1 :
        value += special[1] + "(" + str( res.pop() ) + ") "
    else :
        for i in range(0, special[0]) :
            value += str( res.pop() ) + special[1]

    value = value[:-1]

    stack.push( value )

def push_integer_i(_vm, ins, special, stack, res, ret_v) :
    value = ins.get_operands()
    stack.push( value )

def push_integer_d(_vm, ins, special, stack, res, ret_v) :
    stack.push( special )

def push_float_d(_vm, ins, special, stack, res, ret_v) :
    stack.push( special )

def putfield(_vm, ins, special, stack, res, ret_v) :
    ret_v.add_return( stack.pop() )

def putstatic(_vm, ins, special, stack, res, ret_v) :
    stack.pop()

def getfield(_vm, ins, special, stack, res, ret_v) :
    ret_v.add_return( stack.pop() )
    stack.push( "FIELD" )

def getstatic(_vm, ins, special, stack, res, ret_v) :
    stack.push( "FIELD_STATIC" )

def new(_vm, ins, special, stack, res, ret_v) :
    stack.push( "NEW_OBJ" )

def dup(_vm, ins, special, stack, res, ret_v) :
    l = []

    for i in range(0, special+1) :
        l.append( stack.pop() )
    l.reverse()

    l.insert( 0, l[-1] )
    for i in l :
        stack.push( i )

def dup2(_vm, ins, special, stack, res, ret_v) :
    l = []

    for i in range(0, special+1) :
        l.append( stack.pop() )
    l.reverse()

    l.insert( 0, l[-1] )
    l.insert( 1, l[-2] )
    for i in l :
        stack.push( i )

#FIXME
def ldc(_vm, ins, special, stack, res, ret_v) :
    #print ins.get_name(), ins.get_operands(), special
    stack.push( "STRING" )

def invoke(_vm, ins, special, stack, res, ret_v) :
    desc = ins.get_operands()[-1]
    param = desc[1:desc.find(")")]
    ret = desc[desc.find(")")+1:]

#   print "DESC --->", param, calc_nb( param ), ret, calc_nb( ret )

    for i in range(0, calc_nb( param )) :
        stack.pop()

    # objectref : static or not
    for i in range(0, special) :
        stack.pop()

    for i in range(0, calc_nb( ret )):
        stack.push( "E" )

def set_arrayref(_vm, ins, special, stack, res, ret_v) :
    ret_v.add_msg( "SET VALUE %s %s @ ARRAY REF %s %s" % (special, str(stack.pop()), str(stack.pop()), str(stack.pop())) )

def set_objectref(_vm, ins, special, stack, res, ret_v) :
    ret_v.add_msg( "SET OBJECT REF %d --> %s" % (special, str(stack.pop())) )

def set_objectref_i(_vm, ins, special, stack, res, ret_v) :
    ret_v.add_msg( "SET OBJECT REF %d --> %s" % (ins.get_operands(), str(stack.pop())) )

def swap(_vm, ins, special, stack, res, ret_v) :
    l = stack.pop()
    l2 = stack.pop()

    stack.push(l2)
    stack.push(l)

def calc_nb(info) :
    if info == "" or info == "V" :
        return 0

    if ";" in info :
        n = 0
        for i in info.split(";") :
            if i != "" :
                n += 1
        return n
    else :
        return len(info) - info.count('[')

INSTRUCTIONS_ACTIONS = {
         "aaload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "aastore" : [ { set_arrayref : None } ],
         "aconst_null" : [ { push_objectref : "null" } ],
         "aload" : [ { push_objectref_l_i : None } ],
         "aload_0" : [ { push_objectref_l : 0 } ],
         "aload_1" : [ { push_objectref_l : 1 } ],
         "aload_2" : [ { push_objectref_l : 2 } ],
         "aload_3" : [ { push_objectref_l : 3 } ],
         "anewarray" : [ { pop_objectref : None }, { push_objectref : [ 1, "ANEWARRAY" ] } ],
         "areturn" : [ { pop_objectref : None } ],
         "arraylength" : [ { pop_objectref : None }, { push_objectres : [ 1, 'LENGTH' ] } ],
         "astore" : [ { set_objectref_i : None } ],
         "astore_0" : [ { set_objectref : 0 } ],
         "astore_1" : [ { set_objectref : 1 } ],
         "astore_2" : [ { set_objectref : 2 } ],
         "astore_3" : [ { set_objectref : 3 } ],
         "athrow" : [ { pop_objectref : None }, { push_objectres : [ 1, "throw" ] } ],
         "baload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "bastore" : [ { set_arrayref : "byte" } ],
         "bipush" :  [ { push_integer_i : None } ],
         "caload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "castore" : [ { set_arrayref : "char" } ],
         "checkcast" : [ { pop_objectref : None }, { push_objectres : [ 1, "checkcast" ] } ],
         "d2f" : [ { pop_objectref : None }, { push_objectres : [ 1, 'float' ] } ],
         "d2i" : [ { pop_objectref : None }, { push_objectres : [ 1, 'integer' ] } ],
         "d2l" : [  { pop_objectref : None }, { push_objectres : [ 1, 'long' ] } ],
         "dadd" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '+' ] } ],
         "daload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "dastore" : [ { set_arrayref : "double" } ],
         "dcmpg" : [  { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "dcmpl" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "dconst_0" : [ { push_float_d : 0.0 } ],
         "dconst_1" : [ { push_float_d : 1.0 } ],
         "ddiv" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '&' ] } ],
         "dload" : [ { push_objectref_l_i : None } ],
         "dload_0" : [ { push_objectref_l : 0 } ],
         "dload_1" : [  { push_objectref_l : 1 } ],
         "dload_2" : [  { push_objectref_l : 2 } ],
         "dload_3" : [  { push_objectref_l : 3 } ],
         "dmul" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '*' ] } ],
         "dneg" : [ { pop_objectref : None }, { push_objectres : [ 1, '-' ] } ],
         "drem" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, 'rem' ] } ],
         "dreturn" : [ { pop_objectref : None } ],
         "dstore" : [ { set_objectref_i : None } ],
         "dstore_0" : [ { set_objectref : 0 } ],
         "dstore_1" : [ { set_objectref : 1 } ],
         "dstore_2" : [ { set_objectref : 2 } ],
         "dstore_3" : [ { set_objectref : 3 } ],
         "dsub" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '-' ] } ],
         "dup" : [ { dup : 0 } ],
         "dup_x1" : [ { dup : 1 } ],
         "dup_x2" : [ { dup : 2 } ],
         "dup2" : [ { dup2 : 0 } ],
         "dup2_x1" : [ { dup2 : 1 } ],
         "dup2_x2" : [ { dup2 : 2 } ],
         "f2d" : [ { pop_objectref : None }, { push_objectres : [ 1, 'double' ] }  ],
         "f2i" : [ { pop_objectref : None }, { push_objectres : [ 1, 'integer' ] } ],
         "f2l" : [ { pop_objectref : None }, { push_objectres : [ 1, 'long' ] } ],
         "fadd" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '+' ] } ],
         "faload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "fastore" : [ { set_arrayref : "float" } ],
         "fcmpg" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "fcmpl" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "fconst_0" : [ { push_float_d : 0.0 } ],
         "fconst_1" : [ { push_float_d : 1.0 } ],
         "fconst_2" : [ { push_float_d : 2.0 } ],
         "fdiv" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '&' ] } ],
         "fload" : [ { push_objectref_l_i : None } ],
         "fload_0" : [ { push_objectref_l : 0 } ],
         "fload_1" : [ { push_objectref_l : 1 } ],
         "fload_2" : [ { push_objectref_l : 2 } ],
         "fload_3" : [ { push_objectref_l : 3 } ],
         "fmul" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '*' ] } ],
         "fneg" : [ { pop_objectref : None }, { push_objectres : [ 1, '-' ] } ],
         "freturn" : [ { pop_objectref : None } ],
         "fstore" : [ { set_objectref_i : None } ],
         "fstore_0" : [ { set_objectref : 0 } ],
         "fstore_1" : [ { set_objectref : 1 } ],
         "fstore_2" : [ { set_objectref : 2 } ],
         "fstore_3" : [ { set_objectref : 3 } ],
         "fsub" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '-' ] } ],
         "getfield" : [ { getfield : None } ],
         "getstatic" : [ { getstatic : None } ],
         "goto" : [ {} ],
         "goto_w" : [ {} ],
         "i2b" : [ { pop_objectref : None }, { push_objectres : [ 1, 'byte' ] } ],
         "i2c" : [ { pop_objectref : None }, { push_objectres : [ 1, 'char' ] }  ],
         "i2d" : [ { pop_objectref : None }, { push_objectres : [ 1, 'double' ] } ],
         "i2f" : [ { pop_objectref : None }, { push_objectres : [ 1, 'float' ] } ],
         "i2l" : [ { pop_objectref : None }, { push_objectres : [ 1, 'long' ] } ],
         "i2s" : [ { pop_objectref : None }, { push_objectres : [ 1, 'string' ] } ],
         "iadd" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '+' ] } ],
         "iaload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "iand" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '&' ] } ],
         "iastore" : [ { set_arrayref : "int" } ],
         "iconst_m1" : [ { push_integer_d : -1 } ],
         "iconst_0" : [ { push_integer_d : 0 } ],
         "iconst_1" : [ { push_integer_d : 1 } ],
         "iconst_2" : [ { push_integer_d : 2 } ],
         "iconst_3" : [ { push_integer_d : 3 } ],
         "iconst_4" : [ { push_integer_d : 4 } ],
         "iconst_5" : [ { push_integer_d : 5 } ],
         "idiv" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '/' ] } ],
         "if_acmpeq" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_acmpne" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_icmpeq" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_icmpne" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_icmplt" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_icmpge" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_icmpgt" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "if_icmple" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "ifeq" : [ { pop_objectref : None } ],
         "ifne" : [ { pop_objectref : None } ],
         "iflt" : [ { pop_objectref : None } ],
         "ifge" : [ { pop_objectref : None } ],
         "ifgt" : [ { pop_objectref : None } ],
         "ifle" : [ { pop_objectref : None } ],
         "ifnonnull" : [ { pop_objectref : None } ],
         "ifnull" : [ { pop_objectref : None } ],
         "iinc" : [ {} ],
         "iload" : [ { push_objectref_l_i : None } ],
         "iload_1" : [ { push_objectref_l : 1 } ],
         "iload_2" : [ { push_objectref_l : 2 } ],
         "iload_3" : [ { push_objectref_l : 3 } ],
         "imul" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '*' ] } ],
         "ineg" : [ { pop_objectref : None }, { push_objectres : [ 1, '-' ] } ],
         "instanceof" : [ { pop_objectref : None }, { push_objectres : [ 1, 'instanceof' ] } ],
         "invokeinterface" : [ { invoke : 1 } ],
         "invokespecial" : [ { invoke : 1 } ],
         "invokestatic" : [ { invoke : 0 } ],
         "invokevirtual": [ { invoke : 1 } ],
         "ior" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '|' ] } ],
         "irem" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, 'REM' ] } ],
         "ireturn" : [ { pop_objectref : None } ],
         "ishl" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '<<' ] } ],
         "ishr" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '>>' ] } ],
         "istore" : [ { set_objectref_i : None } ],
         "istore_0" : [ { set_objectref : 0 } ],
         "istore_1" : [ { set_objectref : 1 } ],
         "istore_2" : [ { set_objectref : 2 } ],
         "istore_3" : [ { set_objectref : 3 } ],
         "isub" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '-' ] } ],
         "iushr" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '>>' ] } ],
         "ixor" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '^' ] } ],
         "jsr" : [ { push_integer_i : None } ],
         "jsr_w" : [ { push_integer_i : None } ],
         "l2d" : [ { pop_objectref : None }, { push_objectres : [ 1, 'double' ] } ],
         "l2f" : [ { pop_objectref : None }, { push_objectres : [ 1, 'float' ] } ],
         "l2i" : [ { pop_objectref : None }, { push_objectres : [ 1, 'integer' ] } ],
         "ladd" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '+' ] } ],
         "laload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "land" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '&' ] } ],
         "lastore" : [ { set_arrayref : "long" } ],
         "lcmp" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "lconst_0" : [ { push_float_d : 0.0 } ],
         "lconst_1" : [ { push_float_d : 1.0 } ],
         "ldc" : [ { ldc : None } ],
         "ldc_w" : [ { ldc : None } ],
         "ldc2_w" : [ { ldc : None } ],
         "ldiv" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '/' ] } ],
         "lload" : [ { push_objectref_l_i : None } ],
         "lload_0" : [ { push_objectref_l : 0 } ],
         "lload_1" : [ { push_objectref_l : 1 } ],
         "lload_2" : [ { push_objectref_l : 2 } ],
         "lload_3" : [ { push_objectref_l : 3 } ],
         "lmul" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '*' ] } ],
         "lneg" : [ { pop_objectref : None }, { push_objectres : [ 1, '-' ] } ],
         "lookupswitch" : [ { pop_objectref : None } ],
         "lor" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '|' ] } ],
         "lrem" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, 'REM' ] } ],
         "lreturn" : [ { pop_objectref : None } ],
         "lshl" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '<<' ] } ],
         "lshr" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '>>' ] } ],
         "lstore" : [ { set_objectref_i : None } ],
         "lstore_0" : [ { set_objectref : 0 } ],
         "lstore_1" : [ { set_objectref : 1 } ],
         "lstore_2" : [ { set_objectref : 2 } ],
         "lstore_3" : [ { set_objectref : 3 } ],
         "lsub" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '-' ] } ],
         "lushr" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '>>' ] } ],
         "lxor" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectres : [ 2, '^' ] } ],
         "monitorenter" : [ { pop_objectref : None } ],
         "monitorexit" : [ { pop_objectref : None } ],
         "multianewarray" : [ { multi_pop_objectref_i : None }, { push_objectref : 0 } ],
         "new" : [ { new : None } ],
         "newarray" : [ { pop_objectref : None }, { push_objectref : [ 1, "NEWARRAY" ] } ],
         "nop" : [ {} ],
         "pop" : [ { pop_objectref : None } ],
         "pop2" : [ { pop_objectref : None }, { pop_objectref : None } ],
         "putfield" : [ { putfield : None }, { pop_objectref : None } ],
         "putstatic" : [ { putstatic : None } ],
         "ret" : [ {} ],
         "return" : [ {} ],
         "saload" : [ { pop_objectref : None }, { pop_objectref : None }, { push_objectref : 0 } ],
         "sastore" : [ { set_arrayref : "short" } ],
         "sipush" :  [ { push_integer_i : None } ],
         "swap" : [ { swap : None } ],
         "tableswitch" : [ { pop_objectref : None } ],
         "wide" : [ {} ],
}


class ReturnValues :
    def __init__(self) :
        self.__elems = []
        self.__msgs = []

    def add_msg(self, e) :
        self.__msgs.append( e )

    def add_return(self, e) :
        self.__elems.append( e )

    def get_msg(self) :
        return self.__msgs

    def get_return(self) :
        return self.__elems

class ExternalMethod :
    def __init__(self, class_name, name, descriptor) :
        self.__class_name = class_name
        self.__name = name
        self.__descriptor = descriptor

    def get_name(self) :
        return "M@[%s][%s]-[%s]" % (self.__class_name, self.__name, self.__descriptor)

    def set_fathers(self, f) :
        pass

class JVMBasicBlock :
    def __init__(self, start, _vm, _method, _context) :
        self.__vm = _vm
        self.__method = _method
        self.__context = _context

        self.__stack = Stack()
        self.stack_traces = StackTraces()

        self.ins = []

        self.fathers = []
        self.childs = []

        self.start = start
        self.end = self.start

        self.break_blocks = []

        self.free_blocks_offsets = []

        self.name = "%s-BB@0x%x" % (self.__method.get_name(), self.start)

    def get_stack(self) :
        return self.__stack.gets()

    def get_method(self) :
        return self.__method

    def get_name(self) :
        return self.name

    def get_start(self) :
        return self.start

    def get_end(self) :
        return self.end

    def get_last(self) :
        return self.ins[-1]

    def push(self, i) :
        self.ins.append( i )
        self.end += i.get_length()

    def set_fathers(self, f) :
        self.fathers.append( f )

    def set_childs(self, values) :
#      print self, self.start, self.end, values, self.ins[-1].get_name()
        if values == [] :
            next_block = self.__context.get_basic_block( self.end + 1 )
            if next_block != None :
                self.childs.append( ( self.end - self.ins[-1].get_length(), self.end, next_block ) )
        else :
            for i in values :
                #print i, self.__context.get_basic_block( i )
                if i != -1 :
                    self.childs.append( ( self.end - self.ins[-1].get_length(), i, self.__context.get_basic_block( i ) ) )

        for c in self.childs :
            if c[2] != None :
                c[2].set_fathers( ( c[1], c[0], self ) )

    def prev_free_block_offset(self, idx=0) :
        last = -1

        #print "IDX", idx, self.free_blocks_offsets

        if self.free_blocks_offsets == [] :
            return -1

        for i in self.free_blocks_offsets :
            if i <= idx :
                last = i
            else :
                return last

        return last

    def random_free_block_offset(self) :
        return self.free_blocks_offsets[ random.randint(0, len(self.free_blocks_offsets) - 1) ]

    def next_free_block_offset(self, idx=0) :
        #print idx, self.__free_blocks_offsets
        for i in self.free_blocks_offsets :
            if i > idx :
                return i
        return -1

    def get_random_free_block_offset(self) :
        return self.free_blocks_offsets[ random.randint(0, len(self.free_blocks_offsets) - 1) ]

    def get_random_break_block(self) :
        return self.break_blocks[ random.randint(0, len(self.break_blocks) - 1) ]

    def get_break_block(self, idx) :
        for i in self.break_blocks :
            if idx >= i.get_start() and idx <= i.get_end() :
                return i
        return None

    def analyze_break_blocks(self) :
        idx = self.get_start()

        current_break = JVMBreakBlock( self.__vm, idx )
        self.break_blocks.append(current_break)
        for i in self.ins :
            name = i.get_name()

            ##################### Break Block ########################
            match = False
            for j in BREAK_JVM_OPCODES_RE :
                if j.match(name) != None :
                    match = True
                    break

            current_break.push( i )
            if match == True :
                current_break.analyze()
                current_break = JVMBreakBlock( self.__vm, current_break.get_end() )

                self.break_blocks.append( current_break )
            #########################################################

            idx += i.get_length()

    def analyze(self) :
        idx = 0
        for i in self.ins :
            ################### TAINTED LOCAL VARIABLES ###################
            if "load" in i.get_name() or "store" in i.get_name() :
                action = i.get_name()

                access_flag = [ "R", "load" ]
                if "store" in action :
                    access_flag = [ "W", "store" ]

                if "_" in action :
                    name = i.get_name().split(access_flag[1])
                    value = name[1][-1]
                else :
                    value = i.get_operands()

                variable_name = "%s-%s" % (i.get_name()[0], value)

                self.__context.get_tainted_variables().add( variable_name, TAINTED_LOCAL_VARIABLE, self.__method )
                self.__context.get_tainted_variables().push_info( TAINTED_LOCAL_VARIABLE, variable_name, (access_flag[0], idx, self, self.__method) )
            #########################################################

            ################### TAINTED FIELDS ###################
            elif i.get_name() in FIELDS :
                o = i.get_operands()
                desc = getattr(self.__vm, "get_field_descriptor")(o[0], o[1], o[2])

                # It's an external
                if desc == None :
                    desc = ExternalFM( o[0], o[1], o[2] )

#               print "RES", res, "-->", desc.get_name()
                self.__context.get_tainted_variables().push_info( TAINTED_FIELD, desc, (FIELDS[ i.get_name() ][0], idx, self, self.__method) )
            #########################################################

            ################### TAINTED PACKAGES ###################
            elif "new" in i.get_name() or "invoke" in i.get_name() or "getstatic" in i.get_name() :
                if "new" in i.get_name() :
                    self.__context.get_tainted_packages()._push_info( i.get_operands(), (TAINTED_PACKAGE_CREATE, idx, self, self.__method) )
                else :
                    self.__context.get_tainted_packages()._push_info( i.get_operands()[0], (TAINTED_PACKAGE_CALL, idx, self, self.__method, i.get_operands()[1], i.get_operands()[2]) )
            #########################################################

            ################### TAINTED INTEGERS ###################
            if "ldc" == i.get_name() :
                o = i.get_operands()

                if o[0] == "CONSTANT_Integer" :
                    self.__context.get_tainted_integers().push_info( i, (o[1], idx, self, self.__method) )

            elif "sipush" in i.get_name() :
                self.__context.get_tainted_integers().push_info( i, (i.get_operands(), idx, self, self.__method) )

            elif "bipush" in i.get_name() :
                self.__context.get_tainted_integers().push_info( i, (i.get_operands(), idx, self, self.__method) )

            #########################################################

            idx += i.get_length()

    # FIXME : create a recursive function to follow the cfg, because it does not work with obfuscator
    def analyze_code(self) :
        self.analyze_break_blocks()

        #print "ANALYZE CODE -->", self.name
        d = {}
        for i in self.fathers :
        #   print "\t FATHER ->", i[2].get_name(), i[2].get_stack(), i[0], i[1]
            d[ i[0] ] = i[2]

        self.free_blocks_offsets.append( self.get_start() )

        idx = 0
        for i in self.ins :
#         print i.get_name(), self.start + idx, idx
#         i.show(idx)

            if self.start + idx in d :
                self.__stack.insert_stack( 0, d[ self.start + idx ].get_stack() )

            ret_v = ReturnValues()

            res = []
            try :
                #print i.get_name(), i.get_name() in INSTRUCTIONS_ACTIONS

                if INSTRUCTIONS_ACTIONS[ i.get_name() ] == [] :
                    print "[[[[ %s is not yet implemented ]]]]" % i.get_name()
                    raise("ooops")

                i_idx = 0
                for actions in INSTRUCTIONS_ACTIONS[ i.get_name() ] :
                    for action in actions :
                        action( self.__vm, i, actions[action], self.__stack, res, ret_v )
                        for val in ret_v.get_return() :
                            res.append( val )

                    #self.__stack.show()
                    self.stack_traces.save( idx, i_idx, i, cPickle.dumps( self.__stack ), cPickle.dumps( ret_v.get_msg() ) )
                    i_idx += 1

            except KeyError :
                print "[[[[ %s is not in INSTRUCTIONS_ACTIONS ]]]]" % i.get_name()
            except IndexError :
                print "[[[[ Analysis failed in %s-%s-%s ]]]]" % (self.__method.get_class_name(), self.__method.get_name(), self.__method.get_descriptor())

            idx += i.get_length()

            if self.__stack.nil() == True and i != self.ins[-1] :
                self.free_blocks_offsets.append( idx + self.get_start() )

    def show(self) :
        print "\t@", self.name

        idx = 0
        nb = 0
        for i in self.ins :
            print "\t\t", nb, idx,
            i.show(nb)
            nb += 1
            idx += i.get_length()

        print ""
        print "\t\tFree blocks offsets --->", self.free_blocks_offsets
        print "\t\tBreakBlocks --->", len(self.break_blocks)

        print "\t\tF --->", ', '.join( i[2].get_name() for i in self.fathers )
        print "\t\tC --->", ', '.join( i[2].get_name() for i in self.childs )

        self.stack_traces.show()

    def get_ins(self) :
        return self.ins

class JVMBreakBlock(BreakBlock) :
    def __init__(self, _vm, idx) :
        super(JVMBreakBlock, self).__init__(_vm, idx)

        self.__info = {
                          "F" : [ "get_field_descriptor", self._fields, ContextField ],
                          "M" : [ "get_method_descriptor", self._methods, ContextMethod ],
                      }


    def get_free(self) :
        if self._ins == [] :
            return False

        if "store" in self._ins[-1].get_name() :
            return True
        elif "putfield" in self._ins[-1].get_name() :
            return True

        return False

    def analyze(self) :
        ctt = []

        stack = Stack()
        for i in self._ins :
            v = self.trans(i)
            if v != None :
                ctt.append( v )

            t = ""

            for mre in jvm.MATH_JVM_RE :
                if mre[0].match( i.get_name() ) :
                    self._ops.append( mre[1] )
                    break

            # Woot it's a field !
            if i.get_name() in FIELDS :
                t = "F"
            elif i.get_name() in METHODS :
                t = "M"

            if t != "" :
                o = i.get_operands()
                desc = getattr(self._vm, self.__info[t][0])(o[0], o[1], o[2])

                # It's an external
                if desc == None :
                    desc = ExternalFM( o[0], o[1], o[2] )

                if desc not in self.__info[t][1] :
                    self.__info[t][1][desc] = []

                if t == "F" :
                    self.__info[t][1][desc].append( self.__info[t][2]( FIELDS[ i.get_name() ][0] ) )

#               print "RES", res, "-->", desc.get_name()
#               self.__tf.push_info( desc, [ FIELDS[ i.get_name() ][0], res ] )
                elif t == "M" :
                    self.__info[t][1][desc].append( self.__info[t][2]() )

        for i in self._fields :
            for k in self._fields[i] :
                k.set_details( ctt )

        for i in self._methods :
            for k in self._methods[i] :
                k.set_details( ctt )

    def trans(self, i) :
        v = i.get_name()[0:2]
        if v == "il" or v == "ic" or v == "ia" or v == "si" or v == "bi" :
            return "I"

        if v == "ba" :
            return "B"

        if v == "if" :
            return "IF"

        if v == "ir" :
            return "RET"

        if "and" in i.get_name() :
            return "&"

        if "add" in i.get_name() :
            return "+"

        if "sub" in i.get_name() :
            return "-"

        if "xor" in i.get_name() :
            return "^"

        if "ldc" in i.get_name() :
            return "I"

        if "invokevirtual" in i.get_name() :
            return "M" + i.get_operands()[2]

        if "getfield" in i.get_name() :
            return "F" + i.get_operands()[2]


DVM_FIELDS_ACCESS = {
      "iget" : "R",
      "iget-wide" : "R",
      "iget-object" : "R",
      "iget-boolean" : "R",
      "iget-byte" : "R",
      "iget-char" : "R",
      "iget-short" : "R",

      "iput" : "W",
      "iput-wide" : "W",
      "iput-object" : "W",
      "iput-boolean" : "W",
      "iput-byte" : "W",
      "iput-char" : "W",
      "iput-short" : "W",

      "sget" : "R",
      "sget-wide" : "R",
      "sget-object" : "R",
      "sget-boolean" : "R",
      "sget-byte" : "R",
      "sget-char" : "R",
      "sget-short" : "R",

      "sput" : "W",
      "sput-wide" : "W",
      "sput-object" : "W",
      "sput-boolean" : "W",
      "sput-byte" : "W",
      "sput-char" : "W",
      "sput-short" : "W",
   }

class DVMBasicBlock :
    def __init__(self, start, _vm, _method, _context) :
        self.__vm = _vm
        self.__method = _method
        self.__context = _context

        self.ins = []

        self.fathers = []
        self.childs = []

        self.start = start
        self.end = self.start

        self.break_blocks = []

        self.free_blocks_offsets = []

        self.name = "%s-BB@0x%x" % (self.__method.get_name(), self.start)

    def get_method(self) :
        return self.__method

    def get_name(self) :
        return self.name

    def get_start(self) :
        return self.start

    def get_end(self) :
        return self.end

    def get_last(self) :
        return self.ins[-1]

    def push(self, i) :
        self.ins.append( i )
        self.end += i.get_length()

    def set_fathers(self, f) :
        self.fathers.append( f )

    def set_childs(self, values) :
        #print self, self.start, self.end, values, self.ins[-1].get_name()
        if values == [] :
            next_block = self.__context.get_basic_block( self.end + 1 )
            if next_block != None :
                self.childs.append( ( self.end - self.ins[-1].get_length(), self.end, next_block ) )
        else :
            for i in values :
                if i != -1 :
                    next_block = self.__context.get_basic_block( i )
                    #FIXME
                    #print self, self.start, self.end, values, self.ins[-1].get_name()
                    #   raise("ooo")
                    if next_block != None :
                        self.childs.append( ( self.end - self.ins[-1].get_length(), i, next_block) )

        for c in self.childs :
            if c[2] != None :
                c[2].set_fathers( ( c[1], c[0], self ) )

    def analyze(self) :
        idx = 0
        for i in self.ins :
            if i.get_name() in DVM_FIELDS_ACCESS :
                o = i.get_operands()
                desc = self.__vm.get_class_manager().get_field(o[-1][1], True)
                if desc == None :
                    raise("oo")

                self.__context.get_tainted_variables().push_info( TAINTED_FIELD, desc, (DVM_FIELDS_ACCESS[ i.get_name() ][0], idx, self, self.__method) )
            elif "invoke" in i.get_name() :
                idx_meth = 0
                for op in i.get_operands() :
                    if op[0] == "meth@" :
                        idx_meth = op[1]
                        break

                method_info = self.__vm.get_class_manager().get_method( idx_meth )
                self.__context.get_tainted_packages()._push_info( method_info[0], (TAINTED_PACKAGE_CALL, idx, self, self.__method, method_info[2], method_info[1][0] + method_info[1][1]) )
            elif "new-instance" in i.get_name() :
                type_info = self.__vm.get_class_manager().get_type( i.get_operands()[-1][1] )
                self.__context.get_tainted_packages()._push_info( type_info, (TAINTED_PACKAGE_CREATE, idx, self, self.__method) )
            elif "const-string" in i.get_name() :
                string_name = self.__vm.get_class_manager().get_string( i.get_operands()[-1][1] )
                self.__context.get_tainted_variables().add( string_name, TAINTED_STRING )
                self.__context.get_tainted_variables().push_info( TAINTED_STRING, string_name, ("R", idx, self, self.__method) )

            idx += i.get_length()

    def analyze_code(self) :
        pass

    def get_ins(self) :
        return self.ins

TAINTED_LOCAL_VARIABLE = 0
TAINTED_FIELD = 1
TAINTED_STRING = 2
class Path :
    def __init__(self, info) :
        self.access_flag = info[0]
        self.idx = info[1]
        self.bb = info[2]
        self.method = info[3]

    def get_access_flag(self) :
        return self.access_flag

    def get_idx(self) :
        return self.idx

    def get_bb(self) :
        return self.bb

    def get_method(self) :
        return self.method

class TaintedVariable :
    def __init__(self, var, _type) :
        self.var = var
        self.type = _type

        self.paths = []

    def get_type(self) :
        return self.type

    def get_info(self) :
        if self.type == TAINTED_FIELD :
            return [ self.var.get_class_name(), self.var.get_name(), self.var.get_descriptor() ]
        return self.var

    def push(self, info) :
        p = Path( info )
        self.paths.append( p )
        return p

    def get_paths_access(self, mode) :
        for i in self.paths :
            if i.get_access_flag() in mode :
                yield i

    def get_paths(self) :
        for i in self.paths :
            yield i

    def get_paths_length(self) :
        return len(self.paths)

    def show_paths(self) :
        for path in self.paths :
            print path.get_access_flag(), path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), path.get_bb().get_name(), "%x" % (path.get_bb().start + path.get_idx() )

class TaintedVariables :
    def __init__(self, _vm) :
        self.__vm = _vm
        self.__vars = {
           TAINTED_LOCAL_VARIABLE : {},
           TAINTED_FIELD : {},
           TAINTED_STRING : {},
        }

        self.__methods = {
           TAINTED_FIELD : {},
           TAINTED_STRING : {},
        }

    # functions to get particulars elements

    def get_string(self, s) :
        try :
            return self.__vars[ TAINTED_STRING ][ s ]
        except KeyError :
            return None

    def get_field(self, class_name, name, descriptor) :
        for i in self.__vars[ TAINTED_FIELD ] :
            if i.get_class_name() == class_name and i.get_name() == name and i.get_descriptor() == descriptor :
                return self.__vars[ TAINTED_FIELD ] [i]
        return None


    def get_field_by_ref(self, ref) :
        for i in self.__vars[ TAINTED_FIELD ] :
            if i.get_class_name() == ref.get_class_name() and i.get_name() == ref.get_name() and i.get_descriptor() == ref.get_descriptor() :
                return self.__vars[ TAINTED_FIELD ] [i]
        return None

    # global functions

    def get_strings(self) :
        for i in self.__vars[ TAINTED_STRING ] :
            yield self.__vars[ TAINTED_STRING ][ i ], i

    def get_fields(self) :
        for i in self.__vars[ TAINTED_FIELD ] :
            yield self.__vars[ TAINTED_FIELD ][ i ], i

    # specifics functions

    def get_strings_by_method(self, method) :
        try :
            return self.__methods[ TAINTED_STRING ][ method ]
        except KeyError :
            return {}

    def get_fields_by_method(self, method) :
        try :
            return self.__methods[ TAINTED_FIELD ][ method ]
        except KeyError :
            return {}

    def get_local_variables(self, _method) :
        try :
            return self.__vars[ TAINTED_LOCAL_VARIABLE ][ _method ]
        except KeyError :
            return None

    def get_fields_by_bb(self, bb) :
        l = []
        for i in self.__vars[ TAINTED_FIELD ] :
            for j in self.__vars[ TAINTED_FIELD ][i].gets() :
                if j.get_bb() == bb :
                    l.append( (i.get_name(), j.get_access_flag()) )
        return l

    def add(self, var, _type, _method=None) :
        if _type == TAINTED_FIELD :
            if var not in self.__vars[ TAINTED_FIELD ] :
                self.__vars[ TAINTED_FIELD ][ var ] = TaintedVariable( var, _type )
        elif _type == TAINTED_STRING :
            if var not in self.__vars[ TAINTED_STRING ] :
                self.__vars[ TAINTED_STRING ][ var ] = TaintedVariable( var, _type )
        elif _type == TAINTED_LOCAL_VARIABLE :
            if _method not in self.__vars[ TAINTED_LOCAL_VARIABLE ] :
                self.__vars[ TAINTED_LOCAL_VARIABLE ][ _method ] = {}

            if var not in self.__vars[ TAINTED_LOCAL_VARIABLE ][ _method ] :
                self.__vars[ TAINTED_LOCAL_VARIABLE ][ _method ][ var ] = TaintedVariable( var, _type )
        else :
            raise("ooop")

    def push_info(self, _type, var, info) :
        if _type == TAINTED_FIELD or _type == TAINTED_STRING :
            self.add( var, _type )
            p = self.__vars[ _type ][ var ].push( info )

            try :
                self.__methods[ _type ][ p.get_method() ][ var ].append( p )
            except KeyError :
                try :
                    self.__methods[ _type ][ p.get_method() ][ var ] = []
                except KeyError :
                    self.__methods[ _type ][ p.get_method() ] = {}
                    self.__methods[ _type ][ p.get_method() ][ var ] = []

                self.__methods[ _type ][ p.get_method() ][ var ].append( p )

        elif _type == TAINTED_LOCAL_VARIABLE :
            self.add( var, _type, info[-1] )
            self.__vars[ TAINTED_LOCAL_VARIABLE ][ info[-1] ][ var ].push( info )
        else :
            raise("ooop")

class PathI(Path) :
    def __init__(self, info) :
        Path.__init__( self, info )
        self.value = info[0]

    def get_value(self) :
        return self.value

class TaintedInteger :
    def __init__(self, info) :
        self.info = PathI( info )

    def get(self) :
        return self.info

class TaintedIntegers :
    def __init__(self, _vm) :
        self.__vm = _vm
        self.__integers = []
        self.__hash = {}

    def get_method(self, method) :
        try :
            return self.__hash[ method ]
        except KeyError :
            return []

    def push_info(self, ins, info) :
        #print ins, ins.get_name(), ins.get_operands(), info

        ti = TaintedInteger( info )
        self.__integers.append( ti )

        try :
            self.__hash[ info[-1] ].append( ti )
        except KeyError :
            self.__hash[ info[-1] ] = []
            self.__hash[ info[-1] ].append( ti )

    def get_integers(self) :
        for i in self.__integers :
            yield i

TAINTED_PACKAGE_CREATE = 0
TAINTED_PACKAGE_CALL = 1

TAINTED_PACKAGE = {
   TAINTED_PACKAGE_CREATE : "C",
   TAINTED_PACKAGE_CALL : "M"
}

def show_PathP(paths) :
    for path in paths :
        print "%s %s %s (@%s-0x%x)  ---> %s %s %s" % (path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), \
                                                      path.get_bb().get_name(), path.get_bb().start + path.get_idx(), \
                                                      path.get_class_name(), path.get_name(), path.get_descriptor())

class PathP(Path) :
    def __init__(self, info, class_name) :
        Path.__init__( self, info )
        self.class_name = class_name
        if info[0] == TAINTED_PACKAGE_CALL :
            self.name = info[-2]
            self.descriptor = info[-1]

    def get_class_name(self) :
        return self.class_name

    def get_name(self) :
        return self.name

    def get_descriptor(self) :
        return self.descriptor

class TaintedPackage :
    def __init__(self, name) :
        self.name = name
        self.paths = { TAINTED_PACKAGE_CREATE : [], TAINTED_PACKAGE_CALL : [] }

    def get_name(self) :
        return self.name

    # FIXME : remote it to use get_name
    def get_info(self) :
        return self.name

    def gets(self) :
        return self.paths

    def push(self, info) :
        p = PathP( info, self.get_name() )
        self.paths[ info[0] ].append( p )
        return p

    def search_method(self, name, descriptor) :
        """
            @param name : a regexp for the name of the method
            @param descriptor : a regexp for the descriptor of the method

            @rtype : a list of called paths
        """
        l = []
        m_name = re.compile(name)
        m_descriptor = re.compile(descriptor)
        
        for path in self.paths[ TAINTED_PACKAGE_CALL ] :
            if m_name.match( path.get_name() ) != None and m_descriptor.match( path.get_descriptor() ) != None :
                l.append( path )
        return l

    def get_method(self, name, descriptor) :
        l = []
        for path in self.paths[ TAINTED_PACKAGE_CALL ] :
            if path.get_name() == name and path.get_descriptor() == descriptor :
                l.append( path )
        return l

    def get_paths(self) :
        for i in self.paths :
            for j in self.paths[ i ] :
                yield j

    def get_paths_length(self) :
        x = 0
        for i in self.paths :
            x += len(self.paths[ i ])
        return x

    def get_methods(self) :
        return [ path for path in self.paths[ TAINTED_PACKAGE_CALL ] ]

    def show(self, format) :
        print self.name
        for _type in self.paths :
            print "\t -->", _type
            if _type == TAINTED_PACKAGE_CALL :
                for path in sorted(self.paths[ _type ], key=lambda x: getattr(x, format)()) :
                    print "\t\t => %s %s <-- %s@%x in %s" % (path.get_name(), path.get_descriptor(), path.get_bb().get_name(), path.get_idx(), path.get_method().get_name())
            else :
                for path in self.paths[ _type ] :
                    print "\t\t => %s@%x in %s" % (path.get_bb().get_name(), path.get_idx(), path.get_method().get_name())

class TaintedPackages :
    def __init__(self, _vm) :
        self.__vm = _vm
        self.__packages = {}
        self.__methods = {}

    def _add_pkg(self, name) :
        if name not in self.__packages :
            self.__packages[ name ] = TaintedPackage( name )

    def _push_info(self, class_name, info) :
        self._add_pkg( class_name )
        p = self.__packages[ class_name ].push( info )

        try :
            self.__methods[ p.get_method() ][ class_name ].append( p )
        except :
            try :
                self.__methods[ p.get_method() ][ class_name ] = []
            except :
                self.__methods[ p.get_method() ] = {}
                self.__methods[ p.get_method() ][ class_name ] = []

            self.__methods[ p.get_method() ][ class_name ].append( p )

    def get_packages_by_method(self, method) :
        try :
            return self.__methods[ method ]
        except KeyError :
            return {}

    def get_packages_by_bb(self, bb):
        """
            @rtype : return a list of packaged used in a basic block
        """
        l = []
        for i in self.__packages :
            paths = self.__packages[i].gets()
            for j in paths :
                for k in paths[j] :
                    if k.get_bb() == bb :
                        l.append( (i, k.get_access_flag(), k.get_idx(), k.get_method()) )

        return l

    def get_packages(self) :
        for i in self.__packages :
            yield self.__packages[ i ], i

    def get_internal_packages(self) :
        """
            @rtype : return a list of the internal packages called in the application
        """
        classes = self.__vm.get_classes_names()
        l = []
        for m, _ in self.get_packages() :
            paths = m.get_methods()
            for j in paths :
                if j.get_method().get_class_name() in classes and m.get_info() in classes :
                    if j.get_access_flag() == TAINTED_PACKAGE_CALL :
                        l.append( j )
        return l
       
    def get_external_packages(self) :
        """
        @rtype : return a list of the external packages called in the application
        """
        classes = self.__vm.get_classes_names()
        l = []
        for m, _ in self.get_packages() :
            paths = m.get_methods()
            for j in paths :
                if j.get_method().get_class_name() in classes and m.get_info() not in classes :
                    if j.get_access_flag() == TAINTED_PACKAGE_CALL :
                        l.append( j )
        return l

    def search_packages(self, package_name) :
        """
            @param package_name : a regexp for the name of the package
        
            @rtype : a list of called packages' paths
        """
        ex = re.compile( package_name )
    
        l = []
        for m, _ in self.get_packages() :
            if ex.match( m.get_info() ) != None :
                l.extend( m.get_methods() )
        return l

    def search_methods(self, class_name, name, descriptor) :
        """
            @param class_name : a regexp for the class name of the method (the package)
            @param name : a regexp for the name of the method
            @param descriptor : a regexp for the descriptor of the method

            @rtype : a list of called methods' paths
        """
        ex = re.compile( class_name )
        l = []

        for m, _ in self.get_packages() :
            if ex.match( m.get_info() ) != None :
                l.extend( m.search_method( name, descriptor ) )
        return l

    def search_crypto_packages(self) :
        """
            @rtype : a list of called crypto packages
        """
        return self.search_packages( "Ljavax/crypto/" )

    def search_telephony_packages(self) :
        """
            @rtype : a list of called telephony packages
        """
        return self.search_packages( "Landroid/telephony/" )

    def search_net_packages(self) :
        """
            @rtype : a list of called net packages 
        """
        return self.search_packages( "Landroid/net/" )

    def get_method(self, class_name, name, descriptor) :
        try :
            return self.__packages[ class_name ].get_method( name, descriptor )
        except KeyError :
            return []

    def get_permissions(self, permissions_needed) :
        """
            @param permissions_needed : a list of restricted permissions to get ([] returns all permissions)
            
            @rtype : a dictionnary of permissions' paths
        """
        permissions = {}

        pn = permissions_needed
        if permissions_needed == [] :
            pn = DVM_PERMISSIONS_BY_PERMISSION.keys()

        classes = self.__vm.get_classes_names()

        for m, _ in self.get_packages() :
            paths = m.get_methods()
            for j in paths :
                if j.get_method().get_class_name() in classes and m.get_info() not in classes :
                    if j.get_access_flag() == TAINTED_PACKAGE_CALL :
                        data = "%s-%s-%s" % (m.get_info(), j.get_name(), j.get_descriptor())
                        if data in DVM_PERMISSIONS_BY_ELEMENT :
                            if DVM_PERMISSIONS_BY_ELEMENT[ data ] in pn :
                                try :
                                    permissions[ DVM_PERMISSIONS_BY_ELEMENT[ data ] ].append( j )
                                except KeyError :
                                    permissions[ DVM_PERMISSIONS_BY_ELEMENT[ data ] ] = []
                                    permissions[ DVM_PERMISSIONS_BY_ELEMENT[ data ] ].append( j )

        return permissions

class BasicBlocks :
    def __init__(self, _vm, _tv) :
        self.__vm = _vm
        self.__tainted = _tv

        self.bb = []

    def push(self, bb):
        self.bb.append( bb )

    def pop(self, idx) :
        return self.bb.pop( idx )

    def get_basic_block(self, idx) :
        for i in self.bb :
            if idx >= i.get_start() and idx < i.get_end() :
                return i
        return None

    def get_tainted_integers(self) :
        return self.__tainted["integers"]

    def get_tainted_packages(self) :
        return self.__tainted["packages"]

    def get_tainted_variables(self) :
        return self.__tainted["variables"]

    def get_random(self) :
        """
            @rtype : return a random basic block
        """
        return self.bb[ random.randint(0, len(self.bb) - 1) ]

    def get(self) :
        """
            @rtype : return each basic block
        """
        for i in self.bb :
            yield i

    def gets(self) :
        """
            @rtype : a list of basic blocks
        """
        return self.bb

class MethodAnalysis :
    """
       This class analyses in details a method of a class/dex file
    """
    def __init__(self, _vm, _method, _tv, code_analysis=False) :
        """
            @param _vm :  a L{JVMFormat} or L{DalvikVMFormat} object
            @param _method : a method object
            @param tv : a dictionnary of tainted information
        """
        self.__vm = _vm
        self.__method = _method

        self.__tainted = _tv

        BO = { "BasicOPCODES" : jvm.BRANCH2_JVM_OPCODES, "BasicClass" : JVMBasicBlock, "Dnext" : jvm.determineNext,
               "TS" : JVM_TOSTRING }
        if self.__vm.get_type() == "DVM" :
            BO = { "BasicOPCODES" : dvm.BRANCH_DVM_OPCODES, "BasicClass" : DVMBasicBlock, "Dnext" : dvm.determineNext,
                   "TS" : DVM_TOSTRING }

        self.__TS = ToString( BO[ "TS" ] )

        BO["BasicOPCODES_H"] = []
        for i in BO["BasicOPCODES"] :
            BO["BasicOPCODES_H"].append( re.compile( i ) )

        self.basic_blocks = BasicBlocks( self.__vm, self.__tainted )

        code = self.__method.get_code()
        if code == None :
            return

        current_basic = BO["BasicClass"]( 0, self.__vm, self.__method, self.basic_blocks )
        self.basic_blocks.push( current_basic )

        ##########################################################

        bc = code.get_bc()
        l = []
        h = {}
        idx = 0
        for i in bc.get() :
            for j in BO["BasicOPCODES_H"] :
                if j.match(i.get_name()) != None :
                    v = BO["Dnext"]( i, idx, self.__method )
                    h[ idx ] = v
                    l.extend( v )
                    break

            idx += i.get_length()

    #   print self.__method.get_name(), sorted(l), h
        idx = 0
        for i in bc.get() :
            name = i.get_name()

            self.__TS.push( name )

            here = False
            # index is a destination
            if idx in l :
                if current_basic.ins != [] :
                    current_basic = BO["BasicClass"]( current_basic.get_end(), self.__vm, self.__method, self.basic_blocks )
                    self.basic_blocks.push( current_basic )
                here = True

            current_basic.push( i )

            # index is a branch instruction
            if idx in h : #and here == False :
                current_basic = BO["BasicClass"]( current_basic.get_end(), self.__vm, self.__method, self.basic_blocks )
                self.basic_blocks.push( current_basic )

            idx += i.get_length()


        if current_basic.ins == [] :
            self.basic_blocks.pop( -1 )

        for i in self.basic_blocks.get() :
            try :
                i.set_childs( h[ i.end - i.ins[-1].get_length() ] )
            except KeyError :
                i.set_childs( [] )


        for i in self.basic_blocks.get() :
            i.analyze()

        if code_analysis == True :
            for i in self.basic_blocks.get() :
                i.analyze_code()

    def get_length(self) :
        """
            @rtype : an integer which is the length of the code
        """
        return self.get_code().get_length()

    def prev_free_block_offset(self, idx=0) :
        l = []
        for i in self.basic_blocks.get() :
            if i.get_start() <= idx :
                l.append( i )

        l.reverse()
        for i in l :
            x = i.prev_free_block_offset( idx )
            if x != -1 :
                return x
        return -1

    def random_free_block_offset(self) :
        b = self.basic_blocks.get_random()
        x = b.random_free_block_offset()
        return x

    def next_free_block_offset(self, idx=0) :
        for i in self.basic_blocks.get() :
            x = i.next_free_block_offset( idx )
            if x != -1 :
                return x
        return -1

    def get_break_block(self, idx) :
        for i in self.basic_blocks.get() :
            if idx >= i.get_start() and idx <= i.get_end() :
                return i.get_break_block( idx )
        return None

    def get_ts(self) :
        return self.__TS.get_string()

    def get_vm(self) :
        return self.__vm

    def get_method(self) :
        return self.__method

    def get_op(self, op) :
        return []

    def get_local_variables(self) :
        return self.__tainted["variables"].get_local_variables( self.__method )

    def get_ops(self) :
        l = []
        for i in self.__bb :
            for j in i.get_ops() :
                l.append( j )
        return l

    def show(self) :
        print "METHOD", self.__method.get_class_name(), self.__method.get_name(), self.__method.get_descriptor()
        print "\tTOSTRING = ", self.__TS.get_string()

        for i in self.basic_blocks.get() :
            print "\t", i
            i.show()
            print ""

    def show_methods(self) :
        print "\t #METHODS :"
        l = []
        for i in self.__bb :
            methods = i.get_methods()
            for method in methods :
                print "\t\t-->", method.get_class_name(), method.get_name(), method.get_descriptor()
                for context in methods[method] :
                    print "\t\t\t |---|", context.details

SIGNATURE_L0_0 = "L0_0"
SIGNATURE_L0_1 = "L0_1"
SIGNATURE_L0_2 = "L0_2"
SIGNATURE_L0_3 = "L0_3"
SIGNATURE_L0_4 = "L0_4" 
SIGNATURE_L0_5 = "L0_5"
SIGNATURE_L0_6 = "L0_6"
SIGNATURE_L0_0_L1 = "L0_0:L1"
SIGNATURE_L0_1_L1 = "L0_1:L1"
SIGNATURE_L0_2_L1 = "L0_2:L1"
SIGNATURE_L0_3_L1 = "L0_3:L1"
SIGNATURE_L0_4_L1 = "L0_4:L1"
SIGNATURE_L0_5_L1 = "L0_5:L1"
SIGNATURE_L0_0_L2 = "L0_0:L2"
SIGNATURE_L0_0_L3 = "L0_0:L3"

SIGNATURES = {
                SIGNATURE_L0_0 : { "type" : 0 },
                SIGNATURE_L0_1 : { "type" : 1 },
                SIGNATURE_L0_2 : { "type" : 2, "arguments" : ["Landroid"] },
                SIGNATURE_L0_3 : { "type" : 2, "arguments" : ["Ljava"] },
                SIGNATURE_L0_4 : { "type" : 2, "arguments" : ["Landroid", "Ljava"] },
                SIGNATURE_L0_5 : { "type" : 3, "arguments" : ["Landroid"] },
                SIGNATURE_L0_6 : { "type" : 3, "arguments" : ["Ljava"] },
            }

from sign import Signature

class VMAnalysis :
    """
       This class analyses a class file or a dex file

       @param _vm : a virtual machine object
    """
    def __init__(self, _vm, code_analysis=False) :
        """
            @param _vm : a L{JVMFormat} or L{DalvikFormatVM}
            @param code_analysis : True if you would like to do an advanced analyse of the code (e.g : to search free offset to insert codes
        """

        self.__vm = _vm

        self.tainted_variables = TaintedVariables( self.__vm )
        self.tainted_packages = TaintedPackages( self.__vm )
        self.tainted_integers = TaintedIntegers( self.__vm )

        self.tainted = { "variables" : self.tainted_variables,
                         "packages" : self.tainted_packages,
                         "integers" : self.tainted_integers,
                       }

        self.signature = Signature( self.tainted )

        for i in self.__vm.get_all_fields() :
            self.tainted_variables.add( i, TAINTED_FIELD )

        self.methods = []
        self.hmethods = {}
        self.__nmethods = {}
        for i in self.__vm.get_methods() :
            x = MethodAnalysis( self.__vm, i, self.tainted, code_analysis )
            self.methods.append( x )
            self.hmethods[ i ] = x
            self.__nmethods[ i.get_name() ] = x

    def get_method(self, method) :
        """
            Return an analysis method

            @param method : a classical method object
            @rtype : L{MethodAnalysis}
        """
        return self.hmethods[ method ]

    # FIXME
    def get_like_field(self) :
        return [ random.choice( string.letters ) + ''.join([ random.choice(string.letters + string.digits) for i in range(10 - 1) ]),
                 "ACC_PUBLIC",
                 "I"
               ]

    # FIXME
    def get_init_method(self) :
        m = self.__vm.get_method("<init>")
        return m[0]

    # FIXME
    def get_random_integer_value(self, method, descriptor) :
        return 0

    def prev_free_block_offset(self, method, idx=0) :
        """
           Find the previous offset where you can insert a block

           @param method : a reference of a method object where you would like the offset
           @param idx : the index to start the research

           @rtype : return -1 if an error occured, otherwise the offset
        """
        # We would like a specific free offset in a method
        try :
            return self.hmethods[ method ].prev_free_block_offset( idx )
        except KeyError :
            # We haven't found the method ...
            return -1

    def random_free_block_offset(self, method) :
        """
           Find a random offset where you can insert a block

           @param method : a reference of method object or a string which represents a regexp

           @rtype : return -1 if an error occured, otherwise the offset
        """
        if isinstance(method, str) :
            p = re.compile(method)
            for i in self.hmethods :
                if random.randint(0, 1) == 1 :
                    if p.match( i.get_name() ) == None :
                        return i, self.hmethods[i].random_free_block_offset()

            for i in self.hmethods :
                if p.match( i.get_name() ) == None :
                    return i, self.hmethods[i].random_free_block_offset()

        # We would like a specific free offset in a method
        try :
            return self.hmethods[ method ].random_free_block_offset()
        except KeyError :
            # We haven't found the method ...
            return -1

    def next_free_block_offset(self, method, idx=0) :
        """
           Find the next offset where you can insert a block

           @param method : a reference of a method object where you would like the offset
           @param idx : the index to start the research

           @rtype : return -1 if an error occured, otherwise the offset
        """
        # We would like a specific free offset in a method
        try :
            return self.hmethods[ method ].next_free_block_offset( idx )
        except KeyError :
            # We haven't found the method ...
            return -1

    def get_tainted_variables(self) :
        """
           Return the tainted variables

           @rtype : L{TaintedVariables}
        """
        return self.tainted_variables

    def get_tainted_packages(self) :
        """
           Return the tainted packages

           @rtype : L{TaintedPackages}
        """
        return self.tainted_packages

    def get_tainted_field(self, class_name, name, descriptor) :
        """
           Return a specific tainted field

           @param class_name : the name of the class
           @param name : the name of the field
           @param descriptor : the descriptor of the field

           @rtype : L{TaintedVariable}
        """
        return self.tainted_variables.get_field( class_name, name, descriptor )

    def get_methods(self) :
        """
           Return each analysis method

           @rtype : L{MethodAnalysis}
        """
        for i in self.hmethods :
            yield self.hmethods[i]

    def get_method_signature(self, method, grammar_type="", options={}, predef_sign="") :
        """
            Return a specific signature for a specific method
            
            @param method : a reference to method from a vm class
            @param grammar_type : the type of the signature
            @param options : the options of the signature
            @param predef_sign : used a predefined signature

            @rtype : L{Sign}
        """
        if predef_sign != "" :
            g = ""
            o = {} 

            for i in predef_sign.split(":") :
                if "_" in i :
                    g += "L0:"
                    o[ "L0" ] = SIGNATURES[ i ]
                else :
                    g += i
                    g += ":" 
            
            return self.signature.get_method( self.get_method( method ), g[:-1], o )
        else : 
            return self.signature.get_method( self.get_method( method ), grammar_type, options )


    # FIXME
    def get_op(self, op) :
        return [ (i.get_method(), i.get_op(op)) for i in self.l ]

    # FIXME
    def get_ops(self, method) :
        return [ (i.get_method(), i.get_ops()) for i in self.l ]
