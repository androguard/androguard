from __future__ import print_function
# This file is part of Androguard.
#
# Copyright (C) 2013, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
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

from builtins import range
from builtins import object
from subprocess import Popen, PIPE, STDOUT

import tempfile
import os

from androguard.core.androconf import rrmdir
from androguard.decompiler.dad import decompile
from androguard.util import read

from pygments.filter import Filter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.token import Token

import logging

log = logging.getLogger("androguard.decompiler")


class JADXDecompilerError(Exception):
    """
    Exception for JADX related problems
    """
    pass


class MethodFilter(Filter):
    def __init__(self, **options):
        """
        Filter Method Code from a whole class

        :param options:
        """
        Filter.__init__(self, **options)

        self.method_name = options["method_name"]
        # self.descriptor = options["descriptor"]

        self.present = False
        self.get_desc = True  # False

    def filter(self, lexer, stream):
        a = []
        l = []
        rep = []

        for ttype, value in stream:
            if self.method_name == value and (ttype is Token.Name.Function or
                                                      ttype is Token.Name):
                # print ttype, value

                item_decl = -1
                for i in range(len(a) - 1, 0, -1):
                    if a[i][0] is Token.Keyword.Declaration:
                        if a[i][1] != "class":
                            item_decl = i
                        break

                if item_decl != -1:
                    self.present = True
                    l.extend(a[item_decl:])

            if self.present and ttype is Token.Keyword.Declaration:
                item_end = -1
                for i in range(len(l) - 1, 0, -1):
                    if l[i][0] is Token.Operator and l[i][1] == "}":
                        item_end = i
                        break

                if item_end != -1:
                    rep.extend(l[:item_end + 1])
                    l = []
                    self.present = False

            if self.present:
                l.append((ttype, value))

            a.append((ttype, value))

        if self.present:
            nb = 0
            item_end = -1
            for i in range(len(l) - 1, 0, -1):
                if l[i][0] is Token.Operator and l[i][1] == "}":
                    nb += 1
                    if nb == 2:
                        item_end = i
                        break

            rep.extend(l[:item_end + 1])

        return rep


# TODO move it somewhere else
class Dex2Jar(object):
    def __init__(self,
                 vm,
                 bin_dex2jar="dex2jar.sh",
                 tmp_dir="/tmp/"):
        """
        DEX2JAR is a tool to convert a Dalvik file into Java Classes

        :param vm:
        :param bin_dex2jar:
        :param tmp_dir:
        """
        pathtmp = tmp_dir
        if not os.path.exists(pathtmp):
            os.makedirs(pathtmp)

        fd, fdname = tempfile.mkstemp(dir=pathtmp)
        with os.fdopen(fd, "w+b") as fd:
            fd.write(vm.get_buff())
            fd.flush()

        cmd = Popen([bin_dex2jar, fdname],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname)

        self.jarfile = fdname + "_dex2jar.jar"

    def get_jar(self):
        return self.jarfile


