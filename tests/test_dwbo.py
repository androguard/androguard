#!/usr/bin/env python

import sys, time

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL)

from androguard.core import androconf
from androguard.core.wm.wm import DWBO, DWBOCheck

def test(obc, secret, x) :
    r = obc.verify_with_X( x )
    print "%s x:%d solutions:%d" % ( secret in r, len(x), len(r) )


SECRET = "ANDROGUARD"
J1 = [ 2, 3, 4, 5, 6 ]
J2 = [ 2, 3, 6, 20, 40, 1, 30, 15, 25, 10 ]

T = [
      [ 2, 3, 6, 20, 40, 1, 30, 15, 25, 10, 40 ],
      [ 98364, 846388, 114078, 504558, 838754, 118930, 941266, 582751, 968751, 946943 ],
      [ 169402, 307842, 140128, 204405, 815962, 639408, 748573, 131504, 844589, 32945 ],
      [ 6, 5, 4, 3, 2 ],
]

ob = DWBO( SECRET, J1 )
secret_long = androconf.str2long(ob.get_secret())
print "%s %d --> threshold:%d y:%s" % ( ob.get_secret(), secret_long, ob.get_threshold(), ob.get_y() )

obc = DWBOCheck( ob.get_y(), ob.get_threshold() )

t1 = time.clock()
for i in T :
    test(obc, secret_long, i)
t2 = time.clock()
print t2 - t1
