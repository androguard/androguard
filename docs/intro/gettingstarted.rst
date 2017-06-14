Getting Started
===============

The easiest way to analyze APK files, is by using `androlyze.py`.
It will start a iPython shell and has all modules loaded to get into action.

Open a terminal and type `androlyze.py -s`.

For analyzing and loading APK or DEX files, some wrapper functions exists.
Use `AnalyzeAPK(filename)` or `AnalyzeDEX(filename)` to load a file and start analyzing:


    a, d, dx = AnalyzeAPK("/home/user/some-app.apk")

The three objects you get are `a` an `APK` object, `d` a `DalvikVMFormat` object and `dx` an `Analysis` object.

Inside the `APK` object, you can find all information about the APK, like package name, permissions, the AndroidManifest.xml
or its resources.

The `DalvikVMFormat` corresponds to the DEX file found inside the APK file. You can get classes, methods or strings from
the DEX file.

The `Analysis` object contains special classes, which link information about the classes.dex.