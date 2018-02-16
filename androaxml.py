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

from __future__ import print_function
import sys
from lxml import etree
from optparse import OptionParser

from androguard.core import androconf
from androguard.core.bytecodes import apk
from androguard.util import read

option_0 = {
    'name': ('-i', '--input'),
    'help': 'filename input (APK or android\'s binary xml)',
    'nargs': 1
}
option_1 = {
    'name': ('-o', '--output'),
    'help': 'filename output of the xml',
    'nargs': 1
}
option_2 = {
    'name': ('-v', '--version'),
    'help': 'version of the API',
    'action': 'count'
}
options = [option_0, option_1, option_2]


def main(options, arguments):
    if options.input is not None:
        ret_type = androconf.is_android(options.input)
        if ret_type == "APK":
            a = apk.APK(options.input)
            axml = a.get_android_manifest_xml()
        elif ".xml" in options.input:
            axml = apk.AXMLPrinter(read(options.input)).get_xml_obj()
        else:
            print("Unknown file type")
            return

        buff = etree.tostring(axml, pretty_print=True)
        if options.output:
            with open(options.output, "wb") as fd:
                fd.write(buff)
        else:
            print(buff.decode("UTF-8"))

    elif options.version is not None:
        print("Androaxml version %s" % androconf.ANDROGUARD_VERSION)


if __name__ == "__main__":
    parser = OptionParser()
    for option in options:
        param = option['name']
        del option['name']
        parser.add_option(*param, **option)

    options, arguments = parser.parse_args()
    sys.argv[:] = arguments
    main(options, arguments)
