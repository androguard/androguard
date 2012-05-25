#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

import sys, os, cmd, threading, code, re


from optparse import OptionParser

from androguard.core import *
from androguard.core.androgen import *
from androguard.core.androconf import *
from androguard.core.bytecode import *
from androguard.core.bytecodes.jvm import *
from androguard.core.bytecodes.dvm import *
from androguard.core.bytecodes.apk import *

from androguard.core.analysis.analysis import *
from androguard.core.analysis.ganalysis import *
from androguard.core.analysis.risk import *

from androguard.decompiler.decompiler import *

from androguard.core import androconf

from IPython.frontend.terminal.embed import InteractiveShellEmbed
from IPython.config.loader import Config

from cPickle import dumps, loads

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use this filename', 'nargs' : 1 }
option_1 = { 'name' : ('-d', '--display'), 'help' : 'display the file in human readable format', 'action' : 'count' }
option_2 = { 'name' : ('-m', '--method'), 'help' : 'display method(s) respect with a regexp', 'nargs' : 1 }
option_3 = { 'name' : ('-f', '--field'), 'help' : 'display field(s) respect with a regexp', 'nargs' : 1 }
option_4 = { 'name' : ('-s', '--shell'), 'help' : 'open an interactive shell to play more easily with objects', 'action' : 'count' }
option_5 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }
option_6 = { 'name' : ('-p', '--pretty'), 'help' : 'pretty print !', 'action' : 'count' }
option_7 = { 'name' : ('-t', '--type_pretty'), 'help' : 'set the type of pretty print (0, 1) !', 'nargs' : 1 }
option_8 = { 'name' : ('-x', '--xpermissions'), 'help' : 'show paths of permissions', 'action' : 'count' }

options = [option_0, option_1, option_2, option_3, option_4, option_5, option_6, option_7, option_8]

def save_session(l, filename) :
    """
        save your session !

        @param l : a list of objects
        @param filename : output filename to save the session
    """
    fd = open(filename, "w")
    fd.write( dumps(l, -1) )
    fd.close()

def load_session(filename) :
    """
        load your session !

        @param filename : the filename where the sessions has been saved
        @rtype : the elements of your session
    """
    return loads( open(filename, "r").read() )

def interact() :
    cfg = Config()
    ipshell = InteractiveShellEmbed(config=cfg, banner1="Androlyze version %s" % androconf.ANDROGUARD_VERSION)
    ipshell()

def AnalyzeAPK(filename, raw=False) :
    """
        Analyze an android application and setup all stuff for a more quickly analysis !

        @param filename : the filename of the android application or a buffer which represents the application
        @param raw : True is you would like to use a buffer
        
        @rtype : return the APK, DalvikVMFormat, and VMAnalysis objects
    """
    androconf.debug("APK ...")
    a = APK(filename, raw)

    d, dx = AnalyzeDex( filename, a.get_dex() )

    return a, d, dx


def AAnalyzeAPK(filename, raw=False, decompiler="dad") :
    """
        Analyze (and decompile) an android application and setup all stuff for a more quickly analysis !

        @param filename : the filename of the android application or a buffer which represents the application
        @param raw : True is you would like to use a buffer
        @param decompiler : ded, dex2jad, dad
        
        @rtype : return the APK, DalvikVMFormat, and VMAnalysis objects
    """
    a, d, dx = AnalyzeAPK( filename, raw )

    androconf.debug("Decompiler ...")
    decompiler = decompiler.lower()
    if decompiler == "dex2jad" :
        d.set_decompiler( DecompilerDex2Jad( d, androconf.CONF["PATH_DEX2JAR"], androconf.CONF["BIN_DEX2JAR"], androconf.CONF["PATH_JAD"], androconf.CONF["BIN_JAD"] ) )
    elif decompiler == "ded" :
        d.set_decompiler( DecompilerDed( d, androconf.CONF["PATH_DED"], androconf.CONF["BIN_DED"] ) )
    elif decompiler == "dad" :
        d.set_decompiler( DecompilerDAD( d, dx ) )
    else :
        print "Unknown decompiler, use default", decompiler
        d.set_decompiler( DecompilerDAD( d, dx ) )

    return a, d, dx

