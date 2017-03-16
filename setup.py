#!/usr/bin/env python
import sys
import os

from setuptools import setup, find_packages

# TODO this is actually a hack... How to copy the files to the right folder?
#guidir = os.path.join(sys.prefix, 'Scripts', 'androguard', 'gui')
#if not os.path.isdir(guidir):
#    os.makedirs(guidir)

setup(
    name='androguard',
    description='Androguard is a full python tool to play with Android files.',
    version='2.0',
    packages=find_packages(),
    #data_files = [(guidir, ["androguard/gui/annotation.ui", "androguard/gui/search.ui", "androguard/gui/androguard.ico"])],
    scripts=['androaxml.py',
             'androlyze.py',
             'androdd.py',
             'androgui.py',],
    install_requires=['pyasn1', 'cryptography>=1.0', 'future', 'ipython>=5.0.0', 'networkx', 'pygments'],
    extras_require={
        'GUI': ["pyperclip", "PyQt5"],
        'docs': ['sphinx', 'sphinxcontrib-programoutput'],
        # If you are installing on debian, you can use python3-magic instead
        'magic': ['filemagic'],
        'graphing': ['pydot'],
    },
    setup_requires=['setuptools'],
    
)
