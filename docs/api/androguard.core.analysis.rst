androguard.core.analysis package
================================

The analysis module implements an abstraction layer for :class:`androguard.core.bytecodes.dvm.DalvikVMFormat` objects.
The the help of the :class:`androguard.core.analysis.analysis.Analsyis` object, you can bundle several DEX files together.
This is not only useful for multidex files, but also for a single dex, as Analysis offers many features to investigate
DEX files.
One of these features is crossreferencing (XREF). It allows you to build a graph of the methods inside the DEX files.
You can then create callgraphs or find methods which use a specific API method.

Submodules
----------

androguard.core.analysis.analysis module
----------------------------------------

.. automodule:: androguard.core.analysis.analysis
    :members:
    :undoc-members:
    :show-inheritance:

androguard.core.analysis.auto module
------------------------------------

.. automodule:: androguard.core.analysis.auto
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: androguard.core.analysis
    :members:
    :undoc-members:
    :show-inheritance:
