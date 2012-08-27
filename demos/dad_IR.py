import sys
sys.path.append('./')

from pprint import pprint

from androguard.core.bytecodes import dvm
from androguard.core.analysis.analysis import uVMAnalysis
from dad.basic_blocks import GenInvokeRetName
from dad.decompile import DvMethod
from dad.opcode_ins import INSTRUCTION_SET
from dad.util import log

TEST = './examples/dalvik/test/bin/classes.dex'

vm = dvm.DalvikVMFormat(open(TEST).read())
vma = uVMAnalysis(vm)

method = vma.get_method(vm.get_method('test_base')[0])
basic_blocks = method.basic_blocks.bb

return_generator = GenInvokeRetName() # generator of instructions' return var
vmap = {} # map of variables {var: IForm of var}
lins = [] # list of ins in IRForm
for bb in basic_blocks:
    idx = bb.get_start()
    for ins in bb.get_instructions():
        opcode = ins.get_op_value()
        #check-cast
        if opcode == 0x1f :
            idx += ins.get_length()
            continue
        _ins = INSTRUCTION_SET.get(ins.get_name().lower())
        # _ins is one of the function in dad/opcode_ins.py
        if _ins is None:
            log('Unknown ins : %s.' % _ins.get_name().lower(), 'error')
        # fill-array-data
        if opcode == 0x26:
            fillarray = bb.get_special_ins(idx)
            lins.append(_ins(ins, vmap, fillarray))
        # invoke-kind[/range]
        elif (0x6e <= opcode <= 0x72 or 0x74 <= opcode <= 0x78):
            lins.append(_ins(ins, vmap, return_generator))
        # filled-new-array[/range]
        elif 0x24 <= opcode <= 0x25:
            lins.append(_ins(ins, vmap, return_generator.new()))
        # move-result*
        elif 0xa <= opcode <= 0xc:
            lins.append(_ins(ins, vmap, return_generator.last()))
        else:
            lins.append(_ins(ins, vmap))
        idx += ins.get_length()
    name = bb.get_name()

print 'List of ins in IRForm:'
pprint(lins)
