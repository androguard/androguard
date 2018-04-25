androcg - Create Call Graph from APK
====================================

androcg can create files that can be read using graph visualization software, for example gephi_.

Synopsis
--------

.. program-output:: python ../androcg.py -h

Examples
--------

The call graph is constructed from the
:class:`~androguard.analysis.analysis.Analysis` object and then converted into a
networkx `DiGraph`.
Note that calls between methods are only added once. Thus, if a method calls
some other method multiple times, this is not saved.

The methods to construct the callgraph from can be filtered. It is highly
suggested to do that, as call graphs can get very large:

.. image:: screenshot_182338.png

Of course, you can export the call graph with androguard and filter it later.

Here is an example of an already filtered graph, visualized in gephi_.
Each node has an attribute to indicate if it is an internal (defined somewhere
in the DEXs) or external (might be an API, but definetly not defined in the DEXs) method.
In this case all green nodes are internal and all red ones are external.
You can see the calls of some SMS Trojan to the API methods to write SMS.

.. image:: screenshot_182951.png

.. _gephi: https://gephi.org/

