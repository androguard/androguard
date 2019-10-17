Getting Started
===============

Using Androguard tools
----------------------

There are already some tools for specific purposes.

To just decode the AndroidManifest.xml or resources.arsc, there are
`androguard axml` and `androguard arsc`.
To get information about the certificates use `androguard sign`.

If you want to create call graphs, use `androguard cg`, or if you want control flow
graphs, you can use `androguard decompile`.


Using Androlyze and the python API
----------------------------------

The easiest way to analyze APK files, is by using :code:`androguard analyze`.
It will start a iPython shell and has all modules loaded to get into action.

For analyzing and loading APK or DEX files, some wrapper functions exists.
Use :code:`AnalyzeAPK(filename)` or :code:`AnalyzeDEX(filename)` to load a file and start analyzing.
There are already plenty of APKs in the androguard repo, you can either use one
of those, or start your own analysis.

.. code-block:: none

    $ androguard analyze
    Androguard version 3.1.1 started
    In [1]: a, d, dx = AnalyzeAPK("examples/android/abcore/app-prod-debug.apk")
    # Depending on the size of the APK, this might take a while...

    In [2]:

The three objects you get are :code:`a` an :class:`~androguard.core.bytecodes.apk.APK` object, :code:`d` an array of :class:`~androguard.core.bytecodes.dvm.DalvikVMFormat` object and :code:`dx` an :class:`~androguard.core.analysis.analysis.Analysis` object.

Inside the :code:`APK` object, you can find all information about the APK, like package name, permissions, the AndroidManifest.xml
or its resources.

The :class:`~androguard.core.bytecodes.dvm.DalvikVMFormat` corresponds to the DEX file found inside the APK file. You can get classes, methods or strings from
the DEX file.
But when using multi-DEX APK's it might be a better idea to get those from
another place.
The :class:`~androguard.core.analysis.analysis.Analysis` object should be used instead, as it contains special classes, which link information about the classes.dex
and can even handle many DEX files at once.

Getting Information about an APK
--------------------------------

If you have sucessfully loaded your APK using :code:`AnalyzeAPK`, you can now
start getting information about the APK.

For example, getting the permissions of the APK:

.. code-block:: python

    In [2]: a.get_permissions()
    Out[2]:
    ['android.permission.INTERNET',
     'android.permission.WRITE_EXTERNAL_STORAGE',
     'android.permission.ACCESS_WIFI_STATE',
     'android.permission.ACCESS_NETWORK_STATE']

or getting a list of all activites, which are defined in the
AndroidManifest.xml:

.. code-block:: python

    In [3]: a.get_activities()
    Out[3]:
    ['com.greenaddress.abcore.MainActivity',
     'com.greenaddress.abcore.BitcoinConfEditActivity',
     'com.greenaddress.abcore.AboutActivity',
     'com.greenaddress.abcore.SettingsActivity',
     'com.greenaddress.abcore.DownloadSettingsActivity',
     'com.greenaddress.abcore.PeerActivity',
     'com.greenaddress.abcore.ProgressActivity',
     'com.greenaddress.abcore.LogActivity',
     'com.greenaddress.abcore.ConsoleActivity',
     'com.greenaddress.abcore.DownloadActivity']

Get the package name, app name and path of the icon:

.. code-block:: python

    In [4]: a.get_package()
    Out[4]: 'com.greenaddress.abcore'

    In [5]: a.get_app_name()
    Out[5]: u'ABCore'

    In [6]: a.get_app_icon()
    Out[6]: u'res/mipmap-xxxhdpi-v4/ic_launcher.png'


Get the numeric version and the version string, and the minimal, maximal, target
and effective SDK version:

.. code-block:: python

    In [7]: a.get_androidversion_code()
    Out[7]: '2162'

    In [8]: a.get_androidversion_name()
    Out[8]: '0.62'

    In [9]: a.get_min_sdk_version()
    Out[9]: '21'

    In [10]: a.get_max_sdk_version()

    In [11]: a.get_target_sdk_version()
    Out[11]: '27'

    In [12]: a.get_effective_target_sdk_version()
    Out[12]: 27

