Installation
============

There are several ways how to install androguard.

Before you start, make sure you are using a supported python version!
Although androguard should run with python 2.7.x, we highly recommend a newer version like python 3.6!
The python 2.x support might be dropped in the future.
For Windows, we recommend using the Anaconda python 3.6.x package.

Note that there is no PyQT5 for python 2.x! If you like to use the GUI, please
use a newer version of python!

PIP
---

The usual way to install a python packages is by using pypi.python.org and it's package installer `pip`.
Just use

.. code-block:: bash

    $ pip install -U androguard[magic,graphing,GUI]
    
to  install androguard.

You can also make use of an `virtualenv`, to separate the installation from your system wide packages:

.. code-block:: bash

    $ virtualenv venv-androguard
    $ . venv-androguard/bin/activate
    $ pip install -U androguard[magic,graphing,GUI]
    
pip should install all required packages too.

Debian / Ubuntu
---------------

Debian has androguard in its repository. You can just install it using :code:`apt install androguard`.
All required dependencies are automatically installed.

Install from Source
-------------------

Use git to fetch the sources, then install it.
Please install git and python on your own.
Beware, that androguard requires python 2.7 or at least 3.4 to work.
Pypy >= 5.9.0 should work as well but is not tested.
On Windows, there might be some issues with the magic library.
Usually the Anaconda suite works fine!

.. code-block:: bash

    $ git clone --recursive https://github.com/androguard/androguard.git
    $ cd androguard
    $ pip install .[magic]

if you like to install the GUI as well, use

.. code-block:: bash

    $ pip install .[magic,GUI,graphing]

The dependencies, defined in :code:`setup.py` will be automatically installed.

If you are installing the libraries using :code:`pip`, make sure you download the correct packages.
For example, there are a lot of implemenations of the :code:`magic` library.
Get the one, that is shipped with the file command (See [Fine Free File Command](http://www.darwinsys.com/file/)) or use `filemagic`, which should work as well.
