#!/usr/bin/env python

from __future__ import print_function

import os
import re
import shutil
import sys
from argparse import ArgumentParser

from androguard import session
from androguard.misc import clean_file_name
from androguard.core import androconf
from androguard.core.bytecode import method2dot, method2format
from androguard.core.bytecodes import dvm
from androguard.decompiler import decompiler


def valid_class_name(class_name):
    if class_name[-1] == ";":
        class_name = class_name[1:-1]
    return os.path.join(*class_name.split("/"))


def create_directory(pathdir):
    if not os.path.exists(pathdir):
        os.makedirs(pathdir)


def export_apps_to_format(filename,
                          s,
                          output,
                          methods_filter=None,
                          jar=None,
                          decompiler_type=None,
                          form=None):
    print("Dump information %s in %s" % (filename, output))

    if not os.path.exists(output):
        print("Create directory %s" % output)
        os.makedirs(output)
    else:
        print("Clean directory %s" % output)
        androconf.rrmdir(output)
        os.makedirs(output)

    methods_filter_expr = None
    if methods_filter:
        methods_filter_expr = re.compile(methods_filter)

    dump_classes = []
    for _, vm, vmx in s.get_objects_dex():
        print("Decompilation ...", end=' ')
        sys.stdout.flush()

        if decompiler_type == "dex2jad":
            vm.set_decompiler(decompiler.DecompilerDex2Jad(vm,
                                                           androconf.CONF["BIN_DEX2JAR"],
                                                           androconf.CONF["BIN_JAD"],
                                                           androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler_type == "dex2winejad":
            vm.set_decompiler(decompiler.DecompilerDex2WineJad(vm,
                                                               androconf.CONF["BIN_DEX2JAR"],
                                                               androconf.CONF["BIN_WINEJAD"],
                                                               androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler_type == "ded":
            vm.set_decompiler(decompiler.DecompilerDed(vm,
                                                       androconf.CONF["BIN_DED"],
                                                       androconf.CONF["TMP_DIRECTORY"]))
        elif decompiler_type == "dex2fernflower":
            vm.set_decompiler(decompiler.DecompilerDex2Fernflower(vm,
                                                                  androconf.CONF["BIN_DEX2JAR"],
                                                                  androconf.CONF["BIN_FERNFLOWER"],
                                                                  androconf.CONF["OPTIONS_FERNFLOWER"],
                                                                  androconf.CONF["TMP_DIRECTORY"]))

        print("End")

        if jar:
            print("jar ...", end=' ')
            filenamejar = decompiler.Dex2Jar(vm,
                                             androconf.CONF["BIN_DEX2JAR"],
                                             androconf.CONF["TMP_DIRECTORY"]).get_jar()
            shutil.move(filenamejar, os.path.join(output, "classes.jar"))
            print("End")

        for method in vm.get_methods():
            if methods_filter_expr:
                msig = "%s%s%s" % (method.get_class_name(), method.get_name(),
                                   method.get_descriptor())
                if not methods_filter_expr.search(msig):
                    continue

            # Current Folder to write to
            filename_class = valid_class_name(method.get_class_name())
            filename_class = os.path.join(output, filename_class)
            create_directory(filename_class)

            print("Dump %s %s %s ..." % (method.get_class_name(),
                                         method.get_name(),
                                         method.get_descriptor()), end=' ')

            filename = clean_file_name(os.path.join(filename_class, method.get_short_string()))

            buff = method2dot(vmx.get_method(method))
            # Write Graph of method
            if form:
                print("%s ..." % form, end=' ')
                method2format(filename + "." + form, form, None, buff)

            # Write the Java file for the whole class
            if method.get_class_name() not in dump_classes:
                print("source codes ...", end=' ')
                current_class = vm.get_class(method.get_class_name())
                current_filename_class = valid_class_name(current_class.get_name())

                current_filename_class = os.path.join(output, current_filename_class + ".java")
                with open(current_filename_class, "w") as fd:
                    fd.write(current_class.get_source())
                dump_classes.append(method.get_class_name())

            # Write SMALI like code
            print("bytecodes ...", end=' ')
            bytecode_buff = dvm.get_bytecodes_method(vm, vmx, method)
            with open(filename + ".ag", "w") as fd:
                fd.write(bytecode_buff)
            print()


if __name__ == "__main__":
    parser = ArgumentParser(description="Decompile an APK and create Control Flow Graphs")

    parser.add_argument("--version", "-v", action="store_true", default=False,
            help="Print androguard version and exit")
    parser.add_argument("--input", "-i",
            help="resources.arsc or APK to parse (legacy option)")
    parser.add_argument("file", nargs="?",
            help="resources.arsc or APK to parse")
    parser.add_argument("--output", "-o", required=True,
            help="output directory. If the output folder already exsist, it will"
            "be overwritten!")
    parser.add_argument("--format", "-f",
            help="Additionally write control flow graphs for each method,"
            "specify the format for example png, jpg, raw (write dot file), ...")
    parser.add_argument("--jar", "-j", action="store_true", default=False,
            help="Use DEX2JAR to create a JAR file")
    parser.add_argument("--limit", "-l",
            help="Limit to certain methods only by regex (default: '.*')")
    parser.add_argument("--decompiler", "-d",
            help="Use a different decompiler (default: DAD)")

    args = parser.parse_args()

    if args.file and args.input:
        print("Can not give --input and positional argument! Please use only one of them!", file=sys.stderr)
        sys.exit(1)

    if args.version:
        print("Androaxml version %s" % androconf.ANDROGUARD_VERSION)
        sys.exit(0)

    if not args.input and not args.file:
        print("Give one file to decode!", file=sys.stderr)
        sys.exit(1)

    if args.input:
        fname = args.input
    else:
        fname = args.file

    s = session.Session()
    with open(fname, "rb") as fd:
        s.add(fname, fd.read())
    export_apps_to_format(fname, s, args.output, args.limit,
                              args.jar, args.decompiler, args.format)
