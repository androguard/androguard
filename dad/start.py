#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
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

import sys
sys.path.append('./')
import androguard
import analysis
import Structure
import Util
import copy


class This():
    def __init__(self, cls):
        self.cls = cls
        self.used = False
        self.content = self

    def get_type(self):
        return self.cls.name

    def value(self):
        return 'this'

    def get_name(self):
        return 'this'


class Var():
    def __init__(self, name, typeDesc, type, size, content):
        self.name = name
        self.type = type
        self.size = size
        self.content = content
        self.param = False
        self.typeDesc = typeDesc
        self.used = 0
    
    def get_content(self):
        return self.content

    def get_type(self):
        return self.typeDesc

    def init(self):
        if self.typeDesc == 'Z':
            return '%s = %s;\n' % (self.decl(),
                                  ['false', 'true'][self.content])
        if self.typeDesc in Util.TYPE_DESCRIPTOR:
            return '%s = %s;\n' % (self.decl(), self.content)
        return '%s %s = %s;\n' % (self.type, self.name, self.content.value())

    def value(self):
        if self.used < 1 and self.typeDesc in Util.TYPE_DESCRIPTOR:
            return self.name
        if self.content is not None:
            return self.content.value()
        self.used += 1
        return self.name

    def int_value(self):
        return self.content.int_value()

    def get_name(self):
        if self.type is 'void':
            return self.content.value()
        self.used += 1
        return self.name

    def neg(self):
        return self.content.neg()

    def dump(self, indent):
        if str(self.content.value()).startswith('ret'):
            return '   ' * indent + self.content.value() + ';\n'
            #return '   ' * indent + self.content.value() + ';(%d)\n' % self.used

        #if self.type is 'void':
        #    if self.content.value() != 'this':
        #        return '   ' * indent + '%s;(%d)\n' % (self.content.value(), self.used)
        #    return ''

        return '   ' * indent + '%s %s = %s;\n' % (self.type, self.name,
                                                   self.content.value())

        #return '   ' * indent + '%s %s = %s;(%d)\n' % (self.type, self.name,
        #                        self.content.value(), self.used)
    
    def decl(self):
        return '%s %s' % (self.type, self.name)
     
    def __repr__(self):
        if self.content:
            return 'var(%s==%s==%s)' % (self.type, self.name, self.content)
        return 'var(%s===%s)' % (self.type, self.name)


class Variable():
    def __init__(self):
        self.nbVars = {}
        self.vars = []

    def newVar(self, typeDesc, content=None):
        n = self.nbVars.setdefault(typeDesc, 1)
        self.nbVars[typeDesc] += 1
        size = Util.get_type_size(typeDesc)
        _type = Util.get_type(typeDesc)
        if _type:
            type = _type.split('.')[-1]
        Util.log('typeDesc : %s' % typeDesc, 'debug')
        if type.endswith('[]'):
            name = '%sArray%d' % (type.strip('[]'), n)
        else:
            name = '%sVar%d' % (type, n)
        var = Var(name, typeDesc, type, size, content)
        self.vars.append(var)
        return var

    def startBlock(self):
        self.varscopy = copy.deepcopy(self.nbVars)

    def endBlock(self):
        self.nbVars = self.varscopy


