import json
import os
import re
import logging

log = logging.getLogger(__name__)


class APILevelNotFoundError(Exception):
    pass


def load_permissions(apilevel, permtype='permissions'):
    """
    Load the Permissions for the given apilevel.

    The permissions lists are generated using this tool: https://github.com/U039b/aosp_permissions_extraction

    Has a fallback to select the maximum or minimal available API level.
    For example, if 28 is requested but only 26 is available, 26 is returned.
    If 5 is requested but 16 is available, 16 is returned.

    If an API level is requested which is in between of two API levels we got,
    the lower level is returned. For example, if 5,6,7,10 is available and 8 is
    requested, 7 is returned instead.

    :param apilevel:  integer value of the API level
    :param permtype: either load permissions (:code:`'permissions'`) or
    permission groups (:code:`'groups'`)
    :return: a dictionary of {Permission Name: {Permission info}
    """

    if permtype not in ['permissions', 'groups']:
        raise ValueError("The type of permission list is not known.")

    # Usually apilevel is supplied as string...
    apilevel = int(apilevel)

    root = os.path.dirname(os.path.realpath(__file__))
    permissions_file = os.path.join(root, "aosp_permissions", "permissions_{}.json".format(apilevel))

    levels = filter(lambda x: re.match(r'^permissions_\d+\.json$', x), os.listdir(os.path.join(root, "aosp_permissions")))
    levels = list(map(lambda x: int(x[:-5].split('_')[1]), levels))

    if not levels:
        log.error("No Permissions available, can not load!")
        return {}

    log.debug("Available API levels: {}".format(", ".join(map(str, sorted(levels)))))

    if not os.path.isfile(permissions_file):
        if apilevel > max(levels):
            log.warning("Requested API level {} is larger than maximum we have, returning API level {} instead.".format(apilevel, max(levels)))
            return load_permissions(max(levels), permtype)
        if apilevel < min(levels):
            log.warning("Requested API level {} is smaller than minimal we have, returning API level {} instead.".format(apilevel, max(levels)))
            return load_permissions(min(levels), permtype)

        # Missing level between existing ones, return the lower level
        lower_level = max(filter(lambda x: x < apilevel, levels))
        log.warning("Requested API Level could not be found, using {} instead".format(lower_level))
        return load_permissions(lower_level, permtype)

    with open(permissions_file, "r") as fp:
        return json.load(fp)[permtype]


def load_permission_mappings(apilevel):
    """
    Load the API/Permission mapping for the requested API level.
    If the requetsed level was not found, None is returned.

    :param apilevel: integer value of the API level, i.e. 24 for Android 7.0
    :return: a dictionary of {MethodSignature: [List of Permissions]}
    """
    root = os.path.dirname(os.path.realpath(__file__))
    permissions_file = os.path.join(root, "api_permission_mappings", "permissions_{}.json".format(apilevel))

    if not os.path.isfile(permissions_file):
        return {}

    with open(permissions_file, "r") as fp:
        return json.load(fp)
