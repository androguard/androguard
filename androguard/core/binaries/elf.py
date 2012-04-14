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

from elfesteem import *
from miasm.tools.pe_helper import *
from miasm.core import asmbloc
from miasm.arch import arm_arch
from miasm.core import bin_stream


def disasm_at_addr(in_str, ad_to_dis, symbol_pool) :
    kargs = {}
    all_bloc = asmbloc.dis_bloc_all(arm_arch.arm_mn, in_str, ad_to_dis, set(),
                                        symbol_pool=symbol_pool,
                                        dontdis_retcall = False,
                                        follow_call = False,
                                        **kargs)
    print all_bloc

    for i in all_bloc :
        print i.label
        for j in i.lines :
            print "\t", j
        print

class ELF :
    def __init__(self, buff) :
        self.e = elf_init.ELF( buff )

        in_str = bin_stream.bin_stream(self.e.virt)

        dll_dyn_funcs = get_import_address_elf(self.e)

        symbol_pool = asmbloc.asm_symbol_pool()
        for (n,f), ads in dll_dyn_funcs.items() :
            for ad in ads :
                l  = symbol_pool.getby_name_create("%s_%s"%(n, f))
                l.offset = ad
                symbol_pool.s_offset[l.offset] = l

        print symbol_pool
                #print f, hex(ad)
        
        for k, v in self.e.sh.symtab.symbols.items():
            print k, v, type(v), hex(v.value)
            if k == "rootshell" :
                disasm_at_addr( in_str, v.value, symbol_pool )
