#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'androguard',
    version = '1.0',
    packages = find_packages(),
    scripts = ['androaxml.py', 'androcsign.py', 'androdiff.py', 'androgexf.py',
        'androlyze.py', 'andromercury.py', 'androrisk.py', 'androsign.py',
        'androsim.py', 'androxgmml.py', 'apkviewer.py'],
    install_requires=['distribute'],
)
