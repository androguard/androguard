#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'androguard',
    version = '2.0',
    packages = find_packages(),
    scripts = ['androaxml.py', 'androcsign.py', 'androdiff.py', 'androgexf.py',
               'androlyze.py', 'andromercury.py', 'androrisk.py', 'androsign.py',
               'androsim.py', 'androxgmml.py', 'apkviewer.py',
               'androdd.py', 'androapkinfo.py', 'androgui.py',
               ],
    install_requires=['distribute'],
)
