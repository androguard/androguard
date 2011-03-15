##########################################################################
####################### Androguard : Android Guard #######################
##########################################################################
################### http://code.google.com/p/androguard ##################
###################### androguard (at) t0t0 (dot) fr #####################
##########################################################################


1 -] About

Androguard is primarily a tool written in full python to play with :
   - .class (JVM) format
   - .dex (DalvikVM) format

So, you can analyze, display, modify and save your apps easily and 
statically by creating your own software (by using the API), or by using 
the tool (androlyze) in command line.

Moreover, we are trying to obfuscate your apps by using new techniques,
but you must now that obfuscation is a difficult problem, and you can't
hide something into your software in a 'secure manner'. But we can try to
block as possible evil guys to steal a part of your apps, and resell them
into the market.

We are trying to implement dynamic and metamorphism Virtual Machines. For 
example, we can obfuscate classical variable affections with mathematical 
formulas, and integers constants. But the research in this domain is in 
progress and we will publish more information and codes.

You have also the possibility to apply control flow modification, and to
change the name of fields, methods in your apps with random string.

Of course, it's possible to integrate the 'androguard' program into the 
development cycle, for example, directly into ANT (after the java 
compilation, and just before the convertion into .dex format, see USAGE).

This tool has been designed for Android apps, but if you have read this
section, you have seen that we support JVM format, so you can used
this tool with classical Java apps.

If you are interesting to develop and to work on this youth project, you 
can contact me (see the top of this README for my e-mail).

2 -] Usage

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

2.3.1 --] Androlyze 

You can used the command line to display and filter information. But it's better to use the shell :

./androlyze.py -s
Welcome to Androlyze ALPHA 0-update1
>>> j = JVMFormat( open("./VM.class").read() )
>>> j.show()

# Get specific methods
>>> x = j.get_method("<init>")[0]
>>> x.show()

# Change name
>>> x.set_name("toto")

# Save it
>>> fd = open("VM2.class", "w")
>>> fd.write(j.save())
>>> fd.close()

2.3.2 --] Androxgmml

http://androguard.blogspot.com/2011/02/android-apps-visualization.html

You can used it to transform an apk/jar/class/dex files format into an xgmml graph which represent the control flow graph or the functions call.

$ ./androxgmml.py -h
Usage: androxgmml.py [options]

Options:
-h, --help            show this help message and exit
-i INPUT, --input=INPUT 
                     filename input
-o OUTPUT, --output=OUTPUT
                     filename output of the xgmml
-f, --functions       include function calls
-e, --externals       include extern function calls
-v, --version         version of the API

./androxgmml.py -i myapp.jar -o output.xgmml
./androxgmml.py -i myapp.apk -o output.xgmml
./androxgmml.py -i myclass.class -o output.xgmml
./androxgmml.py -i mydex.dex -o output.xgmml

# with functions call :
./androxgmml.py -i myapp.jar -f -o output.xgmml

# with external function calls
./androxgmml.py -i myapp.jar -e -o output.xgmml

# with both
./androxgmml.py -i myapp.jar -e -f -o output.xgmml

2.3.3 --] Androaxml

http://androguard.blogspot.com/2011/03/androids-binary-xml.html

You can used it to transform Android's binary XML (eg: AndroidManifest?.xml) into classic xml (human readable ;)).

$ ./androaxml.py -h
Usage: androaxml.py [options]

Options:
-h, --help            show this help message and exit
-i INPUT, --input=INPUT
                     filename input (APK or android's binary xml)
-o OUTPUT, --output=OUTPUT
                     filename output of the xml
-v, --version         version of the API


$ ./androaxml.py -i yourfile.apk -o output.xml
$ ./androaxml.py -i AndroidManifest.xml -o output.xml

2.3.4 --] Androdump

http://androguard.blogspot.com/2010/11/androdump-dump-your-jvm.htm

$ ./androdump.py -h
Usage: androdump.py [options]

Options:
-h, --help            show this help message and exit
-i INPUT, --input=INPUT 
                      pid
-v, --version         version of the API

pouik@camelot:~/androguard$ ps aux |grep java
   pouik 21008 0.1 0.5 673840 10688 pts/5 Sl+ 10:28 0:02 java Test2
   pouik 21548 0.0 0.0 3060 812 pts/2 S+ 11:00 0:00 grep java
pouik@camelot:~/androguard$ ./androdump.py -i 21008
   HEADER 0x6f990000-0x6fee0000 (rw-p)

   Test2 ()V
   Test2 get_x ()I
   Test2 main ([Ljava/lang/String;)V
   Test2bis ()V
   Test2bis get_T ()Ljava/lang/String;

2.4 --] Disassembler 

http://code.google.com/p/androguard/wiki/Disassembler

2.5 --] Analysis 

http://code.google.com/p/androguard/wiki/Analysis

3 -] References

4 -] Benchmark 

5 -] Roadmap 
http://code.google.com/p/androguard/wiki/RoadMap

6 -] License

Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>                                                                                                                                                                         
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
