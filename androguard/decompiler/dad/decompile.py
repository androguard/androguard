# This file is part of Androguard.
#
# Copyright (c) 2012 Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
# All Rights Reserved.
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

import util
from androguard.core.analysis import analysis
from androguard.core.bytecodes import dvm
from graph import construct
from dataflow import build_def_use, dead_code_elimination, register_propagation
from control_flow import identify_structures
from instruction import Param, ThisParam
from writer import Writer


class DvMethod():
    def __init__(self, methanalysis):
        self.method = methanalysis.get_method()
        self.metha = methanalysis
        self.name = self.method.get_name()
        self.lparams = []
        self.basic_blocks = [bb for bb in methanalysis.basic_blocks.get()]
        self.var_to_name = {}
        self.writer = None

        access = self.method.get_access_flags()
        self.access = [flag for flag in util.ACCESS_FLAGS_METHODS
                                     if flag & access]
        desc = self.method.get_descriptor()
        self.type = util.get_type(desc.split(')')[-1])
        self.params_type = util.get_params_type(desc)

        self.exceptions = methanalysis.exceptions.exceptions

        code = self.method.get_code()
        if code is None:
            util.log('No code : %s %s' % (self.name,
                                            self.method.get_class_name()),
                                            'debug')
        else:
            start = code.registers_size - code.ins_size
            if 0x8 not in self.access:
                self.var_to_name[start] = ThisParam(start, self.name)
                self.lparams.append(start)
                start += 1
            num_param = 0
            for ptype in self.params_type:
                param = start + num_param
                self.lparams.append(param)
                self.var_to_name.setdefault(param, Param(param, ptype))
                num_param += util.get_type_size(ptype)

    def process(self):
        util.log('METHOD : %s' % self.name, 'debug')
        if 0:
            from androguard.core import bytecode
            bytecode.method2png('/tmp/dad/graphs/%s#%s.png' % \
                (self.method.get_class_name().split('/')[-1][:-1], self.name),
                                                        self.metha)

        graph = construct(self.basic_blocks, self.var_to_name, self.exceptions)
        self.graph = graph
        if graph is None:
            return

        if 0:
            util.create_png(self.basic_blocks, graph, '/tmp/dad/blocks')

        defs, uses = build_def_use(graph, self.lparams)
        dead_code_elimination(graph, uses, defs)
        register_propagation(graph, uses, defs)

        # After the DCE pass, some nodes may be empty, so we can simplify the
        # graph to delete these nodes.
        # We start by restructuring the graph by spliting the conditional nodes
        # into a pre-header and a header part.
        graph.split_if_nodes()
        # We then simplify the graph by merging multiple statement nodes into
        # a single statement node when possible. This also delete empty nodes.
        graph.simplify()
        graph.reset_rpo()

        idoms = graph.immediate_dominators()
        identify_structures(graph, idoms)

        if 0:
            util.create_png(self.basic_blocks, graph, '/tmp/dad/structured')

        self.writer = Writer(graph, self)
        self.writer.write_method()

    def show_source(self):
        if self.writer is not None:
            print self.writer

    def get_source(self):
        if self.writer is not None:
            return '%s' % self.writer
        return ''

    def __repr__(self):
        return 'Method %s' % self.name


