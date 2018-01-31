# Convert the Mappings from axplorer to JSON and convert to the format androguard uses.

from androguard.core.bytecodes.dvm import TYPE_DESCRIPTOR
import os
import sys
import re
from collections import defaultdict
from pprint import pprint
import json
import datetime
import time

# Create a reverse mapping of the TYPE_DESCRIPTORS
R_TYPE_DESCRIPTOR = {v: k for k, v in TYPE_DESCRIPTOR.items()}


def name_to_androguard(n):
    """
    Convert a object or primitive name into androguard syntax

    For example:
        byte --> B
        foo.bar.bla --> Lfoo/bar/bla;
        [int --> [I

    There is also a special case, where some arrays are specified differently:
        B[] --> [B
        foo.bar.bla[] --> [Lfoo/bar/bla;

    :param n:
    :return:
    """
    if n == "":
        return ""
    is_array = ""
    if n.startswith("["):
        is_array = "["
        n = n[1:]
    elif n.endswith("[]"):
        # Another special array type...
        # Probably a bug? See
        if n[:-2] in TYPE_DESCRIPTOR:
            return "[{}".format(n[0])
        else:
            n = n[:-2]
            is_array = "["
    if n in R_TYPE_DESCRIPTOR:
        return "{}{}".format(is_array, R_TYPE_DESCRIPTOR[n])
    else:
        # assume class
        return "{}L{};".format(is_array, n.replace(".", "/"))


def convert_name(s):
    """
    Converts a line of axplorer format into androguard method signature + permission
    :param s:
    :return:
    """
    m = re.compile(r"^(.*)\.(.*)\((.*)\)(.*)  ::  (.*)$")
    res = m.search(s)
    if res:
        clname, methodname, all_args, ret, perm = res.groups()
        args = " ".join(map(name_to_androguard, all_args.split(",")))

        clname = name_to_androguard(clname)
        ret = name_to_androguard(ret)

        return "{}-{}-({}){}".format(clname, methodname, args, ret), perm
    else:
        raise ValueError("what?")


def generate_mappings(axplorerdir="libraries/axplorer", outfolder="androguard/core/api_specific_resources/api_permission_mappings"):
    """
    Generate the permission mappings from a axplorer root dir into a given folder.
    For each API Level, separate json file will be created.

    :param axplorerdir: path to the axplorer dir
    :param outfolder: path to the folder where the resulting json files are put
    """
    res = dict()
    for root, dirs, files in os.walk(os.path.join(axplorerdir, "permissions")):
        for fi in files:
            if fi.startswith("cp-map-"):
                # We currently do not parse those files
                print("ignored {}".format(fi))
                continue
            elif fi.startswith("framework-map-") or fi.startswith("sdk-map-"):
                sdk_version = fi.rsplit("-", 1)[1][:-4]
                print("Found file:", fi, "for API level:", sdk_version)
                if sdk_version not in res:
                    res[sdk_version] = defaultdict(list)
                with open(os.path.join(root, fi), "r") as f:
                    for line in f.read().splitlines():
                        meth, perm = convert_name(line)
                        res[sdk_version][meth].append(perm)

    for api, v in res.items():
        with open(os.path.join(outfolder, "permissions_{}.json".format(api)), "w") as fp:
            fp.write("# API Permission mappings for API Version {}, generated from axplorer data\n".format(api))
            fp.write("# at {}\n".format(datetime.datetime.today()))
            fp.write("\n")
            json.dump(v, fp)

if __name__ == "__main__":
    if not os.path.isfile(os.path.join("libraries/axplorer", "README.md")):
        print("It does not look like the axplorer repo is checked out!", file=sys.stderr)
        sys.exit(1)

    generate_mappings()
