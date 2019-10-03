.. Androguard documentation master file, created by
   sphinx-quickstart on Tue Feb  7 12:16:00 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Androguard's documentation!
======================================

Androguard is a full python tool to play with Android files.
It is designed to work with Python 3 only.

* DEX, ODEX
* APK
* Android's binary xml
* Android resources
* Disassemble DEX/ODEX bytecodes
* Decompiler for DEX/ODEX files

You can either use the cli or graphical frontend for androguard,
or use androguard purely as a library for your own tools and scripts.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   intro/index
   tools/tools


Commonly used APIs
------------------

This is a just a selection of the most important top level API classes.

:APK parser: :class:`androguard.core.bytecodes.apk.APK`
:DEX parser: :class:`androguard.core.bytecodes.dvm.DalvikVMFormat`
:AXML parser: :class:`androguard.core.bytecodes.axml.AXMLPrinter`
:ARSC parser: :class:`androguard.core.bytecodes.axml.ARSCParser`
:Analysis: :class:`androguard.core.analysis.analysis.Analysis`
:Session: :class:`androguard.session.Session`
:Automated Analysis: :class:`androguard.core.analysis.auto.AndroAuto`
:Decompilers: :class:`androguard.decompiler.decompiler`


Complete Python API
-------------------

.. toctree::
   :maxdepth: 2

   api/androguard

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

