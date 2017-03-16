#!/usr/bin/env python
'''Androguard Gui'''

import argparse
import sys

from androguard.core import androconf
from androguard.gui.mainwindow import MainWindow

from PyQt5 import QtWidgets, QtGui


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Androguard GUI")
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument("-i", "--input_file", default=None)
    parser.add_argument("-p", "--input_plugin", default=None)

    args = parser.parse_args()

    if args.debug:
        androconf.set_debug()

    # We need that to save huge sessions when leaving and avoid
    # RuntimeError: maximum recursion depth exceeded while pickling an object
    # or
    # RuntimeError: maximum recursion depth exceeded in cmp
    # http://stackoverflow.com/questions/2134706/hitting-maximum-recursion-depth-using-pythons-pickle-cpickle
    sys.setrecursionlimit(50000)

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("./androguard/gui/androguard.ico"))

    window = MainWindow(input_file=args.input_file,
                        input_plugin=args.input_plugin)
    window.resize(1024, 768)
    window.show()

    sys.exit(app.exec_())