class DecompilerDex2Jad(object):
    def __init__(self,
                 vm,
                 bin_dex2jar="dex2jar.sh",
                 bin_jad="jad",
                 tmp_dir="/tmp/"):
        """
        Decompiler interface for JAD
        JAD is not a native Dalvik decompiler, therefore dex2jar is required.

        .. deprecated:: 3.3.5
            JAD is not supported anymore in androguard!

        :param vm:
        :param bin_dex2jar:
        :param bin_jad:
        :param tmp_dir:
        """
        warnings.warn("JAD is deprecated since 3.3.5.", DeprecationWarning)

        self.classes = {}
        self.classes_failed = []

        pathtmp = tmp_dir
        if not os.path.exists(pathtmp):
            os.makedirs(pathtmp)

        fd, fdname = tempfile.mkstemp(dir=pathtmp)
        with os.fdopen(fd, "w+b") as fd:
            fd.write(vm.get_buff())
            fd.flush()

        cmd = Popen([bin_dex2jar, fdname],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname)

        pathclasses = fdname + "dex2jar/"
        cmd = Popen(["unzip", fdname + "_dex2jar.jar", "-d", pathclasses],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname + "_dex2jar.jar")

        for root, dirs, files in os.walk(pathclasses, followlinks=True):
            if files:
                for f in files:
                    real_filename = root
                    if real_filename[-1] != "/":
                        real_filename += "/"
                    real_filename += f

                    cmd = Popen([bin_jad, "-o", "-d", root,
                                     real_filename],
                                    stdout=PIPE,
                                    stderr=STDOUT)
                    stdout, stderr = cmd.communicate()

        for i in vm.get_classes():
            fname = pathclasses + "/" + i.get_name()[1:-1] + ".jad"
            if os.path.isfile(fname):
                self.classes[i.get_name()] = read(fname, binary=False)
            else:
                self.classes_failed.append(i.get_name())

        rrmdir(pathclasses)

    def get_source_method(self, method):
        class_name = method.get_class_name()
        method_name = method.get_name()

        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        lexer.add_filter(MethodFilter(method_name=method_name))
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_source(self, method):
        print(self.get_source_method(method))

    def get_source_class(self, _class):
        return self.classes[_class.get_name()]

    def get_all(self, class_name):
        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_all(self, _class):
        print(self.get_all(_class.get_name()))


class DecompilerDex2WineJad(object):
    def __init__(self,
                 vm,
                 bin_dex2jar="dex2jar.sh",
                 bin_jad="jad",
                 tmp_dir="/tmp/"):
        """
        Use JAD on wine

        .. deprecated:: 3.3.5
            JAD is not supported anymore by androguard!

        :param vm:
        :param bin_dex2jar:
        :param bin_jad:
        :param tmp_dir:
        """
        warnings.warn("JAD is deprecated since 3.3.5.", DeprecationWarning)

        self.classes = {}
        self.classes_failed = []

        pathtmp = tmp_dir
        if not os.path.exists(pathtmp):
            os.makedirs(pathtmp)

        fd, fdname = tempfile.mkstemp(dir=pathtmp)
        with os.fdopen(fd, "w+b") as fd:
            fd.write(vm.get_buff())
            fd.flush()

        cmd = Popen([bin_dex2jar, fdname],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname)

        pathclasses = fdname + "dex2jar/"
        cmd = Popen(["unzip", fdname + "_dex2jar.jar", "-d", pathclasses],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname + "_dex2jar.jar")

        for root, dirs, files in os.walk(pathclasses, followlinks=True):
            if files:
                for f in files:
                    real_filename = root
                    if real_filename[-1] != "/":
                        real_filename += "/"
                    real_filename += f

                    cmd = Popen(["wine", bin_jad, "-o", "-d",
                                     root, real_filename],
                                    stdout=PIPE,
                                    stderr=STDOUT)
                    stdout, stderr = cmd.communicate()

        for i in vm.get_classes():
            fname = pathclasses + "/" + i.get_name()[1:-1] + ".jad"
            if os.path.isfile(fname):
                self.classes[i.get_name()] = read(fname, binary=False)
            else:
                self.classes_failed.append(i.get_name())

        rrmdir(pathclasses)

    def get_source_method(self, method):
        class_name = method.get_class_name()
        method_name = method.get_name()

        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        lexer.add_filter(MethodFilter(method_name=method_name))
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_source(self, method):
        print(self.get_source_method(method))

    def get_source_class(self, _class):
        return self.classes[_class.get_name()]

    def get_all(self, class_name):
        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_all(self, _class):
        print(self.get_all(_class.get_name()))


