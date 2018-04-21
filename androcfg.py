#!/usr/bin/env python3
from androguard.misc import AnalyzeAPK
from androguard.core.androconf import show_logging
from androguard.core.analysis.analysis import ExternalMethod
import matplotlib.pyplot as plt
import networkx as nx
from argparse import ArgumentParser
import sys
import logging

log = logging.getLogger("androcfg")


def generate_graph(dx, classname=".*", methodname=".*", descriptor=".*",
        accessflags=".*"):
    """
    Generate a directed graph based on the methods found by the filters applied.
    The filters are the same as in
    :meth:`~androguard.core.analaysis.analaysis.Analysis.find_methods`

    A networkx.DiGraph is returned, containing all edges only once!
    that means, if a method calls some method twice or more often, there will
    only be a single connection.

    :param dx: :class:`~androguard.core.analysis.analysis.Analysis`

    :rtype: DiGraph
    """

    CFG = nx.DiGraph()

    # Note: If you create the CFG from many classes at the same time, the drawing
    # will be a total mess...
    for m in dx.find_methods(classname=classname, methodname=methodname,
            descriptor=descriptor, accessflags=accessflags):
        orig_method = m.get_method()
        print("Found Method --> {}".format(orig_method))
        # orig_method might be a ExternalMethod too...
        # so you can check it here also:
        if isinstance(orig_method, ExternalMethod):
            is_this_external = True
            # If this class is external, there will be very likely
            # no xref_to stored! If there is, it is probably a bug in androguard...
        else:
            is_this_external = False

        CFG.add_node(orig_method, external=is_this_external)

        for other_class, callee, offset in m.get_xref_to():
            if isinstance(callee, ExternalMethod):
                is_external = True
            else:
                is_external = False

            if callee not in CFG.node:
                CFG.add_node(callee, external=is_external)

            # As this is a DiGraph and we are not interested in duplicate edges,
            # check if the edge is already in the edge set.
            # If you need all calls, you probably want to check out MultiDiGraph
            if not CFG.has_edge(orig_method, callee):
                CFG.add_edge(orig_method, callee)

    return CFG


def plot(CFG):
    """
    Plot the call graph using matplotlib
    For larger graphs, this should not be used!
    """
    pos = nx.spring_layout(CFG)

    internal = []
    external = []

    for n in CFG.node:
        if isinstance(n, ExternalMethod):
            external.append(n)
        else:
            internal.append(n)

    nx.draw_networkx_nodes(CFG, pos=pos, node_color='r', nodelist=internal)
    nx.draw_networkx_nodes(CFG, pos=pos, node_color='b', nodelist=external)
    nx.draw_networkx_edges(CFG, pos, arrow=True)
    nx.draw_networkx_labels(CFG, pos=pos, labels={x: "{} {}".format(x.get_class_name(), x.get_name()) for x in CFG.edge})
    plt.draw()
    plt.show()

def _write_gml(G, path):
    """
    Wrapper around nx.write_gml
    """
    return nx.write_gml(G, path, stringizer=str)


def main():
    parser = ArgumentParser(description="Create a Call Graph based on the data"
            "of Analysis and export it into a graph format.")

    parser.add_argument("APK", nargs=1, help="The APK to analyze")
    parser.add_argument("--output", "-o", default="callgraph.gml",
            help="Filename of the output file, the extension is used to decide which format to use (default callgraph.gml)")
    parser.add_argument("--show", "-s", action="store_true", default=False,
            help="instead of saving the graph, print it with mathplotlib (you might not see anything!")
    parser.add_argument("--verbose", "-v", action="store_true", default=False,
            help="Print more output")

    args = parser.parse_args()

    if args.verbose:
        show_logging(logging.INFO)

    a, d, dx = AnalyzeAPK(args.APK)

    CFG = generate_graph(dx)

    write_methods = dict(gml=_write_gml,
                         gexf=nx.write_gexf,
                         gpickle=nx.write_gpickle,
                         graphml=nx.write_graphml,
                         yaml=nx.write_yaml,
                         net=nx.write_pajek,
                        )

    if args.show:
        plot(CFG)
    else:
        writer = args.output.rsplit(".", 1)[1]
        if writer in ["bz2", "gz"]:
            writer = args.output.rsplit(".", 2)[1]
        if writer not in write_methods:
            print("Could not find a method to export files to {}!".format(writer))
            sys.exit(1)

        write_methods[writer](CFG, args.output)


if __name__ == "__main__":
    main()
