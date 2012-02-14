#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = 'androguard',
    version = '1.0',
    packages = find_packages(),
    scripts = ['androaxml.py'],
    install_requires=['distribute'],
)
