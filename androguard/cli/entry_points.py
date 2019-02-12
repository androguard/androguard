#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Androguard is a full Python tool to play with Android files."""

from __future__ import print_function

# core modules
import sys
import logging

# 3rd party modules
import click

# local modules
import androguard
from androguard.core.androconf import show_logging
from androguard.cli import (androarsc_main,
                            androaxml_main,
                            androcg_main,
                            export_apps_to_format,
                            androsign_main,
                            androlyze_main,
                            androgui_main,
                            androdis_main
                            )


@click.group(help=__doc__)
@click.version_option(version=androguard.__version__)
@click.option("--verbose", "--debug", 'verbosity', flag_value='verbose', help="Print more")
@click.option("--quiet", 'verbosity', flag_value='quiet', help="Print less (only warnings and above)")
@click.option("--silent", 'verbosity', flag_value='silent', help="Print no log messages")
def entry_point(verbosity):
    level = logging.INFO

    if verbosity == 'verbose':
        level = logging.DEBUG
    if verbosity == 'quiet':
        level = logging.WARNING

    # If something out of this module is imported, activate console logging
    if verbosity != 'silent':
        show_logging(level=level)


@entry_point.command()
@click.option(
    '--input', '-i', 'input_',
    type=click.Path(exists=True),
    help='AndroidManifest.xml or APK to parse (legacy option)',
)
@click.option(
    '--output', '-o',
    help='filename to save the decoded AndroidManifest.xml to, default stdout',
)
@click.option("--resource", "-r",
        help="Resource inside the APK to parse instead of AndroidManifest.xml"
)
@click.argument(
    'file_',
    type=click.Path(exists=True),
    # help='AndroidManifest.xml or APK to parse',
    required=False,
)
def axml(input_, output, file_, resource):
    """
    Parse the AndroidManifest.xml.

    Parsing is either direct or from a given APK and prints in XML format or
    saves to file.

    This tool can also be used to process any AXML encoded file, for example
    from the layout directory.

    Example:

    \b
        $ androguard axml AndroidManifest.xml
    """
    if file_ is not None and input_ is not None:
        print("Can not give --input and positional argument! "
              "Please use only one of them!")
        sys.exit(1)

    if file_ is None and input_ is None:
        print("Give one file to decode!")
        sys.exit(1)

    if file_ is not None:
        androaxml_main(file_, output, resource)
    elif input_ is not None:
        androaxml_main(input_, output, resource)