You can even get the decoded XML for the AndroidManifest.xml:

.. code-block:: python

    In [15]: a.get_android_manifest_axml().get_xml()
    Out[15]: '<manifest xmlns:android="http://schemas.android.com/apk/res/android" android:versionCode="2162" android:versionName="0.62" package="com.greenaddress.abcore">\n<uses-sdk android:minSdkVersion="21" android:targetSdkVersion="27">\n</uses-sdk>\n<uses-permission android:name="android.permission.INTERNET">\n</uses-permission>\n<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE">\n</uses-permission>\n<uses-permission android:name="android.permission.ACCESS_WIFI_STATE">\n</uses-permission>\n<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE">\n</uses-permission>\n<application android:theme="@7F0F0006" android:label="@7F0E001D" android:icon="@7F0D0000" android:debuggable="true" android:allowBackup="false" android:supportsRtl="true">\n<activity android:name="com.greenaddress.abcore.MainActivity">\n<intent-filter>\n<action android:name="android.intent.action.MAIN">\n</action>\n<category android:name="android.intent.category.LAUNCHER">\n</category>\n</intent-filter>\n</activity>\n<service android:name="com.greenaddress.abcore.DownloadInstallCoreIntentService" android:exported="false">\n</service>\n<service android:name="com.greenaddress.abcore.RPCIntentService" android:exported="false">\n</service>\n<service android:name="com.greenaddress.abcore.ABCoreService" android:exported="false">\n</service>\n<activity android:name="com.greenaddress.abcore.BitcoinConfEditActivity">\n<intent-filter>\n<category android:name="android.intent.category.DEFAULT">\n</category>\n<action android:name="com.greenaddress.abcore.BitcoinConfEditActivity">\n</action>\n</intent-filter>\n</activity>\n<activity android:name="com.greenaddress.abcore.AboutActivity">\n</activity>\n<activity android:label="@7F0E0038" android:name="com.greenaddress.abcore.SettingsActivity" android:noHistory="true">\n</activity>\n<activity android:label="@7F0E0035" android:name="com.greenaddress.abcore.DownloadSettingsActivity" android:noHistory="true">\n</activity>\n<activity android:theme="@7F0F0006" android:label="@7F0E0036" android:name="com.greenaddress.abcore.PeerActivity">\n</activity>\n<activity android:theme="@7F0F0006" android:label="@7F0E0037" android:name="com.greenaddress.abcore.ProgressActivity">\n</activity>\n<activity android:name="com.greenaddress.abcore.LogActivity">\n</activity>\n<activity android:name="com.greenaddress.abcore.ConsoleActivity">\n</activity>\n<activity android:name="com.greenaddress.abcore.DownloadActivity">\n</activity>\n<receiver android:name="com.greenaddress.abcore.PowerBroadcastReceiver">\n<intent-filter>\n<action android:name="android.intent.action.ACTION_POWER_CONNECTED">\n</action>\n<action android:name="android.intent.action.ACTION_POWER_DISCONNECTED">\n</action>\n<action android:name="android.intent.action.ACTION_SHUTDOWN">\n</action>\n<action android:name="android.intent.action.ACTION_BATTERY_LOW">\n</action>\n<action android:name="android.net.wifi.STATE_CHANGE">\n</action>\n</intent-filter>\n</receiver>\n</application>\n</manifest>\n'

Or if you like to use the AndroidManifest.xml as an ElementTree object, use the
following method:

.. code-block:: python

    In [13]: a.get_android_manifest_xml()
    Out[13]: <Element manifest at 0x7f9d01587b00>

There are many more methods to explore, just take a look at the API for
:class:`~androguard.core.bytecodes.apk.APK`.