class DvClass():
    def __init__(self, dvclass, vma):
        name = dvclass.get_name()
        if name.find('/') > 0:
            pckg, name = name.rsplit('/', 1)
        else:
            pckg, name = '', name
        self.package = pckg[1:].replace('/', '.')
        self.name = name[:-1]

        self.methods = dict((meth.get_method_idx(),
                             DvMethod(vma.get_method(meth)))
                            for meth in dvclass.get_methods())
        self.fields = {}
        for field in dvclass.get_fields():
            self.fields[field.get_name()] = field
        self.subclasses = {}
        self.code = []
        self.inner = False

        access = dvclass.get_access_flags()
        self.access = [util.ACCESS_FLAGS_CLASSES.get(flag) for flag in
                            util.ACCESS_FLAGS_CLASSES if flag & access]
        self.prototype = '%s class %s' % (' '.join(self.access), self.name)

        self.interfaces = dvclass.interfaces
        self.superclass = dvclass.get_superclassname()

        util.log('Class : %s' % self.name, 'log')
        util.log('Methods added :', 'log')
        for index, meth in self.methods.iteritems():
            util.log('%s (%s, %s)' % (index, meth.method.get_class_name(),
                                   meth.name), 'log')
        util.log('', 'log')

    def add_subclass(self, innername, dvclass):
        self.subclasses[innername] = dvclass
        dvclass.inner = True

    def get_methods(self, meths=None):
        if meths is None:
            meths = self.methods.copy()
        for klass in self.subclasses.values():
            meths.update(klass.get_methods())
        return meths

    def process_method(self, num):
        meths = self.get_methods()
        if num in meths:
            meths[num].process()
        else:
            util.log('Method %s not found.' % num, 'error')

    def get_source(self):
        source = []
        if not self.inner and self.package:
            source.append('package %s;\n' % self.package)

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

        source.append('%s {\n' % self.prototype)
        for field in self.fields.values():
            access = [util.ACCESS_FLAGS_FIELDS.get(flag) for flag in
                util.ACCESS_FLAGS_FIELDS if flag & field.get_access_flags()]
            f_type = util.get_type(field.get_descriptor())
            name = field.get_name()
            source.append('    %s %s %s;\n' % (' '.join(access), f_type, name))

        for klass in self.subclasses.values():
            source.append(klass.get_source())

        for num, method in self.methods.iteritems():
            source.append(method.get_source())
        source.append('}\n')
        return ''.join(source)

    def show_source(self):
        if not self.inner and self.package:
            print 'package %s;\n' % self.package

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

        print '%s {\n' % self.prototype
        for field in self.fields.values():
            access = [util.ACCESS_FLAGS_FIELDS.get(flag) for flag in
                util.ACCESS_FLAGS_FIELDS if flag & field.get_access_flags()]
            f_type = util.get_type(field.get_descriptor())
            name = field.get_name()
            print '    %s %s %s;\n' % (' '.join(access), f_type, name)

        for klass in self.subclasses.values():
            klass.show_source()

        for num, method in self.methods.iteritems():
            method.show_source()
        print '}\n'

    def process(self):
        for klass in self.subclasses.values():
            klass.process()
        for meth in self.methods:
            self.process_method(meth)

    def __str__(self):
        return 'Class name : %s.' % self.name

    def __repr__(self):
        if not self.subclasses:
            return 'Class(%s)' % self.name
        return 'Class(%s) -- Subclasses(%s)' % (self.name, self.subclasses)


class DvMachine():
    def __init__(self, name):
        vm = dvm.DalvikVMFormat(open(name, 'rb').read())
        self.vma = analysis.uVMAnalysis(vm)
        self.classes = dict((dvclass.get_name(), dvclass)
                            for dvclass in vm.get_classes())
        #util.merge_inner(self.classes)

    def process(self):
        for name, klass in self.classes.iteritems():
            util.log('Processing class: %s' % name, 'log')
            if isinstance(klass, DvClass):
                klass.process()
            else:
                dvclass = self.classes[name] = DvClass(klass, self.vma)
                dvclass.process()

    def get_classes(self):
        return self.classes.keys()

    def get_class(self, class_name):
        for name, klass in self.classes.iteritems():
            if class_name in name:
                if isinstance(klass, DvClass):
                    return klass
                dvclass = self.classes[name] = DvClass(klass, self.vma)
                return dvclass

    def show_source(self):
        for klass in self.classes.values():
            klass.show_source()


if __name__ == '__main__':
    # Uncomment to increase the size of the stack.
    """
    from resource import setrlimit, RLIMIT_STACK
    setrlimit(RLIMIT_STACK, (2 ** 29, -1))
    sys.setrecursionlimit(10 ** 6)
    """

    FILE = 'examples/android/TestsAndroguard/bin/classes.dex'
    if len(sys.argv) > 1:
        MACHINE = DvMachine(sys.argv[1])
    else:
        MACHINE = DvMachine(FILE)

    from pprint import pprint
    TMP = util.PprintStream()
    util.log('===========================', 'log')
    util.log('Classes :', 'log')
    pprint(MACHINE.get_classes(), TMP)
    util.log(TMP, 'log')
    util.log('===========================', 'log')

    CLS_NAME = raw_input('Choose a class: ')
    if CLS_NAME == '*':
        MACHINE.process()
        util.log('\n\nSource:', 'log')
        util.log('===========================', 'log')
        MACHINE.show_source()
        util.log('===========================', 'log')
    else:
        CLS = MACHINE.get_class(CLS_NAME)
        if CLS is None:
            util.log('%s not found.' % CLS_NAME, 'error')
        else:
            util.log('======================', 'log')
            TMP.clean()
            pprint(CLS.get_methods(), TMP)
            util.log(TMP, 'log')
            util.log('======================', 'log')
            METH = raw_input('Method: ')
            if METH == '*':
                util.log('CLASS = %s' % CLS, 'log')
                CLS.process()
            else:
                CLS.process_method(int(METH))
            util.log('\n\nSource:', 'log')
            util.log('===========================', 'log')
            CLS.show_source()
