from error import log_loading, warning
import misc

class ProtectCode :
   def __init__(self, vms, libs_output) :
      print vms, libs_output

      for i in vms :
         print i.get_vm(), i.get_analysis()

         for inte, _ in i.get_analysis().tainted_integers.get_integers() :
            print "integer : ", repr(inte.get_info())
