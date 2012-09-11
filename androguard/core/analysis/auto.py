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

import os
import Queue
import threading
import time
import zlib

from androguard.core import androconf
from androguard.core.bytecodes import apk, dvm
from androguard.core.analysis import analysis
from androguard.core.androconf import debug


class AndroAuto(object):
  """
    The main class which analyse automatically android apps
    :param settings: the settings of the analysis
    :type settings: dict
  """
  def __init__(self, settings):
    self.settings = settings

  def dump(self):
    self.settings["my"].dump()

  def dump_file(self, filename):
    self.settings["my"].dump_file(filename)

  def go(self):
    myandro = self.settings["my"]

    def worker(idx, q):
      debug("Running worker-%d" % idx)

      while True:
        a, d, dx = None, None, None
        try:
          filename, fileraw = q.get()
          id_file = zlib.adler32(fileraw)

          debug("(worker-%d) get %s %d" % (idx, filename, id_file))

          log = self.settings["log"](id_file, filename)

          is_analysis_dex, is_analysis_adex = True, True
          debug("(worker-%d) filtering file %d" % (idx, id_file))
          filter_file_ret, filter_file_type = myandro.filter_file(log, fileraw)
          if filter_file_ret:
            debug("(worker-%d) analysis %s" % (id_file, filter_file_type))

            if filter_file_type == "APK":
              a = myandro.create_apk(log, fileraw)
              is_analysis_dex = myandro.analysis_apk(log, a)
              fileraw = a.get_dex()
              filter_file_type = "DEX"

            if is_analysis_dex and filter_file_type == "DEX":
              d = myandro.create_dex(log, fileraw)
              is_analysis_adex = myandro.analysis_dex(log, d)

            elif is_analysis_dex and filter_file_type == "DEY":
              d = myandro.create_dey(log, fileraw)
              is_analysis_adex = myandro.analysis_dey(log, d)

            if is_analysis_adex and d:
              dx = myandro.create_adex(log, d)
              myandro.analysis_adex(log, dx)

            myandro.analysis_app(log, a, d, dx)

          myandro.finish(log)
          del a, d, dx
          q.task_done()
        except Exception, why:
          myandro.crash(log, why)
          myandro.finish(log)
          q.task_done()

    q = Queue.Queue(self.settings["max_fetcher"])
    for i in range(self.settings["max_fetcher"]):
      t = threading.Thread(target=worker, args=[i, q])
      t.daemon = True
      t.start()

    terminated = True
    while terminated:
      terminated = myandro.fetcher(q)

      try:
        if terminated:
          time.sleep(10)
      except KeyboardInterrupt:
        terminated = False

    q.join()


class DefaultAndroAnalysis(object):
  def fetcher(self, q):
    pass

  def filter_file(self, log, fileraw):
    file_type = androconf.is_android_raw(fileraw)
    if file_type == "APK" or file_type == "DEX" or file_type == "DEY":
      if file_type == "APK":
        if androconf.is_valid_android_raw(fileraw):
          return (True, "APK")
      else:
        return (True, file_type)
    return (False, None)

  def create_apk(self, log, fileraw):
    return apk.APK(fileraw, raw=True, zipmodule=2)

  def create_dex(self, log, dexraw):
    return dvm.DalvikVMFormat(dexraw)

  def create_adex(self, log, dexobj):
    return analysis.uVMAnalysis(dexobj)

  def analysis_apk(self, log, apkobj):
    return True

  def analysis_dex(self, log, dexobj):
    return True

  def analysis_dey(self, log, deyobj):
    return True

  def analysis_adex(self, log, adexobj):
    return True

  def analysis_app(self, log, apkobj, dexobj, adexobj):
    pass

  def finish(self, log):
    pass

  def crash(self, log, why):
    pass

  def dump(self):
    pass

  def dump_file(self, filename):
    pass


class DirectoryAndroAnalysis(DefaultAndroAnalysis):
  def __init__(self, directory):
    self.directory = directory
    self.collect = []

  def fetcher(self, q):
    for root, dirs, files in os.walk(self.directory, followlinks=True):
      if files != []:
        for f in files:
          real_filename = root
          if real_filename[-1] != "/":
            real_filename += "/"
          real_filename += f
          q.put((real_filename, open(real_filename, "rb").read()))
    return False

  def analysis_app(self, log, apkobj, dexobj, adexobj):
    self.collect.append([apkobj, dexobj, adexobj])

  def dump(self):
    for i in self.collect:
      print i
