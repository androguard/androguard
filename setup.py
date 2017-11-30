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

# workaround issue on OSX, where sys.prefix is not an installable location
if sys.platform == 'darwin' and sys.prefix.startswith('/System'):
    data_prefix = os.path.join('.', 'share', 'androguard')
elif sys.platform == 'win32':
    data_prefix = os.path.join(sys.prefix, 'Scripts', 'androguard')
else:
    data_prefix = os.path.join(sys.prefix, 'share', 'androguard')

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

setup(
    name='androguard',
    description='Androguard is a full python tool to play with Android files.',
    version=__version__,
    packages=find_packages(),
    data_files=[(data_prefix,
                 ['androguard/gui/annotation.ui',
                  'androguard/gui/search.ui',
                  'androguard/gui/androguard.ico'])],
    scripts=['androaxml.py',
             'androlyze.py',
             'androdd.py',
             'androgui.py',],
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
	'tests': ['mock>=2.0', 'nose', 'codecov', 'coverage'],
    },
    setup_requires=['setuptools'],

)
