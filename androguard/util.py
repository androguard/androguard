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
    _ = {
        'business_category' : ("businessCategory", "businessCategory"),
        'serial_number' : ("serialNumber", "serialNumber"),
        'country_name' : ("C", "countryName"),
        'postal_code' : ("postalCode", "postalCode"),
        'state_or_province_name' : ("ST", "stateOrProvinceName"),
        'locality_name' : ("L", "localityName"),
        'street_address' : ("street", "streetAddress"),
        'organization_name' : ("O", "organizationName"),
        'organizational_unit_name' : ("OU", "organizationalUnitName"),
        'title' : ("title", "title"),
        'common_name' : ("CN", "commonName"),
        'initials' : ("initials", "initials"),
        'generation_qualifier' : ("generationQualifier", "generationQualifier"),
        'surname' : ("SN", "surname"),
        'given_name' : ("GN", "givenName"),
        'name' : ("name", "name"),
        'pseudonym' : ("pseudonym", "pseudonym"),
        'dn_qualifier' : ("dnQualifier", "dnQualifier"),
        'telephone_number' : ("telephoneNumber", "telephoneNumber"),
        'email_address' : ("E", "emailAddress"),
        'domain_component' : ("DC", "domainComponent"),
        'name_distinguisher' : ("nameDistinguisher", "nameDistinguisher"),
        'organization_identifier' : ("organizationIdentifier", "organizationIdentifier"),
    }
    return ", ".join(["{}={}".format(_.get(attr,(attr,attr))[0 if short else 1], name[attr]) for attr in name])
