Working with Sessions
=====================

If you are working on a larger APK, you might want to save your current work and
come back later.
That's the reason for sessions: They allow you to save your work on disk and
resume it at any point.
Sessions could also be used to store the analysis on disk, for example if you do
automated analysis and want to analyse certain files later.

There are several ways to work with sessions.
The easiest way is to use :func:`~androguard.misc.AnalyzeAPK` with a session:

.. code-block:: python

    from androguard import misc
    from androguard import session

    # get a default session
    sess = misc.get_default_session()

    # Use the session
    a, d, dx = misc.AnalyzeAPK("examples/android/abcore/app-prod-debug.apk", session=sess)

    # Show the current Session information
    sess.show()

    # Do stuff...

    # Save the session to disk
    session.Save(sess, "androguard_session.ag")

    # Load it again
    sess = session.Load("androguard_session.ag")

The session information will look like this:

.. code-block:: guess

    APKs in Session: 1
        d5e26acca809e9cdfaece18afd8e63c60a26d7b6d566d70bd9f44d6934d5c433: [<androguard.core.bytecodes.apk.APK object at 0x7fcecf4f3f10>]
    DEXs in Session: 2
        8bd7e9f48a6ed29e4c678633364e8bfd4e6ae76ef3e50c43a5ec3c00eb10a5bc: <analysis.Analysis VMs: 2, Classes: 3092, Strings: 3293>
        e2a1e46ecd03b701ce72c31057581e0104279d142fca06cdcdd000dd94a459e0: <analysis.Analysis VMs: 2, Classes: 3092, Strings: 3293>
    Analysis in Session: 1
        d5e26acca809e9cdfaece18afd8e63c60a26d7b6d566d70bd9f44d6934d5c433: <analysis.Analysis VMs: 2, Classes: 3092, Strings: 3293>


Similar functionality is available from the Session directly, but needs a second
function to retrieve the analyzed objects from the Session:

.. code-block:: python

   from androguard.session import Session

   s = Session()
   sha256 = s.add("examples/android/abcore/app-prod-debug.apk")

   a, d, dx = s.get_objects_apk(digest=sha256)

   s.show()

   # When no filename is given, the Session will be saved at the current directory
   saved_file = s.save()
   # ... and return the filename of the Session file
   print(saved_file)


.. note::
   Session objects store a lot of data and can get very big!

It is recommended not to use sessions in automated environments, where hundreds or
thousands of APKs are loaded.

If you want to use sessions but keep the session alive only for one or multiple
APKs, you can call the :meth:`~androguard.session.Session.reset` method on a
session, to remove all stored analysis data.

.. code-block:: python

    from androguard import misc
    from androguard import session
    import os

    # get a default session
    sess = misc.get_default_session()

    for root, dirs, files in os.walk("examples")
        for f in files:
            if f.endswith(".apk"):
                # Use the session
                a, d, dx = misc.AnalyzeAPK(os.path.join(root, f), session=sess)

                # Do your stuff

                # Maybe save the session to disk...

                # But now reset the session for the next analysis
                sess.reset()


