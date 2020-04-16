Android Binary XML Format
=========================

Android uses a special format to save XML and resource files.
Also resource files are XML files in the source folder, but all resources are packed into a single
resource file called :code:`resources.arsc`.
The underlying format is chunk based and is capable for storing several different information.

The most common AXML file is the :code:`AndroidManifest.xml`. This file must be part of every APK,
and contains the meta-information about the package.

Androguard is capable of decoding such files and two different tools exists for decoding:

1) :code:`androguard arsc` for decoding :code:`resources.arsc`.
2) :code:`androguard axml` for decoding :code:`AndroidManifest.xml` and all other XML files

Decode the AndroidManifest.xml
------------------------------

Let's use one of the example files provided by androguard.
To decode the AndroidManifest.xml of an APK file, simply give :code:`androguard axml` the APK file
as an argument:

.. code-block:: bash

    $ androguard axml examples/android/TestsAndroguard/bin/TestActivity.apk

The output will look like this:

.. code-block:: xml

    <manifest xmlns:android="http://schemas.android.com/apk/res/android" android:versionCode="1" android:versionName="1.0" package="tests.androguard">
      <uses-sdk android:minSdkVersion="9" android:targetSdkVersion="16"/>
      <application android:label="@7F040001" android:icon="@7F020000" android:debuggable="true" android:allowBackup="false">
        <activity android:label="@7F040001" android:name="TestActivity">
          <intent-filter>
            <action android:name="android.intent.action.MAIN"/>
            <category android:name="android.intent.category.LAUNCHER"/>
          </intent-filter>
        </activity>
      </application>
    </manifest>

You can check with the original, uncompiled, XML file, which can be found here:

.. code-block:: bash

    $ cat examples/android/TestsAndroguard/AndroidManifest.xml

The original file will print:

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8"?>
    <manifest xmlns:android="http://schemas.android.com/apk/res/android"
        package="tests.androguard"
        android:versionCode="1"
        android:versionName="1.0" >

        <uses-sdk
            android:minSdkVersion="9"
            android:targetSdkVersion="16" />

        <application
            android:allowBackup="false"
            android:icon="@drawable/icon"
            android:label="@string/app_name" >
            <activity
                android:name="TestActivity"
                android:label="@string/app_name" >
                <intent-filter>
                    <action android:name="android.intent.action.MAIN" />

                    <category android:name="android.intent.category.LAUNCHER" />
                </intent-filter>
            </activity>
        </application>



Note, that the overall structure is equal but there are certain differences.

1) Resource labels are hex numbers in the decompiled version but strings in the original one
2) Newlines and whitespaces are different.

Due to the compilation, this information is lost. But it does not matter, as the structure of the Manifest does not matter.
To get some information about the resource IDs, we need information from the :code:`resources.arsc`.

To retrieve information about a single ID, simply run the following:

.. code-block:: bash

    $ androguard arsc examples/android/TestsAndroguard/bin/TestActivity.apk  --id 7F040001
    @7f040001 resolves to '@tests.androguard:string/app_name'

    <default> = 'TestsAndroguardApplication'

You can see, that the ID :code:`7F040001` was successfully resolved to the same string from the source file.
To understand how Android handles resource configurations, you should read HandlingResources_.


Decode any other XML file
-------------------------

Also layout files or other XML files provided with the APK are compiled.
To decompile them, just give the path inside the APK as an argument, or specify the binary XML file directly:

.. code-block:: bash

    $ androguard axml examples/android/TestsAndroguard/bin/TestActivity.apk -r res/layout/main.xml
    $ androguard axml examples/axml/test.xml


Decode information from the resources.arsc
------------------------------------------

To get XML resource files out of the binary :code:`resources.arsc`, use :code:`androguard arsc`.

For example, get all string resources of an APK:

.. code-block:: bash

    $ androguard arsc examples/android/TestsAndroguard/bin/TestActivity.apk --type string

will give the following output:

.. code-block:: xml

    <resources>
    <string name="hello">Hello World, TestActivity! kikoololmodif</string>
    <string name="app_name">TestsAndroguardApplication</string>
    </resources>

You can also list all resource types:

.. code-block:: bash

    $ androguard arsc examples/android/TestsAndroguard/bin/TestActivity.apk --list-types
    In Package: tests.androguard
      In Locale: \x00\x00
        drawable
        layout
        public
        string


Working with AXML and Resource files from python
------------------------------------------------

To load an AXML file, for example the :code:`AndroidManifest.xml`, use the :class:`~androguard.core.bytecodes.axml.AXMLPrinter`:

.. code-block:: python

    from androguard.core.bytecodes.axml import AXMLPrinter
    with open("AndroidManifest.xml", "rb") as fp:
        a = AXMLPrinter(fp.read())

    # Get the lxml.etree.Element from the AXMLPrinter:
    xml = a.get_xml_obj()

    # For example, get all uses-permission:
    xml.findall("uses-permission")

In order to use resources, you need the :class:`~androguard.core.bytecodes.axml.ARSCParser`:

.. code-block:: python

    from androguard.core.bytecodes.axml import ARSCParser

    with open("resouces.arsc", "rb") as fp:
        res = ARSCParser(fp.read())

    # Now you can resolve IDs:
    name = res.get_resource_xml_name(0x7F040001)
    if name:
        print(name)

    # To get the content of an ID, you need to iterate over configurations
    # You need to decide which configuration to use...
    for config, entry in res.get_res_configs(0x7F040001):
        # You can query `config` for specific configuration
        # or check with `is_default()` if this is a default configuration.
        print("{} = '{}'".format(config.get_qualifier() if not config.is_default() else "<default>", entry.get_key_data()))



.. _HandlingResources: https://developer.android.com/guide/topics/resources/providing-resources
