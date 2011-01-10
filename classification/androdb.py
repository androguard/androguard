#!/usr/bin/env python

import hashlib

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker, backref, relationship 
from sqlalchemy.ext.declarative import declarative_base

DBNAME = "sqlite:///class.db"

APKSRAW_TABLE_NAME = "apks_raw"
APKS_TABLE_NAME = "apks"

Base = declarative_base()
class APKRaw(Base) :
   __tablename__ = APKSRAW_TABLE_NAME
   id = Column(Integer, primary_key=True)
   raw = Column(String)
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

   def __init__(self, apkraw_id) :
      self.apkraw_id = apkraw_id

   def __repr__(self) :
      return "<APK('')>"

class AndroDB :
   def __init__(self, name) :
      self._engine = create_engine(name, echo=True)
      self.__Session = sessionmaker(bind=self._engine)
      self._session = self.__Session()

      metadata = Base.metadata
      metadata.create_all(self._engine)

   def add(self, raw) :
      a_raw = APKRaw( raw )
      self._session.add( a_raw )
      # commit to have the id of the apk raw
      self._session.commit()
      
      a = APK( a_raw.id )
      self._session.add( a )
     
      # commit the new analysis of apk
      self._session.commit()

   def show(self) :
      for row in self._session.query(APKRaw, APKRaw.id, APKRaw.hash).all():
         print "APKRAW -->", row.id, row.hash

      for row in self._session.query(APK, APK.id, APK.apkraw_id).all():
         print "APK -->", row.id, row.apkraw_id

adb = AndroDB( DBNAME )
adb.add( open("../examples/android/Test/bin/Test-debug.apk", "r").read() )

adb.show()