@entry_point.command()
@click.option(
    '--input', '-i', 'input_',
    type=click.Path(exists=True),
    help='resources.arsc or APK to parse (legacy option)',
)
@click.argument(
    'file_',
    # help='resources.arsc or APK to parse',
    required=False,
)
@click.option(
    '--output', '-o',
    # required=True,  #  not required due to --list-types
    help='filename to save the decoded resources to',
)
@click.option(
    '--package', '-p',
    help='Show only resources for the given package name '
         '(default: the first package name found)',
)
@click.option(
    '--locale', '-l',
    help='Show only resources for the given locale (default: \'\\x00\\x00\')',
)
@click.option(
    '--type', '-t', 'type_',
    help='Show only resources of the given type (default: public)',
)
@click.option(
    '--id', 'id_',
    help="Resolve the given ID for the given locale and package. Provide the hex ID!"
)
@click.option(
    '--list-packages', '-t', is_flag=True,
    default=False,
    help='List all package names and exit',
)
@click.option(
    '--list-locales', '-t', is_flag=True,
    default=False,
    help='List all package names and exit',
)
@click.option(
    '--list-types', '-t', is_flag=True,
    default=False,
    help='List all types and exit',
)
def arsc(input_,
         file_,
         output,
         package,
         locale,
         type_,
         id_,
         list_packages,
         list_locales,
         list_types):
    """
    Decode resources.arsc either directly from a given file or from an APK.

    Example:

    \b
        $ androguard arsc app.apk
    """
    from androguard.core import androconf
    from androguard.core.bytecodes import apk

    if file_ and input_:
        print("Can not give --input and positional argument! "
              "Please use only one of them!",
              file=sys.stderr)
        sys.exit(1)

    if not input_ and not file_:
        print("Give one file to decode!", file=sys.stderr)
        sys.exit(1)

    if input_:
        fname = input_
    else:
        fname = file_

    ret_type = androconf.is_android(fname)
    if ret_type == "APK":
        a = apk.APK(fname)
        arscobj = a.get_android_resources()
        if not arscobj:
            print("The APK does not contain a resources file!", file=sys.stderr)
            sys.exit(0)
    elif ret_type == "ARSC":
        with open(fname, 'rb') as fp:
            arscobj = apk.ARSCParser(fp.read())
            if not arscobj:
                print("The resources file seems to be invalid!", file=sys.stderr)
                sys.exit(1)
    else:
        print("Unknown file type!", file=sys.stderr)
        sys.exit(1)

    if id_:
        # Strip the @, if any
        if id_[0] == "@":
            id_ = id_[1:]
        try:
            i_id = int(id_, 16)
        except ValueError:
            print("ID '{}' could not be parsed! have you supplied the correct hex ID?".format(id_))
            sys.exit(1)

        name = arscobj.get_resource_xml_name(i_id)
        if not name:
            print("Specified resource was not found!")
            sys.exit(1)

        print("@{:08x} resolves to '{}'".format(i_id, name))
        print()

        # All the information is in the config.
        # we simply need to get the actual value of the entry
        for config, entry in arscobj.get_resolved_res_configs(i_id):
            print("{} = '{}'".format(config.get_qualifier() if not config.is_default() else "<default>", entry))

        sys.exit(0)

    if list_packages:
        print("\n".join(arscobj.get_packages_names()))
        sys.exit(0)

    if list_locales:
        for p in arscobj.get_packages_names():
            print("In Package:", p)
            print("\n".join(map(lambda x: "  \\x00\\x00"
                                if x == "\x00\x00"
                                else "  {}".format(x),
                                     sorted(arscobj.get_locales(p)))))
        sys.exit(0)

    if list_types:
        for p in arscobj.get_packages_names():
            print("In Package:", p)
            for locale in sorted(arscobj.get_locales(p)):
                print("  In Locale: {}".format("\\x00\\x00"
                      if locale == "\x00\x00" else locale))
                print("\n".join(map("    {}".format,
                                    sorted(arscobj.get_types(p, locale)))))
        sys.exit(0)

    androarsc_main(arscobj,
                   outp=output,
                   package=package,
                   typ=type_,
                   locale=locale)


@entry_point.command()
@click.option(
    '--output', '-o',
    default="callgraph.gml", show_default=True,
    help='Filename of the output file, the extension is used to decide which '
         'format to use (default callgraph.gml)',
)
@click.option(
    '--show', '-s',
    default=False,
    help='instead of saving the graph, print it with mathplotlib '
         '(you might not see anything!)',
)
@click.option(
    '--verbose', '-v', is_flag=True,
    default=False,
    help='Print more output',
)
@click.option(
    '--classname',
    default='.*', show_default=True,
    help='Regex to filter by classname',
)
@click.option(
    '--methodname',
    default='.*', show_default=True,
    help='Regex to filter by methodname',
)
@click.option(
    '--descriptor',
    default='.*', show_default=True,
    help='Regex to filter by descriptor',
)
@click.option(
    '--accessflag',
    default='.*', show_default=True,
    help='Regex to filter by accessflags',
)
@click.option(
    '--no-isolated/--isolated',
    default=False,
    help='Do not store methods which has no xrefs',
)
@click.argument(
    'APK',
    # help='The APK to analyze',
    nargs=1,
    required=False,
    type=click.Path(exists=True),
)
def cg(output,
       show,
       verbose,
       classname,
       methodname,
       descriptor,
       accessflag,
       no_isolated,
       apk):
    """
    Create a call graph and export it into a graph format.

    Example:

    \b
        $ androguard cg APK
    """
    androcg_main(verbose=verbose,
                 APK=apk,
                 classname=classname,
                 methodname=methodname,
                 descriptor=descriptor,
                 accessflag=accessflag,
                 no_isolated=no_isolated,
                 show=show,
                 output=output)


