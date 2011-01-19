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

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, LargeBinary, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker, backref, relationship 
from sqlalchemy.ext.declarative import declarative_base

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis

DBNAME = "sqlite:///class.db"

APKSRAW_TABLE_NAME = "apksraw"
APKS_TABLE_NAME = "apks"

SIGNATURES_TABLE_NAME = "signatures"
METHODS_TABLE_NAME = "methods"

Base = declarative_base()

class Method(Base) :
   __tablename__ = METHODS_TABLE_NAME
   id = Column(Integer, primary_key=True)
   name = Column(String)
   class_name = Column(String)
   descriptor = Column(String)
  
   apk_id = Column(Integer, ForeignKey(APKS_TABLE_NAME + ".id"))
   signatures = relationship("Signature", order_by="Signature.id", backref=METHODS_TABLE_NAME)

   def __init__(self, method, vm_analysis) :
      self.name = method.get_name()
      self.class_name = method.get_class_name()
      self.descriptor = method.get_descriptor()

#      self.signatures.append( Signature( analysis.GRAMMAR_TYPE_PSEUDO_ANONYMOUS, vm_analysis.get_method_signature(method, analysis.GRAMMAR_TYPE_PSEUDO_ANONYMOUS) ) )
      self.signatures.append( Signature( analysis.GRAMMAR_TYPE_ANONYMOUS, vm_analysis.get_method_signature(method, analysis.GRAMMAR_TYPE_ANONYMOUS) ) )

   def __repr__(self) :
      return "<Method('%s, %s, %s')>" % (self.class_name, self.name, self.descriptor)

class Signature(Base) :
   __tablename__ = SIGNATURES_TABLE_NAME
   id = Column(Integer, primary_key=True)
   grammar = Column(Integer)
   value = Column(String)

   method_id = Column(Integer, ForeignKey(METHODS_TABLE_NAME + ".id"))

   def __init__(self, grammar, value) :
      self.grammar = grammar
      self.value = value

   def __repr__(self) :
      return "<Signature('%d, %s')>" % (self.grammar, self.value)

class APKRaw(Base) :
   __tablename__ = APKSRAW_TABLE_NAME
   id = Column(Integer, primary_key=True)
   raw = Column(LargeBinary)
   hash = Column(String(512))

   def __init__(self, raw) :
      self.raw = raw
      self.hash = hashlib.sha512( raw ).hexdigest()

   def __repr__(self) :
      return "<APKRaw('%s')>" % self.hash

class APK(Base) :
   __tablename__ = APKS_TABLE_NAME
   id = Column(Integer, primary_key=True)
   
   apkraw_id = Column(Integer, ForeignKey(APKSRAW_TABLE_NAME + ".id"))
   apkraw = relationship("APKRaw", backref=backref(APKS_TABLE_NAME, uselist=False))

   methods = relationship("Method", order_by="Method.id", backref=APKS_TABLE_NAME)
   
   def __init__(self, _andro, _analysis, apkraw_id) :
      self.apkraw_id = apkraw_id
      
      for method in _andro.get_methods() :
         if method.get_code() != None and method.get_code().get_length() > 15 :
            m = Method( method, _analysis )
            self.methods.append( m )

   def __repr__(self) :
      return "<APK('')>"

class AndroDB :
   def __init__(self, name) :
      self._engine = create_engine(name)#, echo=True)
      self.__Session = sessionmaker(bind=self._engine)
      self._session = self.__Session()

      metadata = Base.metadata
      metadata.create_all(self._engine)

   def add(self, filename) :
      _a = androguard.AndroguardS( filename )
      _x = analysis.VM_BCA( _a.get_vm() )

      raw = _a.get_orig_raw() 
      if self._session.query(APKRaw).filter_by(hash=hashlib.sha512( raw ).hexdigest()).count() > 0 :
         return 

      a_raw = APKRaw( raw )
      self._session.add( a_raw )
      # commit to have the id of the apk raw
      self._session.commit()
      
      a = APK( _a, _x, a_raw.id )
      self._session.add( a )
     
      # commit the new analysis of apk
      self._session.commit()


   def show(self) :
      for row in self._session.query(APKRaw).all():
         print "APKRAW -->", row.id, row.hash

      for row in self._session.query(APK).all():
         print "APK -->", row.id, row.apkraw_id, len(row.methods)

#      for row in self._session.query(Method).all():
#         print "Method -->", row, row.id, row.apk_id, row.signatures

#      for row in self._session.query(Signature).all():
#         print "Signature -->", row.id, row.method_id, row.grammar, row.value

if __name__ == "__main__" :
   try :
      import psyco
      psyco.full()
   except ImportError :
      pass

   adb = AndroDB( DBNAME )
   #adb.add( "./examples/android/Test/bin/Test-debug.apk" )
   #adb.add( "./examples/android/Demo1/bin/Demo1-debug.apk" )
   adb.add("./apks/superuser.apk")

   adb.show()
