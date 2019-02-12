from __future__ import print_function

# core modules
import os
import re
import shutil
import sys

# 3rd party modules
from lxml import etree

# internal modules
from androguard.core import androconf
from androguard.core.bytecodes import apk
from androguard.core.bytecodes.axml import AXMLPrinter
from androguard.util import read

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.terminal import TerminalFormatter


def androaxml_main(inp, outp=None, resource=None):
    ret_type = androconf.is_android(inp)
    if ret_type == "APK":
        a = apk.APK(inp)
        if resource:
            if resource not in a.files:
                print("The APK does not contain a file called '{}'".format(resource), file=sys.stderr)
                sys.exit(1)

            axml = AXMLPrinter(a.get_file(resource)).get_xml_obj()
        else:
            axml = a.get_android_manifest_xml()
    elif ".xml" in inp:
        axml = AXMLPrinter(read(inp)).get_xml_obj()
    else:
        print("Unknown file type")
        sys.exit(1)

    buff = etree.tostring(axml, pretty_print=True, encoding="utf-8")
    if outp:
        with open(outp, "wb") as fd:
            fd.write(buff)
    else:
        sys.stdout.write(highlight(buff.decode("UTF-8"), get_lexer_by_name("xml"), TerminalFormatter()))


def androarsc_main(arscobj, outp=None, package=None, typ=None, locale=None):
    package = package or arscobj.get_packages_names()[0]
    ttype = typ or "public"
    locale = locale or '\x00\x00'

    # TODO: be able to dump all locales of a specific type
    # TODO: be able to recreate the structure of files when developing, eg a
    # res folder with all the XML files

    if not hasattr(arscobj, "get_{}_resources".format(ttype)):
        print("No decoder found for type: '{}'! Please open a bug report."
              .format(ttype),
              file=sys.stderr)
        sys.exit(1)

    x = getattr(arscobj, "get_" + ttype + "_resources")(package, locale)

    buff = etree.tostring(etree.fromstring(x),
                          pretty_print=True,
                          encoding="UTF-8")

    if outp:
        with open(outp, "wb") as fd:
            fd.write(buff)
    else:
        sys.stdout.write(highlight(buff.decode("UTF-8"), get_lexer_by_name("xml"), TerminalFormatter()))


def androcg_main(verbose,
                 APK,
                 classname,
                 methodname,
                 descriptor,
                 accessflag,
                 no_isolated,
                 show,
                 output):
    from androguard.core.androconf import show_logging
    from androguard.core.bytecode import FormatClassToJava
    from androguard.misc import AnalyzeAPK
    import networkx as nx
    import logging
    log = logging.getLogger("androcfg")
    if verbose:
        show_logging(logging.INFO)

    a, d, dx = AnalyzeAPK(APK)

    entry_points = map(FormatClassToJava,
                       a.get_activities() + a.get_providers() +
                       a.get_services() + a.get_receivers())
    entry_points = list(entry_points)

    log.info("Found The following entry points by search AndroidManifest.xml: "
             "{}".format(entry_points))

    CG = dx.get_call_graph(classname,
                           methodname,
                           descriptor,
                           accessflag,
                           no_isolated,
                           entry_points,
                           )

    write_methods = dict(gml=_write_gml,
                         gexf=nx.write_gexf,
                         gpickle=nx.write_gpickle,
                         graphml=nx.write_graphml,
                         yaml=nx.write_yaml,
                         net=nx.write_pajek,
                         )

    if show:
        plot(CG)
    else:
        writer = output.rsplit(".", 1)[1]
        if writer in ["bz2", "gz"]:
            writer = output.rsplit(".", 2)[1]
        if writer not in write_methods:
            print("Could not find a method to export files to {}!"
                  .format(writer))
            sys.exit(1)

        write_methods[writer](CG, output)


def plot(cg):
    """
    Plot the call graph using matplotlib
    For larger graphs, this should not be used, as it is very slow
    and probably you can not see anything on it.

    :param cg: A networkx call graph to plot
    """
    from androguard.core.analysis.analysis import ExternalMethod
    import matplotlib.pyplot as plt
    import networkx as nx
    pos = nx.spring_layout(cg)

    internal = []
    external = []

    for n in cg.node:
        if isinstance(n, ExternalMethod):
            external.append(n)
        else:
            internal.append(n)

    nx.draw_networkx_nodes(cg, pos=pos, node_color='r', nodelist=internal)
    nx.draw_networkx_nodes(cg, pos=pos, node_color='b', nodelist=external)
    nx.draw_networkx_edges(cg, pos, arrow=True)
    nx.draw_networkx_labels(cg, pos=pos,
                            labels={x: "{} {}".format(x.get_class_name(),
                                                      x.get_name())
                                    for x in cg.edge})
    plt.draw()
    plt.show()


