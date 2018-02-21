# Convert the Mappings from axplorer to JSON and convert to the format androguard uses.

from androguard.core.bytecodes.dvm_types import TYPE_DESCRIPTOR
import os
import sys
import re
from collections import defaultdict
from pprint import pprint
import json
import datetime
from lxml import etree
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
    # FIXME what about n-dimensional arrays?
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

        # perm is actually a comma separated list of permissions
        return "{}-{}-({}){}".format(clname, methodname, args, ret), perm.split(", ")
    else:
        raise ValueError("what?")


def generate_mappings(axplorerdir="libraries/axplorer", outfolder="androguard/core/api_specific_resources"):
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
                        for p in perm:
                            res[sdk_version][meth].append(p)

    for api, v in res.items():
        with open(os.path.join(outfolder, "api_permission_mappings", "permissions_{}.json".format(api)), "w") as fp:
            json.dump(v, fp, indent="    ")

    # Next, we generate the permission lists, based on the AndroidManifest.xml files.
    # Thise files typically reside in the platform_framework_base repository
    # in the folder "master/core/res/". This AndroidManifest.xml file contains
    # all the permissions that are defined by the android system.
    # Of course, there are even more files (platform packages)
    # but the question is always, if these should be put into this list as well...
    # In this case, we collect all permissions that are extracted by axplorer as well.
    res = defaultdict(dict)
    XMLNS = '{http://schemas.android.com/apk/res/android}'

    re_api = re.compile(r".*manifests[\\/]api-([0-9]+)")
    for root, dirs, files in os.walk(os.path.join(axplorerdir, "manifests")):
        for fi in files:
            reres = re_api.match(root)
            if not reres:
                continue
            api = int(reres[1])
            p = os.path.join(root, fi)

            with open(p, "rb") as f:
                tree = etree.XML(f.read())
            matches = tree.xpath('permission')

            def _get_attrib(elem, attr):
                if XMLNS + attr in elem.attrib:
                    return elem.attrib[XMLNS + attr]
                else:
                    return ""

            for match in matches:
                name = match.attrib[XMLNS + "name"]
                d = dict(permissionGroup=_get_attrib(match, "permissionGroup"),
                         description=_get_attrib(match, "description"),
                         protectionLevel=_get_attrib(match, "protectionLevel"),
                         label=_get_attrib(match, "label"))

                if name in res[api]:
                    print("Potential collision of permission in api {}: {}".format(api, name))
                res[api][name] = d

    for api, v in res.items():
        print("Permissions for API: {}, found {} permissions".format(api, len(v)))
        with open(os.path.join(outfolder, "aosp_permissions", "permissions_{}.json".format(api)), "w") as fp:
            json.dump(v, fp, indent="    ")



if __name__ == "__main__":
    if not os.path.isfile(os.path.join("libraries/axplorer", "README.md")):
        print("It does not look like the axplorer repo is checked out!", file=sys.stderr)
        sys.exit(1)

    generate_mappings()
