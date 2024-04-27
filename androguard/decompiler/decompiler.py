# This file is part of Androguard.
#
# Copyright (C) 2013, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Allows type hinting of types not-yet-declared
# in Python >= 3.7
# see https://peps.python.org/pep-0563/
from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from androguard.core.analysis.analysis import Analysis, MethodAnalysis
    from androguard.core.dex import DEX, ClassDefItem

from androguard.decompiler import decompile

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.token import Token

from loguru import logger


class DecompilerDAD:
    def __init__(self, vm: DEX, vmx: Analysis) -> None:
        """
        Decompiler wrapper for DAD: **D**AD is **A** **D**ecompiler
        DAD is the androguard internal decompiler.

        This Method does not use the :class:`~androguard.decompiler.decompile.DvMachine` but
        creates :class:`~androguard.decompiler.decompile.DvClass` and
        :class:`~androguard.decompiler.decompile.DvMethod` on demand.

        :param androguard.core.bytecodes.DEX vm: `DEX` object
        :param androguard.core.analysis.analysis.Analysis vmx: `Analysis` object
        """
        self.vm = vm
        self.vmx = vmx

    def get_source_method(self, m: MethodAnalysis) -> str:
        mx = self.vmx.get_method(m)
        z = decompile.DvMethod(mx)
        z.process()
        return z.get_source()

    def get_ast_method(self, m: MethodAnalysis) -> dict:
        mx = self.vmx.get_method(m)
        z = decompile.DvMethod(mx)
        z.process(doAST=True)
        return z.get_ast()

    def display_source(self, m: MethodAnalysis) -> None:
        result = self.get_source_method(m)

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(result, lexer, formatter)
        print(result)

    def get_source_class(self, _class: ClassDefItem) -> str:
        c = decompile.DvClass(_class, self.vmx)
        c.process()
        return c.get_source()

    def get_ast_class(self, _class: ClassDefItem) -> dict:
        c = decompile.DvClass(_class, self.vmx)
        c.process(doAST=True)
        return c.get_ast()

    def get_source_class_ext(self, _class: ClassDefItem) -> list[tuple[str, list]]:
        c = decompile.DvClass(_class, self.vmx)
        c.process()

        result = c.get_source_ext()

        return result

    def display_all(self, _class: ClassDefItem) -> None:
        result = self.get_source_class(_class)

        lexer = get_lexer_by_name("java", stripall=True)
        formatter = TerminalFormatter()
        result = highlight(result, lexer, formatter)
        print(result)