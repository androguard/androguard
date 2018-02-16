import json
import os


class APILevelNotFoundError(Exception):
    pass


def load_permissions(apilevel):
    """
    Load the Permissions for the given apilevel

    :param apilevel:  integer value of the API level
    :return: a dictionary of {Permission Name: {Permission info}
    """
    permissions_file = os.path.join("aosp_permissions", "permissions_{}.json".format(apilevel))

    if not os.path.isfile(permissions_file):
        return {}

    with open(permissions_file, "r") as fp:
        return json.load(fp)


def load_permission_mappings(apilevel):
    """
    Load the API/Permission mapping for the requested API level.
    If the requetsed level was not found, None is returned.

    :param apilevel: integer value of the API level, i.e. 24 for Android 7.0
    :return: a dictionary of {MethodSignature: [List of Permissions]}
    """
    permissions_file = os.path.join("api_permission_mappings", "permissions_{}.json".format(apilevel))

    if not os.path.isfile(permissions_file):
        return {}

    with open(permissions_file, "r") as fp:
        return json.load(fp)
