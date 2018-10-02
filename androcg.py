#!/usr/bin/env python3
from argparse import ArgumentParser

from androguard.cli import androcg_main


def create_parser():
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
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    androcg_main(args.verbose,
                 args.APK[0],
                 args.classname,
                 args.methodname,
                 args.descriptor,
                 args.accessflag,
                 args.no_isolated,
                 args.show,
                 args.output)


if __name__ == "__main__":
    main()
