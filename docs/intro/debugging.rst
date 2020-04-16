Debugging Broken APKs
=====================

Sometimes you will have troubles to get something done with androguard.
This is usually the case if an APK uses some edge cases or
deliberately tries to break parsers - which is not uncommon for malware.

Please feel free to open a bug report in such cases, so this error can be fixed.
But before you do, try to gather some more information about the APK.
Sometimes not only androguard fails to decode the file, but the official tools do as well!

It is also always interesting to know, if such a broken file can still be installed on an Android
system. If you like to test this, fire up an emulator_ and try to run the APK there.

AXML Parser / AndroidManifest.xml
---------------------------------

Many errors happen in the parsing of the `AndroidManifest.xml`.

There are two official tools you can use to decode the `AndroidManifest.xml`:

1. aapt2_
2. apkanalyzer_

Both are available in the AndroidSDK.
While aapt2 can only decode the structure of the file, apkanalyzer can give an actual XML:

.. code-block::

    $ apkanalyzer manifest print org.fdroid.fdroid_1002052.apk | head
    <?xml version="1.0" encoding="utf-8"?>
    <manifest
        xmlns:android="http://schemas.android.com/apk/res/android"
        android:versionCode="1002052"
        android:versionName="1.2.2"
        android:installLocation="0"
        package="org.fdroid.fdroid"
        platformBuildVersionCode="24"
        platformBuildVersionName="7.0">

    $ aapt2 dump org.fdroid.fdroid_1002052.apk --file AndroidManifest.xml | head
    Binary XML
    N: android=http://schemas.android.com/apk/res/android (line=2)
      E: manifest (line=2)
        A: http://schemas.android.com/apk/res/android:versionCode(0x0101021b)=1002052
        A: http://schemas.android.com/apk/res/android:versionName(0x0101021c)="1.2.2" (Raw: "1.2.2")
        A: http://schemas.android.com/apk/res/android:installLocation(0x010102b7)=0
        A: package="org.fdroid.fdroid" (Raw: "org.fdroid.fdroid")
        A: platformBuildVersionCode=24 (Raw: "24")
        A: platformBuildVersionName=7 (Raw: "7.0")
          E: uses-sdk (line=8)

Both outputs are actually useful, as aapt2 can provide much more detailed information
about the format than apkanalyzer does.


Broken ZIP files
----------------

As you might know, APK files are actually just ZIP files.
You can test the zip file integrity using the ZIP command itself:

.. code-block::

    $ zip -T org.fdroid.fdroid_1002052.apk
    test of org.fdroid.fdroid_1002052.apk OK

If there are any errors, like wrong CRC32, these get reported here.
Other ZIP implementations have similar tools to check ZIP files.

Verifying the APK Signature
---------------------------

You can check the signature of the file using apksigner_ from the AndroidSDK:

.. code-block::

    $ apksigner verify --verbose --print-certs org.fdroid.fdroid_1002052.apk
    Verifies
    Verified using v1 scheme (JAR signing): true
    Verified using v2 scheme (APK Signature Scheme v2): false
    Number of signers: 1
    Signer #1 certificate DN: CN=Ciaran Gultnieks, OU=Unknown, O=Unknown, L=Wetherby, ST=Unknown, C=UK
    Signer #1 certificate SHA-256 digest: 43238d512c1e5eb2d6569f4a3afbf5523418b82e0a3ed1552770abb9a9c9ccab
    Signer #1 certificate SHA-1 digest: 05f2e65928088981b317fc9a6dbfe04b0fa13b4e
    Signer #1 certificate MD5 digest: 17c55c628056e193e95644e989792786
    Signer #1 key algorithm: RSA
    Signer #1 key size (bits): 2048
    Signer #1 public key SHA-256 digest: e3d2cc87a245da2e84d4fb71e527c164e084d48bccf76ffad46ad17f1bfde388
    Signer #1 public key SHA-1 digest: 26ef7882633282a9b04688178ee7f372fbec7c3d
    Signer #1 public key MD5 digest: 9225fccafb33b605a86cfc09d7f38ec6
    WARNING: META-INF/rxandroid.properties not protected by signature. Unauthorized modifications to this JAR entry will not be detected. Delete or move the entry outside of META-INF/.
    WARNING: META-INF/rxjava.properties not protected by signature. Unauthorized modifications to this JAR entry will not be detected. Delete or move the entry outside of META-INF/.
    WARNING: META-INF/services/com.fasterxml.jackson.core.JsonFactory not protected by signature. Unauthorized modifications to this JAR entry will not be detected. Delete or move the entry outside of META-INF/.
    WARNING: META-INF/services/com.fasterxml.jackson.core.ObjectCodec not protected by signature. Unauthorized modifications to this JAR entry will not be detected. Delete or move the entry outside of META-INF/.
    WARNING: META-INF/buildserverid not protected by signature. Unauthorized modifications to this JAR entry will not be detected. Delete or move the entry outside of META-INF/.
    WARNING: META-INF/fdroidserverid not protected by signature. Unauthorized modifications to this JAR entry will not be detected. Delete or move the entry outside of META-INF/.


.. _aapt2: https://developer.android.com/studio/command-line/aapt2
.. _apkanalyzer: https://developer.android.com/studio/command-line/apkanalyzer
.. _apksigner: https://developer.android.com/studio/command-line/apksigner
.. _emulator: https://developer.android.com/studio/run/emulator
