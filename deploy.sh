#! /bin/bash
#
# deploy.sh
# Copyright (C) 2016 dhilipsiva <dhilipsiva@gmail.com>
#
# Distributed under terms of the MIT license.
#

rm -rf dist/
python setup.py sdist
python setup.py bdist_wheel
twine upload dist/*
