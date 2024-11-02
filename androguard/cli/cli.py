#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Androguard is a full Python tool to reverse Android Applications."""
import json
import sys

import click
from loguru import logger

import androguard.core.apk
from androguard import util
from androguard.cli.main import (androarsc_main,
                                 androaxml_main,
                                 export_apps_to_format,
                                 androsign_main,
                                 androlyze_main,
                                 androdis_main,
                                 androtrace_main,
                                 androdump_main,
                                 )

import networkx as nx

@click.group(help=__doc__)
@click.version_option(version=androguard.__version__)
@click.option("--verbose", "--debug", 'verbosity', flag_value='verbose', help="Print more")
def entry_point(verbosity):
    if verbosity is None:
        util.set_log("ERROR")
    else:
        util.set_log("INFO")
    logger.add("androguard.log", retention="10 days")


@entry_point.command()
@click.option(
    '--input', '-i', 'input_',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help='AndroidManifest.xml or APK to parse (legacy option)',
)
@click.option(
    '--output', '-o',
    help='filename to save the decoded AndroidManifest.xml to, default stdout',
)
@click.option("--resource", "-r",
              help="Resource (any binary XML file) inside the APK to parse instead of AndroidManifest.xml"
              )
@click.argument(
    'file_',
    required=False,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
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
    '--list-packages', is_flag=True,
    default=False,
    help='List all package names and exit',
)
@click.option(
    '--list-locales', is_flag=True,
    default=False,
    help='List all package names and exit',
)
@click.option(
    '--list-types', is_flag=True,
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
    from androguard.core import axml, apk

    if file_ and input_:
        logger.info("Can not give --input and positional argument! Please use only one of them!")
        sys.exit(1)

    if not input_ and not file_:
        logger.info("Give one file to decode!")
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
            logger.error("The APK does not contain a resources file!")
            sys.exit(0)
    elif ret_type == "ARSC":
        with open(fname, 'rb') as fp:
            arscobj = axml.ARSCParser(fp.read())
            if not arscobj:
                logger.error("The resources file seems to be invalid!")
                sys.exit(1)
    else:
        logger.error("Unknown file type!")
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
    '--input', '-i', 'input_',
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help='APK to parse (legacy option)',
)
@click.argument(
    'file_',
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
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
    type=click.Choice(['png', 'jpg', 'raw'])
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
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
)
def sign(hash_, print_all_hashes, show, apk):
    """Return the fingerprint(s) of all certificates inside an APK."""
    androsign_main(apk, hash_, print_all_hashes, show)


