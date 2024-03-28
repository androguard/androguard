# This file is part of Androguard.
#
# Copyright (c) 2012 Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
# All Rights Reserved.
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

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from loguru import logger

from androguard.core.dex import Instruction, PackedSwitch, SparseSwitch
from androguard.decompiler.instruction import (
    ConditionalExpression,
    ConditionalZExpression,
    IRForm,
    MoveExceptionExpression,
    Variable,
)
from androguard.decompiler.node import Node
from androguard.decompiler.opcode_ins import INSTRUCTION_SET
from androguard.decompiler.util import get_type

if TYPE_CHECKING:
    from typing import Any

    from androguard.core.analysis.analysis import DEXBasicBlock
    from androguard.decompiler.graph import GenInvokeRetName
    from androguard.decompiler.instruction import (
        AssignExpression,
        ThisParam,
    )
    from androguard.decompiler.writer import Writer


class BasicBlock(Node):
    ins: list[IRForm]
    ins_range: tuple[int, int] | None
    loc_ins: list[tuple[int, IRForm]] | None
    var_to_declare: set[Variable]
    catch_type: str | None

    def __init__(self, name: str, block_ins: list[IRForm]):
        super().__init__(name)
        self.ins = block_ins
        self.ins_range = None
        self.loc_ins = None
        self.var_to_declare = set()
        self.catch_type = None

    def get_ins(self) -> list[IRForm] | None:
        return self.ins

    def get_loc_with_ins(self) -> list[tuple[int, IRForm]] | None:
        if self.loc_ins is None:
            assert self.ins_range is not None
            self.loc_ins = list(zip(range(*self.ins_range), self.ins))
        return self.loc_ins

    def remove_ins(self, loc: int, ins: AssignExpression) -> None:
        assert self.loc_ins is not None
        self.ins.remove(ins)
        self.loc_ins.remove((loc, ins))

    def add_ins(self, new_ins_list: list[IRForm]) -> None:
        for new_ins in new_ins_list:
            self.ins.append(new_ins)

    def add_variable_declaration(self, variable: Variable) -> None:
        self.var_to_declare.add(variable)

    def number_ins(self, num: int) -> int:
        last_ins_num = num + len(self.ins)
        self.ins_range = (num, last_ins_num)
        self.loc_ins = None
        return last_ins_num

    def set_catch_type(self, _type: str) -> None:
        self.catch_type = _type


class StatementBlock(BasicBlock):
    def __init__(self, name: str, block_ins: list[IRForm]) -> None:
        super().__init__(name, block_ins)
        self.type.is_stmt = True

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_statement_node(self)

    def __str__(self):
        return '%d-Statement(%s)' % (self.num, self.name)


class ReturnBlock(BasicBlock):
    def __init__(self, name: str, block_ins: list[IRForm]) -> None:
        super().__init__(name, block_ins)
        self.type.is_return = True

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_return_node(self)

    def __str__(self) -> str:
        return '%d-Return(%s)' % (self.num, self.name)


class ThrowBlock(BasicBlock):
    def __init__(self, name: str, block_ins: list[IRForm]) -> None:
        super().__init__(name, block_ins)
        self.type.is_throw = True

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_throw_node(self)

    def __str__(self) -> str:
        return '%d-Throw(%s)' % (self.num, self.name)


class SwitchBlock(BasicBlock):
    switch: PackedSwitch | SparseSwitch
    cases: list[Node]
    default: Node | None
    node_to_case: dict[Node, Any]

    def __init__(self, name: str, switch: PackedSwitch | SparseSwitch, block_ins: list[IRForm]) -> None:
        super().__init__(name, block_ins)
        self.switch = switch
        self.cases = []
        self.default = None
        self.node_to_case = defaultdict(list)
        self.type.is_switch = True

    def add_case(self, case: SwitchBlock) -> None:
        self.cases.append(case)

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_switch_node(self)

    def copy_from(self, node: Node) -> None:
        assert isinstance(node, SwitchBlock)
        super().copy_from(node)
        self.cases = node.cases[:]
        self.switch = node.switch[:]

    def update_attribute_with(self, n_map: dict[Node, Any]) -> None:
        super().update_attribute_with(n_map)
        self.cases = [n_map.get(n, n) for n in self.cases]
        for node1, node2 in n_map.items():
            if node1 in self.node_to_case:
                self.node_to_case[node2] = self.node_to_case.pop(node1)

    def order_cases(self) -> None:
        values = self.switch.get_values()
        if len(values) < len(self.cases):
            self.default = self.cases.pop(0)
        for case, node in zip(values, self.cases):
            self.node_to_case[node].append(case)

    def __str__(self) -> str:
        return '%d-Switch(%s)' % (self.num, self.name)