class DvMethod():
    def __init__(self, methanalysis, this):
        self.memory = {}
        self.method = methanalysis.get_method()
        self.name = self.method.get_name()
        self.lparams = []
        self.variables = Variable()
        self.tabsymb = {}
        
        if self.name == '<init>':
            self.name = self.method.get_class_name()[1:-1].split('/')[-1]
        self.basic_blocks = methanalysis.basic_blocks.bb
        code = self.method.get_code()

        access = self.method.get_access()
        self.access = [flag for flag in Util.ACCESS_FLAGS_METHODS
                                     if flag & access]
        desc = self.method.get_descriptor()
        self.type = Util.get_type(desc.split(')')[-1])
        self.paramsType = Util.get_params_type(desc)

        Util.log('Searching loops in method %s' % self.name, 'debug')
        
        exceptions = methanalysis.exceptions.exceptions
        Util.log('METHOD : %s' % self.name, 'debug')
        #print "excepts :", [ e.exceptions for e in exceptions ]
        self.graph = Structure.ConstructAST(self.basic_blocks, exceptions)

        #androguard.bytecode.method2png('graphs/%s#%s.png' % \
        #        (self.method.get_class_name().split('/')[-1][:-1], self.name),
        #                                                         methanalysis)

        if code is None:
            Util.log('CODE NONE : %s %s' % (self.name,
                                            self.method.get_class_name()),
                                            'debug')
        else:
            start = code.registers_size.get_value() - code.ins_size.get_value()
            # 0x8 == Static : 'this' is not passed as a parameter
            if 0x8 in self.access:
                self._add_parameters(start)
            else:
                self.memory[start] = this
                self._add_parameters(start + 1)
        self.ins = []
        self.cur = 0

    def _add_parameters(self, start):
        size = 0
        for paramType in self.paramsType:
            param = self.variables.newVar(paramType)
            self.tabsymb[param.get_name()] = param
            param.param = True
            self.memory[start + size] = param
            self.lparams.append(param)
            size += param.size

    def process(self):
        if self.graph is None: return
        Util.log('METHOD : %s' % self.name, 'debug')
        Util.log('Processing %s' % self.graph.first_node(), 'debug')
        node = self.graph.first_node()
        blockins = node.process(self.memory, self.tabsymb, self.variables,
                                0, None, None)
        if blockins:
            self.ins.append(blockins)

    def debug(self, code=None):
        if code is None:
            code = []
        Util.log('Dump of method :', 'debug')
        for j in self.memory.values():
            Util.log(j, 'debug')
        Util.log('Dump of ins :', 'debug')
        acc = []
        for i in self.access:
            if i == 0x10000:
                self.type = None
            else:
                acc.append(Util.ACCESS_FLAGS_METHODS.get(i))
        if self.type:
            proto = '    %s %s %s(' % (' '.join(acc), self.type, self.name)
        else:
            proto = '    %s %s(' % (' '.join(acc), self.name)
        if self.paramsType:
            proto += ', '.join(['%s' % param.decl() for param in self.lparams])
        proto += ')\n    {\n'
#        for _, v in sorted(self.tabsymb.iteritems(), key=lambda x: x[0]):
#            if not (v in self.lparams):
#                proto += '%s%s' % ('   ' * 2, v.init())
        Util.log(proto, 'debug')
        code.append(proto)
        for i in self.ins:
            Util.log('%s' % i, 'debug')
            code.append(''.join(['   ' * 2 + '%s\n' % ii for ii in
                                                            i.splitlines()]))
        Util.log('}', 'debug')
        code.append('    }')
        return ''.join(code)

    def __repr__(self):
        return 'Method %s' % self.name


class DvClass():
    def __init__(self, dvclass, bca):
        self.name = dvclass.get_name()
        self.package = dvclass.get_name().rsplit('/', 1)[0][1:].replace('/',
                                                                        '.')
        self.this = This(self)
        lmethods = [(method.get_idx(), DvMethod(bca.get_method(method),
                       self.this)) for method in dvclass.get_methods()]
        self.methods = dict(lmethods)
        self.fields = {}
        for field in dvclass.get_fields():
            self.fields[field.get_name()] = field
        self.access = []
        self.prototype = None
        self.subclasses = {}
        self.code = []
        self.inner = False

        Util.log('Class : %s' % self.name, 'log')
        Util.log('Methods added :', 'log')
        for index, meth in self.methods.iteritems():
            Util.log('%s (%s, %s)' % (index, meth.method.get_class_name(),
                                   meth.name), 'log')
        Util.log('\n', 'log')

        access = dvclass.format.get_value().access_flags
        access = [flag for flag in Util.ACCESS_FLAGS_CLASSES if flag & access]
        for i in access:
            self.access.append(Util.ACCESS_FLAGS_CLASSES.get(i))
        
        self.prototype = '%s class %s' % (' '.join(self.access), self.name)
        
        self.interfaces = dvclass._interfaces
        self.superclass = dvclass._sname

    def add_subclass(self, innername, dvclass):
        self.subclasses[innername] = dvclass
        dvclass.inner = True

    def get_methods(self):
        meths = copy.copy(self.methods)
        for cls in self.subclasses.values():
            meths.update(cls.get_methods())
        return meths

    def select_meth(self, nb):
        if nb in self.methods:
            self.methods[nb].process()
            self.code.append(self.methods[nb].debug())
        elif self.subclasses.values():
            for cls in self.subclasses.values():
                cls.select_meth(nb)
        else:
            Util.log('Method %s not found.' % nb, 'error')

    def show_code(self):
        if not self.inner and self.package:
            Util.log('package %s;\n' % self.package, 'log')

        if self.superclass is not None:
            self.superclass = self.superclass[1:-1].replace('/', '.')
            if self.superclass.split('.')[-1] == 'Object':
                self.superclass = None
            if self.superclass is not None:
                self.prototype += ' extends %s' % self.superclass
        if self.interfaces is not None:
            self.interfaces = self.interfaces[1:-1].split(' ')
            self.prototype += ' implements %s' % ', '.join(
                        [n[1:-1].replace('/', '.') for n in self.interfaces])

        Util.log('%s {' % self.prototype, 'log')
        for field in self.fields.values():
            access =  [Util.ACCESS_FLAGS_FIELDS.get(flag) for flag in
                        Util.ACCESS_FLAGS_FIELDS if flag & field.get_access()]
            type = Util.get_type(field.get_descriptor())
            name = field.get_name()
            Util.log('\t%s %s %s;' % (' '.join(access), type, name), 'log')

        Util.log('', 'log')
        for cls in self.subclasses.values():
            cls.show_code()

        for ins in self.code:
            Util.log(ins, 'log')
        Util.log('}', 'log')

    def process(self):
        Util.log('SUBCLASSES : %s' % self.subclasses, 'debug')
        for cls in self.subclasses.values():
            cls.process()
        Util.log('METHODS : %s' % self.methods, 'debug')
        for meth in self.methods:
            self.select_meth(meth)

    def __str__(self):
        return 'Class name : %s.' % self.name

    def __repr__(self):
        if self.subclasses == {}:
            return 'Class(%s)' % self.name
        return 'Class(%s) -- Subclasses(%s)' % (self.name, self.subclasses)


