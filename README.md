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

##1. Authors: Androguard Team

Androguard + tools: Anthony Desnos (desnos at t0t0.fr).

DAD (DAD is A Decompiler): Geoffroy Gueguen (geoffroy dot gueguen at gmail dot com)

##2. Stable release

See the stable release here:
https://github.com/androguard/androguard/releases

You can also install androguard from the Debian repositories: [androguard](http://packages.debian.org/androguard).

##3. Documentation

Link here to the documentation... sometime...

Meanwhile you can build the documentation with `sphinx`!

##4. Building and Requirements

Assuming you are using Debian, most of the packages are available from standard repos.

For androguard and elsim:

`apt install python python-pyqt5 python-pyperclip python-networkx ipython libstdc++6 libgcc1 lib6 liblzma5 libmuparser2v5 libsnappy1v5 libbz2-1.0 zlib1g`

There are some additional dependencies, which are optional. They are unfortunately not in the
Debian repos, thus must be installed from the sources:

* `elfesteem` can be found here" [elfesteem](https://github.com/serpilliere/elfesteem)
* Radare2 Bindings can be found here: [radare2-bindings](https://github.com/radare/radare2-bindings)
* `miasm` can be found here: [miasm](https://github.com/cea-sec/miasm)
* `idaapi` can be found here: [idapython](https://github.com/idapython/src) (Needs Hex-Rays IDA Pro as well)

To build androguard and elsim from scratch, you need some additional packages.

`apt install build-essential liblzma-dev libmuparser-dev libsnappy-dev libbz2-dev zlib1g-dev libsparsehash-dev`

and for building the documentation:

`apt install python-sphinx python-sphinxcontrib.programoutput`


##5. Licenses

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