@entry_point.command()
@click.option(
    '--input', '-i', 'input_',
    type=click.Path(exists=True),
    help='APK to parse (legacy option)',
)
@click.argument(
    'file_',
    type=click.Path(exists=True),
    # help='APK to parse',
    required=False,
)
@click.option(
    '--output', '-o',
    required=True,
    help='output directory. If the output folder already exsist, '
         'it will be overwritten!',
)
@click.option(
    '--format', '-f', 'format_',
    help='Additionally write control flow graphs for each method, specify '
         'the format for example png, jpg, raw (write dot file), ...',
)
@click.option(
    '--jar', '-j',
    is_flag=True,
    default=False,
    help='Use DEX2JAR to create a JAR file',
)
@click.option(
    '--limit', '-l',
    help='Limit to certain methods only by regex (default: \'.*\')',
)
@click.option(
    '--decompiler', '-d',
    help='Use a different decompiler (default: DAD)',
)
def decompile(input_, file_, output, format_, jar, limit, decompiler):
    """
    Decompile an APK and create Control Flow Graphs.

    Example:

    \b
        $ androguard resources.arsc
    """
    from androguard import session
    if file_ and input_:
        print("Can not give --input and positional argument! "
              "Please use only one of them!", file=sys.stderr)
        sys.exit(1)

    if not input_ and not file_:
        print("Give one file to decode!", file=sys.stderr)
        sys.exit(1)

    if input_:
        fname = input_
    else:
        fname = file_

    s = session.Session()
    with open(fname, "rb") as fd:
        s.add(fname, fd.read())
    export_apps_to_format(fname, s, output, limit,
                          jar, decompiler, format_)


@entry_point.command()
@click.option(
    '--hash', 'hash_',
    type=click.Choice(['md5', 'sha1', 'sha256', 'sha512']),
    default='sha1', show_default=True,
    help='Fingerprint Hash algorithm',
)
@click.option(
    '--all', '-a', 'print_all_hashes',
    is_flag=True,
    default=False, show_default=True,
    help='Print all supported hashes',
)
@click.option(
    '--show', '-s',
    is_flag=True,
    default=False, show_default=True,
    help='Additionally of printing the fingerprints, show more '
         'certificate information',
)
@click.argument(
    'apk',
    # help='APK(s) to extract the Fingerprint of Certificates from',
    nargs=-1,
    required=False,
    type=click.Path(exists=True),
)
def sign(hash_, print_all_hashes, show, apk):
    """Return the fingerprint(s) of all certificates inside an APK."""
    androsign_main(apk, hash_, print_all_hashes, show)

@entry_point.command()
@click.argument(
    'apks',
    nargs=-1,
    required=False,
    type=click.Path(exists=True),
)
def apkid(apks):
    """Return the packageName/versionCode/versionName per APK as JSON."""
    import json
    import logging
    logging.getLogger("androguard.axml").setLevel(logging.ERROR)
    results = dict()
    for apk in apks:
        results[apk] = androguard.core.bytecodes.apk.get_apkid(apk)
    print(json.dumps(results, indent=2))


@entry_point.command()
@click.option(
    '--input_file', '-i',
    type=click.Path(exists=True),
)
@click.option(
    '--input_plugin', '-p',
    type=click.Path(exists=True),
)
def gui(input_file, input_plugin):
    """Androguard GUI"""
    androgui_main(input_file, input_plugin)


@entry_point.command()
@click.option(
    '--session',
    help='Previously saved session to load instead of a file',
    type=click.Path(exists=True),
)
@click.argument(
    'apk',
    # help='Start the shell with the given APK. a, d, dx are available then. Loading might be slower in this case!',
    default=None,
    required=False,
    type=click.Path(exists=True),
)
def analyze(session, apk):
    """Open a IPython Shell and start reverse engineering."""
    androlyze_main(session, apk)


@entry_point.command()
@click.option("-o", "--offset",
        default=0,
        type=int,
        help="Offset to start dissassembly inside the file")
@click.option("-s", "--size",
        default=0,
        type=int,
        help="Number of bytes from offset to disassemble, 0 for whole file")
@click.argument("DEX")
def disassemble(offset, size, dex):
    """
    Disassemble Dalvik Code with size SIZE starting from an offset
    """
    androdis_main(offset, size, dex)


if __name__ == '__main__':
    entry_point()
