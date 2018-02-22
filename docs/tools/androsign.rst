androsign - Print Certificate Fingerprints
==========================================

Get the fingerprints of the signing certificates inside an APK.

.. program-output:: python ../androsign.py -h

An example:

.. code-block:: bash

    $ androsign.py --all files/golden-aligned-v1v2-out.apk
    golden-aligned-v1v2-out.apk, package: 'android.appsecurity.cts.tinyapp'
    Is signed v1: True
    Is signed v2: True
    Found 1 unique certificates
    md5 e995a5ed7137307661f854e66901ee9e
    sha1 0aa07c0f297b4ae834dc85a17eea8c2cf9380ff7
    sha512 4da6e6744a4dabef192b198be13b4492b0ce97469f3ce223dd9b7e8df2ee952328e06651e5e65dd3b60ac5e3946e16cf7059b20d4d4a649957c1e3055c2e1fb8
    sha256 fb5dbd3c669af9fc236c6991e6387b7f11ff0590997f22d0f5c74ff40e04fca8
