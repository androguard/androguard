import idaapi
from idc import *

PATH_INSTALL = "/home/pouik/androguard"

sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/predicates")
sys.path.append(PATH_INSTALL + "/core/analysis")
sys.path.append(PATH_INSTALL + "/core/vm")
sys.path.append(PATH_INSTALL + "/core/wm")

import bytecode, dvm

DVM_FORMAT_NAME = "Dalvik dex file"

def accept_file(li, n):
   # we support only one format per file
   if n > 0:
      return 0

   li.seek(0)
   if li.read(8) == dvm.DEX_FILE_MAGIC :
      return DVM_FORMAT_NAME

   return 0

def load_file(li, neflags, format) :
   print "Loading ..."
   idaapi.set_processor_type("dalvik", SETPROC_ALL|SETPROC_FATAL)

   print "Load OK"
   return 1

# -----------------------------------------------------------------------
def move_segm(frm, to, sz, fileformatname):                                                                                                                                                                                       
   Warning("move_segm(from=%s, to=%s, sz=%d, formatname=%s" % (hex(frm), hex(to), sz, fileformatname))
   return 0
