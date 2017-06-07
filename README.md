# Androguard

[![Build Status](https://travis-ci.org/androguard/androguard.svg?branch=master)](https://travis-ci.org/androguard/androguard)

## Features

Androguard is a full python tool to play with Android files.

* DEX, ODEX
* APK
* Android's binary xml
* Android resources
* Disassemble DEX/ODEX bytecodes
* Decompiler for DEX/ODEX files

## 1. Authors: Androguard Team

Androguard + tools: Anthony Desnos (desnos at t0t0.fr).

DAD (DAD is A Decompiler): Geoffroy Gueguen (geoffroy dot gueguen at gmail dot com)

## 2. Stable release

See the stable release here:
https://github.com/androguard/androguard/releases

You can also install androguard from the Debian repositories: [androguard](http://packages.debian.org/androguard).

## 3. Documentation

Link here to the documentation... sometime...

Meanwhile you can build the documentation with `sphinx`!

## 4. Building and Requirements

### Using Debian based Distributions
Assuming you are using Debian, most of the packages are available from standard repos.

For androguard:

`apt install python python-pyqt5 python-pyperclip python-networkx ipython python-future python-pyasn1 python-cryptography python-magic python-pydot`

You should be able to use python3 as well:

`apt install python3 python3-pyqt5 python3-pyperclip python3-networkx ipython3 python3-future python3-pyasn1 python3-cryptography python3-magic python3-pydot`

If you are installing the libraries using `pip`, make sure you download the correct packages. For example, there are a lot of implemenations of the `magic` library. Get the one, that is shipped with the file command (See [Fine Free File Command](http://www.darwinsys.com/file/)) or use `filemagic`, which should work as well.

and for building the documentation (optional):

`apt install python-sphinx python-sphinxcontrib.programoutput`

or

`apt install python3-sphinx python3-sphinxcontrib.programoutput`

when using python3.

To install androguard, just use:

`python setup.py install`

The documentation can be build using:

`python setup.py build_sphinx`

For running the unit tests, the `mock` library is required:

`apt install python-mock` or `apt install python3-mock`


### Using Windows

Using Anaconda with python3, most of the used packages are pre-installed.

Additional packages, that might be required are:

`pyperclip sphinxcontrib-programoutput future pydot`

You can simply run

`python setup.py install`

to install androguard.

and

`python setup.py build_sphinx`

to create the documentation.


## 5. Licenses

* Androguard

Copyright (C) 2012 - 2016, Anthony Desnos (desnos at t0t0.fr)
All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS-IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

* DAD

Copyright (C) 2012 - 2016, Geoffroy Gueguen (geoffroy dot gueguen at gmail dot com)
All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS-IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
