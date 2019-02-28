Installation
============

There are several ways how to install androguard.

Before you start, make sure you are using a supported python version!
For Windows, we recommend using the Anaconda python 3.6.x package.

.. warning::

   The magic library might not work out of the box. If your magic library does not work,
   please refer to the installation instructions of python-magic_.

PIP
---

The usual way to install a python packages is by using pypi.python.org and it's package installer `pip`.
Just use

.. code-block:: bash

    $ pip install -U androguard[magic,GUI]


to  install androguard including the GUI and magic file type detection.
In order to use features which use :code:`dot`, you need Graphviz_ installed.
This is not a python dependency but a binary package! Please follow the installation instructions for GraphvizInstall_.

You can also make use of an `virtualenv`, to separate the installation from your system wide packages:

.. code-block:: bash

    $ virtualenv venv-androguard
    $ source venv-androguard/bin/activate
    $ pip install -U androguard[magic,GUI]
    
pip should install all required packages too.

Debian / Ubuntu
---------------

Debian has androguard in its repository. You can just install it using :code:`apt install androguard`.
All required dependencies are automatically installed.

Install from Source
-------------------

Use git to fetch the sources, then install it.
Please install git and python on your own.
Androguard requires Python at least 3.4 to work.
Pypy >= 5.9.0 should work as well but is not tested.


.. code-block:: bash

    $ git clone --recursive https://github.com/androguard/androguard.git
    $ cd androguard
    $ virtualenv -p python3 venv-androguard
    $ source venv-androguard/bin/activate
    $ pip install .[magic,GUI]

The dependencies, defined in :code:`setup.py` will be automatically installed.

For development purposes, you might want to install the extra dependecies for
`docs` and `tests` as well:

.. code-block:: bash

    $ git clone --recursive https://github.com/androguard/androguard.git
    $ cd androguard
    $ virtualenv -p python3 venv-androguard
    $ source venv-androguard/bin/activate
    $ pip install -e .[magic,GUI,tests,docs]

You can then create a local copy of the documentation:


.. code-block:: bash

   $ python3 setup.py build_sphinx

Which is generated in :code:`build/sphinx/html`.

.. _Graphviz: https://graphviz.org/
.. _GraphvizInstall: https://graphviz.org/download/
.. _python-magic: https://github.com/ahupp/python-magic/#installation
