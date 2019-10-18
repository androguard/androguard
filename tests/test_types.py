#!/usr/bin/env python3

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
import unittest
from struct import pack, unpack, calcsize

from androguard.session import Session

TEST_CASE = 'examples/android/TestsAndroguard/bin/classes.dex'

VALUES = {
    'Ltests/androguard/TestActivity; testDouble ()V': [
        ('<d', -5),
        ('<d', -4),
        ('<d', -3),
        ('<d', -2),
        ('<d', -1),
        ('<d', 0),
        ('<d', 1),
        ('<d', 2),
        ('<d', 3),
        ('<d', 4),
        ('<d', 5),

        ('<l', -5),
        ('<l', -4),
        ('<l', -3),
        ('<l', -2),
        ('<l', -1),
        ('<l', 0),
        ('<l', 1),
        ('<l', 2),
        ('<l', 3),
        ('<l', 4),
        ('<l', 5),

        ('<f', -5),
        ('<f', -4),
        ('<f', -3),
        ('<f', -2),
        ('<f', -1),
        ('<f', 0),
        ('<f', 1),
        ('<f', 2),
        ('<f', 3),
        ('<f', 4),
        ('<f', 5),

        ('<d', 65534),
        ('<d', 65535),
        ('<d', 65536),
        ('<d', 65537),

        ('<d', 32769),
        ('<d', 32768),
        ('<d', 32767),
        ('<d', 32766),

        ('<l', 65534),
        ('<l', 65535),
        ('<l', 65536),
        ('<l', 65537),

        ('<l', 32769),
        ('<l', 32768),
        ('<l', 32767),
        ('<l', 32766),

        ('<f', 65534),
        ('<f', 65535),
        ('<f', 65536),
        ('<f', 65537),

        ('<f', 32769),
        ('<f', 32768),
        ('<f', 32767),
        ('<f', 32766),

        ('<d', 5346952),
        ('<l', 5346952),
        ('<f', 5346952),

        ('<d', 65534.50),
        ('<d', 65535.50),
        ('<d', 65536.50),
        ('<d', 65537.50),

        ('<d', 32769.50),
        ('<d', 32768.50),
        ('<d', 32767.50),
        ('<d', 32766.50),

        ('<f', 65534.50),
        ('<f', 65535.50),
        ('<f', 65536.50),
        ('<f', 65537.50),

        ('<f', 32769.50),
        ('<f', 32768.50),
        ('<f', 32767.50),
        ('<f', 32766.50),

        ('<f', -5),
        ('<f', -65535),
        ('<f', -65536),
        # ('<f', -123456789123456789.555555555), --> this value will be -123456790519087104 as float!
        ('<f', -123456790519087104),
        ('<d', -123456789123456789.555555555),
        # int boom
        ('<i', -606384730),
        # float reboom
        ('<f', -123456790519087104),
        # not in the java file, but appears due to the calculation: boom again
        # but the two is added already -> some compiler optimization
        ('<i', -606384730 + 2),
        # the 3.5 from the calculation
        ('<f', 3.5),
    ],
}


def format_value(literal, ins, to):
    # Need to convert the instruction (which is always signed)
    # to the requested format.
    formats = dict(i='i', h='i', l='q', s='h')
    char = ins.__class__.__name__[-1]
    if char not in formats:
        raise ValueError("wrong type of instruction")

    # Special treatment for const/high16 and const-wide/high16
    if char == 'h' and 'wide' in ins.get_name():
        formats['h'] = 'q'

    # Need to calculate for extra padding bytes
    # if the number is negative, trailing \xff are added (sign extension)
    print(calcsize(to), calcsize(formats[char]))
    packed = pack('<{}'.format(formats[char]), literal)
    padding = bytearray()
    trailing = bytearray()
    print(packed)
    if to == '<l' and packed[-1] & 0x80 == 0x80:
        # Sign extension
        trailing = bytearray([0xff] * (calcsize(to) - calcsize(formats[char])))
    elif to == '<l' and packed[-1] & 0x80 == 0x00:
        # no sign extension, but requires zero trailing
        trailing = bytearray([0] * (calcsize(to) - calcsize(formats[char])))
    else:
        padding = bytearray([0] * (calcsize(to) - calcsize(formats[char])))

    print(ins.__class__.__name__, char, formats[char], to, padding, trailing, literal)
    return unpack(to, padding + packed + trailing)[0]


class TypesTest(unittest.TestCase):

    def testTypes(self):
        s = Session()
        with open(TEST_CASE, "rb") as fd:
            digest, d, dx = s.addDEX(TEST_CASE, fd.read())

        for method in filter(lambda x: x.full_name in VALUES, d.get_methods()):
            print("METHOD", method.full_name)

            for i in filter(lambda x: 'const' in x.get_name(), method.get_instructions()):
                i.show(0)
                # ins should only have one literal
                self.assertEquals(len(i.get_literals()), 1)

                fmt, value = VALUES[method.full_name].pop(0)
                converted = format_value(i.get_literals()[0], i, fmt)
                print(i.get_literals(), fmt, value, converted)
                self.assertEqual(converted, value)
                print()


if __name__ == '__main__':
    unittest.main()
