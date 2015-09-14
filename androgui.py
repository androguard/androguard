#!/usr/bin/env python2
'''Androguard Gui'''

import argparse
import sys

from androguard.core import androconf
from androguard.session import Session
from androguard.gui.mainwindow import MainWindow
from androguard.misc import init_print_colors

from PySide import QtCore, QtGui
from threading import Thread


class IpythonConsole(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        from IPython.terminal.embed import InteractiveShellEmbed
        from traitlets.config import Config

        cfg = Config()
        ipshell = InteractiveShellEmbed(
            config=cfg,
            banner1="Androguard version %s" % androconf.ANDROGUARD_VERSION)
        init_print_colors()
        ipshell()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Androguard GUI")
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument("-i", "--input_file", default=None)
    parser.add_argument("-c", "--console", action="store_true", default=False)

    args = parser.parse_args()

    if args.debug:
        androconf.set_debug()

    # We need that to save huge sessions when leaving and avoid
    # RuntimeError: maximum recursion depth exceeded while pickling an object
    # or
    # RuntimeError: maximum recursion depth exceeded in cmp
    # http://stackoverflow.com/questions/2134706/hitting-maximum-recursion-depth-using-pythons-pickle-cpickle
    sys.setrecursionlimit(50000)

    session = Session(export_ipython=args.console)
    console = None
    if args.console:
        console = IpythonConsole()
        console.start()

    app = QtGui.QApplication(sys.argv)
    window = MainWindow(session=session, input_file=args.input_file)
    window.resize(1024, 768)
    window.show()

    sys.exit(app.exec_())
