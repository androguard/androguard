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

from error import error

from analysis import TAINTED_PACKAGE_CREATE, TAINTED_PACKAGE_CALL

FIELD_ACCESS = { "R" : 0, "W" : 1 }
PACKAGE_ACCESS = { TAINTED_PACKAGE_CREATE : 0, TAINTED_PACKAGE_CALL : 1 }
class Sign : 
    def __init__(self) :
        self.levels = {} 
        self.hlevels = []

    def add(self, level, value) :
        self.levels[ level ] = value
        self.hlevels.append( level )

    def get_level(self, l) :
        return self.levels[ "L%d" % l ]

    def get_string(self) :
        buff = ""
        for i in self.hlevels :
            buff += self.levels[ i ]
        return buff

class Signature :
    def __init__(self, tainted_information) :
        self.__tainted = tainted_information

        self._cached_signatures = {}
        self._cached_fields = {}
        self._cached_packages = {}

        self.levels = {
                        # Classical method signature with basic blocks, strings, fields, packages
                        "L0" : {
                                    0 : ( "_get_strings_a",     "_get_fields_a",    "_get_packages_a" ),
                                    1 : ( "_get_strings_pa",    "_get_fields_a",    "_get_packages_a" ),
                                    2 : ( "_get_strings_a",     "_get_fields_a",    "_get_packages_pa_1" ),
                                    3 : ( "_get_strings_a",     "_get_fields_a",    "_get_packages_pa_2" ),
                                },
                        
                        # strings
                        "L1" : [ "_get_strings_a1" ],

                        # exceptions
                        "L2" : [ "_get_exceptions" ],
                        
                        # fill array data
                        "L3" : [ "_get_fill_array_data" ],

                        # instructions


                    }

        self._init_caches()

    def _get_bb(self, analysis_method, functions, options) :
        l = []
        for b in analysis_method.basic_blocks.get() :
            l.append( (b.start, "B") )
            l.append( (b.start, "[") )

            internal = []

            if "return" in b.get_last().get_name() :
                internal.append( (b.end, "R") )
            elif "if" in b.get_last().get_name() :
                internal.append( (b.end, "I") )
            elif "goto" in b.get_last().get_name() :
                internal.append( (b.end, "G") )
            
            for f in functions :
                try :
                    internal.extend( getattr( self, f )( analysis_method, options ) )
                except TypeError :
                    internal.extend( getattr( self, f )( analysis_method ) )

            internal.sort()

            for i in internal :
                if i[0] >= b.start and i[0] <= b.end :
                    l.append( i )

            del internal

            l.append( (b.end, "]") )
        return l

    def _init_caches(self) :
        if self._cached_fields == {} :
            for f_t, f in self.__tainted["variables"].get_fields() :
                self._cached_fields[ f ] = f_t.get_paths_length()
            n = 0
            for f in sorted( self._cached_fields ) :
                self._cached_fields[ f ] = n
                n += 1

        if self._cached_packages == {} :
            for m_t, m in self.__tainted["packages"].get_packages() :
                self._cached_packages[ m ] = m_t.get_paths_length()
            n = 0
            for m in sorted( self._cached_packages ) :
                self._cached_packages[ m ] = n
                n += 1

    def _get_fill_array_data(self, analysis_method) :
        buff = ""
        for b in analysis_method.basic_blocks.get() :
            for i in b.ins :
                if i.op_name == "FILL-ARRAY-DATA" :
                    buff_tmp = i.get_operands()
                    for j in range(0, len(buff_tmp)) :
                        buff += "\\x%02x" % ord( buff_tmp[j] )
        return buff

    def _get_exceptions(self, analysis_method) :
        buff = ""

        method = analysis_method.get_method()
        code = method.get_code()
        if code == None :
            return buff

        handlers = code.handlers
