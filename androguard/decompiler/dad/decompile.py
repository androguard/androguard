from __future__ import print_function

import logging
import struct
import sys
from builtins import input
from builtins import map
# This file is part of Androguard.
#
# Copyright (c) 2012 Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from builtins import next
from builtins import object
from builtins import range
from builtins import str
from collections import defaultdict

import androguard.core.androconf as androconf
import androguard.decompiler.dad.util as util
from androguard.core.analysis import analysis
from androguard.core.bytecodes import apk, dvm
from androguard.decompiler.dad.control_flow import identify_structures
from androguard.decompiler.dad.dast import (
    JSONWriter,
    parse_descriptor,
    literal_string,
    literal_hex_int,
    dummy
)
from androguard.decompiler.dad.dataflow import (
    build_def_use,
    place_declarations,
    dead_code_elimination,
    register_propagation,
    split_variables
)
from androguard.decompiler.dad.graph import construct, simplify, split_if_nodes
from androguard.decompiler.dad.instruction import Param, ThisParam
from androguard.decompiler.dad.writer import Writer
from androguard.util import read

logger = logging.getLogger('dad')


# No seperate DvField class currently
def get_field_ast(field):
    triple = field.get_class_name()[1:-1], field.get_name(
    ), field.get_descriptor()

    expr = None
    if field.init_value:
        val = field.init_value.value
        expr = dummy(str(val))

        if val is not None:
            if field.get_descriptor() == 'Ljava/lang/String;':
                expr = literal_string(val)
            elif field.proto == 'B':
                expr = literal_hex_int(struct.unpack('<b', struct.pack("B", val))[0])

    return {
        'triple': triple,
        'type': parse_descriptor(field.get_descriptor()),
        'flags': util.get_access_field(field.get_access_flags()),
        'expr': expr,
    }


class DvMethod(object):
    """
    This is a wrapper around :class:`~androguard.core.analysis.analysis.MethodAnalysis` and
    :class:`~androguard.core.bytecodes.dvm.EncodedMethod` inside the decompiler.
    """
    def __init__(self, methanalysis):
        """
        :param androguard.core.analysis.analysis.MethodAnalysis methanalysis:
        """
        method = methanalysis.get_method()
        self.method = method
        self.start_block = next(methanalysis.get_basic_blocks().get(), None)
        self.cls_name = method.get_class_name()
        self.name = method.get_name()
        self.lparams = []
        self.var_to_name = defaultdict()
        self.writer = None
        self.graph = None
        self.ast = None

        self.access = util.get_access_method(method.get_access_flags())

        desc = method.get_descriptor()
        self.type = desc.split(')')[-1]
        self.params_type = util.get_params_type(desc)
        self.triple = method.get_triple()

        self.exceptions = methanalysis.exceptions.exceptions

        code = method.get_code()
        if code is None:
            logger.debug('No code : %s %s', self.name, self.cls_name)
        else:
            start = code.registers_size - code.ins_size
            if 'static' not in self.access:
                self.var_to_name[start] = ThisParam(start, self.cls_name)
                self.lparams.append(start)
                start += 1
            num_param = 0
            for ptype in self.params_type:
                param = start + num_param
                self.lparams.append(param)
                self.var_to_name[param] = Param(param, ptype)
                num_param += util.get_type_size(ptype)

        if not __debug__:
            from androguard.core import bytecode
            # TODO: use tempfile to create a correct tempfile (cross platform compatible)
            bytecode.method2png('/tmp/dad/graphs/%s#%s.png' % (self.cls_name.split('/')[-1][:-1], self.name), methanalysis)

    def process(self, doAST=False):
        logger.debug('METHOD : %s', self.name)

        # Native methods... no blocks.
        if self.start_block is None:
            logger.debug('Native Method.')
            if doAST:
                self.ast = JSONWriter(None, self).get_ast()
            else:
                self.writer = Writer(None, self)
                self.writer.write_method()
            return

        # Construct the CFG
        graph = construct(self.start_block, self.var_to_name, self.exceptions)
        self.graph = graph

        if not __debug__:
            # TODO: use tempfile to create a correct tempfile (cross platform compatible)
            util.create_png(self.cls_name, self.name, graph, '/tmp/dad/blocks')

        use_defs, def_uses = build_def_use(graph, self.lparams)
        split_variables(graph, self.var_to_name, def_uses, use_defs)
        dead_code_elimination(graph, def_uses, use_defs)
        register_propagation(graph, def_uses, use_defs)

        # FIXME var_to_name need to contain the created tmp variables.
        # This seems to be a workaround, we add them into the list manually
        for var, i in def_uses:
            if not isinstance(var, int):
                self.var_to_name[var] = var.upper()

        place_declarations(graph, self.var_to_name, def_uses, use_defs)
        del def_uses, use_defs
        # After the DCE pass, some nodes may be empty, so we can simplify the
        # graph to delete these nodes.
        # We start by restructuring the graph by spliting the conditional nodes
        # into a pre-header and a header part.
        split_if_nodes(graph)
        # We then simplify the graph by merging multiple statement nodes into
        # a single statement node when possible. This also delete empty nodes.

        simplify(graph)
        graph.compute_rpo()

        if not __debug__:
            # TODO: use tempfile to create a correct tempfile (cross platform compatible)
            util.create_png(self.cls_name, self.name, graph, '/tmp/dad/pre-structured')

        identify_structures(graph, graph.immediate_dominators())

        if not __debug__:
            # TODO: use tempfile to create a correct tempfile (cross platform compatible)
            util.create_png(self.cls_name, self.name, graph, '/tmp/dad/structured')

        if doAST:
            self.ast = JSONWriter(graph, self).get_ast()
        else:
            self.writer = Writer(graph, self)
            self.writer.write_method()

    def get_ast(self):
        return self.ast

    def show_source(self):
        print(self.get_source())

    def get_source(self):
        if self.writer:
            return str(self.writer)
        return ''

    def get_source_ext(self):
        if self.writer:
            return self.writer.str_ext()
        return []

    def __repr__(self):
        # return 'Method %s' % self.name
        return 'class DvMethod(object): %s' % self.name


