import binascii
import hashlib
import sys
from typing import BinaryIO, Union

from asn1crypto import keys, x509

#  External dependencies
# import asn1crypto
from asn1crypto.x509 import Name
from loguru import logger


class MyFilter:
    def __init__(self, level: str) -> None:
        self.level = level

    def __call__(self, record):
        levelno = logger.level(self.level).no
        return record["level"].no >= levelno

def set_log(level:str) -> None:
    """
    Sets the log for loguru based on the level being passed.
    The possible string values are:
     
    * `TRACE`
    * `DEBUG`
    * `INFO`
    * `SUCCESS`
    * `WARNING`
    * `ERROR`
    * `CRITICAL`
    
    :param level: the log level string
    """
    logger.remove(0)
    my_filter = MyFilter(level)
    logger.add(sys.stderr, filter=my_filter, level=0)


# Stuff that might be useful


def read_at(buff: BinaryIO, offset: int, size: int = -1) -> bytes:
    idx = buff.tell()
    buff.seek(offset)
    d = buff.read(size)
    buff.seek(idx)
    return d


def readFile(filename: str, binary: bool = True) -> bytes:
    """
    Open and read a file
    :param filename: filename to open and read
    :param binary: `True` if the file should be read as binary
    :return: bytes if binary is `True`, str otherwise
    """
    with open(filename, 'rb' if binary else 'r') as f:
        return f.read()


def get_certificate_name_string(
    name: Union[dict, Name], short: bool = False, delimiter: str = ', '
) -> str:
    """
    Format the Name type of a X509 Certificate in a human readable form.

    :param name: Name object to return the DN from
    :param short: Use short form (default: False)
    :param delimiter: Delimiter string or character between two parts (default: ', ')

    :returns: the name string
    """
    if isinstance(name, Name):  # asn1crypto.x509.Name):
        name = name.native

    # For the shortform, we have a lookup table
    # See RFC4514 for more details
    _ = {
        'business_category': ("businessCategory", "businessCategory"),
        'serial_number': ("serialNumber", "serialNumber"),
        'country_name': ("C", "countryName"),
        'postal_code': ("postalCode", "postalCode"),
        'state_or_province_name': ("ST", "stateOrProvinceName"),
        'locality_name': ("L", "localityName"),
        'street_address': ("street", "streetAddress"),
        'organization_name': ("O", "organizationName"),
        'organizational_unit_name': ("OU", "organizationalUnitName"),
        'title': ("title", "title"),
        'common_name': ("CN", "commonName"),
        'initials': ("initials", "initials"),
        'generation_qualifier': ("generationQualifier", "generationQualifier"),
        'surname': ("SN", "surname"),
        'given_name': ("GN", "givenName"),
        'name': ("name", "name"),
        'pseudonym': ("pseudonym", "pseudonym"),
        'dn_qualifier': ("dnQualifier", "dnQualifier"),
        'telephone_number': ("telephoneNumber", "telephoneNumber"),
        'email_address': ("E", "emailAddress"),
        'domain_component': ("DC", "domainComponent"),
        'name_distinguisher': ("nameDistinguisher", "nameDistinguisher"),
        'organization_identifier': (
            "organizationIdentifier",
            "organizationIdentifier",
        ),
    }
    return delimiter.join(
        [
            "{}={}".format(
                _.get(attr, (attr, attr))[0 if short else 1], name[attr]
            )
            for attr in name
        ]
    )


def parse_public(data):
    from asn1crypto import keys, pem, x509

    """
    Loads a public key from a DER or PEM-formatted input.
    Supports RSA, DSA, EC public keys, and X.509 certificates.

    :param data: A byte string of the public key or certificate
    :raises ValueError: If the input data is not a known format
    :return: A keys.PublicKeyInfo object containing the parsed public key
    """

    # Check if the data is in PEM format (starts with "-----")
    if pem.detect(data):
        type_name, _, der_bytes = pem.unarmor(data)
        if type_name in ['PRIVATE KEY', 'RSA PRIVATE KEY']:
            raise ValueError(
                "The data specified appears to be a private key, not a public key."
            )
    else:
        # If not PEM, assume it's DER-encoded
        der_bytes = data

    # Try to parse the data as PublicKeyInfo (standard public key structure)
    try:
        public_key_info = keys.PublicKeyInfo.load(der_bytes)
        public_key_info.native  # Fully parse the object (asn1crypto is lazy)
        return public_key_info
    except ValueError:
        pass  # Not a PublicKeyInfo structure

    # Try to parse the data as an X.509 certificate
    try:
        certificate = x509.Certificate.load(der_bytes)
        public_key_info = certificate['tbs_certificate'][
            'subject_public_key_info'
        ]
        public_key_info.native  # Fully parse the object
        return public_key_info
    except ValueError:
        pass  # Not a certificate

    # Try to parse the data as RSAPublicKey
    try:
        rsa_public_key = keys.RSAPublicKey.load(der_bytes)
        rsa_public_key.native  # Fully parse the object
        # Wrap the RSAPublicKey in PublicKeyInfo
        return keys.PublicKeyInfo.wrap(rsa_public_key, 'rsa')
    except ValueError:
        pass  # Not an RSAPublicKey structure

    raise ValueError(
        "The data specified does not appear to be a known public key or certificate format."
    )


def calculate_fingerprint(key_object):
    """
    Calculates a SHA-256 fingerprint of the public key based on its components.

    :param key_object: A keys.PublicKeyInfo object containing the parsed public key
    :return: The fingerprint of the public key as a byte string
    """

    to_hash = None

    # RSA Public Key
    if key_object.algorithm == 'rsa':
        key = key_object['public_key'].parsed
        # Prepare string with modulus and public exponent
        to_hash = '%d:%d' % (
            key['modulus'].native,
            key['public_exponent'].native,
        )

    # DSA Public Key
    elif key_object.algorithm == 'dsa':
        key = key_object['public_key'].parsed
        params = key_object['algorithm']['parameters']
        # Prepare string with p, q, g, and public key
        to_hash = '%d:%d:%d:%d' % (
            params['p'].native,
            params['q'].native,
            params['g'].native,
            key.native,
        )

    # EC Public Key
    elif key_object.algorithm == 'ec':
        public_key = key_object['public_key'].native
        # Prepare byte string with curve name and public key
        to_hash = '%s:' % key_object.curve[1]
        to_hash = to_hash.encode('utf-8') + public_key

    # Ensure to_hash is encoded as bytes if it's a string
    if isinstance(to_hash, str):
        to_hash = to_hash.encode('utf-8')

    # Return the SHA-256 hash of the formatted key data
    return hashlib.sha256(to_hash).digest()