class DecompilerDed(object):
    def __init__(self,
                 vm,
                 bin_ded="ded.sh",
                 tmp_dir="/tmp/"):
        """
        DED is an old, probably deprecated, decompiler
        http://siis.cse.psu.edu/ded/

        .. deprecated:: 3.3.5
            DED is not supported by androguard anymore!

        It is now replaced by DARE.

        :param vm: `DalvikVMFormat` object
        :param bin_ded:
        :param tmp_dir:
        """
        warnings.warn("DED is deprecated since 3.3.5.", DeprecationWarning)

        self.classes = {}
        self.classes_failed = []

        pathtmp = tmp_dir
        if not os.path.exists(pathtmp):
            os.makedirs(pathtmp)

        fd, fdname = tempfile.mkstemp(dir=pathtmp)
        with os.fdopen(fd, "w+b") as fd:
            fd.write(vm.get_buff())
            fd.flush()

        dirname = tempfile.mkdtemp(prefix=fdname + "-src")
        cmd = Popen([bin_ded, "-c", "-o", "-d", dirname, fdname],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname)

        findsrc = None
        for root, dirs, files in os.walk(dirname + "/optimized-decompiled/"):
            if dirs:
                for f in dirs:
                    if f == "src":
                        findsrc = root
                        if findsrc[-1] != "/":
                            findsrc += "/"
                        findsrc += f
                        break
            if findsrc is not None:
                break

        for i in vm.get_classes():
            fname = findsrc + "/" + i.get_name()[1:-1] + ".java"
            # print fname
            if os.path.isfile(fname):
                self.classes[i.get_name()] = read(fname, binary=False)
            else:
                self.classes_failed.append(i.get_name())

        rrmdir(dirname)

    def get_source_method(self, method):
        class_name = method.get_class_name()
        method_name = method.get_name()

        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        lexer.add_filter(MethodFilter(method_name=method_name))
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_source(self, method):
        print(self.get_source_method(method))

    def get_all(self, class_name):
        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def get_source_class(self, _class):
        return self.classes[_class.get_name()]

    def display_all(self, _class):
        print(self.get_all(_class.get_name()))


class DecompilerDex2Fernflower(object):
    def __init__(self,
                 vm,
                 bin_dex2jar="dex2jar.sh",
                 bin_fernflower="fernflower.jar",
                 options_fernflower={"dgs": '1',
                                     "asc": '1'},
                 tmp_dir="/tmp/"):
        """
        Decompiler interface for Fernflower
        Fernflower is a java decompiler by IntelliJ:
        https://github.com/JetBrains/intellij-community/tree/master/plugins/java-decompiler/engine

        As it can not decompile Dalvik code directly, the DEX is first
        decompiled as a JAR file.

        .. deprecated:: 3.3.5
            Fernflower is not supported anymore by androguard.


        :param vm: `DalvikVMFormtat` object
        :param bin_dex2jar:
        :param bin_fernflower:
        :param options_fernflower:
        :param tmp_dir:
        """
        warnings.warn("Fernflower is deprecated since 3.3.5.", DeprecationWarning)

        self.classes = {}
        self.classes_failed = []

        pathtmp = tmp_dir
        if not os.path.exists(pathtmp):
            os.makedirs(pathtmp)

        fd, fdname = tempfile.mkstemp(dir=pathtmp)
        with os.fdopen(fd, "w+b") as fd:
            fd.write(vm.get_buff())
            fd.flush()

        cmd = Popen([bin_dex2jar, fdname],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname)

        pathclasses = fdname + "dex2jar/"
        cmd = Popen(["unzip", fdname + "_dex2jar.jar", "-d", pathclasses],
                        stdout=PIPE,
                        stderr=STDOUT)
        stdout, stderr = cmd.communicate()
        os.unlink(fdname + "_dex2jar.jar")

        for root, dirs, files in os.walk(pathclasses, followlinks=True):
            if files:
                for f in files:
                    real_filename = root
                    if real_filename[-1] != "/":
                        real_filename += "/"
                    real_filename += f

                    l = ["java", "-jar", bin_fernflower]

                    for option in options_fernflower:
                        l.append("-%s:%s" %
                                 (option, options_fernflower[option]))
                    l.append(real_filename)
                    l.append(root)

                    cmd = Popen(l, stdout=PIPE, stderr=STDOUT)
                    stdout, stderr = cmd.communicate()

        for i in vm.get_classes():
            fname = pathclasses + "/" + i.get_name()[1:-1] + ".java"
            if os.path.isfile(fname):
                self.classes[i.get_name()] = read(fname, binary=False)
            else:
                self.classes_failed.append(i.get_name())

        rrmdir(pathclasses)

    def get_source_method(self, method):
        class_name = method.get_class_name()
        method_name = method.get_name()

        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        lexer.add_filter(MethodFilter(method_name=method_name))
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_source(self, method):
        print(self.get_source_method(method))

    def get_source_class(self, _class):
        return self.classes[_class.get_name()]

    def get_all(self, class_name):
        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def display_all(self, _class):
        print(self.get_all(_class.get_name()))


