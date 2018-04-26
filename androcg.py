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


def plot(CG):
    """
    Plot the call graph using matplotlib
    For larger graphs, this should not be used, as it is very slow
    and probably you can not see anything on it.

    :param CG: A networkx graph to plot
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

    CG = dx.get_call_graph(args.classname,
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