class DvMachine():
    def __init__(self, name):
        vm = androguard.AndroguardS(name).get_vm()
        bca = analysis.VMAnalysis(vm)
        self.vm = vm
        self.bca = bca
        ldict = [(dvclass.get_name(), DvClass(dvclass, bca))
                 for dvclass in vm.get_classes()]
        self.classes = dict(ldict)
        Util.merge_inner(self.classes)

    def get_class(self, className):
        for name, cls in self.classes.iteritems():
            if className in name:
                return cls

    def process_class(self, cls):
        if cls is None:
            Util.log('No class to process.', 'error')
        else:
            cls.process()

    def process_method(self, cls, meth):
        if cls is None:
            Util.log('No class to process.', 'error')
        else:
            cls.select_meth(meth)

    def show_code(self, cls):
        if cls is None:
            Util.log('Class not found.', 'error')
        else:
            cls.show_code()


if __name__ == '__main__':
    Util.DEBUG_LEVEL = 'debug'

#    MACHINE = DvMachine('examples/android/TestsAndroguard/bin/classes.dex')
    MACHINE = DvMachine('examples/android/TestsAndroguard/bin/droiddream.dex')

    from pprint import pprint
    temp = Util.wrap_stream()
    Util.log('===========================', 'log')
    Util.log('dvclass.get_Classes :', 'log')
    pprint(MACHINE.classes, temp)
    Util.log(temp, 'log')
    Util.log('===========================', 'log')

    CLS = raw_input('Choose a class: ')
    if CLS == '*':
        for CLS in MACHINE.classes:
            Util.log('CLS : %s' % CLS, 'log')
            cls = MACHINE.get_class(CLS)
            if cls is None:
                Util.log('%s not found.' % CLS, 'error')
            else:
                MACHINE.process_class(cls)
        Util.log('\n\nDump of code:', 'log')
        Util.log('===========================', 'log')
        for CLS in MACHINE.classes:
            MACHINE.show_code(MACHINE.get_class(CLS))
            Util.log('===========================', 'log')
    else:
        cls = MACHINE.get_class(CLS)
        if cls is None:
            Util.log('%s not found.' % CLS, 'error')
        else:
            Util.log('======================', 'log')
            temp.clean()
            pprint(cls.get_methods(), temp)
            Util.log(temp, 'log')
            Util.log('======================', 'log')
            METH = raw_input('Method: ')
            if METH == '*':
                Util.log('CLASS = %s' % cls, 'log')
                MACHINE.process_class(cls)
            else:
                MACHINE.process_method(cls, int(METH))
            Util.log('\n\nDump of code:', 'log')
            Util.log('===========================', 'log')
            MACHINE.show_code(cls)
