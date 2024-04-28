# core modules
import os
import re
import shutil
import sys
from typing import Union

# 3rd party modules
from lxml import etree
from loguru import logger
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters.terminal import TerminalFormatter
from oscrypto import asymmetric

# internal modules
from androguard.core.axml import ARSCParser
from androguard.session import Session
from androguard.core import androconf
from androguard.core import apk
from androguard.core.axml import AXMLPrinter
from androguard.core.dex import get_bytecodes_method
from androguard.util import readFile
from androguard.ui import DynamicUI

def androaxml_main(
        inp:str,
        outp:Union[str,None]=None,
        resource:Union[str,None]=None) -> None:
    
    ret_type = androconf.is_android(inp)
    if ret_type == "APK":
        a = apk.APK(inp)
        if resource:
            if resource not in a.files:
                logger.error("The APK does not contain a file called '{}'".format(resource), file=sys.stderr)
                sys.exit(1)

            axml = AXMLPrinter(a.get_file(resource)).get_xml_obj()
        else:
            axml = a.get_android_manifest_xml()
    elif ".xml" in inp:
        axml = AXMLPrinter(readFile(inp)).get_xml_obj()
    else:
        logger.error("Unknown file type")
        sys.exit(1)

    buff = etree.tostring(axml, pretty_print=True, encoding="utf-8")
    if outp:
        with open(outp, "wb") as fd:
            fd.write(buff)
    else:
        sys.stdout.write(highlight(buff.decode("UTF-8"), get_lexer_by_name("xml"), TerminalFormatter()))


def androarsc_main(
        arscobj: ARSCParser,
        outp:Union[str,None]=None,
        package:Union[str,None]=None,
        typ:Union[str,None]=None,
        locale:Union[str,None]=None) -> None:
    
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


def export_apps_to_format(
        filename:str,
        s: Session,
        output: str,
        methods_filter:Union[str,None]=None,
        jar:bool=False,
        decompiler_type:Union[str,None]=None,
        form:Union[str,None]=None) -> None:
    
    from androguard.misc import clean_file_name
    from androguard.core.bytecode import method2dot, method2format
    from androguard.decompiler import decompiler
    print("Dump information {} in {}".format(filename, output))

    if not os.path.exists(output):
        print("Create directory %s" % output)
        os.makedirs(output)
    else:
        while True:
            user_input = input(f"Do you want to clean the directory {output}? (Y/N): ").strip().lower()

            if user_input == 'y':
                print("Deleting...")
                androconf.rrmdir(output)
                os.makedirs(output)
                break
            elif user_input == 'n':
                print("Not deleting.")
                break
            else:
                print("Invalid input. Please enter Y or N.")

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

        for method in vm.get_encoded_methods():
            if methods_filter_expr:
                msig = "{}{}{}".format(method.get_class_name(), method.get_name(),
                                       method.get_descriptor())
                if not methods_filter_expr.search(msig):
                    continue

            # Current Folder to write to
            filename_class = valid_class_name(str(method.get_class_name()))
            filename_class = os.path.join(output, filename_class)
            create_directory(filename_class)

            print("Dump {} {} {} ...".format(method.get_class_name(),
                                             method.get_name(),
                                             method.get_descriptor()), end=' ')

            filename = clean_file_name(os.path.join(filename_class, method.get_short_string()))

            buff = method2dot(vmx.get_method(method))
            # Write Graph of method
            if form:
                print("%s ..." % form, end=' ')
                method2format(filename + "." + form, form, None, buff)

            # Write the Java file for the whole class
            if str(method.get_class_name()) not in dump_classes:
                print("source codes ...", end=' ')
                current_class = vm.get_class(method.get_class_name())
                current_filename_class = valid_class_name(str(current_class.get_name()))

                current_filename_class = os.path.join(output, current_filename_class + ".java")
                with open(current_filename_class, "w") as fd:
                    fd.write(current_class.get_source())
                dump_classes.append(method.get_class_name())

            # Write SMALI like code
            print("bytecodes ...", end=' ')
            bytecode_buff = get_bytecodes_method(vm, vmx, method)
            with open(filename + ".ag", "w") as fd:
                fd.write(bytecode_buff)
            print()


def valid_class_name(class_name:str) -> str:
    if class_name[-1] == ";":
        class_name = class_name[1:-1]
    return os.path.join(*class_name.split("/"))


def create_directory(pathdir:str) -> None:
    if not os.path.exists(pathdir):
        os.makedirs(pathdir)


