.. _xrefs:

Crossreferences (XREFs)
=======================

Crossreferences or simply XREFs are the main thing which :class:`~androguard.core.analysis.analysis.Analysis` provides.
XREFs are generated for Classes, Methods, Fields and Strings.

Next, we want to show a few usecases for XREFs and how they can be obtained.

Start up a ipython shell using :code:`androguard analyze` in order to play through the example.
We use an example from the androguard repo here:

.. code-block:: none

    $ androguard analyze examples/android/TestsAndroguard/bin/TestActivity.apk
    Please be patient, this might take a while.
    Found the provided file is of type 'APK'
    [INFO    ] androguard.analysis: End of creating cross references (XREF)
    [INFO    ] androguard.analysis: run time: 0min 00s
    Added file to session: SHA256::3bb32dd50129690bce850124ea120aa334e708eaa7987cf2329fd1ea0467a0eb
    Loaded APK file...
    >>> a
    <androguard.core.bytecodes.apk.APK object at 0x000000000581D710>
    >>> d
    [<androguard.core.bytecodes.dvm.DalvikVMFormat object at 0x000000000D847400>]
    >>> dx
    <analysis.Analysis VMs: 1, Classes: 495, Strings: 496>

    Androguard version 3.3.5 started
    In [1]:


Get XREFs for method calls
--------------------------

The first example would be to query all called classes from the class :code:`tests.androguard.TestActivity`.
Remember, that you need to provide the class name as a type format with forward slashes instead of dots.
In order to get the class, you can simply use :py:attr:`~androguard.core.analysis.analysis.Analysis.classes`
or :meth:`~androguard.core.analysis.analysis.Analysis.find_classes`:

.. code-block:: ipython

    In [4]: dx.classes['Ltests/androguard/TestActivity;']
    Out[4]: <analysis.ClassAnalysis Ltests/androguard/TestActivity;>

This will return a :class:`~androguard.core.analysis.analysis.ClassAnalysis` object.
Now you can iterate over all methods inside the class and query for the xrefs (the output is abbreviated):

.. code-block:: ipython

    In [10]: for meth in dx.classes['Ltests/androguard/TestActivity;'].get_methods():
        ...:     print("inside method {}".format(meth.name))
        ...:     for _, call, _ in meth.get_xref_to():
        ...:         print("  calling -> {} -- {}".format(call.class_name, call.name))
        ...:
    inside method testCall1
      calling -> Ljava/lang/StringBuilder; -- toString
      calling -> Ljava/lang/StringBuilder; -- append
      calling -> Ljava/lang/StringBuilder; -- <init>
      calling -> Ljava/io/PrintStream; -- println
    inside method testCalls
      calling -> Ljava/lang/Object; -- getClass
      calling -> Ljava/io/PrintStream; -- println
      calling -> Ltests/androguard/TestIfs; -- testIF
      calling -> Ltests/androguard/TestActivity; -- testCall2
    [...]

Here you can see, that :code:`tests.androguard.TestActivity.testCall1` uses a :code:`StringBuilder` as well as :code:`println`.
The method :code:`testCalls` is calling other functions from the same package.

The other way around is also possible. Especially for Android API's, this is very interesting!

.. note:: External method, like the API calls, will not give any XREFs for :meth:`~androguard.core.analysis.analysis.MethodClassAnalysis.xref_to`.

Lets say, you want all calls to the API class :code:`java.io.file`:

.. code-block:: ipython

    In [3]: dx.classes['Ljava/io/File;']
    Out[3]: <analysis.ClassAnalysis Ljava/io/File; EXTERNAL>

    In [4]: for meth in dx.classes['Ljava/io/File;'].get_methods():
       ...:     print("usage of method {}".format(meth.name))
       ...:     for _, call, _ in meth.get_xref_from():
       ...:         print("  called by -> {} -- {}".format(call.class_name, call.name))
       ...:
    usage of method getPath
      called by -> Landroid/support/v4/util/AtomicFile; -- <init>
    usage of method <init>
      called by -> Landroid/support/v4/util/AtomicFile; -- <init>
    usage of method delete
      called by -> Landroid/support/v4/util/AtomicFile; -- failWrite
      called by -> Landroid/support/v4/util/AtomicFile; -- delete
      called by -> Landroid/support/v4/util/AtomicFile; -- delete
      called by -> Landroid/support/v4/util/AtomicFile; -- startWrite
      called by -> Landroid/support/v4/util/AtomicFile; -- openRead
      called by -> Landroid/support/v4/util/AtomicFile; -- finishWrite
    usage of method renameTo
      called by -> Landroid/support/v4/util/AtomicFile; -- openRead
      called by -> Landroid/support/v4/util/AtomicFile; -- failWrite
      called by -> Landroid/support/v4/util/AtomicFile; -- startWrite
    usage of method exists
      called by -> Landroid/support/v4/util/AtomicFile; -- startWrite
      called by -> Landroid/support/v4/util/AtomicFile; -- openRead
      called by -> Landroid/support/v4/util/AtomicFile; -- startWrite
    usage of method getParentFile
      called by -> Landroid/support/v4/util/AtomicFile; -- startWrite
    usage of method mkdir
      called by -> Landroid/support/v4/util/AtomicFile; -- startWrite

.. note:: An external class or method is simply a class or method which could not be found inside the loaded DEX files
    at the time the XREFs were created! Thus, it is important to always load all DEX files of a multidex file.
    On the other hand, beware that classes might not be defined as they could be loaded dynamically later.
    External does not automatically mean that this class/method is an Android or Java API!

Get XREFs for Strings
---------------------

Next, we want to see where certain strings are used.
For example, you found the interesting String :code:`'boom'` and would like to know where it is used.
You can use either :py:attr:`~androguard.core.analysis.analysis.Analysis.strings` or :meth:`~androguard.core.analysis.analysis.Analysis.find_strings` to get the proper object for the XREFs:

.. code-block:: ipython

    In [12]: dx.strings['boom']
    Out[12]: <analysis.StringAnalysis 'boom'>

The resulting object is of type :class:`~androguard.core.analysis.analysis.StringAnalysis`.

.. note::
    :class:`~androguard.core.analysis.analysis.StringAnalysis` does not have a :code:`xref_to` method, which is obvious,
    as a String does nothing but is always used.

Now we can call :meth:`~androguard.core.analysis.analysis.StringAnalysis.xref_from` to get the usage of the String:

.. code-block:: ipython

    In [14]: for _, meth in dx.strings['boom'].get_xref_from():
        ...:     print("Used in: {} -- {}".format(meth.class_name, meth.name))
        ...:
    Used in: Ltests/androguard/TestActivity; -- test_base

So, we know that this specific String is used once in the :code:`test_base` method.

Get XREFs for Fields
--------------------

The last XREF we can use are fields.
Fields are a little bit different and do not use :code:`xref_from` and :code:`xref_to` but
:meth:`~androguard.core.analysis.analysis.FieldAnalysis.xref_read` and :meth:`~androguard.core.analysis.analysis.FieldAnalysis.xref_write`.
You can use the method :meth:`~androguard.core.analysis.analysis.Analysis.find_methods` in order to find fields.

.. note:: Calls to static fields are usually not tracked, as they are optimized by the compiler to const calls!

For example, you want to get the read's and write's to the field :code:`value` inside :code:`tests.androguard.TestActivity`:

.. code-block:: ipython

    In [25]: for field in dx.find_fields(classname='Ltests/androguard/TestActivity;', fieldname='^value$'):
        ...:     print("Field: {}".format(field.name))
        ...:     for _, meth in field.get_xref_read():
        ...:         print("  read in {} -- {}".format(meth.class_name, meth.name))
        ...:     for _, meth in field.get_xref_write():
        ...:         print("  write in {} -- {}".format(meth.class_name, meth.name))
        ...:
    Field: value
      read in Ltests/androguard/TestActivity; -- pouet
      read in Ltests/androguard/TestActivity; -- test1
      read in Ltests/androguard/TestActivity; -- test_base
      read in Ltests/androguard/TestActivity; -- testVars
      write in Ltests/androguard/TestActivity; -- <init>
      write in Ltests/androguard/TestActivity; -- pouet2
      write in Ltests/androguard/TestActivity; -- <init>
      write in Ltests/androguard/TestActivity; -- <init>
