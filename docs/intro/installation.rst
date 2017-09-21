Installation
============

There are several ways how to install androguard.

Debian
------

Debian has androguard in its repository. You can just install it using :code:`apt install androguard`.
All required dependencies are automatically installed.

Install from Source
-------------------

Use git to fetch the sources, then install it.
Please install git and python on your own.
Beware, that androguard requires python 2.7 or at least 3.3 to work.

.. code-block:: bash

    git clone https://github.com/androguard/androguard.git
    cd androguard
    pip install .

The dependencies, defined in :code:`setup.py` will be automatically installed.
