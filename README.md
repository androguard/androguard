
<p align="center"><img width="120" src="./.github/logo.png"></p>
<h2 align="center">Androguard</h2>

# Androguard: Reverse engineering and pentesting for Android applications

<div align="center">

![Powered By: Androguard](https://img.shields.io/badge/androguard-green?style=for-the-badge&label=Powered%20by&link=https%3A%2F%2Fgithub.com%2Fandroguard)

</div>


[![PyPI Upload](https://github.com/androguard/androguard/actions/workflows/pythonpublish.yml/badge.svg)](https://github.com/androguard/androguard/actions/workflows/pythonpublish.yml)
![PyPI - Version](https://img.shields.io/pypi/v/androguard)
![Static Badge](https://img.shields.io/badge/Documentation-InProgress-red)

Do you think your phone has been pwned ? please check [IsMyPhonePwned](https://github.com/IsMyPhonePwned)


## Installation

```bash
pip install androguard

# optional Dalvik disassembly (Rust extension)
pip install 'androguard[disasm]'

# optional Java decompiler (Rust extension)
pip install 'androguard[decompile]'

# both extensions
pip install 'androguard[full]'
```

**DEX parsing** ([dex-parser](https://github.com/androguard/dex-parser)) ships as a native extension (`dexparser-ag`). For development from source you need Rust and [maturin](https://www.maturin.rs/):

```bash
git clone https://github.com/androguard/dex-parser.git
cd dex-parser
python3 -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop --manifest-path dexparser-py/Cargo.toml
pip install androguard
```

> [!IMPORTANT]
> Versions >= 4.0.0 are new releases after a long time, where the project has substantial differences from the previous stable version 3.3.5 from 2019. This means that certain functionalities have been removed. If you notice an issue with your project using the latest version, please open up an [issue](https://github.com/androguard/androguard/issues).

## Ecosystem

Androguard v5 is built on dedicated libraries:

| Layer | Library | Role |
|-------|---------|------|
| APK archive | [apk-parser](https://github.com/androguard/apk-parser) (`apkparser-ag`) | ZIP structure, signatures, manifest hooks |
| DEX structure | [dex-parser](https://github.com/androguard/dex-parser) (`dexparser-ag`) | Rust core + Python bindings: classes, methods, fields, bytecode |
| Binary XML / ARSC | [axml](https://github.com/androguard/axml) / [axml-parser](https://github.com/androguard/axml-parser) (Rust) | `AndroidManifest.xml`, `resources.arsc` |
| Bytecode (optional) | [dex-bytecode](https://github.com/androguard/dex-bytecode) | Dalvik disassembly via `androguard[disasm]` |
| Decompiler (optional) | [dex-decompiler](https://github.com/androguard/dex-decompiler) | DEX → Java via `androguard[decompile]` |

## Quick start

### Command line

```bash
# Summary: package, main activity, dex count, classes, methods
androguard -i my.apk

# List classes or methods
androguard -i my.apk --list-classes
androguard -i my.apk --list-methods

# Disassemble methods matching regex (requires androguard[disasm])
androguard -i my.apk --disasm --class 'TestActivity' --method 'onCreate'
androguard -i my.apk --disasm --class 'Ltests/androguard/.*' --method '<init>'
androguard -i my.apk --disasm --method 'onCreate' --limit 10

# Decompile to Java (requires androguard[decompile])
androguard -i my.apk --decompile-method 'tests.androguard.TestActivity#onCreate'
androguard -i my.apk --decompile --class TestActivity --method onCreate
androguard -i my.apk --decompile -o out.java
androguard -i my.apk -d decompiled/ --only-package tests.androguard
```

### High-level API (`Application`)

```python
from androguard import Application

app = Application("my.apk")

print(app.summary())
# {'app_name': '...', 'main_activity': '...', 'package': 'com.example',
#  'dex_files': ['classes.dex', ...], 'classes': 1234, 'strings': 5678,
#  'methods': 8900, 'signed': True}

for name in app.class_names[:10]:
    print(name)

for method in app.methods:
    if method.get_code():
        print(method.class_name, method.name, method.get_code().insns_size)
```

### APK layer (`apkparser-ag`)

```python
import io
from apkparser import APK, OPTION_AXML, OPTION_SIGNATURE, OPTION_PERMISSION

with open("my.apk", "rb") as f:
    apk = APK(
        io.BytesIO(f.read()),
        {
            OPTION_AXML: True,
            OPTION_SIGNATURE: True,
            OPTION_PERMISSION: True,
        },
    )

print(apk.get_app_name())
print(apk.get_main_activity())
print(apk.axml.package if apk.axml else "")  # from decoded manifest
print(list(apk.get_dex_names()))  # classes.dex, classes2.dex, ...

manifest_xml = apk.get_android_manifest()
raw_manifest = apk.get_file("AndroidManifest.xml")
```

Or through Androguard re-exports:

```python
from androguard.core.apk import APK, OPTION_AXML
```

### DEX layer ([dex-parser](https://github.com/androguard/dex-parser))

From an APK’s DEX blobs:

```python
from dexparser import DEX, DEXHelper, DEX_from_source

# From APK bytes (via apkparser)
raw = apk.get_file("classes.dex")
dh = DEXHelper.from_string(raw)

# From a .dex file on disk
d = DEX.from_path("classes.dex")
dh = DEXHelper.from_rawdex(d)

# Path, bytes, or stream
dh = DEXHelper.from_rawdex(DEX_from_source("classes.dex"))
```

Iterate structure:

```python
for cls in dh.get_classes():
    print("CLASS", cls.name, "extends", cls.sname)

for method in dh.get_methods():
    print("METHOD", method.class_name, method.name, method.proto)
    code = method.get_code()
    if code:
        insns = code["insns"].value   # raw Dalvik bytecode (bytes)
        print("  insns:", code.insns_size, "bytes:", len(insns))

for field in dh.get_fields():
    print("FIELD", field.class_name, field.name, field.type_field)

for s in dh.get_strings():
    if "password" in s.lower():
        print(s)
```

Header as a dict:

```python
d = DEX(bytes_data)
print(d["header"])  # file_size, class_defs_size, string_ids_size, ...
```

Androguard shortcuts:

```python
from androguard.misc import AnalyzeAPK, AnalyzeDex

apk_obj, dex_helpers, app = AnalyzeAPK("my.apk")
dh = AnalyzeDex("classes.dex")       # path or bytes
```

### Dalvik disassembly (`dex-bytecode`, optional)

```python
from androguard.core.bytecode import disassemble, disassemble_method_code

# Raw bytecode
for ins in disassemble(b"\x00\x00\x0e\x00"):
    print(f"{ins['offset']:08x}  {ins['mnemonic']} {ins['operands']}")

# From a parsed method
code = method.get_code()
if code:
    for ins in disassemble_method_code(code):
        print(ins["disasm"])
```

Through `Application`:

```python
for method in app.methods:
    code = method.get_code()
    if not code:
        continue
    for line in app.iter_disassembly(method):
        print(line)
```

### Java decompilation ([dex-decompiler](https://github.com/androguard/dex-decompiler), optional)

```python
from androguard.core.decompiler import (
    parse_dex,
    decompile_method,
    descriptor_to_java,
)

raw = apk.get_file("classes.dex")
dex = parse_dex(raw)

# Entire DEX as one Java source string
print(dex.decompile()[:2000])

# One method (Java class names)
java = dex.decompile_method("tests.androguard.TestActivity", "onCreate")

# Package layout on disk
dex.decompile_to_dir("out/")

# Dalvik descriptor → Java name
print(descriptor_to_java("Ltests/androguard/TestActivity;"))
# tests.androguard.TestActivity
```

Through `Application`:

```python
# CLASS#METHOD selector (Java names, same as dex-decompiler CLI)
print(app.decompile_method_selector("tests.androguard.TestActivity#onCreate"))

# Regex on Dalvik descriptors / method names
for method, source in app.iter_decompiled_methods(
    class_pattern=r"TestActivity",
    method_pattern=r"onCreate",
):
    print(method.class_name, "→", len(source), "chars")

# All DEX files from the APK → decompiled/ classes/ classes2/ …
app.decompile_apk_to_dir("decompiled/", only_package="tests.androguard")
```

Build from source (requires Rust + maturin):

```bash
git clone https://github.com/androguard/dex-decompiler.git
cd dex-decompiler/dex-decompiler-py
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 maturin develop --release
```

### Legacy entry point

Scripts that used `AnalyzeAPK` in older Androguard versions can keep the same call pattern; the third return value is now a full `Application` instead of a cross-reference `Analysis` object (not yet restored in v5):

```python
from androguard.misc import AnalyzeAPK

apk_obj, dex_list, app = AnalyzeAPK("my.apk")
print(app.summary())
```

## Documentation

**Documentation contains outdated information — in progress of updating**

The [Github Pages Documentation](http://androguard.github.io/androguard/) is the most up to date source.

Additional documentation that contains outdated information is available at [ReadTheDocs](http://androguard.readthedocs.io/en/latest/).

## Authors: Androguard Team

Androguard + tools: Anthony Desnos (anthony at 42.bzh).

## Projects using Androguard

In alphabetical order:

* [AndroPyTool](https://github.com/alexMyG/AndroPyTool)
* [AppKnox](http://appknox.com)
* [Cuckoo Sandbox](https://cuckoosandbox.org)
* [Deckard](https://github.com/hrkfdn/deckard)
* [Droidbot](https://github.com/honeynet/droidbot)
* [Droidstatx](https://github.com/integrity-sa/droidstatx)
* [εxodus](https://github.com/Exodus-Privacy/exodus)
* [F-Droid Server](https://gitlab.com/fdroid/fdroidserver)
* [gplaycli](https://github.com/matlink/gplaycli)
* [Koodous](https://koodous.com)
* [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF)
* [qiew](https://github.com/mtivadar/qiew)
* [Quark-Engine](https://github.com/quark-engine/quark-engine)
* [Virustotal](https://virustotal.readme.io/reference/androguard)
* [Viper Framework](https://github.com/viper-framework/viper)
* ... and many more!

You are using Androguard and are not listed here? Just create a [ticket](https://github.com/androguard/androguard/issues) or send us a [pull request](https://github.com/androguard/androguard/pulls) with your project!

## Licenses

### Androguard

Copyright (C) 2012 - 2026, Anthony Desnos (anthony at 42.bzh)
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
