Android Signing Certificates
============================

Androguard has the ability to get information about the signing certificate
found in APKs. Over the last versions of Androguard, different parsers has been
used to get certificate information.
The first parser was Chilkat_, then a mixture of pyasn1_ and cryptography_ was
used, while the latest parser uses the asn1crypto_ library.
Not all x509 parsers work with all certificates as there are plenty of examples
where the certificate creator does not follow the RFCs for creating
certificates. Some parsers do not accept such broken certificates and will fail
to parse them.

The purpose of Androids signing process is not to provide verified information
about the author, like with JAR signing, but only provide a way to check the
integrity of the APK as well as check if an APK can be upgraded by comparing the
certificate fingerprints.
In some sense, the certificate information can be used to find other APKs from
the same author - as long as the signing key was kept secret! There are also
public available signing keys, like the ones from AOSP, thus the same fingerprint of
two APKs does not always tell you it was signed by the same person.

If you like to know more about the APK signing process, please read the official
documentation about Signing_.
There is also an official tool to verify and sign APKs called apksigner_.

Working with certificates
-------------------------

Inside the APK, there are two places for certificates:

* v1 aka JAR signing: PKCS#7 files in the :code:`META-INF` folder
* v2 aka APK signing: a special section in the ZIP containing DER coded
  certificates

The easiest way to get to the certificate information is :ref:`androsign`.
It gives similar output to apksigner_, but uses only androguard.
It can not verify the integrity of the file though.

.. code-block:: bash

    $ androsign.py --all --show examples/signing/apksig/golden-aligned-v1v2-out.apk
    golden-aligned-v1v2-out.apk, package: 'android.appsecurity.cts.tinyapp'
    Is signed v1: True
    Is signed v2: True
    Found 1 unique certificates
    Issuer: CN=rsa-2048
    Subject: CN=rsa-2048
    Serial Number: 0x8e35306cdd0115f7L
    Hash Algorithm: sha256
    Signature Algorithm: rsassa_pkcs1v15
    Valid not before: 2016-03-31 14:57:49+00:00
    Valid not after: 2043-08-17 14:57:49+00:00
    sha1 0aa07c0f297b4ae834dc85a17eea8c2cf9380ff7
    sha256 fb5dbd3c669af9fc236c6991e6387b7f11ff0590997f22d0f5c74ff40e04fca8
    sha512 4da6e6744a4dabef192b198be13b4492b0ce97469f3ce223dd9b7e8df2ee952328e06651e5e65dd3b60ac5e3946e16cf7059b20d4d4a649957c1e3055c2e1fb8
    md5 e995a5ed7137307661f854e66901ee9e

As a comparison, here is the output of apksigner_:

.. code-block:: bash

    $ apksigner verify -verbose --print-certs examples/signing/apksig/golden-aligned-v1v2-out.apk
    Verifies
    Verified using v1 scheme (JAR signing): true
    Verified using v2 scheme (APK Signature Scheme v2): true
    Number of signers: 1
    Signer #1 certificate DN: CN=rsa-2048
    Signer #1 certificate SHA-256 digest: fb5dbd3c669af9fc236c6991e6387b7f11ff0590997f22d0f5c74ff40e04fca8
    Signer #1 certificate SHA-1 digest: 0aa07c0f297b4ae834dc85a17eea8c2cf9380ff7
    Signer #1 certificate MD5 digest: e995a5ed7137307661f854e66901ee9e
    Signer #1 key algorithm: RSA
    Signer #1 key size (bits): 2048
    Signer #1 public key SHA-256 digest: 8cabaedf32f1052f6bc5edbeb84d1c500f8c1aa15f8944bf22c46e44c5c4f7e8
    Signer #1 public key SHA-1 digest: a708f9a777bac814e6634b02521224537ec3e019
    Signer #1 public key MD5 digest: c0c8801fabf2ad970282be1c41584003

The most interesting part is probably the fingerprint of the certificate (not of
the public key!).
You can use it to search for similar APKs.
Sometimes there is a confusion about this fingerprint: The fingerprint is not
the checksum of the whole PKCS#7 file, but only of a certain part of it!
Calculating the hash of a PKCS#7 file from two different, but equally signed
APKs will result in a different hash. The fingerprint will stay the same though.

Androguard offers methods in the :class:`androguard.core.bytecodes.apk.APK`
class to iterate over the certificates found there.

.. code-block:: python

    from androguard.core.bytecodes.apk import APK

    a = APK('examples/signing/apksig/golden-aligned-v1v2-out.apk')

    # first check if this APK is signed
    print("APK is signed: {}".format(a.is_signed()))

    if a.is_signed():
        # Test if signed v1 or v2 or both
        print("APK is signed with: {}".format("both" if a.is_signed_v1() and
        a.is_signed_v2() else "v1" if a.is_signed_v1() else "v2"))

    # Iterate over all certificates
    for cert in a.get_certificates():
        # Each cert is now a asn1crypt.x509.Certificate object
        # From the Certificate object, we can query stuff like:
        cert.sha1  # the sha1 fingerprint
        cert.sha256  # the sha256 fingerprint
        cert.issuer.human_friendly  # issuer
        cert.subject.human_friendly  # subject, usually the same
        cert.hash_algo  # hash algorithm
        cert.signature_algo  # Signature algorithm
        cert.serial_number  # Serial number
        cert.contents  # The DER coded bytes of the certificate itself
        # ...


Please refer to the asn1crypto documentation_ for more information on the
features of the :code:`Certificate` class!


.. _Chilkat: https://www.chilkatsoft.com/
.. _pyasn1: https://pypi.org/project/pyasn1/
.. _cryptography: https://pypi.org/project/cryptography/
.. _asn1crypto: https://pypi.org/project/asn1crypto/
.. _Signing: https://source.android.com/security/apksigning/
.. _apksigner: https://developer.android.com/studio/command-line/apksigner
.. _documentation: https://github.com/wbond/asn1crypto#documentation