def _write_gml(G, path):
    """
    Wrapper around nx.write_gml
    """
    import networkx as nx
    return nx.write_gml(G, path, stringizer=str)


def export_apps_to_format(filename,
                          s,
                          output,
                          methods_filter=None,
                          jar=None,
                          decompiler_type=None,
                          form=None):
    from androguard.misc import clean_file_name
    from androguard.core.bytecodes import dvm
    from androguard.core.bytecode import method2dot, method2format
    from androguard.decompiler import decompiler
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


def valid_class_name(class_name):
    if class_name[-1] == ";":
        class_name = class_name[1:-1]
    return os.path.join(*class_name.split("/"))


def create_directory(pathdir):
    if not os.path.exists(pathdir):
        os.makedirs(pathdir)


def androgui_main(input_file, input_plugin):
    # Load pyqt5 after argument processing, so we can collect the arguments
    # on a system without PyQT5.
    try:
        from PyQt5 import QtWidgets, QtGui
    except ImportError:
        print("No PyQT5 found! Exiting...", file=sys.stderr)
        sys.exit(1)
    try:
        import pyperclip
    except ImportError:
        print("No pyperclip found! Exiting...", file=sys.stderr)
        sys.exit(1)

    from androguard.gui.mainwindow import MainWindow

    # We need that to save huge sessions when leaving and avoid
    # RuntimeError: maximum recursion depth exceeded while pickling an object
    # or
    # RuntimeError: maximum recursion depth exceeded in cmp
    # http://stackoverflow.com/questions/2134706/hitting-maximum-recursion-depth-using-pythons-pickle-cpickle
    sys.setrecursionlimit(50000)

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow(input_file=input_file,
                        input_plugin=input_plugin)
    window.resize(1024, 768)
    window.show()

    sys.exit(app.exec_())


def androlyze_main(session, filename):
    """
    Start an interactive shell

    :param session: Session file to load
    :param filename: File to analyze, can be APK or DEX (or ODEX)
    """
    from androguard.core.androconf import ANDROGUARD_VERSION, CONF
    from IPython.terminal.embed import InteractiveShellEmbed
    from traitlets.config import Config
    from androguard.misc import init_print_colors
    from androguard.session import Session, Load
    from colorama import Fore
    import colorama
    import atexit

    # Import commonly used classes, for further usage...
    from androguard.core.bytecodes.apk import APK
    from androguard.core.bytecodes.dvm import DalvikVMFormat
    from androguard.core.analysis.analysis import Analysis

    colorama.init()

    if session:
        print("Restoring session '{}'...".format(session))
        s = CONF['SESSION'] = Load(session)
        print("Successfully restored {}".format(s))
        # TODO Restore a, d, dx etc...
    else:
        s = CONF["SESSION"] = Session(export_ipython=True)

    if filename:
        ("Loading apk {}...".format(os.path.basename(filename)))
        print("Please be patient, this might take a while.")

        filetype = androconf.is_android(filename)

        print("Found the provided file is of type '{}'".format(filetype))

        if filetype not in ['DEX', 'DEY', 'APK']:
            print(Fore.RED + "This file type is not supported by androlyze for auto loading right now!" + Fore.RESET, file=sys.stderr)
            print("But your file is still available:")
            print(">>> filename")
            print(repr(filename))
            print()

        else:
            with open(filename, "rb") as fp:
                raw = fp.read()

            h = s.add(apk, raw)
            print("Added file to session: SHA256::{}".format(h))

            if filetype == 'APK':
                print("Loaded APK file...")
                a, d, dx = s.get_objects_apk(digest=h)

                print(">>> a")
                print(a)
                print(">>> d")
                print(d)
                print(">>> dx")
                print(dx)
                print()
            elif filetype in ['DEX', 'DEY']:
                print("Loaded DEX file...")
                for h_, d, dx in s.get_objects_dex():
                    if h == h_:
                        break
                print(">>> d")
                print(d)
                print(">>> dx")
                print(dx)
                print()

    def shutdown_hook():
        """Save the session on exit, if wanted"""
        if not s.isOpen():
            return

        res = input("Do you want to save the session? (y/[n])?").lower()
        if res == "y":
            # TODO: if we already started from a session, probably we want to save it under the same name...
            # TODO: be able to take any filename you want
            fname = s.save()
            print("Saved Session to file: '{}'".format(fname))

    cfg = Config()
    _version_string = "Androguard version {}".format(ANDROGUARD_VERSION)
    ipshell = InteractiveShellEmbed(config=cfg, banner1="{} started"
                                    .format(_version_string))
    atexit.register(shutdown_hook)
    init_print_colors()
    ipshell()