class DvClass(object):
    """
    This is a wrapper for :class:`~androguard.core.bytecodes.dvm.ClassDefItem` inside the decompiler.

    At first, :py:attr:`methods` contains a list of :class:`~androguard.core.bytecodes.dvm.EncodedMethods`,
    which are successively replaced by :class:`DvMethod` in the process of decompilation.
    """
    def __init__(self, dvclass, vma):
        """
        :param androguard.core.bytecodes.dvm.ClassDefItem dvclass: the class item
        :param androguard.core.analysis.analysis.Analysis vma: an Analysis object
        """
        name = dvclass.get_name()
        if name.find('/') > 0:
            pckg, name = name.rsplit('/', 1)
        else:
            pckg, name = '', name
        self.package = pckg[1:].replace('/', '.')
        self.name = name[:-1]

        self.vma = vma
        self.methods = dvclass.get_methods()
        self.fields = dvclass.get_fields()
        self.code = []
        self.inner = False

        access = dvclass.get_access_flags()
        # If interface we remove the class and abstract keywords
        if 0x200 & access:
            prototype = '%s %s'
            if access & 0x400:
                access -= 0x400
        else:
            prototype = '%s class %s'

        self.access = util.get_access_class(access)
        self.prototype = prototype % (' '.join(self.access), self.name)

        self.interfaces = dvclass.get_interfaces()
        self.superclass = dvclass.get_superclassname()
        self.thisclass = dvclass.get_name()

        logger.debug('Class : %s', self.name)
        logger.debug('Methods added :')
        for meth in self.methods:
            logger.debug('%s (%s, %s)', meth.get_method_idx(), self.name, meth.name)
        logger.debug('')

    def get_methods(self):
        return self.methods

    def process_method(self, num, doAST=False):
        method = self.methods[num]
        if not isinstance(method, DvMethod):
            self.methods[num] = DvMethod(self.vma.get_method(method))
            self.methods[num].process(doAST=doAST)
        else:
            method.process(doAST=doAST)

    def process(self, doAST=False):
        for i in range(len(self.methods)):
            try:
                self.process_method(i, doAST=doAST)
            except Exception as e:
                # FIXME: too broad exception?
                logger.warning('Error decompiling method %s: %s', self.methods[i], e)

    def get_ast(self):
        fields = [get_field_ast(f) for f in self.fields]
        methods = []
        for m in self.methods:
            if isinstance(m, DvMethod) and m.ast:
                methods.append(m.get_ast())
        isInterface = 'interface' in self.access
        return {
            'rawname': self.thisclass[1:-1],
            'name': parse_descriptor(self.thisclass),
            'super': parse_descriptor(self.superclass),
            'flags': self.access,
            'isInterface': isInterface,
            'interfaces': list(map(parse_descriptor, self.interfaces)),
            'fields': fields,
            'methods': methods,
        }

    def get_source(self):
        source = []
        if not self.inner and self.package:
            source.append('package %s;\n' % self.package)

        superclass, prototype = self.superclass, self.prototype
        if superclass is not None and superclass != 'Ljava/lang/Object;':
            superclass = superclass[1:-1].replace('/', '.')
            prototype += ' extends %s' % superclass

        if len(self.interfaces) > 0:
            prototype += ' implements %s' % ', '.join(
                [n[1:-1].replace('/', '.') for n in self.interfaces])

        source.append('%s {\n' % prototype)
        for field in self.fields:
            name = field.get_name()
            access = util.get_access_field(field.get_access_flags())
            f_type = util.get_type(field.get_descriptor())
            source.append('    ')
            if access:
                source.append(' '.join(access))
                source.append(' ')
            init_value = field.get_init_value()
            if init_value:
                value = init_value.value
                if f_type == 'String':
                    if value:
                        value = '"%s"' % value.encode("unicode-escape").decode("ascii")
                    else:
                        # FIXME we can not check if this value here is null or ""
                        # In both cases we end up here...
                        value = '""'
                elif field.proto == 'B':
                    # byte value: convert from unsiged int to signed and print as hex
                    # as bytes are signed in Java
                    value = hex(struct.unpack("b", struct.pack("B", value))[0])
                source.append('%s %s = %s;\n' % (f_type, name, value))
            else:
                source.append('%s %s;\n' % (f_type, name))

        for method in self.methods:
            if isinstance(method, DvMethod):
                source.append(method.get_source())

        source.append('}\n')
        return ''.join(source)

    def get_source_ext(self):
        source = []
        if not self.inner and self.package:
            source.append(
                ('PACKAGE', [('PACKAGE_START', 'package '), (
                    'NAME_PACKAGE', '%s' % self.package), ('PACKAGE_END', ';\n')
                             ]))
        list_proto = [('PROTOTYPE_ACCESS', '%s class ' % ' '.join(self.access)),
                      ('NAME_PROTOTYPE', '%s' % self.name, self.package)]
        superclass = self.superclass
        if superclass is not None and superclass != 'Ljava/lang/Object;':
            superclass = superclass[1:-1].replace('/', '.')
            list_proto.append(('EXTEND', ' extends '))
            list_proto.append(('NAME_SUPERCLASS', '%s' % superclass))

        if len(self.interfaces) > 0:
            list_proto.append(('IMPLEMENTS', ' implements '))
            for i, interface in enumerate(self.interfaces):
                if i != 0:
                    list_proto.append(('COMMA', ', '))
                list_proto.append(
                    ('NAME_INTERFACE', interface[1:-1].replace('/', '.')))
        list_proto.append(('PROTOTYPE_END', ' {\n'))
        source.append(("PROTOTYPE", list_proto))

        for field in self.fields:
            field_access_flags = field.get_access_flags()
            access = [util.ACCESS_FLAGS_FIELDS[flag]
                      for flag in util.ACCESS_FLAGS_FIELDS
                      if flag & field_access_flags]
            f_type = util.get_type(field.get_descriptor())
            name = field.get_name()
            if access:
                access_str = '    %s ' % ' '.join(access)
            else:
                access_str = '    '

            value = None
            init_value = field.get_init_value()
            if init_value:
                value = init_value.value
                if f_type == 'String':
                    if value:
                        value = ' = "%s"' % value.encode("unicode-escape").decode("ascii")
                    else:
                        # FIXME we can not check if this value here is null or ""
                        # In both cases we end up here...
                        value = ' = ""'
                elif field.proto == 'B':
                    # a byte
                    value = ' = %s' % hex(struct.unpack("b", struct.pack("B", value))[0])
                else:
                    value = ' = %s' % str(value)
            if value:
                source.append(
                    ('FIELD', [('FIELD_ACCESS', access_str), (
                        'FIELD_TYPE', '%s' % f_type), ('SPACE', ' '), (
                                   'NAME_FIELD', '%s' % name, f_type, field), ('FIELD_VALUE', value), ('FIELD_END',
                                                                                                       ';\n')]))
            else:
                source.append(
                    ('FIELD', [('FIELD_ACCESS', access_str), (
                        'FIELD_TYPE', '%s' % f_type), ('SPACE', ' '), (
                                   'NAME_FIELD', '%s' % name, f_type, field), ('FIELD_END',
                                                                               ';\n')]))

        for method in self.methods:
            if isinstance(method, DvMethod):
                source.append(("METHOD", method.get_source_ext()))
        source.append(("CLASS_END", [('CLASS_END', '}\n')]))
        return source

    def show_source(self):
        print(self.get_source())

    def __repr__(self):
        return 'Class(%s)' % self.name


