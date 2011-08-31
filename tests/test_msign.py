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

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, androconf, apk, dvm, msign
import os

TESTS = {
    # malwares
    "./apks/mixe/594ebcc14a163b86222bd09adfe95498da81ceaeb772b706339d0a24858b1267" : "GoldDream",
    "./apks/mixe/c1a94e9fd0a6bda7e5ead89d8ef9ee064aeccdaf65238bf604f33e987a8656b9" : "DogoWar", 
    "./apks/mixe/d615dd181124ca0fde3d4785786586c3593a61d2c25c567ff93b230eb6d3a97a" : "DroidDream-Included",
    "./apks/mixe/137274dccff625eb1f9d647b09ed50cdfa8f86fe1a893d951f1f04e0d91f85bc" : "DroidDream",
    "./apks/mixe/d615dd181124ca0fde3d4785786586c3593a61d2c25c567ff93b230eb6d3a97a" : "DroidDreamLight",
    "./apks/mixe/c6eb43f2b7071bbfe893fc78419286c3cb7c83ce56517bd281db5e7478caf995" : "Wat",
    "./apks/mixe/7513c6a11b88b87f528b88624d1b198b5bcc325864b328e32cc0d790b0bfc1c4" : "DroidKungfu",
    "./apks/mixe/03fbe528af4e8d17aef4b8db67f96f2905a7f52e0342826aeb3ec21b16dfc283" : "DroidKungfu2",
    "./apks/mixe/76e91e1f9cc3422c333e51b65bb98dd50d00f1f45a15d2008807b06c125e651a" : "NickySpy",
    "./apks/mixe/c687e2f0b4992bd368df0c24b76943c99ac3eb9e4e8c13422ebf1a872a06070a" : "Geinimi",
    "./apks/mixe/35bda16e09b2e789602f07c08e0ba2c45393a62c6e52aa081b5b45e2e766edcb" : "GingerMaster",
    "./apks/mixe/1dd0ccbb47e46144a5e68afc619098730f561741618d89200ac9c06c460bf6e4" : "Plankton",
    "./apks/mixe/c8518d4d64a84099abfadc25eb1516957898326546b8e4bfb88066912a06dd56" : "Plankton.B",
    "./apks/mixe/7f0aaf040b475085713b09221c914a971792e1810b0666003bf38ac9a9b013e6" : "Plankton.C",

    # safe applications ?:)
    "./apks/mixe/zimperlich.apk" : None,
    "./apks/mixe/com.rovio.angrybirdsseasons-1.apk" : None,
}

DATABASE = "./signatures/dbandroguard"
DBCONFIG = "./signatures/dbconfig"

def test(got, expected):
    if got == expected:
        prefix = ' OK '
    else:
        prefix = '  X '
    print '%s got: %s expected: %s' % (prefix, repr(got), repr(expected))


s = msign.MSignature( DATABASE, DBCONFIG )
s.load()

for i in TESTS :
    ret_type = androconf.is_android( i )
    if ret_type == "APK"  :
        print os.path.basename( i ), ":",
        a = apk.APK( i )
        if a.is_valid_APK() :
            test( s.check_apk( a )[0], TESTS[i] )
        else :
            print "INVALID APK"
    elif ret_type == "DEX" :
        try :
            print os.path.basename( i ), ":",
            test( s.check_dex( open(i, "rb").read() )[0], TESTS[i] )
        except Exception, e :
            print "ERROR", e
