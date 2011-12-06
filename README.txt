##########################################################################
####################### Androguard : Android Guard #######################
##########################################################################
################### http://code.google.com/p/androguard ##################
###################### androguard (at) t0t0 (dot) fr #####################
##########################################################################


1 -] About

Androguard (Android Guard) is primarily a tool written in full python to 
play with :
    - .dex (DalvikVM)
    - APK
    - Android's binary xml
    - .class (JavaVM)
    - JAR

Androguard has the following features :
    - Map and manipulate (read/write) DEX/CLASS/APK/JAR files into full 
      Python objects,
    - Native support of DEX code in a c++ library,
    - Access to the static analysis of your code (basic blocks, 
      instructions, permissions (with database from 
      http://www.android-permissions.org/) ...) and create your own static
      analysis tool,
    - Check if an android application is present in a database (malwares, 
      goodwares ?),
    - Open source database of android malwares,
    - Diffing of android applications,
    - Measure the efficiency of obfuscators (proguard, ...),
    - Determine if your application has been pirated (rip-off indicator),
    - Risk indicator of malicious application,
    - Reverse engineering of applications (goodwares, malwares),
    - Transform Android's binary xml (like AndroidManifest.xml) into 
      classic xml,
    - Visualize your application into cytoscape (by using xgmml format), 
      or PNG/DOT output,
    - Patch JVM classes, add native library dependencies,
    - Dump the jvm process to find classes into memory,
    - Add a watermark into your application (in progress),
    - Classify android apks (in progress),
    - Protect your application against thefts on android market (in 
      progress),
    - ...

So, you can analyze, display, modify and save your apps easily and 
statically by creating your own software (by using the API), or by
using the tool (androlyze) in command line. This tool is useful 
when you would like to do reverse engineering on a specific 
application (e.g : malware).

The second part of the tool is to do new tools to get differences 
between two android/java applications, or to find similarities 
in different applications (e.g : to check if a part or entire 
application has been stolen).

And for now, you can check if an android application is present 
in a database (like a malware).

This tool has been designed for Android apps, but if you have read 
this section, you have seen that we support JVM format, so you can
used this tool with classical Java apps.

If you are interesting to develop and to work on this youth project, you 
can contact me (see the top of this README for my e-mail).

2 -] Usage

You need to follow the following information to install dependencies
for androguard :
    http://code.google.com/p/androguard/wiki/Installation

All objects can be access directly, and most of the time, there is 
a field called "format" which contained the raw fields which can 
be changed :
>>> j = JVMFormat( open("./VM.class").read() )
>>> x = j.get_method("<init>")[0]
>>> print x.format
MethodInfo(access_flags=0, name_index=40, descriptor_index=41, \
           attributes_count=1)
>>> x.format.get_value_buff()
'\x00\x00\x00(\x00)\x00\x01'
>>> x.format.set_value( { "access_flags" : 1 } )
>>> x.format.get_value_buff()
'\x00\x01\x00(\x00)\x00\x01'
>>> print x.format
MethodInfo(access_flags=1, name_index=40, descriptor_index=41, \
           attributes_count=1)


So you can do what you would like with that, but be carefull because it's
possible to have an unusable format if you change something that you don't
know correctly. But most of the time there will be no problem, but if you
don't know what you are doing, it's better to use the providing API to
change a field.

You must go to the website to see more example :
   http://code.google.com/p/androguard/wiki/Usage

2.1 --] API

see the directory 'doc'

2.1.1 --] Instructions

http://code.google.com/p/androguard/wiki/Instructions

2.2 --] Demos

see the source codes in the directory 'demos'

2.3 --] Tools 

http://code.google.com/p/androguard/wiki/Usage

2.4 --] Disassembler 

http://code.google.com/p/androguard/wiki/Disassembler

2.5 --] Analysis 

http://code.google.com/p/androguard/wiki/Analysis

2.6 --] Visualization

http://code.google.com/p/androguard/wiki/Visualization

2.7 --] Similarities, Diffing, plagiarism/rip-off indicator 

http://code.google.com/p/androguard/wiki/Similarity
http://code.google.com/p/androguard/wiki/DetectingApplications

2.8 --] Open Source database of android malwares

http://code.google.com/p/androguard/wiki/DatabaseAndroidMalwares

2.9 --] Decompiler

3 -] Roadmap/Issues
http://code.google.com/p/androguard/wiki/RoadMap
http://code.google.com/p/androguard/issues/list

4 -] License

Copyright (C) 2011, Anthony Desnos <desnos at t0t0.fr>
All rights reserved.

Androguard is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Androguard is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of  
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Androguard.  If not, see <http://www.gnu.org/licenses/>.
