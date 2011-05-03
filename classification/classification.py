#!/usr/bin/env python

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

import sys, hashlib

import numpy

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, LargeBinary, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import declarative_base

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis, misc
import ncd, androdb

class Classification :
    def __init__(self, dbname) :
        self._adb = androdb.AndroDB( dbname )

        self._ncd = ncd.NCD( "./classification/libncd/libncd.so" )
        self._ncd.set_compress_type( ncd.BZ2_COMPRESS )

    def classification1(self) :
        print self._adb._session.query(androdb.Signature).count()

        signatures = []
        for row in self._adb._session.query(androdb.Signature).all():
            #print "Signature -->", row.id, row.method_id, row.grammar, row.value
            signatures.append( row.value )

        print "BEGIN NCD", len(signatures) * len(signatures)

        widgets = ['Classification NCD ...: ', misc.Percentage(), ' ', misc.Bar(marker=misc.RotatingMarker())]
        pbar = misc.ProgressBar(widgets=widgets, maxval=len(signatures) * len(signatures)).start()

        l = []
        n = 0
        idx = 0
        for x in signatures :
            pbar.update( n )
            for y in signatures :
                l.append( self._ncd.get( x, y ) )

            n = len(signatures) * idx
            idx += 1

        pbar.finish()
        print "END NCD"
        a = numpy.array( l )
        b = numpy.reshape( a, ( len(signatures), len(signatures) ) )
        print b


if __name__ == "__main__" :
    try :
        import psyco
        psyco.full()
    except ImportError :
        pass

    c = Classification( androdb.DBNAME )
    c.classification1()
