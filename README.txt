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

2.1 --] API

see the directory 'doc'

2.2 --] Demos

see the directory 'demos'

2.3 --] Androlyze

You can used the command line to display and filter information. But it's
better to use the shell :

!./androlyze.py -s
Welcome to Androlyze ALPHA 0
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

3 -] References

4 -] Performances

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