def androlyze_main(session:Session, filename:str) -> None:
    """
    Start an interactive shell

    :param session: Session file to load
    :param filename: File to analyze, can be APK or DEX (or ODEX)
    """
    from colorama import Fore
    import colorama
    import atexit

    from IPython.terminal.embed import embed

    from traitlets.config import Config

    from androguard.core.androconf import ANDROGUARD_VERSION, CONF
    from androguard.session import Session

    colorama.init()

    if session:
        logger.info("TODO: Restoring session '{}'...".format(session))
        # s = CONF['SESSION'] = Load(session)
        # logger.info("Successfully restored {}".format(s))
        # TODO actually restore the session a, d, dx etc...
    else:
        s = CONF["SESSION"] = Session(export_ipython=True)

    if filename:
        ("Loading apk {}...".format(os.path.basename(filename)))
        logger.info("Please be patient, this might take a while.")

        filetype = androconf.is_android(filename)

        logger.info("Found the provided file is of type '{}'".format(filetype))

        if filetype not in ['DEX', 'DEY', 'APK']:
            logger.error(
                Fore.RED + "This file type is not supported by androlyze for auto loading right now!" + Fore.RESET,
                file=sys.stderr)
            logger.error("But your file is still available:")
            logger.error(">>> filename")
            logger.error(repr(filename))
            print()

        else:
            with open(filename, "rb") as fp:
                raw = fp.read()

            h = s.add(filename, raw)
            logger.info("Added file to session: SHA256::{}".format(h))

            if filetype == 'APK':
                logger.info("Loaded APK file...")
                a, d, dx = s.get_objects_apk(digest=h)

                print(">>> filename")
                print(filename)
                print(">>> a")
                print(a)
                print(">>> d")
                print(d)
                print(">>> dx")
                print(dx)
                print()
            elif filetype in ['DEX', 'DEY']:
                logger.info("Loaded DEX file...")
                for h_, d, dx in s.get_objects_dex():
                    if h == h_:
                        break
                print(">>> d")
                print(d)
                print(">>> dx")
                print(dx)
                print()

    def shutdown_hook() -> None:
        """Save the session on exit, if wanted"""
        if not s.isOpen():
            return

        try:
            res = input("Do you want to save the session? (y/[n])?").lower()
        except (EOFError, KeyboardInterrupt):
            pass
        else:
            if res == "y":
                # TODO: if we already started from a session, probably we want to save it under the same name...
                # TODO: be able to take any filename you want
                fname = s.save()
                print("Saved Session to file: '{}'".format(fname))

    cfg = Config()
    _version_string = "Androguard version {}".format(ANDROGUARD_VERSION)
    ipshell = embed(config=cfg, banner1="{} started".format(_version_string))
    atexit.register(shutdown_hook)
    ipshell()


def androsign_main(args_apk:list[str], args_hash:str, args_all:bool, show:bool) -> None:
    from androguard.core.apk import APK
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

            certs = set(a.get_certificates_der_v3() + a.get_certificates_der_v2() + [a.get_certificate_der(x) for x in
                                                                                     a.get_signature_names()])
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
                    x509_public_key = asymmetric.load_public_key(public_key)
                    print("PublicKey Algorithm:", x509_public_key.algorithm)
                    print("Bit Size:", x509_public_key.bit_size)
                    print("Fingerprint:", binascii.hexlify(x509_public_key.fingerprint))
                    try:
                        print("Hash Algorithm:", x509_public_key.asn1.hash_algo)
                    except ValueError as ve:
                        # RSA pkey does not have a hash algorithm
                        pass
                print()


        except:
            print(Fore.RED + "Error in {}".format(os.path.basename(path)) + Style.RESET_ALL, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)

        if len(args_apk) > 1:
            print()


def androdis_main(offset:int, size:int, dex_file:str) -> None:
    from androguard.core.dex import DEX

    with open(dex_file, "rb") as fp:
        buf = fp.read()

    d = DEX(buf)

    if size == 0 and offset == 0:
        # Assume you want to just get a disassembly of all classes and methods
        for cls in d.get_classes():
            print("# CLASS: {}".format(cls.get_name()))
            for m in cls.get_methods():
                print("## METHOD: {} {} {}".format(m.get_access_flags_string(), m.get_name(), m.get_descriptor()))
                for idx, ins in m.get_instructions_idx():
                    print('{:08x}  {}'.format(idx, ins.disasm()))

                print()
            print()
    else:
        if size == 0:
            size = len(buf)

        if d:
            idx = offset
            for nb, i in enumerate(d.disassemble(offset, size)):
                print("%-8d(%08x)" % (nb, idx), end=' ')
                i.show(idx)
                print()

                idx += i.get_length()


def androtrace_main(apk_file:str, list_modules:list[str], live:bool=False, enable_ui:bool=False) -> None:
    from androguard.pentest import Pentest
    from androguard.session import Session

    s = Session()

    if not live:
        with open(apk_file, "rb") as fp:
            raw = fp.read()

        h = s.add(apk_file, raw)
        logger.info("Added file to session: SHA256::{}".format(h))

    p = Pentest()
    p.print_devices()
    p.connect_default_usb()
    p.start_trace(apk_file, s, list_modules, live=live)

    if enable_ui:
        logger.remove(1)
        from prompt_toolkit.eventloop.inputhook import InputHookContext, set_eventloop_with_inputhook
        from prompt_toolkit.application import get_app
        import time

        time.sleep(1)

        ui = DynamicUI(p.message_queue)

        def inputhook(inputhook_context: InputHookContext):
            while not inputhook_context.input_is_ready():
                if ui.process_data():
                    get_app().invalidate()
                else:
                    time.sleep(0.1)

        set_eventloop_with_inputhook(inputhook=inputhook)

        ui.run()
    else:
        logger.warning("Type 'e' to exit the strace ")
        s = ""
        while (s != 'e') and (not p.is_detached()):
            s = input("Type 'e' to exit:")


def androdump_main(package_name:str, list_modules:list[str]) -> None:
    from androguard.pentest import Pentest
    from androguard.session import Session

    s = Session()

    p = Pentest()
    p.print_devices()
    p.connect_default_usb()
    p.start_trace(package_name, s, list_modules, live=True, dump=True)
