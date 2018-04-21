androcfg - Create Call Graph from APK
=====================================

.. program-output:: python ../androcfg.py -h

androcfg can create files that can be read using graph visualization software, for example gephi_.
The call graph is constructed from the
:class:`~androguard.analysis.analysis.Analysis` object and then converted into a
networkx `DiGraph`.
Note that calls between methods are only added once. Thus, if a method calls
some other method multiple times, this is not saved.

The methods to construct the callgraph from can be filtered. It is highly
suggested to do that, as call graphs can get very large:

.. image:: screenshot_182338.png

Of course, you can export the call graph with androguard and filter it later.

.. _gephi: https://gephi.org/

