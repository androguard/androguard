Use JADX as a Decompiler
========================

Instead of using the internal decompiler DAD, you can also use JADX_.

Install JADX as described at it's website.
Make sure that the :code:`jadx` executable is in :code:`$PATH`.
Otherwise you might set the argument when calling
:meth:`~androguard.decompiler.decompiler.DecompilerJADX`.

Here is a short demo code, how JADX can be used:

.. code-block:: python

    from androguard.core.bytecodes.apk import APK
    from androguard.core.bytecodes.dvm import DalvikVMFormat
    from androguard.core.analysis.analysis import Analysis
    from androguard.decompiler.decompiler import DecompilerJADX
    from androguard.core.androconf import show_logging
    import logging

    # Enable log output
    show_logging(level=logging.DEBUG)

    # Load our example APK
    a = APK("examples/android/TestsAndroguard/bin/TestActivity.apk")

    # Create DalvikVMFormat Object
    d = DalvikVMFormat(a)
    # Create Analysis Object
    dx = Analysis(d)

    # Load the decompiler
    # Make sure that the jadx executable is found in $PATH
    # or use the argument jadx="/path/to/jadx" to point to the executable
    decompiler = DecompilerJADX(d, dx)

    # propagate decompiler and analysis back to DalvikVMFormat
    d.set_decompiler(decompiler)
    d.set_vmanalysis(dx)

    # Now you can do stuff like:
    for m in d.get_methods()[:10]:
        print(m)
        print(decompiler.get_source_method(m))



.. _JADX: https://github.com/skylot/jadx
