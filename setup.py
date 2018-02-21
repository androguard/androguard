#!/usr/bin/env python
from __future__ import print_function
import sys
import os
from androguard import __version__

from setuptools import setup, find_packages


# We do not support python versions <2.7 and python <3.3
if (sys.version_info.major == 3 and sys.version_info.minor < 3) or (sys.version_info.major == 2 and sys.version_info.minor < 7):
    print("Unfortunatly, your python version is not supported!\n"
          "Please upgrade at least to python 2.7 or 3.3!", file=sys.stderr)
    sys.exit(1)

# PyQT5 is only available for python 3.5 and 3.6
if sys.version_info <= (3, 4) or sys.version_info >= (3, 7):
    print("PyQT5 is probably not available for your system, the GUI might not work!", file=sys.stderr)

# There is a bug in pyasn1 0.3.1, 0.3.2 and 0.3.3, so do not use them!
install_requires = ['pyasn1!=0.3.1,!=0.3.2,!=0.3.3,!=0.4.1',
                    'future',
                    'networkx',
                    'pygments',
                    'lxml',
                    ]

# python version specific library versions:
#
# IPython Issue: For python2.x, a version <6 is required
if sys.version_info >= (3, 3):
    install_requires.append('ipython>=5.0.0')
else:
    install_requires.append('ipython>=5.0.0,<6')

# pycrypography >= 2 is not supported by py3.3
#  See https://cryptography.io/en/latest/changelog/#v2-0
# sphinxcontrib-programoutput >= 0.9 is not supported by python 2.6, 3.2 or 3.3
#  But we do not support 2.6 or 3.2 anyways...
#  See https://sphinxcontrib-programoutput.readthedocs.io/en/latest/#id5
if sys.version_info.major == 3 and sys.version_info.minor == 3:
    install_requires.append('cryptography>=1.0,<2.0')
    sphinxprogram = "sphinxcontrib-programoutput==0.8"
else:
    install_requires.append('cryptography>=1.0')
    sphinxprogram = "sphinxcontrib-programoutput>0.8"

# TODO add the permission mapping generation at a better place!
# from axplorer_to_androguard import generate_mappings
# generate_mappings()

setup(
    name='androguard',
    description='Androguard is a full python tool to play with Android files.',
    version=__version__,
    packages=find_packages(),
    package_data={
        # add the json files, residing in the api_specific_resources package
        "androguard.core.api_specific_resources": ["aosp_permissions/*.json",
                                                   "api_permission_mappings/*.json"],
        "androguard.core.resources": ["public.json"],
        # Collect also the GUI files this way
        "androguard.gui": ["annotation.ui", "search.ui", "androguard.ico"],
    },
    scripts=['androaxml.py',
             'androarsc.py',
             'androauto.py',
             'androdis.py',
             'androlyze.py',
             'androdd.py',
             'androgui.py',
             ],
    install_requires=install_requires,
    extras_require={
        'GUI': ["pyperclip", "PyQt5"],
        # We support the following three magic packages:
        # * filemagic from https://pypi.python.org/pypi/filemagic
        # * file-magic from https://pypi.python.org/pypi/file-magic  (which is the "offical" one, and also in Debian)
        # * python-magic from https://pypi.python.org/pypi/python-magic
        # If you are installing on debian you can use python3-magic instead, which fulfills the dependency to file-magic
        'magic': ['file-magic'],
        'docs': ['sphinx', sphinxprogram, 'sphinx_rtd_theme'],
        'graphing': ['pydot'],
        'tests': ['mock>=2.0', 'nose', 'codecov', 'coverage', 'nose-timer'],
    },
    setup_requires=['setuptools'],

)