class CondBlock(BasicBlock):
    ins: list[ConditionalExpression | ConditionalZExpression]
    true: Node | None
    false: Node | None

    def __init__(self, name: str, block_ins: list[IRForm]) -> None:
        super().__init__(name, block_ins)
        self.true = None
        self.false = None
        self.type.is_cond = True

    def update_attribute_with(self, n_map: dict[Node, Node]) -> None:
        super().update_attribute_with(n_map)
        assert self.true is not None
        assert self.false is not None
        self.true = n_map.get(self.true, self.true)
        self.false = n_map.get(self.false, self.false)

    def neg(self):
        if len(self.ins) != 1:
            raise RuntimeWarning('Condition should have only 1 instruction !')
        self.ins[-1].neg()

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_cond_node(self)

    def visit_cond(self, visitor: Writer) -> None:
        if len(self.ins) != 1:
            raise RuntimeWarning('Condition should have only 1 instruction !')
        return visitor.visit_ins(self.ins[-1])

    def __str__(self) -> str:
        return '%d-If(%s)' % (self.num, self.name)


class Condition:
    cond1: ShortCircuitBlock
    cond2: ShortCircuitBlock
    isand: bool
    isnot: bool

    def __init__(self, cond1: ShortCircuitBlock, cond2: ShortCircuitBlock, isand: bool, isnot: bool):
        self.cond1 = cond1
        self.cond2 = cond2
        self.isand = isand
        self.isnot = isnot

    def neg(self) -> None:
        self.isand = not self.isand
        self.cond1.neg()
        self.cond2.neg()

    def get_ins(self) -> list[IRForm]:
        lins: list[IRForm] = []
        lins.extend(self.cond1.get_ins())
        lins.extend(self.cond2.get_ins())
        return lins

    def get_loc_with_ins(self) -> list[tuple[int, IRForm]]:
        loc_ins: list[tuple[int, IRForm]] = []
        loc_ins.extend(self.cond1.get_loc_with_ins())
        loc_ins.extend(self.cond2.get_loc_with_ins())
        return loc_ins

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_short_circuit_condition(self.isnot, self.isand,
                                                     self.cond1, self.cond2)

    def __str__(self):
        if self.isnot:
            ret = '!%s %s %s'
        else:
            ret = '%s %s %s'
        return ret % (self.cond1, ['||', '&&'][self.isand], self.cond2)


class ShortCircuitBlock(CondBlock):
    cond: ShortCircuitBlock

    def __init__(self, name: str, cond: ShortCircuitBlock):
        super().__init__(name, None)
        self.cond = cond

    def get_ins(self) -> list[IRForm]:
        return self.cond.get_ins()

    def get_loc_with_ins(self) -> list[tuple[int, IRForm]]:
        return self.cond.get_loc_with_ins()

    def neg(self) -> None:
        self.cond.neg()

    def visit_cond(self, visitor: Writer) -> None:
        return self.cond.visit(visitor)

    def __str__(self) -> str:
        return '%d-SC(%s)' % (self.num, self.cond)


class LoopBlock(CondBlock):
    cond: CondBlock

    def __init__(self, name: str, cond: CondBlock):
        super().__init__(name, None)
        self.cond = cond

    def get_ins(self) -> list[IRForm] | None:
        return self.cond.get_ins()

    def neg(self) -> None:
        self.cond.neg()

    def get_loc_with_ins(self) -> list[tuple[int, IRForm]] | None:
        return self.cond.get_loc_with_ins()

    def visit(self, visitor: Writer) -> None:
        return visitor.visit_loop_node(self)

    def visit_cond(self, visitor: Writer) -> None:
        return self.cond.visit_cond(visitor)

    def update_attribute_with(self, n_map: dict[Node, Node]):
        super().update_attribute_with(n_map)
        self.cond.update_attribute_with(n_map)

    def __str__(self) -> str:
        if self.looptype.is_pretest:
            if self.false in self.loop_nodes:
                return '%d-While(!%s)[%s]' % (self.num, self.name, self.cond)
            return '%d-While(%s)[%s]' % (self.num, self.name, self.cond)
        elif self.looptype.is_posttest:
            return '%d-DoWhile(%s)[%s]' % (self.num, self.name, self.cond)
        elif self.looptype.is_endless:
            return '%d-WhileTrue(%s)[%s]' % (self.num, self.name, self.cond)
        return '%d-WhileNoType(%s)' % (self.num, self.name)


