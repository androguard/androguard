#!/usr/bin/env python
from __future__ import print_function
import sys
import os
from androguard import __version__

from setuptools import setup, find_packages


# We do not support python versions <2.7 and python <3.4
if (sys.version_info.major == 3 and sys.version_info.minor < 4) or (sys.version_info.major == 2 and sys.version_info.minor < 7):
    print("Unfortunatly, your python version is not supported!\n"
          "Please upgrade at least to python 2.7 or 3.4!", file=sys.stderr)
    sys.exit(1)

# PyQT5 is only available for python >=3.5
if sys.version_info <= (3, 4):
    print("PyQT5 is probably not available for your system, the GUI might not work!", file=sys.stderr)

install_requires = ['future',
                    'networkx>=1.11',
                    'pygments',
                    'lxml',
                    'colorama',
                    'matplotlib',
                    'asn1crypto>=0.24.0',
                    ]

# python version specific library versions:
#
# IPython Issue: For python2.x, a version <6 is required
if sys.version_info >= (3, 3):
    install_requires.append('ipython>=5.0.0')
else:
    install_requires.append('ipython>=5.0.0,<6')


# TODO add the permission mapping generation at a better place!
# from axplorer_to_androguard import generate_mappings
# generate_mappings()

setup(
    name='androguard',
    description='Androguard is a full python tool to play with Android files.',
    long_description="""Androguard is a tool and python library to interact with Android Files.
    
    Usually they come in the form of Android Packages (APK) or Dalvik Executeable (DEX) files.
    Androguard has tools to read Android's binary format for XML files (AXML) and is also suited with a decompiler for DEX.
    
    Androguard might not only be used as a tool for reverse engineering single applications, but features a lot of functions
    for automated analysis. It provides a pure python framework to build your own analysis tools.
    
    If you encounter bugs while using androguard, please feel free to report them in our bugtracker_.
    
    .. _bugtracker: https://github.com/androguard/androguard/issues
    """,
    version=__version__,
    license="Apache Licence, Version 2.0",
    url="https://github.com/androguard/androguard",
    download_url="https://github.com/androguard/androguard/releases",
    packages=find_packages(),
    package_data={
        # add the json files, residing in the api_specific_resources package
        "androguard.core.api_specific_resources": ["aosp_permissions/*.json",
                                                   "api_permission_mappings/*.json"],
        "androguard.core.resources": ["public.xml"],
        # Collect also the GUI files this way
        "androguard.gui": ["annotation.ui", "search.ui", "androguard.ico"],
    },
    scripts=['androaxml.py',
             'androarsc.py',
             'androsign.py',
             'androauto.py',
             'androdis.py',
             'androlyze.py',
             'androdd.py',
             'androgui.py',
             'androcg.py',
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
        'docs': ['sphinx', "sphinxcontrib-programoutput>0.8", 'sphinx_rtd_theme'],
        'graphing': ['pydot'],
        'tests': ['mock>=2.0', 'nose', 'codecov', 'coverage', 'nose-timer'],
    },
    setup_requires=['setuptools'],

)
