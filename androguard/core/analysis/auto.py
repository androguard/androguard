from builtins import range
from builtins import object
import os
import queue
import threading
import time
import zlib
import multiprocessing


from androguard.core import androconf
from androguard.core.bytecodes import apk, dvm, axml
from androguard.core.analysis import analysis
from androguard.util import read

import logging

l = logging.getLogger("androguard.auto")

class AndroAuto(object):
    """
    The main class which analyse automatically android apps by calling methods
    from a specific object

    Automatic analysis is highly integrated into `androconf` and requires two
    objects to be created:

    1) a Logger, found at key `log` in the settings
    2) a Analysis Runner, found at key `my` in the settings

    example::

        from androguard.core.analysis import auto


        class AndroLog(object):
            # This is the Logger
            def __init__(self, id_file, filename):
                self.id_file = id_file
                self.filename = filename


        class AndroTest(auto.DirectoryAndroAnalysis):
            # This is the Test Runner
            def analysis_app(self, log, apkobj, dexobj, analysisobj):
                print(log.id_file, log.filename, apkobj, dexobj, analysisobj)


        settings = {
            # The directory should contain some APK files
            "my": AndroTest('some/directory'),
            "log": AndroLog,
            "max_fetcher": 3,
        }

        aa = auto.AndroAuto(settings)
        aa.go()

    :param settings: the settings of the analysis
    :type settings: dict
    """

    def __init__(self, settings):
        if not "my" in settings:
            raise ValueError("'my' object not found in settings!")

        if not "log" in settings:
            raise ValueError("'log' object not found in settings!")

        if not "max_fetcher" in settings:
            settings["max_fetcher"] = multiprocessing.cpu_count()
            l.warning("No maximum number of threads found, setting MAX_CPU: {}".format(settings["max_fetcher"]))

        self.settings = settings

    def dump(self):
        """
        Dump the analysis
        """
        self.settings["my"].dump()

    def dump_file(self, filename):
        """
        Dump the analysis in a filename
        """
        self.settings["my"].dump_file(filename)

    def go(self):
        """
        Launch the analysis
        """
        myandro = self.settings["my"]

        def worker(idx, q):
            """
            Worker Thread
            """
            l.debug("Running worker-%d" % idx)

            while True:
                a, d, dx, axmlobj, arscobj = None, None, None, None, None
                try:
                    filename, fileraw = q.get()
                    id_file = zlib.adler32(fileraw)

                    l.debug("(worker-%d) get %s %d" % (idx, filename, id_file))

                    logf = self.settings["log"](id_file, filename)

                    is_analysis_dex, is_analysis_adex = True, True
                    l.debug("(worker-%d) filtering file %d" % (idx, id_file))
                    filter_file_ret, filter_file_type = myandro.filter_file(logf, fileraw)

                    if filter_file_ret:
                        l.debug("(worker-%d) analysis %s" % (id_file, filter_file_type))

                        if filter_file_type == "APK":
                            a = myandro.create_apk(logf, fileraw)
                            is_analysis_dex = myandro.analysis_apk(logf, a)
                            fileraw = a.get_dex()
                            filter_file_type = androconf.is_android_raw(fileraw)

                        elif filter_file_type == "AXML":
                            axmlobj = myandro.create_axml(logf, fileraw)
                            myandro.analysis_axml(logf, axmlobj)

                        elif filter_file_type == "ARSC":
                            arscobj = myandro.create_arsc(logf, fileraw)
                            myandro.analysis_arsc(logf, arscobj)

                        if is_analysis_dex and filter_file_type == "DEX":
                            d = myandro.create_dex(logf, fileraw)
                            is_analysis_adex = myandro.analysis_dex(logf, d)

                        elif is_analysis_dex and filter_file_type == "DEY":
                            d = myandro.create_dey(logf, fileraw)
                            is_analysis_adex = myandro.analysis_dey(logf, d)

                        if is_analysis_adex and d:
                            dx = myandro.create_adex(logf, d)
                            myandro.analysis_adex(logf, dx)

                        myandro.analysis_app(logf, a, d, dx)

                    myandro.finish(logf)
                except Exception as why:
                    myandro.crash(logf, why)
                    myandro.finish(logf)

                del a, d, dx, axmlobj, arscobj
                q.task_done()

        q = queue.Queue(self.settings["max_fetcher"])

        for i in range(self.settings["max_fetcher"]):
            t = threading.Thread(target=worker, args=[i, q])
            t.daemon = True
            t.start()

        # FIXME: Busy waiting with sleep...
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
    """
    This class can be used as a template in order to analyse apps
    """

    def fetcher(self, q):
        """
        This method is called to fetch a new app in order to analyse it. The queue
        must be fill with the following format: (filename, raw)

        must return False if the queue is filled.

        :param q: the Queue to put new app
        """
        return False

    def filter_file(self, log, fileraw):
        """
        This method is called in order to filer a specific app

        :param log: an object which corresponds to a unique app
        :param fileraw: the raw app (a string)
        :rtype: a set with 2 elements, the return value (boolean) if it is necessary to
                continue the analysis and the file type
        """
        file_type = androconf.is_android_raw(fileraw)
        if file_type == "APK" or file_type == "DEX" or file_type == "DEY" or file_type == "AXML" or file_type == "ARSC":
            return True, file_type
        return False, None

    def create_axml(self, log, fileraw):
        """
        This method is called in order to create a new AXML object

        :param log: an object which corresponds to a unique app
        :param fileraw: the raw axml (a string)
        :rtype: an :class:`AXMLPrinter` object
        """
        return axml.AXMLPrinter(fileraw)

    def create_arsc(self, log, fileraw):
        """
        This method is called in order to create a new ARSC object

        :param log: an object which corresponds to a unique app
        :param fileraw: the raw arsc (a string)

        :rtype: an :class:`ARSCParser` object
        """
        return axml.ARSCParser(fileraw)

    def create_apk(self, log, fileraw):
        """
        This method is called in order to create a new APK object

        :param log: an object which corresponds to a unique app
        :param fileraw: the raw apk (a string)

        :rtype: an :class:`APK` object
        """
        return apk.APK(fileraw, raw=True)

    def create_dex(self, log, dexraw):
        """
        This method is called in order to create a DalvikVMFormat object

        :param log: an object which corresponds to a unique app
        :param dexraw: the raw classes.dex (a string)

        :rtype: a :class:`DalvikVMFormat` object
        """
        return dvm.DalvikVMFormat(dexraw)

    def create_dey(self, log, dexraw):
        """
        This method is called in order to create a DalvikOdexVMFormat object

        :param log: an object which corresponds to a unique app
        :param dexraw: the raw odex file (a string)

        :rtype: a :class:`DalvikOdexVMFormat` object
        """
        return dvm.DalvikOdexVMFormat(dexraw)

    def create_adex(self, log, dexobj):
        """
        This method is called in order to create a VMAnalysis object

        :param log: an object which corresponds to a unique app
        :param dexobj: a :class:`DalvikVMFormat` object

        :rytpe: a :class:`Analysis` object
        """
        vm_analysis = analysis.Analysis(dexobj)
        vm_analysis.create_xref()
        return vm_analysis

    def analysis_axml(self, log, axmlobj):
        """
        This method is called in order to know if the analysis must continue

        :param log: an object which corresponds to a unique app
        :param axmlobj: a :class:`AXMLPrinter` object

        :rtype: a boolean
        """
        return True

    def analysis_arsc(self, log, arscobj):
        """
        This method is called in order to know if the analysis must continue

        :param log: an object which corresponds to a unique app
        :param arscobj: a :class:`ARSCParser` object

        :rtype: a boolean
        """
        return True

    def analysis_apk(self, log, apkobj):
        """
        This method is called in order to know if the analysis must continue

        :param log: an object which corresponds to a unique app
        :param apkobj: a :class:`APK` object

        :rtype: a boolean
        """
        return True

    def analysis_dex(self, log, dexobj):
        """
        This method is called in order to know if the analysis must continue

        :param log: an object which corresponds to a unique app
        :param dexobj: a :class:`DalvikVMFormat` object

        :rtype: a boolean
        """
        return True

    def analysis_dey(self, log, deyobj):
        """
        This method is called in order to know if the analysis must continue

        :param log: an object which corresponds to a unique app
        :param deyobj: a :class:`DalvikOdexVMFormat` object

        :rtype: a boolean
        """
        return True

    def analysis_adex(self, log, adexobj):
        """
        This method is called in order to know if the analysis must continue

        :param log: an object which corresponds to a unique app
        :param adexobj: a :class:`VMAnalysis` object

        :rtype: a boolean
        """
        return True

    def analysis_app(self, log, apkobj, dexobj, adexobj):
        """
        This method is called if you wish to analyse the final app

        :param log: an object which corresponds to a unique app
        :param apkobj: a :class:`APK` object
        :param dexobj: a :class:`DalvikVMFormat` object
        :param adexobj: a :class:`VMAnalysis` object
        """
        pass

    def finish(self, log):
        """
        This method is called before the end of the analysis

        :param log: an object which corresponds to a unique app
        """
        pass

    def crash(self, log, why):
        """
        This method is called if a crash appends

        :param log: an object which corresponds to a unique app
        :param why: the string exception
        """
        pass

    def dump(self):
        """
        This method is called to dump the result
        """
        pass

    def dump_file(self, filename):
        """
        This method is called to dump the result in a file

        :param filename: the filename to dump the result
        """
        pass


class DirectoryAndroAnalysis(DefaultAndroAnalysis):
    """
    A simple class example to analyse a whole directory with many APKs in it
    """

    def __init__(self, directory):
        self.directory = directory

    def fetcher(self, q):
        for root, _, files in os.walk(self.directory, followlinks=True):
            for f in files:
                real_filename = os.path.join(root, f)
                q.put((real_filename, read(real_filename)))
        return False