@entry_point.command()
@click.argument(
    'apks',
    nargs=-1,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
def apkid(apks):
    """Return the packageName/versionCode/versionName per APK as JSON."""
    from androguard.core.apk import get_apkid

    logger.debug("APKID")

    results = dict()
    for apk in apks:
        results[apk] = get_apkid(apk)
    print(json.dumps(results, indent=2))


@entry_point.command()
@click.option(
    '--session',
    help='Previously saved session to load instead of a file',
    type=click.Path(exists=True),
)
@click.argument(
    'apk',
    default=None,
    required=False,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
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
@click.argument(
    "DEX",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
)
def disassemble(offset, size, dex):
    """
    Disassemble Dalvik Code with size SIZE starting from an offset
    """
    androdis_main(offset, size, dex)


@entry_point.command()
@click.argument(
    'apk',
    default=None,
    required=False,
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
)
@click.option("-m", "--modules",
              multiple=True, default=[],
              help="A list of modules to load in frida")
@click.option(
    '--enable-ui', is_flag=True,
    default=False,
    help='Enable UI',
)
def trace(apk, modules, enable_ui):
    """
    Push an APK on the phone and start to trace all interesting methods from the modules list

    Example:

    \b
        $ androguard trace test.APK -m "ipc/*"  -m "webviews/*" -m "modules/**"
        $ androguard trace test.APK -m "ipc/*"  -m "webviews/*" -m "modules/**" --enable-ui
    """
    androtrace_main(apk, modules, False, enable_ui)


@entry_point.command()
@click.argument(
    'package_name',
    default=None,
    required=False,
)
@click.option("-m", "--modules",
              multiple=True, default=[],
              help="A list of modules to load in frida")
def dtrace(package_name, modules):
    """
    Start dynamically an installed APK on the phone and start to trace all interesting methods from the modules list

    Example:

    \b
        $ androguard dtrace package_name -m "ipc/*"  -m "webviews/*" -m "modules/**"
    """
    androtrace_main(package_name, modules, True)


@entry_point.command()
@click.argument(
    'package_name',
    default=None,
    required=False,
)
@click.option("-m", "--modules",
              multiple=True, default=["androguard/pentest/modules/helpers/dump/dexdump.js"],
              help="A list of modules to load in frida")
def dump(package_name, modules):
    """
    Start and dump dynamically an installed APK on the phone

    Example:

    \b
        $ androguard dump package_name
    """
    androdump_main(package_name, modules)

# callgraph exporting utility functions
def _write_gml(G, path):
    """Wrapper around nx.write_gml"""
    return nx.write_gml(G, path, stringizer=str)

def _write_gpickle(G, path):
    """Wrapper around pickle dump"""
    import pickle
    with open(path, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

def _write_yaml(G, path):
    """Wrapper around yaml dump"""
    import yaml
    with open(path, 'w') as f:
        yaml.dump(G, f)

# mapping of types to their respective exporting functions
write_methods = dict(
    gml=_write_gml,
    gexf=nx.write_gexf,
    # gpickle=_write_gpickle,   # Pickling can't be done due to BufferedReader attributes (e.g. EncodedMethod.buff) not being serializable
    graphml=nx.write_graphml,
    # yaml=_write_yaml,         # Same limitation as gpickle
    net=nx.write_pajek)

@entry_point.command()
@click.argument(
    'file_',
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    required=True,
)
@click.option(
    '--output', '-o',
    default='callgraph.gml',
    help='Filename of the output graph file',
)
@click.option(
    '--output-type',
    type=click.Choice(
        list(write_methods.keys()),
        case_sensitive=False),
    default='gml',
    help='Type of the graph to output '
)
@click.option(
    '--show', '-s',
    default=False,
    is_flag=True,
    help='instead of saving the graph file, render it with matplotlib',
)
@click.option(
    '--classname',
    default='.*',
    help='Regex to filter by classname',
)
@click.option(
    '--methodname',
    default='.*',
    help='Regex to filter by methodname',
)
@click.option(
    '--descriptor',
    default='.*',
    help='Regex to filter by descriptor',
)
@click.option(
    '--accessflag',
    default='.*',
    help='Regex to filter by accessflag',
)
@click.option(
    '--no-isolated',
    default=False,
    is_flag=True,
    help='Do not store methods which has no xrefs',
)
def cg(
    file_,
    output,
    output_type,
    show,
    classname,
    methodname,
    descriptor,
    accessflag,
    no_isolated):
    """
    Create a call graph based on the data of Analysis and export it into a graph format.
    """
    from androguard.core.bytecode import FormatClassToJava
    from androguard.misc import AnalyzeAPK
    from androguard.core.analysis.analysis import ExternalMethod

    import matplotlib.pyplot as plt

    a, d, dx = AnalyzeAPK(file_)

    entry_points = map(FormatClassToJava,
                       a.get_activities() + a.get_providers() +
                       a.get_services() + a.get_receivers())
    entry_points = list(entry_points)

    callgraph = dx.get_call_graph(
        classname,
        methodname,
        descriptor,
        accessflag,
        no_isolated,
        entry_points
    )

    if show:
        try:
            import PyQt5
        except ImportError:
            print("PyQt5 is not installed. In most OS you can install it by running 'pip install PyQt5'.\n")
            exit()
        pos = nx.spring_layout(callgraph)
        internal = []
        external = []

        for n in callgraph:
            if isinstance(n, ExternalMethod):
                external.append(n)
            else:
                internal.append(n)

        nx.draw_networkx_nodes(
            callgraph,
            pos=pos, node_color='r',
            nodelist=internal)

        nx.draw_networkx_nodes(
            callgraph,
            pos=pos,
            node_color='b',
            nodelist=external)

        nx.draw_networkx_edges(
            callgraph,
            pos,
            width=0.5,
            arrows=True)

        nx.draw_networkx_labels(callgraph,
                                pos=pos,
                                font_size=6,
                                labels={n: f"{n.get_class_name()} {n.name} {n.descriptor}"
                                        for n in callgraph.nodes})

        plt.draw()
        plt.show()

    else:
        output_type_lower = output_type.lower()
        if output_type_lower not in write_methods:
            print(f"Could not find a method to export files to {output_type_lower}!")
            sys.exit(1)

        write_methods[output_type_lower](callgraph, output)


if __name__ == '__main__':
    entry_point()
