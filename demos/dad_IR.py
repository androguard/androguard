#!/usr/bin/env python

import sys
sys.path.append('./')

from androguard.core.bytecodes import apk, dvm
from androguard.core.analysis.analysis import uVMAnalysis
from dad.decompile import DvMethod
from dad.visitor_template import Visitor

TEST = '../DroidDream/magicspiral.apk'

vm = dvm.DalvikVMFormat(apk.APK(TEST).get_dex())
vma = uVMAnalysis(vm)

method = vm.get_method('crypt')[0]
method.show()

amethod = vma.get_method(method)
dvmethod = DvMethod(amethod)

dvmethod.process() # build IR Form / control flow...

graph = dvmethod.graph

print 'Entry block : %s\n' % graph.get_entry()

for block in graph: # graph.get_rpo() to iterate in reverse post order
    print 'Block : %s' % block
    for ins in block.get_ins():
        print '  - %s' % ins

visitor = Visitor(graph)
graph.get_entry().visit(visitor)