class DecompilerDAD:
    def __init__(self, vm, vmx):
        """
        Decompiler wrapper for DAD: **D**AD is **A** **D**ecompiler
        DAD is the androguard internal decompiler.

        This Method does not use the :class:`~androguard.decompiler.dad.decompile.DvMachine` but
        creates :class:`~androguard.decompiler.dad.decompile.DvClass` and
        :class:`~androguard.decompiler.dad.decompile.DvMethod` on demand.

        :param androguard.core.bytecodes.dvm.DalvikVMFormat vm: `DalvikVMFormat` object
        :param androguard.core.analysis.analysis.Analysis vmx: `Analysis` object
        """
        self.vm = vm
        self.vmx = vmx

    def get_source_method(self, m):
        mx = self.vmx.get_method(m)
        z = decompile.DvMethod(mx)
        z.process()
        return z.get_source()

    def get_ast_method(self, m):
        mx = self.vmx.get_method(m)
        z = decompile.DvMethod(mx)
        z.process(doAST=True)
        return z.get_ast()

    def display_source(self, m):
        result = self.get_source_method(m)

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(result, lexer, formatter)
        print(result)

    def get_source_class(self, _class):
        c = decompile.DvClass(_class, self.vmx)
        c.process()
        return c.get_source()

    def get_ast_class(self, _class):
        c = decompile.DvClass(_class, self.vmx)
        c.process(doAST=True)
        return c.get_ast()

    def get_source_class_ext(self, _class):
        c = decompile.DvClass(_class, self.vmx)
        c.process()

        result = c.get_source_ext()

        return result

    def display_all(self, _class):
        result = self.get_source_class(_class)

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(result, lexer, formatter)
        print(result)

    def get_all(self, class_name):
        pass