class DvMachine(object):
    """
    Wrapper class for a Dalvik Object, like a DEX or ODEX file.

    The wrapper allows to take a Dalvik file and get a list of Classes out of it.
    The :class:`~androguard.decompiler.dad.decompile.DvMachine` can take either an APK file directly,
    where all DEX files from the multidex are used, or a single DEX or ODEX file as an argument.

    At first, :py:attr:`classes` contains only :class:`~androguard.core.bytecodes.dvm.ClassDefItem` as values.
    Then these objects are replaced by :class:`DvClass` items successively.
    """
    def __init__(self, name):
        """

        :param name: filename to load
        """
        self.vma = analysis.Analysis()

        # Proper detection which supports multidex inside APK
        ftype = androconf.is_android(name)
        if ftype == 'APK':
            for d in apk.APK(name).get_all_dex():
                self.vma.add(dvm.DalvikVMFormat(d))
        elif ftype == 'DEX':
            self.vma.add(dvm.DalvikVMFormat(read(name)))
        elif ftype == 'DEY':
            self.vma.add(dvm.DalvikOdexVMFormat(read(name)))
        else:
            raise ValueError("Format not recognised for filename '%s'" % name)

        self.classes = dict((dvclass.orig_class.get_name(), dvclass.orig_class) for dvclass in self.vma.get_classes())
        # TODO why not?
        # util.merge_inner(self.classes)

    def get_classes(self):
        """
        Return a list of classnames contained in this machine.
        The format of each name is Lxxx;

        :return: list of class names
        """
        return list(self.classes.keys())

    def get_class(self, class_name):
        """
        Return the :class:`DvClass` with the given name

        The name is partially matched against the known class names and the first result is returned.
        For example, the input `foobar` will match on Lfoobar/bla/foo;

        :param str class_name:
        :return: the class matching on the name
        :rtype: DvClass
        """
        for name, klass in self.classes.items():
            # TODO why use the name partially?
            if class_name in name:
                if isinstance(klass, DvClass):
                    return klass
                dvclass = self.classes[name] = DvClass(klass, self.vma)
                return dvclass

    def process(self):
        """
        Process all classes inside the machine.

        This calls :meth:`~androgaurd.decompiler.dad.decompile.DvClass.process` on each :class:`DvClass`.
        """
        for name, klass in self.classes.items():
            logger.debug('Processing class: %s', name)
            if isinstance(klass, DvClass):
                klass.process()
            else:
                dvclass = self.classes[name] = DvClass(klass, self.vma)
                dvclass.process()

    def show_source(self):
        """
        Calls `show_source` on all classes inside the machine.
        This prints the source to stdout.

        This calls :meth:`~androgaurd.decompiler.dad.decompile.DvClass.show_source` on each :class:`DvClass`.
        """
        for klass in self.classes.values():
            klass.show_source()

    def process_and_show(self):
        """
        Run :meth:`process` and :meth:`show_source` after each other.
        """
        for name, klass in sorted(self.classes.items()):
            logger.debug('Processing class: %s', name)
            if not isinstance(klass, DvClass):
                klass = DvClass(klass, self.vma)
            klass.process()
            klass.show_source()

    def get_ast(self):
        """
        Processes each class with AST enabled and returns a dictionary with all single ASTs
        Classnames as keys.

        :return: an dictionary for all classes
        :rtype: dict
        """
        ret = dict()
        for name, cls in sorted(self.classes.items()):
            logger.debug('Processing class: %s', name)
            if not isinstance(cls, DvClass):
                cls = DvClass(cls, self.vma)
            cls.process(doAST=True)
            ret[name] = cls.get_ast()
        return ret


