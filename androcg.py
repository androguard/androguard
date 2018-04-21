#!/usr/bin/env python3
from androguard.misc import AnalyzeAPK
from androguard.core.androconf import show_logging
from androguard.core.analysis.analysis import ExternalMethod
from androguard.core.bytecode import FormatClassToJava
import matplotlib.pyplot as plt
import networkx as nx
from argparse import ArgumentParser
import sys
import logging

log = logging.getLogger("androcfg")


def _add_node(G, method, entry_points):
    """
    Wrapper to add methods to a graph
    """
    if method not in G.node:
        if isinstance(method, ExternalMethod):
            is_external = True
        else:
            is_external = False

        if method.get_class_name() in entry_points:
            is_entry_point = True
        else:
            is_entry_point = False

        G.add_node(method, external=is_external, entrypoint=is_entry_point)


def generate_graph(dx, classname=".*", methodname=".*", descriptor=".*",
        accessflags=".*", no_isolated=False, entry_points=[]):
    """
    Generate a directed graph based on the methods found by the filters applied.
    The filters are the same as in
    :meth:`~androguard.core.analaysis.analaysis.Analysis.find_methods`

    A networkx.DiGraph is returned, containing all edges only once!
    that means, if a method calls some method twice or more often, there will
    only be a single connection.

    :param dx: :class:`~androguard.core.analysis.analysis.Analysis`
    :param entry_points: A list of classes that are marked as entry point

    :rtype: DiGraph
    """

    CG = nx.DiGraph()

    # Note: If you create the CG from many classes at the same time, the drawing
    # will be a total mess...
    for m in dx.find_methods(classname=classname, methodname=methodname,
            descriptor=descriptor, accessflags=accessflags):
        orig_method = m.get_method()
        log.info("Found Method --> {}".format(orig_method))

        if no_isolated and len(m.get_xref_to) == 0:
            log.info("Skipped {}, because if has no xrefs".format(orig_method))
            continue

        _add_node(CG, orig_method, entry_points)

        for other_class, callee, offset in m.get_xref_to():
            _add_node(CG, callee, entry_points)

            # As this is a DiGraph and we are not interested in duplicate edges,
            # check if the edge is already in the edge set.
            # If you need all calls, you probably want to check out MultiDiGraph
            if not CG.has_edge(orig_method, callee):
                CG.add_edge(orig_method, callee)

    return CG


def plot(CG):
    """
    Plot the call graph using matplotlib
    For larger graphs, this should not be used!
    """
    pos = nx.spring_layout(CG)

    internal = []
    external = []

    for n in CG.node:
        if isinstance(n, ExternalMethod):
            external.append(n)
        else:
            internal.append(n)

    nx.draw_networkx_nodes(CG, pos=pos, node_color='r', nodelist=internal)
    nx.draw_networkx_nodes(CG, pos=pos, node_color='b', nodelist=external)
    nx.draw_networkx_edges(CG, pos, arrow=True)
    nx.draw_networkx_labels(CG, pos=pos, labels={x: "{} {}".format(x.get_class_name(), x.get_name()) for x in CG.edge})
    plt.draw()
    plt.show()

def _write_gml(G, path):
    """
    Wrapper around nx.write_gml
    """
    return nx.write_gml(G, path, stringizer=str)


def main():
    parser = ArgumentParser(description="Create a call graph based on the data"
            "of Analysis and export it into a graph format.")

    parser.add_argument("APK", nargs=1, help="The APK to analyze")
    parser.add_argument("--output", "-o", default="callgraph.gml",
            help="Filename of the output file, the extension is used to decide which format to use (default callgraph.gml)")
    parser.add_argument("--show", "-s", action="store_true", default=False,
            help="instead of saving the graph, print it with mathplotlib (you might not see anything!")
    parser.add_argument("--verbose", "-v", action="store_true", default=False,
            help="Print more output")
    parser.add_argument("--classname", default=".*", help="Regex to filter by classname")
    parser.add_argument("--methodname", default=".*", help="Regex to filter by methodname")
    parser.add_argument("--descriptor", default=".*", help="Regex to filter by descriptor")
    parser.add_argument("--accessflag", default=".*", help="Regex to filter by accessflags")
    parser.add_argument("--no-isolated", default=False, action="store_true",
            help="Do not store methods which has no xrefs")

    args = parser.parse_args()

    if args.verbose:
        show_logging(logging.INFO)

    a, d, dx = AnalyzeAPK(args.APK[0])

    entry_points = map(FormatClassToJava, a.get_activities() + a.get_providers() + a.get_services() + a.get_receivers())
    entry_points = list(entry_points)

    log.info("Found The following entry points by search AndroidManifest.xml: {}".format(entry_points))

    CG = generate_graph(dx,
                        args.classname,
                        args.methodname,
                        args.descriptor,
                        args.accessflag,
                        args.no_isolated,
                        entry_points,
                       )

    write_methods = dict(gml=_write_gml,
                         gexf=nx.write_gexf,
                         gpickle=nx.write_gpickle,
                         graphml=nx.write_graphml,
                         yaml=nx.write_yaml,
                         net=nx.write_pajek,
                        )

    if args.show:
        plot(CG)
    else:
        writer = args.output.rsplit(".", 1)[1]
        if writer in ["bz2", "gz"]:
            writer = args.output.rsplit(".", 2)[1]
        if writer not in write_methods:
            print("Could not find a method to export files to {}!".format(writer))
            sys.exit(1)

        write_methods[writer](CG, args.output)


if __name__ == "__main__":
    main()