class DecompilerJADX:
    def __init__(self, vm, vmx, jadx="jadx", keepfiles=False):
        """
        DecompilerJADX is a wrapper for the jadx decompiler:
        https://github.com/skylot/jadx

        Note, that jadx need to write files to your local disk.

        :param vm: `DalvikVMFormat` object
        :param vmx: `Analysis` object
        :param jadx: path to the jadx executable
        :param keepfiles: set to True, if you like to keep temporary files
        """
        self.vm = vm
        self.vmx = vmx
        # Dictionary to store classnames: sourcecode
        self.classes = {}

        # Result directory:
        # TODO need to remove the folder correctly!
        tmpfolder = tempfile.mkdtemp()

        # We need to decompile the whole dex file, as we do not have an API...
        # dump the dex file into a temp file
        # THIS WILL NOT WORK ON WINDOWS!!!
        # See https://stackoverflow.com/q/15169101/446140
        # Files can not be read, only if they specify temp file. But jadx does not do that...
        #
        # We need to trick jadx by setting the suffix, otherwise the file will not be loaded
        with tempfile.NamedTemporaryFile(suffix=".dex") as tf:
            tf.write(vm.get_buff())

            cmd = [jadx, "-d", tmpfolder, "--escape-unicode", "--no-res", tf.name]
            log.debug("Call JADX with the following cmdline: {}".format(" ".join(cmd)))
            x = Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, _ = x.communicate()
            # Looks like jadx does not use stderr
            log.info("Output of JADX during decompilation")
            for line in stdout.decode("UTF-8").splitlines():
                log.info(line)

            if x.returncode != 0:
                rrmdir(tmpfolder)
                raise JADXDecompilerError("Could not decompile file. Args: {}".format(" ".join(cmd)))

        # Next we parse the folder structure for later lookup
        # We read the content of each file here, so we can later delete the folder
        # We check here two ways, first we iterate all files and see if the class exists
        # in androguard
        # then, we iterate all classes in androguard and check if the file exists.

        andr_class_names = {x.get_name()[1:-1]: x for x in vm.get_classes()}

        # First, try to find classes for the files we have
        for root, dirs, files in os.walk(tmpfolder):
            for f in files:
                if not f.endswith(".java"):
                    log.warning("found a file in jadx folder which is not a java file: {}".format(f))
                    continue
                # as the path begins always with `self.res` (hopefully), we remove that length
                # also, all files should end with .java
                path = os.path.join(root, f)[len(tmpfolder) + 1:-5]
                path = path.replace(os.sep, "/")

                # Special care for files without package
                # All files that have no package set, will get the
                # package `defpackage` automatically
                if path.startswith("defpackage"):
                    path = path[len("defpackage/"):]

                if path in andr_class_names:
                    with open(os.path.join(root, f), "rb") as fp:
                        # Need to convert back to the "full" classname
                        self.classes["L{};".format(path)] = fp.read().decode("UTF-8")
                else:
                    log.warning("Found a class called {}, which is not found by androguard!".format(path))

        # Next, try to find files for the classes we have
        for cl in andr_class_names:
            fname = self._find_class(cl, tmpfolder)
            if fname:
                if "L{};".format(cl) not in self.classes:
                    with open(fname, "rb") as fp:
                        # TODO need to snip inner class from file
                        self.classes["L{};".format(cl)] = fp.read().decode("UTF-8")
                else:
                    # Class was already found...
                    pass
            else:
                log.warning("Found a class called {} which is not decompiled by jadx".format(cl))

        # check if we have good matching
        if len(self.classes) == len(andr_class_names):
            log.debug("JADX looks good, we have the same number of classes: {}".format(len(self.classes)))
        else:
            log.info("Looks like JADX is missing some classes or "
                 "we decompiled too much: decompiled: {} vs androguard: {}".format(len(self.classes),
                                                                                   len(andr_class_names)))

        if not keepfiles:
            rrmdir(tmpfolder)

    def _find_class(self, clname, basefolder):
        # check if defpackage
        if "/" not in clname:
            # this is a defpackage class probably...
            # Search first for defpackage, then search for requested string
            res = self._find_class("defpackage/{}".format(clname), basefolder)
            if res:
                return res

        # We try to map inner classes here
        if "$" in clname:
            # sometimes the inner class get's an extra file, sometimes not...
            # So we try all possibilities
            for x in range(clname.count("$")):
                tokens = clname.split("$", x + 1)
                base = "$".join(tokens[:-1])
                res = self._find_class(base, basefolder)
                if res:
                    return res

        # Check the whole supplied name
        fname = os.path.join(basefolder, clname.replace("/", os.sep) + ".java")
        if not os.path.isfile(fname):
            return None
        return fname

    def get_source_method(self, m):
        """
        Return the Java source of a single method

        :param m: `EncodedMethod` Object
        :return:
        """
        class_name = m.get_class_name()
        method_name = m.get_name()

        if class_name not in self.classes:
            return ""

        lexer = get_lexer_by_name("java", stripall=True)
        lexer.add_filter(MethodFilter(method_name=method_name))
        formatter = TerminalFormatter()
        result = highlight(self.classes[class_name], lexer, formatter)
        return result

    def get_source_class(self, _class):
        """
        Return the Java source code of a whole class

        :param _class: `ClassDefItem` object, to get the source from
        :return:
        """
        if not _class.get_name() in self.classes:
            return ""
        return self.classes[_class.get_name()]

    def display_source(self, m):
        """
        This method does the same as `get_source_method`
        but prints the result directly to stdout

        :param m: `EncodedMethod` to print
        :return:
        """
        print(self.get_source_method(m))

    def display_all(self, _class):
        """
        ???

        :param _class:
        :return:
        """
        pass

    def get_all(self, class_name):
        """
        ???

        :param class_name:
        :return:
        """
        pass
