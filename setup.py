#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# vim: fenc=utf-8
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#

"""
File name: setup.py
Version: 0.1
Author: dhilipsiva <dhilipsiva@gmail.com>
Date created: 2015-11-24
"""

from setuptools import setup, find_packages

setup(
    name='ak-androguard',
    version='3.2.1',
    description="A fork of official Androguard project",
    url='https://github.com/appknox/ak-androguard',
    author='dhilipsiva',
    author_email='dhilipsiva@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='A fork of official Androguard project',
    packages=find_packages(),
    entry_points='''
    ''',
    scripts=[
        'androaxml.py', 'androcsign.py', 'androdiff.py', 'androgexf.py',
        'androlyze.py', 'androsign.py', 'androsim.py', 'apkviewer.py',
        'androdd.py', 'androgui.py',
    ],
    install_requires=['distribute'],
    extras_require={
        'dev': [''],
        'test': [''],
    },
)
