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

import sys, hashlib, os

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, DateTime, LargeBinary, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker, backref, relationship 
from sqlalchemy.ext.declarative import declarative_base

import datetime

from optparse import OptionParser
from xml.dom import minidom

PATH_INSTALL = "./"
sys.path.append(PATH_INSTALL + "./")

import androguard, analysis, dvm


option_0 = { 'name' : ('-c', '--config'), 'help' : 'config filename', 'nargs' : 1 }
option_1 = { 'name' : ('-i', '--input'), 'help' : 'input filename (APK, dex)', 'nargs' : 1 }
option_2 = { 'name' : ('-s', '--set'), 'help' : 'set attribute of a specific raw (id)', 'nargs' : 1 }
option_3 = { 'name' : ('-a', '--attribute'), 'help' : 'set attribute to a new value (name_attribute:value)', 'nargs' : 1 }
option_4 = { 'name' : ('-v', '--version'), 'help' : 'version of the API', 'action' : 'count' }
options = [option_0, option_1, option_2, option_3, option_4]

RAW_TABLE_NAME = "raw"
APPS_RAW_TABLE_NAME = "appsraw"
APKS_TABLE_NAME = "apks"

SIGNATURES_TABLE_NAME = "signatures"
METHODS_TABLE_NAME = "methods"

Base = declarative_base()

class Method :
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

class Signature :
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

APK_RAW = 0
DEX_RAW = 1

MALWARE_APPLICATION = 0
GOODWARE_APPLICATION = 1
EXPLOIT_APPLICATION = 2
class Raw(Base) :
   __tablename__ = RAW_TABLE_NAME
   id = Column(Integer, primary_key=True)
   raw = Column(LargeBinary)

   def __init__(self, raw) :
      self.raw = raw

class AppsRaw(Base) :
   __tablename__ = APPS_RAW_TABLE_NAME
   id = Column(Integer, primary_key=True)
   original_name = Column(String(512))
   raw_id = Column(Integer, ForeignKey(RAW_TABLE_NAME + ".id"))
   raw = relationship("Raw", backref=backref(APPS_RAW_TABLE_NAME, uselist=False))
   date = Column( DateTime )

   raw_type = Column(Integer)
   hashraw = Column(String(512))
   hashdex = Column(String(512))
   information = Column(Integer)

   def __init__(self, original_name, raw_id, raw_type, hash_raw, hash_dex=None) :
      self.original_name = original_name
      self.raw_id = raw_id
      self.raw_type = raw_type
      self.date = datetime.datetime.utcnow()

      self.hashraw = hash_raw
      self.information = GOODWARE_APPLICATION

      if raw_type == DEX_RAW :
         self.hashdex = self.hashraw
      else :
         self.hashdex = hash_dex

   def __repr__(self) :
      return "<Raw('%d-%s-%d-%s-%d')>" % (self.id, self.original_name, self.raw_type, self.hashraw, self.information)

class APK :
   __tablename__ = APKS_TABLE_NAME
   id = Column(Integer, primary_key=True)
   
   apkraw_id = Column(Integer, ForeignKey(RAW_TABLE_NAME + ".id"))
   apkraw = relationship("Raw", backref=backref(APKS_TABLE_NAME, uselist=False))

   methods = relationship("Method", order_by="Method.id", backref=APKS_TABLE_NAME)
   
   def __init__(self, _andro, _analysis, apkraw_id) :
      self.apkraw_id = apkraw_id
      
      for method in _andro.get_methods() :
         if method.get_code() != None and method.get_code().get_length() > 15 :
            m = Method( method, _analysis )
            self.methods.append( m )

   def __repr__(self) :
      return "<APK('')>"

def configtodb(filename) :
   document = minidom.parse(filename)

   db_type = document.getElementsByTagName( "db_type" )[0].firstChild.data
   username = document.getElementsByTagName( "username" )[0].firstChild.data
   password = document.getElementsByTagName( "password" )[0].firstChild.data
   host = document.getElementsByTagName( "host" )[0].firstChild.data
   port = document.getElementsByTagName( "port" )[0].firstChild.data
   dbname = document.getElementsByTagName( "dbname" )[0].firstChild.data

   return "%s://%s:%s@%s:%s/%s" % (db_type, username, password, host, port, dbname)

class AndroDB :
   def __init__(self, name) :
      self._engine = create_engine(name) #, echo=True)
      self.__Session = sessionmaker(bind=self._engine)
      self._session = self.__Session()

      metadata = Base.metadata
      metadata.create_all(self._engine)

   def add_apk_raw(self, filename) :
      print "Processing ....", filename

      a = dvm.APK( filename )
      raw = a.get_raw()
      dex = a.get_dex()

      if len(raw) == 0 or len(dex) == 0 :
         print "Empty raw"
         return -1

      original_name = os.path.basename( filename )

      if self._session.query(AppsRaw).filter_by(hashraw=hashlib.sha512( raw ).hexdigest()).count() > 0 :
         print "HASH RAW is already present"
         return -1

      #if self._session.query(AppsRaw).filter_by(hashdex=hashlib.sha512( dex ).hexdigest()).count() > 0 :
      #   print "HASH DEX is already present"
      #   return -1


      print "ADD it !"

      r = Raw( raw )
      self._session.add( r )
      self._session.commit()

      a_raw = AppsRaw( original_name, r.id, APK_RAW, hashlib.sha512( raw ).hexdigest(), hashlib.sha512( dex ).hexdigest() )
      self._session.add( a_raw )
      self._session.commit()

      return 0
      
   def get_apps_raw(self, id) :
      return self._session.query(AppsRaw).filter_by(id=id).first()

   def set_apps_raw(self, id, attributes) :
      a_raw = self._session.query(AppsRaw).filter_by(id=id).first()
      
      for i in attributes :
         setattr(a_raw, i, attributes[i])
   
      self._session.commit()

   def add(self, filename) :
      _a = androguard.AndroguardS( filename )
      _x = analysis.VM_BCA( _a.get_vm() )

      raw = _a.get_orig_raw() 
      if self._session.query(Raw).filter_by(hash=hashlib.sha512( raw ).hexdigest()).count() > 0 :
         return 

      a_raw = Raw( raw )
      self._session.add( a_raw )
      # commit to have the id of the apk raw
      self._session.commit()
      
      #a = APK( _a, _x, a_raw.id )
      #self._session.add( a )
     
      # commit the new analysis of apk
      #self._session.commit()


   def show(self) :
      for row in self._session.query(AppsRaw).all():
         print "APPSRAW -->", row.id, row.original_name, row.raw_id, row.hashraw, row.hashdex, row.raw_type, row.information

      #for row in self._session.query(APK).all():
      #   print "APK -->", row.id, row.apkraw_id, len(row.methods)

#      for row in self._session.query(Method).all():
#         print "Method -->", row, row.id, row.apk_id, row.signatures

#      for row in self._session.query(Signature).all():
#         print "Signature -->", row.id, row.method_id, row.grammar, row.value