def AnalyzeDex(filename, raw=False) :
    """
        Analyze an android dex file and setup all stuff for a more quickly analysis !

        @param filename : the filename of the android dex file or a buffer which represents the dex file
        @param raw : True is you would like to use a buffe

        @rtype : return the DalvikVMFormat, and VMAnalysis objects
    """
    androconf.debug("DalvikVMFormat ...")
    d = None
    if raw == False :
        d = DalvikVMFormat( open(filename, "rb").read() )
    else :
        d = DalvikVMFormat( raw )

    androconf.debug("EXPORT VM to python namespace")
    ExportVMToPython( d )
    
    androconf.debug("VMAnalysis ...")
    dx = VMAnalysis( d )
    androconf.debug("GVMAnalysis ...")
    gx = GVMAnalysis( dx, None )
    
    d.set_vmanalysis( dx )
    d.set_gvmanalysis( gx )
    
    androconf.debug("XREF ...")
    d.create_xref()
    androconf.debug("DREF ...")
    d.create_dref()
    
    return d, dx

def AAnalyzeDex(filename, raw=False, decompiler="dad") :
    """
        Analyze an android dex file and setup all stuff for a more quickly analysis !

        @param filename : the filename of the android dex file or a buffer which represents the dex file
        @param raw : True is you would like to use a buffe
        @param decompiler : ded, dex2jad, dad

        @rtype : return the DalvikVMFormat, and VMAnalysis objects
    """
    d, dx = AnalyzeDex( filename, raw )

    androconf.debug("Decompiler ...")
    decompiler = decompiler.lower()
    if decompiler == "dex2jad" :
        d.set_decompiler( DecompilerDex2Jad( d, androconf.CONF["PATH_DEX2JAR"], androconf.CONF["BIN_DEX2JAR"], androconf.CONF["PATH_JAD"], androconf.CONF["BIN_JAD"] ) )
    elif decompiler == "ded" :
        d.set_decompiler ( DecompilerDed( d, androconf.CONF["PATH_DED"], androconf.CONF["BIN_DED"] ) )
    elif decompiler == "dad" :
        d.set_decompiler( DecompilerDAD( d, dx ) )
   
    return d, dx

def AnalyzeElf(filename, raw=False) :
    from androguard.core.binaries.elf import ELF 
    e = None
    if raw == False:
        e = ELF( open(filename, "rb").read() )
    else:
        e = ELF( raw )

    ExportElfToPython( e )

    return e

def AnalyzeJAR(filename, raw=False) :
    """
        Analyze an java jar application and setup all stuff for a more quickly analysis !

        @param filename : the filename of the jar or a buffer which represents the application
        @param raw : True is you would like to use a buffer
        
        @rtype : return the JAR, JVMFormat classes
    """
    androconf.debug("JAR ...")
    a = JAR(filename, raw)

    d = AnalyzeClasses( a.get_classes() )

    return a, d

def AnalyzeClasses( classes ) :
  d = {}
  for i in classes :
    d[i[0]] = JVMFormat( i[1] )

  return d

def ExportElfToPython(e) :
    for function in e.get_functions():
        name = "FUNCTION_" + function.name
        setattr( e, name, function )

def sort_length_method(vm) :
    l = []
    for m in vm.get_methods() :
        code = m.get_code()
        if code != None :
            l.append( (code.get_length(), (m.get_class_name(), m.get_name(), m.get_descriptor()) ) )
    l.sort(reverse=True)
    return l

def main(options, arguments) :
    if options.shell != None :
        interact()

    elif options.input != None :
        _a = AndroguardS( options.input )

        if options.type_pretty != None :
            CONF["PRETTY_SHOW"] = int( options.type_pretty )

        if options.display != None :
            if options.pretty != None :
                _a.ianalyze()
                _a.pretty_show()
            else :
                _a.show()

        elif options.method != None :
            for method in _a.get("method", options.method) :
                if options.pretty != None :
                    _a.ianalyze()
                    method.pretty_show() 
                else :
                    method.show()

        elif options.field != None :
            for field in _a.get("field", options.field) :
                field.show()

        elif options.xpermissions != None :
            _a.ianalyze()
            perms_access = _a.get_analysis().get_permissions( [] )
            for perm in perms_access :
                print "PERM : ", perm
                for path in perms_access[ perm ] :
                    print "\t%s %s %s (@%s-0x%x)  ---> %s %s %s" % ( path.get_method().get_class_name(), path.get_method().get_name(), path.get_method().get_descriptor(), \
                                                                     path.get_bb().get_name(), path.get_bb().start + path.get_idx(), \
                                                                     path.get_class_name(), path.get_name(), path.get_descriptor())

    elif options.version != None :
        print "Androlyze version %s" % androconf.ANDROGUARD_VERSION

if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