sys.setrecursionlimit(5000)


def main():
    # logger.setLevel(logging.DEBUG) for debugging output
    # comment the line to disable the logging.
    logger.setLevel(logging.INFO)
    console_hdlr = logging.StreamHandler(sys.stdout)
    console_hdlr.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_hdlr)

    default_file = 'examples/android/TestsAndroguard/bin/TestActivity.apk'
    if len(sys.argv) > 1:
        machine = DvMachine(sys.argv[1])
    else:
        machine = DvMachine(default_file)

    logger.info('========================')
    logger.info('Classes:')
    for class_name in sorted(machine.get_classes()):
        logger.info(' %s', class_name)
    logger.info('========================')

    cls_name = input('Choose a class (* for all classes): ')
    if cls_name == '*':
        machine.process_and_show()
    else:
        cls = machine.get_class(cls_name)
        if cls is None:
            logger.error('%s not found.', cls_name)
        else:
            logger.info('======================')
            for i, method in enumerate(cls.get_methods()):
                logger.info('%d: %s', i, method.name)
            logger.info('======================')
            meth = input('Method (* for all methods): ')
            if meth == '*':
                logger.info('CLASS = %s', cls)
                cls.process()
            else:
                cls.process_method(int(meth))
            logger.info('Source:')
            logger.info('===========================')
            cls.show_source()


if __name__ == '__main__':
    main()
