#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
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

import sys

from optparse import OptionParser

import androguard, androconf, diff

option_0 = { 'name' : ('-i', '--input'), 'help' : 'file : use these filenames', 'nargs' : 2 }
option_1 = { 'name' : ('-d', '--display'), 'help' : 'display the file in human readable format', 'action' : 'count' }
option_2 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }

options = [option_0, option_1, option_2]

def main(options, arguments) :
    if options.input != None :
        a = androguard.Androguard( options.input )
        a.ianalyze()

        vm1 = a.get_bc()[0][1].get_vm()
        vmx1 = a.get_bc()[0][1].get_analysis()

        vm2 = a.get_bc()[1][1].get_vm()
        vmx2 = a.get_bc()[1][1].get_analysis()

        dsim = diff.Sim( [ vm1, vmx1 ], [ vm2, vmx2 ] )

        print "DIFF METHODS :", len(dsim.get_diff_methods())
        print "NEW METHODS :", len(dsim.get_new_methods())
        print "MATCH METHODS :", len(dsim.get_match_methods())
        print "DELETE METHODS :", len(dsim.get_delete_methods())

        print dsim.get_final_score()

        if options.display :
            print "DIFF METHODS :"
            diff_methods = dsim.get_diff_methods()
            diff_methods.sort(key=lambda v: (v.get_length() + ((1 - v.sort_h[0][1]) * v.get_length())))
            diff_methods.reverse()
            for i in diff_methods :
                i.show2()

            print "MATCH METHODS :"
            match_methods = dsim.get_match_methods()
            match_methods.sort(key=lambda v: (v.get_length()))
            match_methods.reverse()
            for i in match_methods :
                i.show2()

            print "NEW METHODS :"
            new_methods = dsim.get_new_methods()
            new_methods.sort(key=lambda v: (v.get_length()))
            new_methods.reverse()
            for i in new_methods :
                i.show2()

            print "DELETE METHODS :"
            del_methods = dsim.get_delete_methods()
            del_methods.sort(key=lambda v: (v.get_length()))
            del_methods.reverse()
            for i in del_methods :
                i.show2()

    elif options.version != None :
        print "Androsimforsign version %s" % androconf.ANDROGUARD_VERSION

if __name__ == "__main__" :
    parser = OptionParser()
    for option in options :
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
