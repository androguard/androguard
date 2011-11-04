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

import androconf 
import hashlib

def INIT() :
    return WM_L1

class WM_L1 :
    def __init__(self, vm, method, analysis) :
        self.__vm = vm
        self.__method = method
        self.__analysis = analysis

        self.__context = {
                             "L_X" : [],
                             "STRING" : "",
                         }

    def get_name(self) :
        return "WM_STRING"

    def run(self) :
        x = self.__analysis.get(self.__method)

        self.__context[ "STRING" ] = x.get_ts()

        self.__context[ "L_X" ].append(
                                         androconf.str2long( hashlib.md5( self.__context[ "STRING" ] ).hexdigest() )
                                      )

    def challenge(self, external_wm) :
        distance = androconf.levenshtein( self.__context["STRING"], external_wm.get_context()["STRING"] )

        if distance <= 2 :
            return self.__context[ "L_X" ]

        return []

    def get(self) :
        return self.__context[ "L_X" ]

    def set_context(self, values) :
        for x in values :
            self.__context[ x ] = values[ x ]

    def get_context(self) :
        return self.__context

    def get_export_context(self) :
        return self.__context

    def get_import_context(self) :
        return {}