class TryBlock(BasicBlock):
    try_start: Node
    catch: list[Node]
    def __init__(self, node: Node) -> None:
        super().__init__('Try-%s' % node.name, None)
        self.try_start = node
        self.catch = []

    # FIXME:
    @property
    def num(self) -> int:
        return self.try_start.num

    @num.setter
    def num(self, value: int) -> None:
        pass

    def add_catch_node(self, node: Node) -> None:
        self.catch.append(node)

    def visit(self, visitor: Writer) -> None:
        visitor.visit_try_node(self)

    def __str__(self) -> str:
        return 'Try({})[{}]'.format(self.name, self.catch)


class CatchBlock(BasicBlock):
    exception_ins: IRForm | None
    catch_start: BasicBlock
    catch_type: str | None

    def __init__(self, node: BasicBlock):
        first_ins = node.ins[0]
        self.exception_ins = None
        if isinstance(first_ins, MoveExceptionExpression):
            self.exception_ins = first_ins
            node.ins.pop(0)
        super().__init__('Catch-%s' % node.name, node.ins)
        self.catch_start = node
        self.catch_type = node.catch_type

    def visit(self, visitor: Writer) -> None:
        visitor.visit_catch_node(self)

    def visit_exception(self, visitor: Writer) -> None:
        if self.exception_ins:
            visitor.visit_ins(self.exception_ins)
        else:
            assert self.catch_type is not None
            visitor.write(get_type(self.catch_type))

    def __str__(self) -> str:
        return 'Catch(%s)' % self.name


def build_node_from_block(block: DEXBasicBlock, vmap: dict[int, ThisParam | Variable], gen_ret: GenInvokeRetName, exception_type: None=None) -> ReturnBlock | SwitchBlock | CondBlock | ThrowBlock | StatementBlock:
    ins: Instruction | None = None
    lins: list[IRForm] = []
    idx = block.get_start()
    opcode: int = 0
    for ins in block.get_instructions():
        opcode = ins.get_op_value()
        if opcode == -1:  # FIXME? or opcode in (0x0300, 0x0200, 0x0100):
            idx += ins.get_length()
            continue
        try:
            _ins = INSTRUCTION_SET[opcode]
        except IndexError:
            logger.error('Unknown instruction : %s.', ins.get_name().lower())
            _ins = INSTRUCTION_SET[0]
        # fill-array-data
        if opcode == 0x26:
            fillarray = block.get_special_ins(idx)
            lins.append(_ins(ins, vmap, fillarray))
        # invoke-kind[/range]
        elif 0x6e <= opcode <= 0x72 or 0x74 <= opcode <= 0x78:
            lins.append(_ins(ins, vmap, gen_ret))
        # filled-new-array[/range]
        elif 0x24 <= opcode <= 0x25:
            lins.append(_ins(ins, vmap, gen_ret.new()))
        # move-result*
        elif 0xa <= opcode <= 0xc:
            lins.append(_ins(ins, vmap, gen_ret.last()))
        # move-exception
        elif opcode == 0xd:
            lins.append(_ins(ins, vmap, exception_type))
        # monitor-{enter,exit}
        elif 0x1d <= opcode <= 0x1e:
            idx += ins.get_length()
            continue
        else:
            lins.append(_ins(ins, vmap))
        idx += ins.get_length()
    name = block.get_name()
    # return*
    if 0xe <= opcode <= 0x11:
        node = ReturnBlock(name, lins)
    # {packed,sparse}-switch
    elif 0x2b <= opcode <= 0x2c:
        assert ins is not None
        idx -= ins.get_length()
        values = block.get_special_ins(idx)
        node = SwitchBlock(name, values, lins)
    # if-test[z]
    elif 0x32 <= opcode <= 0x3d:
        node = CondBlock(name, lins)
        node.off_last_ins = ins.get_ref_off()
    # throw
    elif opcode == 0x27:
        node = ThrowBlock(name, lins)
    else:
        # goto*
        if 0x28 <= opcode <= 0x2a:
            lins.pop()
        node = StatementBlock(name, lins)
    return node
