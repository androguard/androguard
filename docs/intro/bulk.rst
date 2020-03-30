Bulk Analysis
=============

Androguard is capable of analysing probably thousand to millions of APKs.
It is also possible to use tools like `multiprocessing` for this job and
analyse APKs in parallel.
Usually you want to put the results of your analysis somewhere, for example a
database or some log file.
It is also possible to use :class:`~androguard.session.Session` objects for this
job, but you should be aware of some caveats!

1) Sessions take up a lot of space per APK. The resulting Session object can be
more than 30 times larger than the original APK
2) Sessions should not be used to add unrelated APKs, again the size will blow
up and you need to figure out which APK belongs to where

So the rule of thumb would be to not use Sessions for bulk analysis, only if you
know what you are doing.
Another way is to pickle the resulting objects.
As the :class:`~androguard.core.bytecodes.dvm.DalvikVMFormat` are already stored
in the :class:`~androguard.core.analysis.analysis.Analysis` object, there is no
need to pickle them separately.
Thus, it is only required to save the
:class:`~androguard.core.bytecodes.apk.APK` and
:class:`~androguard.core.analysis.analysis.Analysis` object.

This is an example how to obtain the two objects and saving them to disk:

.. code-block:: python

   import sys
   from pickle import dump
   from hashlib import sha512
   from androguard.misc import AnalyzeAPK

   a, _, dx = AnalyzeAPK('examples/tests/a2dp.Vol_137.apk')

   sha = sha512()

   sha.update(a.get_raw())

   with open("{}_apk.p".format(sha.hexdigest()), "wb") as fp:
       dump(a, fp)

   with open("{}_analysis.p".format(sha.hexdigest()), "wb") as fp:
       # It looks like here is the recursion problem...
       sys.setrecursionlimit(50000)
       dump(dx, fp)

But the resulting files are very large, especially the Analysis package:

.. code-block:: bash

   $ du -sh examples/tests/a2dp.Vol_137.apk
   808K	examples/tests/a2dp.Vol_137.apk

   $ du -sh *.p
   31M	24a62690a770891a8f43d71e8f7beb24821d46a75e017ef4f4e6a04624105466621c96305d8e86f9900042e3ef1d5806a5d9ac873bebdf798483790446bd275e_analysis.p
   852K	24a62690a770891a8f43d71e8f7beb24821d46a75e017ef4f4e6a04624105466621c96305d8e86f9900042e3ef1d5806a5d9ac873bebdf798483790446bd275e_apk.p


But it is possible to compress both files to save disk space:

.. code-block:: python

   import sys
   import lzma
   from pickle import dump
   from hashlib import sha512
   from androguard.misc import AnalyzeAPK

   a, _, dx = AnalyzeAPK('examples/tests/a2dp.Vol_137.apk')

   sha = sha512()

   sha.update(a.get_raw())

   with lzma.open("{}_apk.p.lzma".format(sha.hexdigest()), "wb") as fp:
       dump(a, fp)

   with lzma.open("{}_analysis.p.lzma".format(sha.hexdigest()), "wb") as fp:
       # It looks like here is the recursion problem...
       sys.setrecursionlimit(50000)
       dump(dx, fp)

which results in much smaller files:

.. code-block:: bash

   $ du -sh *.lzma
   4,5M	24a62690a770891a8f43d71e8f7beb24821d46a75e017ef4f4e6a04624105466621c96305d8e86f9900042e3ef1d5806a5d9ac873bebdf798483790446bd275e_analysis.p.lzma
   748K	24a62690a770891a8f43d71e8f7beb24821d46a75e017ef4f4e6a04624105466621c96305d8e86f9900042e3ef1d5806a5d9ac873bebdf798483790446bd275e_apk.p.lzma

Obviously, as the APK is already packed, there is not much to compress anymore.


Using AndroAuto
---------------

Another method is to use the framework `AndroAuto`.
AndroAuto allows you to write small python classes which implement some method,
which are then called by AndroAuto at certain points in time.
AndroAuto is capable of analysing thousands of apps, and uses threading to
distribute the load to multiple CPUs. The results of your analysis can then be
dumped to disk, or you could write your own method of saving them - for example,
in a database.

The two key components are a Logger, for example
:class:`~androguard.core.analysis.auto.DefaultAndroLog` and an Analysis Runner,
for example :class:`~androguard.core.analysis.auto.DefaultAndroAnalysis`.
Both are passed via a settings dictionary into
:class:`~androguard.core.analysis.auto.AndroAuto`.

Next, a minimal working example is given:

.. code-block:: python

        from androguard.core.analysis import auto
        import sys

        class AndroTest(auto.DirectoryAndroAnalysis):
            def __init__(self, path):
               super(AndroTest, self).__init__(path)
               self.has_crashed = False

            def analysis_app(self, log, apkobj, dexobj, analysisobj):
                # Just print all objects to stdout
                print(log.id_file, log.filename, apkobj, dexobj, analysisobj)

            def finish(self, log):
               # This method can be used to save information in `log`
               # finish is called regardless of a crash, so maybe store the
               # information somewhere
               if self.has_crashed:
                  print("Analysis of {} has finished with Errors".format(log))
               else:
                  print("Analysis of {} has finished!".format(log))

            def crash(self, log, why):
               # If some error happens during the analysis, this method will be
               # called
               self.has_crashed = True
               print("Error during analysis of {}: {}".format(log, why), file=sys.stderr)

        settings = {
            # The directory `some/directory` should contain some APK files
            "my": AndroTest('some/directory'),
            # Use the default Logger
            "log": auto.DefaultAndroLog,
            # Use maximum of 2 threads
            "max_fetcher": 2,
        }

        aa = auto.AndroAuto(settings)
        aa.go()


In this example, the :meth:`~androguard.core.analysis.auto.DefaultAndroAnalysis.analysis_app` function is used to get all created objects
of the analysis and just print them to stdout.

More information can be found in the documentation of :class:`~androguard.core.analysis.auto.AndroAuto`.