def androsign_main(args_apk, args_hash, args_all, show):
    from androguard.core.bytecodes.apk import APK
    from androguard.util import get_certificate_name_string

    import hashlib
    import binascii
    import traceback
    from colorama import Fore, Style
    from asn1crypto import x509, keys

    # Keep the list of hash functions in sync with cli/entry_points.py:sign
    hashfunctions = dict(md5=hashlib.md5,
                         sha1=hashlib.sha1,
                         sha256=hashlib.sha256,
                         sha512=hashlib.sha512,
                         )

    if args_hash.lower() not in hashfunctions:
        print("Hash function {} not supported!"
              .format(args_hash.lower()), file=sys.stderr)
        print("Use one of {}"
              .format(", ".join(hashfunctions.keys())), file=sys.stderr)
        sys.exit(1)

    for path in args_apk:
        try:
            a = APK(path)

            print("{}, package: '{}'".format(os.path.basename(path), a.get_package()))
            print("Is signed v1: {}".format(a.is_signed_v1()))
            print("Is signed v2: {}".format(a.is_signed_v2()))
            print("Is signed v3: {}".format(a.is_signed_v3()))

            certs = set(a.get_certificates_der_v3() + a.get_certificates_der_v2() + [a.get_certificate_der(x) for x in a.get_signature_names()])
            pkeys = set(a.get_public_keys_der_v3() + a.get_public_keys_der_v2())

            if len(certs) > 0:
                print("Found {} unique certificates".format(len(certs)))

            for cert in certs:
                if show:
                    x509_cert = x509.Certificate.load(cert)
                    print("Issuer:", get_certificate_name_string(x509_cert.issuer, short=True))
                    print("Subject:", get_certificate_name_string(x509_cert.subject, short=True))
                    print("Serial Number:", hex(x509_cert.serial_number))
                    print("Hash Algorithm:", x509_cert.hash_algo)
                    print("Signature Algorithm:", x509_cert.signature_algo)
                    print("Valid not before:", x509_cert['tbs_certificate']['validity']['not_before'].native)
                    print("Valid not after:", x509_cert['tbs_certificate']['validity']['not_after'].native)

                if not args_all:
                    print("{} {}".format(args_hash.lower(), hashfunctions[args_hash.lower()](cert).hexdigest()))
                else:
                    for k, v in hashfunctions.items():
                        print("{} {}".format(k, v(cert).hexdigest()))
                print()

            if len(certs) > 0:
                print("Found {} unique public keys associated with the certs".format(len(pkeys)))

            for public_key in pkeys:
                if show:
                    x509_public_key = keys.PublicKeyInfo.load(public_key)
                    print("PublicKey Algorithm:", x509_public_key.algorithm)
                    print("Bit Size:", x509_public_key.bit_size)
                    print("Fingerprint:", binascii.hexlify(x509_public_key.fingerprint))
                    try:
                        print("Hash Algorithm:", x509_public_key.hash_algo)
                    except ValueError as ve:
                        # RSA pkey does not have an hash algorithm
                        pass
                
                print()


        except:
            print(Fore.RED + "Error in {}".format(os.path.basename(path)) + Style.RESET_ALL, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

        if len(args_apk) > 1:
            print()


def androdis_main(offset, size, dex):
    from androguard.core.bytecodes import dvm

    with open(dex, "rb") as fp:
        buf = fp.read()
    d = dvm.DalvikVMFormat(buf)

    if size == 0:
        size = len(buf)

    if d:
        idx = offset
        for nb, i in enumerate(d.disassemble(offset, size)):
            print("%-8d(%08x)" % (nb, idx), end=' ')
            i.show(idx)
            print()

            idx += i.get_length()
    else:
        print("Dex could not be loaded!", file=sys.stderr)
