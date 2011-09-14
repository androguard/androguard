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
    "./apks/mixe/e5b775383f7a16d96f55701d72a8c87ca27e991d600cb4254bb47dfef556fd18" : "Crusewind",
    "./apks/mixe/7a21caba58a033a696265d2f1a9c421a84293cbba19ed890be3cc26ac584b021" : "YZHCSMS",
    "./apks/mixe/f6239ba0487ffcf4d09255dba781440d2600d3c509e66018e6a5724912df34a9" : "Zitmo",
    "./apks/mixe/77cd811c6bdb8111a98bbb6986d3f17d72c38a78bed33ac18f8938e980783d42" : "RogueSPPush",
    "./apks/mixe/ad785708e2f23c48dc8b3b088cedef5afc97759d5dc92103125a599657fca7fa" : "BaseBridge",
    "./apks/mixe/0d479abe853fcdc8bdb07023f13df79922fcea78b960391ec2a0c1722c2a4ac5" : "BaseBridge.B",
    "./apks/mixe/0d479abe853fcdc8bdb07023f13df79922fcea78b960391ec2a0c1722c2a4ac5" : "BaseBridge.B",
    "./apks/mixe/2681b0ea19336bad9a6ef2ceddd505f9dd4d0a58f967c72fea198a9bc05ec43c" : "BaseBridge.C",
    "./apks/mixe/4ae1c0faa06ee4dfb6c96b6537d027e90c870d7d3ddcfd5fcde680be9dc51c69" : "Hongtoutou",
    "./apks/mixe/b6ff9b61b61abe11a3eba507421a7b5467e7d277ac7801f24fee39bbe5cfaa36" : "SMSHider",
    "./apks/mixe/d5155a2d2f27a1cefb8f005707be1e27a7601888428500aa1665c38a1f2f56f2" : "Lovetrap",
    "./apks/mixe/9ae7270cbd1a2cd562bd10885804329e39a97b8a47cbebbde388bf364a003f05" : "Zsone",
    "./apks/mixe/a80aafb874038fe66ab1cdd17430aa74c90f0544b17de03d24c0594e5ae9465e" : "DroidDeluxe",
    "./apks/mixe/c5b38031ff0ca16d155a4bad40eb53ce99d3b89ff6ebb8958303aea35896ee68" : "GGTracker",
    "./apks/mixe/e042fb40e7159886d195637086c75e0edd486fc1d34e693b0e8dd86c5cafaea9" : "Pjapps",
    "./apks/mixe/24adad503ae6e8a1ec95a625a3a78d3b71711063bb39c11c1a07a51f652d232e" : "Pjapps.B",
    "./apks/mixe/aabe5b64af5e841e02392865dc10dcd2df499ec644839227020999b3ee9a87ec" : "Pjapps.C",
    "./apks/mixe/89b5226b0483c01cc662cb1f7958b78a65e2da1a88947e792416b2d139fcbdba" : "HippoSMS",
    "./apks/mixe/a4dc19c6c1c6d2c6befa1f56d63114a2a9b04b5c0c6a0dd9fbdc335ea5c54f3d" : "SndApps",
    "./apks/mixe/ba1aa326ca5b79e79feba9bbfe85f238b63c317d9329f1f7c28d54fe905353b9" : "Spitmo",

    # exploits


    # safe applications ?:)
    "./apks/mixe/zimperlich.apk" : None,
    "./apks/mixe/com.rovio.angrybirdsseasons-1.apk" : None,
    "./apks/mixe/com.google.android.apps.reader-1.apk" : None,
    "./apks/mixe/gtalksms-debug.apk" : None,
    "./apks/mixe/pes2011.apk" : None,
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
        sys.stdout.flush()
        a = apk.APK( i )
        if a.is_valid_APK() :
            test( s.check_apk( a )[0], TESTS[i] )
        else :
            print "INVALID APK"
    elif ret_type == "DEX" :
        try :
            print os.path.basename( i ), ":",
            sys.stdout.flush()
            test( s.check_dex( open(i, "rb").read() )[0], TESTS[i] )
        except Exception, e :
            print "ERROR", e
