# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>
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

import hashlib

import androconf 
from wm import WM_CLASS, WM_METHOD
import analysis as _analysis

def INIT() :
    return [ BM_A0, BM_A1 ]

class BM_A0 :
    TYPE = WM_CLASS
    NAME = "BM_A0"
    def __init__(self, vm, analysis) :
        self.__vm = vm
        self.__analysis = analysis

        self.__context = {
                             "L_X" : [],
                             "SIGNATURES" : [],
                         }

    def run(self) :
        for i in self.__vm.get_methods() :
            self.__context[ "SIGNATURES" ].append( self.__analysis.get_method_signature( i, _analysis.GRAMMAR_TYPE_ANONYMOUS) )
            self.__context[ "SIGNATURES" ].append( self.__analysis.get( i ).get_ts() )

        for i in self.__context[ "SIGNATURES" ] :
            if len(i) > 10 :
                self.__context[ "L_X" ].append(
                                                 androconf.str2long( hashlib.md5( i ).hexdigest() )
                                              )

    def challenge(self, external_wm) :
        return external_wm.get_context()[ "L_X" ]

    def get(self) :
        return self.__context[ "L_X" ]

    def set_context(self, values) :
        for x in values :
            self.__context[ x ] = values[ x ]

    def get_context(self) :
        return self.__context

    def get_export_context(self) :
        return {}

    def get_import_context(self) :
        return {}

class BM_A1 :
    TYPE = WM_METHOD
    NAME = "BM_A1"
    def __init__(self, vm, method, analysis) :
        self.__vm = vm
        self.__method = method
        self.__analysis = analysis
        if self.__analysis != None :
            self.__method_analysis = self.__analysis.get(self.__method)

        self.__context = {
                             "L_X" : [],
                             "SIGNATURES" : [],
                         }
    def run(self) :
        self.__context[ "SIGNATURES" ].append( self.__analysis.get_method_signature(self.__method, _analysis.GRAMMAR_TYPE_ANONYMOUS) )
        self.__context[ "SIGNATURES" ].append( self.__method_analysis.get_ts() )

        for i in self.__context[ "SIGNATURES" ] :
            if len(i) > 10 :
                self.__context[ "L_X" ].append(
                                                 androconf.str2long( hashlib.md5( i ).hexdigest() )
                                              )

    def challenge(self, external_wm) :
        return external_wm.get_context()[ "L_X" ]

    def get(self) :
        return self.__context[ "L_X" ]

    def set_context(self, values) :
        for x in values :
            self.__context[ x ] = values[ x ]

    def get_context(self) :
        return self.__context

    def get_export_context(self) :
        return {}

    def get_import_context(self) :
        return {}
