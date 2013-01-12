#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012/2013, Anthony Desnos <desnos at t0t0.fr>
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
import os
import re

from optparse import OptionParser

from androguard.core.androgen import Androguard
from androguard.core import androconf
from androguard.core.bytecodes import dvm
from androguard.core.analysis import analysis
from androguard.core.bytecode import method2dot, method2format
from androguard.decompiler import decompiler

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use this filename', 'nargs' : 1 }
option_1 = { 'name' : ('-o', '--output'), 'help' : 'base directory to output all files', 'nargs' : 1 }

option_2 = { 'name' : ('-d', '--dot'), 'help' : 'write the method in dot format', 'action' : 'count' }
option_3 = { 'name' : ('-f', '--format'), 'help' : 'write the method in specific format (png, ...)', 'nargs' : 1 }

option_4 = { 'name' : ('-l', '--limit'), 'help' : 'limit analysis to specific methods/classes by using a regexp', 'nargs' : 1}
option_5 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1, option_2, option_3, option_4, option_5]


def valid_class_name(class_name):
    if class_name[-1] == ";":
        return class_name[1:-1]
    return class_name


def create_directory(class_name, output):
    output_name = output
    if output_name[-1] != "/":
        output_name = output_name + "/"

    pathdir = output_name + class_name
    try:
        if not os.path.exists(pathdir):
            os.makedirs(pathdir)
    except OSError:
        # FIXME
        pass


def get_params_info(nb, proto):
    i_buffer = "# Parameters:\n"

    ret = proto.split(')')
    params = ret[0][1:].split()
    if params:
        i_buffer += "# - local registers: v%d...v%d\n" % (0, nb - len(params) - 1)
        j = 0
        for i in xrange(nb - len(params), nb):
            i_buffer += "# - v%d:%s\n" % (i, dvm.get_type(params[j]))
            j += 1
    else:
        i_buffer += "# local registers: v%d...v%d\n" % (0, nb - 1)

    i_buffer += "#\n# - return:%s\n\n" % dvm.get_type(ret[1])

    return i_buffer


def get_bytecodes_method(dex_object, ana_object, method):
    mx = ana_object.get_method(method)

    basic_blocks = mx.basic_blocks.gets()
    i_buffer = ""

    idx = 0
    nb = 0

    i_buffer += "# %s->%s%s [access_flags=%s]\n#\n" % (method.get_class_name(), method.get_name(), method.get_descriptor(), method.get_access_flags_string())
    if method.code != None:
        i_buffer += get_params_info(method.code.get_registers_size(), method.get_descriptor())

        for i in basic_blocks:
            bb_buffer = ""
            ins_buffer = ""

            bb_buffer += "%s : " % (i.name)

            instructions = i.get_instructions()
            for ins in instructions:
                ins_buffer += "\t%-8d(%08x) " % (nb, idx)
                ins_buffer += "%-20s %s" % (ins.get_name(), ins.get_output(idx))

                op_value = ins.get_op_value()
                if ins == instructions[-1] and i.childs != []:
                    # packed/sparse-switch
                    if (op_value == 0x2b or op_value == 0x2c) and len(i.childs) > 1:
                          values = i.get_special_ins(idx).get_values()
                          bb_buffer += "[ D:%s " % (i.childs[0][2].name)
                          bb_buffer += ' '.join("%d:%s" % (values[j], i.childs[j + 1][2].name) for j in range(0, len(i.childs) - 1)) + " ]"
                    else:
                        #if len(i.childs) == 2:
                        #    i_buffer += "%s[ %s%s " % (branch_false_color, i.childs[0][2].name, branch_true_color))
                        #    print_fct(' '.join("%s" % c[2].name for c in i.childs[1:]) + " ]%s" % normal_color)
                        #else :
                        bb_buffer += "[ " + ' '.join("%s" % c[2].name for c in i.childs) + " ]"

                idx += ins.get_length()
                nb += 1

                ins_buffer += "\n"

            if i.get_exception_analysis() != None:
              ins_buffer += "\t%s\n" % (i.exception_analysis.show_buff())

            i_buffer += bb_buffer + "\n" + ins_buffer + "\n"

    return i_buffer

def export_apps_to_format(a, output, methods_filter=None, dot=None, format=None):
    methods_filter_expr = None
    if methods_filter:
        methods_filter_expr = re.compile(methods_filter)

    output_name = output
    if output_name[-1] != "/":
        output_name = output_name + "/"

    dump_classes = []
    for vm in a.get_vms():
        vmx = analysis.VMAnalysis(vm)
        vm.set_decompiler(decompiler.DecompilerDAD(vm, vmx))

        for method in vm.get_methods():
            if methods_filter_expr:
                msig = "%s%s%s" % (method.get_class_name(),
                                   method.get_name(),
                                   method.get_descriptor())
                if not methods_filter_expr.search(msig):
                    continue

            filename_class = valid_class_name(method.get_class_name())
            create_directory(filename_class, output)

            print "Dump %s %s %s ..." % (method.get_class_name(),
                                         method.get_name(),
                                         method.get_descriptor()),

            filename_class = output_name + filename_class
            if filename_class[-1] != "/":
                filename_class = filename_class + "/"

            descriptor = method.get_descriptor()
            descriptor = descriptor.replace(";", "")
            descriptor = descriptor.replace(" ", "")
            descriptor = descriptor.replace("(", "-")
            descriptor = descriptor.replace(")", "-")
            descriptor = descriptor.replace("/", "_")

            filename = filename_class + method.get_name() + descriptor
            if len(method.get_name() + descriptor) > 250:
                all_identical_name_methods = vm.get_methods_descriptor(method.get_class_name(), method.get_name())
                pos = 0
                for i in all_identical_name_methods:
                    if i.get_descriptor() == method.get_descriptor():
                        break
                    pos += 1

                filename = filename_class + method.get_name() + "_%d" % pos

            buff = method2dot(vmx.get_method(method))

            if dot:
                print "dot ...",
                fd = open(filename + ".dot", "w")
                fd.write(buff)
                fd.close()

            if format:
                print "%s ..." % format,
                method2format(filename + "." + format, format, None, buff)

            if method.get_class_name() not in dump_classes:
                current_class = vm.get_class(method.get_class_name())
                print "source code ...",
                current_filename_class = valid_class_name(current_class.get_name())
                create_directory(filename_class, output)

                current_filename_class = output_name + current_filename_class + ".java"
                fd = open(current_filename_class, "w")
                fd.write(current_class.get_source())
                fd.close()

                dump_classes.append(method.get_class_name())

            print "bytecode ...",
            bytecode_buff = get_bytecodes_method(vm, vmx, method)
            fd = open(filename + ".ag", "w")
            fd.write(bytecode_buff)
            fd.close()

            print


def main(options, arguments):
    if options.input != None and options.output != None:
        a = Androguard([options.input])

        if options.dot != None or options.format != None:
            export_apps_to_format(a, options.output, options.limit, options.dot, options.format)
        else:
          print "Please, specify a format or dot option"
    elif options.version != None:
        print "Androdd version %s" % androconf.ANDROGUARD_VERSION
    else:
      print "Please, specify an input file and an output directory"

if __name__ == "__main__":
    parser = OptionParser()
    for option in options:
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
