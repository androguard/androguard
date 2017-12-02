# Functions that might be useful


def read(filename, binary=True):
    with open(filename, 'rb' if binary else 'r') as f:
        return f.read()


def get_certificate_name_string(name, short=False):
    """
        Return the distinguished name of an X509 Certificate

        :param name: Name object to return the DN from
        :param short: Use short form (Default: False)

        :type name: :class:`cryptography.x509.Name`
        :type short: Boolean

        :rtype: str
    """

    # For the shortform, we have a lookup table
    # See RFC4514 for more details
    sf = {
        "countryName": "C",
        "stateOrProvinceName": "ST",
        "localityName": "L",
        "organizationalUnitName": "OU",
        "organizationName": "O",
        "commonName": "CN",
        "emailAddress": "E",
    }
    return ", ".join(
        ["{}={}".format(attr.oid._name if not short or attr.oid._name not in sf else sf[attr.oid._name], attr.value) for
         attr in name])
