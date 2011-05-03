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

import misc, hashlib, string, random

def INIT() :
    return WM_L5

class WM_L5 :
    def __init__(self, _vm, _method, _analysis) :
        self.__vm = _vm
        self.__method = _method
        self.__analysis = _analysis

        self.__context = {
                             "L_X" : [],
                         }

    def get_name(self) :
        return "WM_GRAPH"

    def run(self) :
        pass

    def challenge(self, external_wm) :
        return self.__context[ "L_X" ]

    def get(self) :
        for i in range(0, 30) :
            self.__context[ "L_X" ].append( i )

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
