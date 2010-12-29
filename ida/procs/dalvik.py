import sys
import idaapi
from idaapi import *

PATH_INSTALL = "/home/pouik/androguard/"

sys.path.append(PATH_INSTALL + "/core")
sys.path.append(PATH_INSTALL + "/core/bytecodes")
sys.path.append(PATH_INSTALL + "/core/predicates")
sys.path.append(PATH_INSTALL + "/core/analysis")
sys.path.append(PATH_INSTALL + "/core/vm")
sys.path.append(PATH_INSTALL + "/core/wm")

import bytecode, dvm

PLFM_DALVIK = 0x10000
class dalvik_processor_t(idaapi.processor_t):                                                                                                                                                                                   
   id = PLFM_DALVIK

   flag = PRN_DEC | PR_RNAMESOK | PR_NOCHANGE | PR_NO_SEGMOVE

   cnbits = 8
   dnbits = 8

   psnames = ['dalvik']
   plnames = ['Dalvik Virtual Machine code']

   tbyte_size = 0
   
   segreg_size = 0
   
   instruc_start = 0
   instruc = [
      {'name': '',  'feature': 0},
      {'name': 'reti', 'feature': CF_STOP          ,   'cmt': "Return from interrupt"},
   ]
   instruc_end = len(instruc) + 1

   assembler = {
      'flag' : AS_COLON | ASH_HEXF3 | ASO_OCTF1 | ASD_DECF0 | AS_ONEDUP | ASB_BINF3,
      'uflag' : 0,
      'name': "Dalvik bytecode assembler",

        # array of automatically generated header lines they appear at the start of disassembled text (optional)
        'header': [".dex"],

        # array of unsupported instructions (array of cmd.itype) (optional)
        #'badworks': [],

        # org directive
        'origin': ".org",

        # end directive
        'end': ".end",

        # comment string (see also cmnt2)
        'cmnt': ";",

        # ASCII string delimiter
        'ascsep': "\"",

        # ASCII char constant delimiter
        'accsep': "'",

        # ASCII special chars (they can't appear in character and ascii constants)
        'esccodes': "\"'",

        #
        #      Data representation (db,dw,...):
        #
        # ASCII string directive
        'a_ascii': ".char",

        # byte directive
        'a_byte': ".byte",

        # word directive
        'a_word': ".short",

        # remove if not allowed
        'a_dword': ".long",

        # remove if not allowed
        # 'a_qword': "dq",

        # float;  4bytes; remove if not allowed
        'a_float': ".float",

        # uninitialized data directive (should include '%s' for the size of data)
        'a_bss': ".space %s",

        # 'equ' Used if AS_UNEQU is set (optional)
        'a_equ': ".equ",

        # 'seg ' prefix (example: push seg seg001)
        'a_seg': "seg",

        # current IP (instruction pointer) symbol in assembler
        'a_curip': "$",

        # "public" name keyword. NULL-gen default, ""-do not generate
        'a_public': ".def",

        # "weak"   name keyword. NULL-gen default, ""-do not generate
        'a_weak': "",

        # "extrn"  name keyword
        'a_extrn': ".ref",

        # "comm" (communal variable)
        'a_comdef': "",

        # "align" keyword
        'a_align': ".align",

        # Left and right braces used in complex expressions
        'lbrace': "(",
        'rbrace': ")",

        # %  mod     assembler time operation
        'a_mod': "%",

        # &  bit and assembler time operation
        'a_band': "&",

        # |  bit or  assembler time operation
        'a_bor': "|",

        # ^  bit xor assembler time operation
        'a_xor': "^",

        # ~  bit not assembler time operation
        'a_bnot': "~",

        # << shift left assembler time operation
        'a_shl': "<<",

        # >> shift right assembler time operation
        'a_shr': ">>",

        # size of type (format string) (optional)
        'a_sizeof_fmt': "size %s",

        'flag2': 0,

        # the include directive (format string) (optional)
        'a_include_fmt': '.include "%s"',
    } # Assembler

   def ana(self):
      print "ANA"

   def emu(self) :
      print "EMU"

   def outop(self, op) :
      print "OUTOP"

   def out(self) :
      print "OUT"

   def get_frame_retsize(self, func_ea) :
      print "get_frame_retsize"

   def notify_get_autocmt(self) :
      print "notify_get_autocmt" 

   def init_instructions(self) :
      print "INIT instructions"
      
      i = 0
      for x in self.instruc:
         if x['name'] != '':                                                                                                                                                                                                   
            setattr(self, 'itype_' + x['name'], i)   
         else:
            setattr(self, 'itype_null', i)   
         i += 1
   
      self.icode_return = self.itype_reti
      print "FIN INST"

   def init_registers(self) :
      print "INIT registers"
      
      self.regNames = [
         "v0",
         "v1",
         "v2",
         "v3",
         "v4",
         "v5",

         "CS",
         "DS",
      ]

      self.regsNum = len(self.regNames)

      # Create the ireg_XXXX constants
      for i in xrange(len(self.regNames)):
         setattr(self, 'ireg_' + self.regNames[i], i)

      # Segment register information (use virtual CS and DS registers if your
      # processor doesn't have segment registers):
      self.regFirstSreg = self.ireg_CS
      self.regLastSreg  = self.ireg_DS

      # number of CS register
      self.regCodeSreg = self.ireg_CS                                                                                                                                                                                           
      
      # number of DS register
      self.regDataSreg = self.ireg_DS
      
      print "FIN REG"

   def notify_oldfile(self, filename) :
      print "oldfile", filename

   def notify_newfile(self, filename) :
      print "newfile", filename

#   def notify_loader(self) :
#      print "notify loader"

   def __init__(self):
      print "INIT"
      idaapi.processor_t.__init__(self)
      self.init_instructions()
      self.init_registers()

      print "FIN INIT"

def PROCESSOR_ENTRY():
       return dalvik_processor_t()   