#       for try_item in method.get_code().tries :
#           print "w00t", try_item

        for handler_catch_list in method.get_code().handlers :
            #print "\t HANDLER_CATCH_LIST SIZE", handler_catch_list.size
            for handler_catch in handler_catch_list.list :
                #print "\t\t HANDLER_CATCH SIZE ", handler_catch.size
                for handler in handler_catch.handlers :
                    buff += analysis_method.get_vm().get_class_manager().get_type( handler.type_idx )
                    #print "\t\t\t HANDLER", handler.type_idx, a.get_vm().get_class_manager().get_type( handler.type_idx ), handler.add
        return buff

    def _get_strings_a1(self, analysis_method) :
        buff = ""

        strings_method = self.__tainted["variables"].get_strings_by_method( analysis_method.get_method() )
        for s in strings_method :
            for path in strings_method[s] :
                buff += s.replace('\n', ' ')
        return buff

    def _get_strings_pa(self, analysis_method) :
        l = []

        strings_method = self.__tainted["variables"].get_strings_by_method( analysis_method.get_method() )
        for s in strings_method :
            for path in strings_method[s] :
                l.append( (path.get_bb().start + path.get_idx(), "S%d" % len(s) ) )
        return l


    def _get_strings_a(self, analysis_method) :
        l = []

        strings_method = self.__tainted["variables"].get_strings_by_method( analysis_method.get_method() )
        for s in strings_method :
            for path in strings_method[s] :
                l.append( (path.get_bb().start + path.get_idx(), "S") )
        return l

    def _get_fields_a(self, analysis_method) :
        fields_method = self.__tainted["variables"].get_fields_by_method( analysis_method.get_method() )

        l = []

        for f in fields_method :
            for path in fields_method[ f ] :
                l.append( (path.get_bb().start + path.get_idx(), "F%d" % FIELD_ACCESS[ path.get_access_flag() ]) )
        return l

    def _get_packages_a(self, analysis_method) :
        packages_method = self.__tainted["packages"].get_packages_by_method( analysis_method.get_method() )

        l = []

        for m in packages_method :
            for path in packages_method[ m ] :
                l.append( (path.get_bb().start + path.get_idx(), "P%s" % (PACKAGE_ACCESS[ path.get_access_flag() ]) ) )
        return l

    def _get_packages_pa_1(self, analysis_method, include_packages) :
        packages_method = self.__tainted["packages"].get_packages_by_method( analysis_method.get_method() )

        l = []

        for m in packages_method :
            for path in packages_method[ m ] :
                present = False
                for i in include_packages :
                    if m.find(i) == 0 :
                        present = True
                        break

                if present == False :
                    continue

                if path.get_access_flag() == 1 :
                    l.append( (path.get_bb().start + path.get_idx(), "P%s{%s%s%s}" % (PACKAGE_ACCESS[ path.get_access_flag() ], path.get_class_name(), path.get_name(), path.get_descriptor()) ) )
                else :
                    l.append( (path.get_bb().start + path.get_idx(), "P%s{%s}" % (PACKAGE_ACCESS[ path.get_access_flag() ], m) ) )

        return l

    def _get_packages_pa_2(self, analysis_method, include_packages) :
        packages_method = self.__tainted["packages"].get_packages_by_method( analysis_method.get_method() )

        l = []

        for m in packages_method :
            for path in packages_method[ m ] :
                present = False
                for i in include_packages :
                    if m.find(i) == 0 :
                        present = True
                        break
                
                if present == True :
                    l.append( (path.get_bb().start + path.get_idx(), "P%s" % (PACKAGE_ACCESS[ path.get_access_flag() ]) ) )
                    continue


                if path.get_access_flag() == 1 :
                    l.append( (path.get_bb().start + path.get_idx(), "P%s{%s%s%s}" % (PACKAGE_ACCESS[ path.get_access_flag() ], path.get_class_name(), path.get_name(), path.get_descriptor()) ) )
                else :
                    l.append( (path.get_bb().start + path.get_idx(), "P%s{%s}" % (PACKAGE_ACCESS[ path.get_access_flag() ], m) ) )

        return l

    def get_method(self, analysis_method, signature_type, signature_arguments={}) :
        key = "%s-%s-%s" % (analysis_method, signature_type, signature_arguments)
        if key in self._cached_signatures :
            return self._cached_signatures[ key ]

        s = Sign()

        #print signature_type, signature_arguments
        for i in signature_type.split(":") :
        #    print i, signature_arguments[ i ]
            if i == "L0" : 
                _type = self.levels[ i ][ signature_arguments[ i ][ "type" ] ]
                try : 
                    _arguments = signature_arguments[ i ][ "arguments" ] 
                except KeyError :
                    _arguments = []

                value = self._get_bb( analysis_method, _type, _arguments ) 
                s.add( i, ''.join(i[1] for i in value))
            
            elif i == "L1" :
                for f in self.levels[ i ] : 
                   value = getattr( self, f )( analysis_method )
                s.add( i, value )

            else :
                for f in self.levels[ i ] : 
                    value = getattr( self, f )( analysis_method )
                s.add( i, value )

        self._cached_signatures[ key ] = s
        return s