Using the Analysis object
-------------------------

The :code:`~androguard.core.analysis.analysis.Analysis` object has all
information about the classes, methods, fields and strings inside one or
multiple DEX files.

Additionally it enables you to get call graphs and crossreferences (XREFs) for
each method, class, field and string.

This means you can investigate the application for certain API calls or create
graphs to see the dependencies of different classes.

As a first example, we will get all classes from the Analysis:

.. code-block:: none

    In [2]: dx.get_classes()
    Out[2]:
    [<analysis.ClassAnalysis Ljava/io/FileNotFoundException; EXTERNAL>,
     <analysis.ClassAnalysis Landroid/content/SharedPreferences; EXTERNAL>,
     <analysis.ClassAnalysis Landroid/support/v4/widget/FocusStrategy$BoundsAdapter;>,
     <analysis.ClassAnalysis Landroid/support/v4/media/MediaBrowserCompat$MediaBrowserServiceCallbackImpl;>,
     <analysis.ClassAnalysis Landroid/support/transition/WindowIdImpl;>,
     <analysis.ClassAnalysis Landroid/media/MediaMetadataEditor; EXTERNAL>,
     <analysis.ClassAnalysis Landroid/support/v4/app/BundleCompat$BundleCompatBaseImpl;>,
     <analysis.ClassAnalysis Landroid/support/transition/MatrixUtils$1;>,
     <analysis.ClassAnalysis Landroid/support/v7/widget/ShareActionProvider;>,
     ...

As you can see, :meth:`~androguard.core.analysis.analysis.Analysis.get_classes` returns a list of
:class:`~androguard.core.analysis.analysis.ClassAnalysis` objects.
Some of them are marked as `EXTERNAL`, which means that the source code of this
class is not defined within the DEX files that are loaded inside the Analysis.
For example the first class :code:`java.io.FileNotFoundException` is an API
class.

A :class:`~androguard.core.analysis.analysis.ClassAnalysis` does not contain the
actual code but the :class:`~androguard.core.bytecodes.dvm.ClassDefItem` can be
loaded using the
:meth:`~androguard.core.analysis.analysis.ClassAnalysis.get_vm_class`:

.. code-block:: none

    In [5]: dx.get_classes()[2].get_vm_class()
    Out[5]: <dvm.ClassDefItem Ljava/lang/Object;->Landroid/support/v4/widget/FocusStrategy$BoundsAdapter;>

If the class is `EXTERNAL`, a
:class:`~androguard.core.analysis.analysis.ExternalClass` is returned instead.

The :class:`~androguard.core.analysis.analysis.ClassAnalysis` also contains all the
information about XREFs, which are explained in more detail in the next section.

XREFs
-----

Consider the following Java source code:

.. code-block:: java

    class Foobar {
        public int afield = 23;

        public void somemethod() {
            String astring = "hello world";
        }
    }

    class Barfoo {
        public void othermethod() {
            Foobar x = new Foobar();

            x.somemethod();

            System.out.println(x.afield);
        }
    }


There are two classes and the class :code:`Barfoo` instanciates the other class
:code:`Foobar` as well as calling methods and reading fields.

XREFs are generated for four things:

* Classes
* Methods
* Fields
* Strings

XREFs work in two directions: `xref_from` and `xref_to`.
`To` means, that the current object is calling another object.
`From` means, that the current object is called by another object.

All XREFs can be visualized as an directed graph and if some object :code:`A` is contained
in the :code:`xref_to`, the called object will contain :code:`A` in their
:code:`xref_from`.

In the case of our Java example, the string :code:`astring` is called in :code:`Foobar.somethod`,
therefore it will be contained in the :code:`xref_to` of
:code:`Foobar.somethod`.

The Field :code:`afield` will be contained in the :code:`xref_to` of
:code:`Barfoo.othermethod` as well as the call to :code:`Foobar.somethod`.

More on XREFs can be found in xrefs_.
