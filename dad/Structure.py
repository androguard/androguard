#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2010, Geoffroy Gueguen <geoffroy.gueguen@gmail.com>
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

import Instruction
import Util
import pydot


LOOP_PRETEST = 0
LOOP_POSTTEST = 1
LOOP_ENDLESS = 2
NODE_IF = 0
NODE_SWITCH = 1
NODE_STMT = 2
NODE_RETURN = 3

def indent(ind):
    return '   ' * ind

class Block(object):
    def __init__(self, node, block):
        self.block = block
        self.node = node
        self.next = None

    def get_next(self):
        return self.next

    def set_next(self, next):
        self.next = next

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        Util.log('Process not done : %s' % self, 'debug')


class StatementBlock(Block):
    def __init__(self, node, block):
        super(StatementBlock, self).__init__(node, block)

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        res = process_block(self.block, memory, tabsymb, vars, ind)
        ins = ''
        for i in res:
            ins += '%s%s;\n' % (indent(ind), i.value())
        if self.next is not None:
            if not self.next.traversed:
                ins += self.next.process(memory, tabsymb, vars,
                                         ind, ifollow, nfollow)
        return ins

    def __str__(self):
        return 'Statement(%s)' % self.block.name


class WhileBlock(Block):
    def __init__(self, node, block):
        super(WhileBlock, self).__init__(node, block)
        self.true = None
        self.false = None

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow): 
        ins = ''
        if self.node.looptype == LOOP_PRETEST:
            lins, cond = self.block.get_cond(memory, tabsymb, vars, ind)
            for i in lins:
                ins += '%s%s;\n' % (indent(ind), i.value())
            if self.false is self.next:
                ins += '%swhile(%s) {\n' % (indent(ind), cond.value())
            else:
                cond.neg()
                ins += '%swhile(%s) {\n' % (indent(ind), cond.value())
        elif self.node.looptype == LOOP_POSTTEST:
            ins += '%sdo {\n' % indent(ind)
        elif self.node.looptype == LOOP_ENDLESS:
            ins += '%swhile(true) {\n' % indent(ind)
            ins += self.block.process(memory, tabsymb, vars,
                                      ind + 1, ifollow, nfollow)
        else:
            Util.log('Error processing loop. No type.', 'error')
        if not self.node.end_loop():
            if self.node.looptype == LOOP_PRETEST:
                suc = self.true
                if suc is self.next:
                    suc = self.false
            else:
                suc = None
                ins += self.block.process(memory, tabsymb, vars, ind + 1, ifollow, nfollow) 
            if suc:
                if not suc.traversed:
                    ins += suc.process(memory, tabsymb, vars, ind + 1, ifollow, nfollow)
                else:
                    print 'node :', self.node, self.block.end_loop()
                    print 'suc :', suc
                    print 'end ?', self.node.end_loop(), self.node.endloop, suc.endloop, suc.end_loop()
                    Util.log('Error, goto needed for the loop.', 'error')
        if self.node.looptype == LOOP_PRETEST:
            #ins += process_block(self.block, memory, tabsymb, vars,
            #                     ind + 1)
            ins += self.block.process(memory, tabsymb, vars,
                                      ind + 1, ifollow, nfollow)
            ins += '%s}\n' % indent(ind)
        elif self.node.looptype == LOOP_POSTTEST:
            if not self.node.endloop:
                end = self.node.loopend.content
                lins, cond = end.get_cond(memory, tabsymb, vars, ind)
                self.node.loopend.traversed = True
                ins += self.block.process(memory, tabsymb, vars,
                                          ind + 1, ifollow, nfollow)
            else:
                end = self.block
                lins, cond = end.get_cond(memory, tabsymb, vars, ind)
                self.node.loopend.traversed = True
            for i in lins:
                ins += '%s%s;\n' % (indent(ind + 1), i.value())
            ins += '%s} while (%s);\n' % (indent(ind), cond.value())
        
        else:
            ins += '%s}\n' % indent(ind)
        if self.next and not self.next.traversed:
            ins += self.next.process(memory, tabsymb, vars,
                                     ind, ifollow, nfollow)
        return ins
            
    def __str__(self):
        if self.node.looptype == LOOP_PRETEST:
            return 'While(%s)' % self.block
        elif self.node.looptype == LOOP_POSTTEST:
            return 'DoWhile(%s)' % self.block
        else:
            return 'WhileTrue(%s)' % self.block


class SwitchBlock(Block):
    def __init__(self, node, block):
        super(SwitchBlock, self).__init__(node, block)

    def get_switch(self, memory, tabsymb, vars, ind):
        lins = process_block(self.block, memory, tabsymb, vars, ind)
        cond = lins[-1]
        return (lins[:-1], cond)

    def compute_follow(self):
        def get_branch(node, l=None):
            if l is None:
                l = set()
            l.add(node)
            for child in node.succs:
                if not (child in l):
                    l.add(child)
                    get_branch(child, l)
            return l
        branches = [get_branch(br) for br in self.node.succs]
        join = reduce(set.intersection, branches)
        if join:
            self.follow = min(join, key=lambda x: x.num)

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        ins = ''
        self.compute_follow()
        lins, switchvalue = self.get_switch(memory, tabsymb, vars, ind)
        for i in lins:
            ins += '%s%s;\n' % (indent(ind), i.value())
        values = self.block.get_special_ins(switchvalue.ins).get_operands()
        initval = values[0]
#        cases = {}
#        for v in values[1]:
#            cases[v] = initval
#            initval += 1
        ins += '%sswitch(%s) {\n' % (indent(ind), switchvalue.value())
#        print 'BLOCK :', self.block
#        print 'STARt :', hex(self.block.get_start())
#        print 'CASES :', cases
        for s in self.node.succs:
#            print 'NEXT :', self.next, hex(self.next.content.block.get_start())
#            print 'S :', s, hex(s.content.block.get_start())
            if not s.traversed:
                ins += '%scase %s:\n' % (indent(ind + 1), initval)
                initval += 1
                ins += s.process(memory, tabsymb, vars,
                                 ind + 2, ifollow, self.follow)
                ins += '%sbreak;\n' % indent(ind + 2)
            else:
                Util.log('Switch node %s already traversed.' % self, 'error')
        if self.next and not self.next.traversed:
            ins += self.next.process(memory, tabsymb, vars,
                                     ind, ifollow, nfollow)
        return ins

    def __str__(self):
        return 'Switch(%s)' % self.block.name


class TryBlock(Block):
    def __init__(self, node, block):
        super(TryBlock, self).__init__(node, block)
        self.catch = []
    
    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        res = process_block(self.block, memory, tabsymb, vars, ind)
        res = ''.join([str(i.value()) for i in res])
        return res

    def add_catch(self, node):
        self.catch.append(node)

    def __str__(self):
        return 'Try(%s)' % self.block.name


class CatchBlock(Block):
    def __init__(self, node, block, type):
        super(CatchBlock, self).__init__(node, block)
        self.exceptionType = type

    def __str__(self):
        return 'Catch(%s)' % self.block.name


class Condition( ):
    def __init__(self, cond1, cond2, isand, isnot):
        self.cond1 = cond1
        self.cond2 = cond2
        self.isand = isand
        self.isnot = isnot

    def neg(self):
        self.cond1.neg()
        self.cond2.neg()
        self.isand = not self.isand

    def get_cond(self, memory, tabsymb, vars, ind):
        lins1, cond1 = self.cond1.content.get_cond(memory, tabsymb, vars, ind)
        lins2, cond2 = self.cond2.content.get_cond(memory, tabsymb, vars, ind)
        if self.isnot:
            cond1.neg()
        self.cond = Condition(cond1, cond2, self.isand, self.isnot)
        lins1.extend(lins2)
        return lins1, self.cond

    def value(self):
        cond = ['||', '&&'][self.isand]
        return '(%s %s %s)' % (self.cond1.value(), cond, self.cond2.value())

    def __str__(self):
        return '(%s %s %s)' % (self.cond1, ['||', '&&'][self.isand], self.cond2)


class ShortCircuitBlock(Block):
    def __init__(self, newNode, cond):
        super(ShortCircuitBlock, self).__init__(newNode, None)
        self.cond = cond
        newNode.type = NODE_IF
        newNode.num = cond.cond1.num
        newNode.looptype = cond.cond1.looptype
        newNode.loophead = cond.cond1.loop_head()
        newNode.startloop = cond.cond1.start_loop()
        newNode.endloop = cond.cond1.end_loop()
        if cond.cond1.loopend is cond.cond1:
            newNode.loopend = self
        else:
            newNode.loopend = cond.cond1.loopend
        self.true = None
        self.false = None
        self.follow = None

    def update(self):
        interval = self.cond.cond1.interval
        interval.content.remove(self.cond.cond1)
        interval.content.remove(self.cond.cond2)
        interval.add(self.node)
        self.node.set_next(self.cond.cond1.get_next())
        for pred in self.cond.cond1.preds:
            if pred.get_next() is self.cond.cond1:
                pred.set_next(self.node)
            pred.del_node(self.cond.cond1)
            pred.add_node(self.node)
        for suc in self.cond.cond1.succs:
            suc.preds.remove(self.cond.cond1)
        for suc in self.cond.cond2.succs:
            suc.preds.remove(self.cond.cond2)
            self.node.add_node(suc)
    
    def get_cond(self, memory, tabsymb, vars, ind):
        return self.cond.get_cond(memory, tabsymb, vars, ind)

    def compute_follow(self):
        def get_branch(node, l=None):
            if l is None:
                l = set()
            l.add(node)
            for child in node.succs:
                if not (child in l):
                    l.add(child)
                    get_branch(child, l)
            return l
        true = get_branch(self.true)
        false = get_branch(self.false)
        join = true & false
        if join:
            self.follow = min(join, key=lambda x: x.num)

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        ins = ''
        lins, cond = self.get_cond(memory, tabsymb, vars, ind)
        for i in lins:
            ins += '%s%s;\n' % (indent(ind), i.value())
        self.compute_follow()
        if self.follow:
            if not self.true.traversed:
                if not (self.true is self.follow):
                    ins += '%sif (%s) {\n' % (indent(ind), cond.value())
                    ins += self.true.process(memory, tabsymb, vars,
                                             ind + 1, self.follow, nfollow)
                else: # no true clause ?
                    cond.neg()
                    ins += '%sif (%s) {\n' % (indent(ind), cond.value())
                    ins += self.false.process(memory, tabsymb, vars,
                                              ind + 1, self.follow, nfollow)
            else:
                cond.neg()
                ins += '%sif (%s) {\n' % (indent(ind), cond.value())
                ins += self.false.process(memory, tabsymb, vars,
                                          ind + 1, self.follow, nfollow)
            if not self.false.traversed:
                if not (self.false is self.follow):
                    ins += '%s} else {\n' % indent(ind)
                    ins += self.false.process(memory, tabsymb, vars,
                                              ind + 1, self.follow, nfollow)
            ins += '%s}\n' % indent(ind)
            if not self.follow.traversed:
                ins += self.follow.process(memory, tabsymb, vars,
                                           ind + 1, ifollow, nfollow)
        else: # if then else
            ins += '%sif(%s) {\n' % (indent(ind), cond.value())
            ins += self.true.process(memory, tabsymb, vars,
                                     ind + 1, ifollow, nfollow)
            ins += '%s} else {\n' % indent(ind)
            ins += self.false.process(memory, tabsymb, vars,
                                      ind + 1, ifollow, nfollow)
            ins += '%s}\n' % indent(ind)
        return ins

    def __str__(self):
        r = 'SC('
        r += str(self.cond)
        r += ')'
        return r


class IfBlock(Block):
    def __init__(self, node, block):
        super(IfBlock, self).__init__(node, block)
        self.true = None
        self.false = None
        self.follow = None

    def get_cond(self, memory, tabsymb, vars, ind):
        lins = process_block(self.block, memory, tabsymb, vars, ind)
        cond = lins[-1]
        return (lins[:-1], cond)

    def compute_follow(self):
        def get_branch(node, l=None):
            if l is None:
                l = set()
            l.add(node)
            for child in node.succs:
                if not (child in l):
                    l.add(child)
                    get_branch(child, l)
            return l
        true = get_branch(self.true)
        false = get_branch(self.false)
        join = true & false
        if join:
            self.follow = min(join, key=lambda x: x.num)

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        ins = ''
        lins, cond = self.get_cond(memory, tabsymb, vars, ind)
        for i in lins:
            ins += '%s%s;\n' % (indent(ind), i.value())
        self.compute_follow()
        if self.follow:
            if not self.true.traversed:
                if not (self.true is self.follow):
                    ins += '%sif (%s) {\n' % (indent(ind), cond.value())
                    ins += self.true.process(memory, tabsymb, vars,
                                             ind + 1, self.follow, nfollow)
                else: # no true clause ?
                    cond.neg()
                    ins += '%sif (%s) {\n' % (indent(ind), cond.value())
                    ins += self.false.process(memory, tabsymb, vars,
                                              ind + 1, self.follow, nfollow)
            else:
                cond.neg()
                ins += '%sif (%s) {\n' % (indent(ind), cond.value())
                ins += self.false.process(memory, tabsymb, vars,
                                          ind + 1, self.follow, nfollow)
            if not self.false.traversed:
                if not (self.false is self.follow):
                    ins += '%s} else {\n' % indent(ind)
                    ins += self.false.process(memory, tabsymb, vars,
                                              ind + 1, self.follow, nfollow)
            ins += '%s}\n' % indent(ind)
            if not self.follow.traversed:
                ins += self.follow.process(memory, tabsymb, vars,
                                           ind + 1, ifollow, nfollow)
        else: # if then else
            ins += '%sif(%s) {\n' % (indent(ind), cond.value())
            ins += self.true.process(memory, tabsymb, vars,
                                     ind + 1, ifollow, nfollow)
            ins += '%s} else {\n' % indent(ind)
            ins += self.false.process(memory, tabsymb, vars,
                                      ind + 1, ifollow, nfollow)
            ins += '%s}\n' % indent(ind)
        return ins

    def __str__(self):
        return 'If(%s)' % self.block.name


class Node(object):
    def __init__(self):
        self.succs = []
        self.preds = []
        self.type = None
        self.content = None
        self.interval = None
        self.next = None
        self.num = 0
        self.looptype = None
        self.loophead = None
        self.loopend = None
        self.startloop = False
        self.endloop = False
        self.traversed = False

    def __contains__(self, item):
        if item == self:
            return True
        return False

    def add_node(self, node):
        if self.type == NODE_IF:
            if self.content.false is None:
                self.content.false = node
            elif self.content.true is None:
                self.content.true = node
        elif self.type == NODE_STMT:
            self.content.next = node
        if node not in self.succs:
            self.succs.append(node)
        if self not in node.preds:
            node.preds.append(self)

    def del_node(self, node):
        if self.type == NODE_IF:
            if self.content.false is None:
                self.content.false = None
            elif self.content.true is node:
                self.content.true = None
        self.succs.remove(node)

    def set_content(self, content):
        self.content = content

    def set_loophead(self, head):
        if self.loophead is None:
            self.loophead = head

    def set_loopend(self, end):
        if self.loopend is None:
            self.loopend = end

    def loop_head(self):
        return self.loophead

    def get_head(self):
        return self
    
    def get_end(self):
        return self

    def set_loop_type(self, type):
        self.looptype = type

    def set_startloop(self):
        self.startloop = True

    def set_endloop(self):
        self.endloop = True

    def start_loop(self):
        return self.startloop

    def end_loop(self):
        return self.endloop

    def process(self, memory, tabsymb, vars, ind, ifollow, nfollow):
        print 'PROCESSING %s' % self.content
        if self in (ifollow, nfollow) or self.traversed:
            print '\tOr not.'
            return ''
        self.traversed = True
        # vars.startBlock() / endBlock ?
        return self.content.process(memory, tabsymb, vars,
                                    ind, ifollow, nfollow)

    def get_next(self):
        return self.content.get_next()

    def set_next(self, next):
        self.content.set_next(next)

    def __repr__(self):
        return '%d-%s' % (self.num, str(self.content))


class Graph( ):
    def __init__(self, nodes, tradBlock):
        self.nodes = nodes
        self.tradBlock = tradBlock
        for node in self.nodes:
            if node.type is None:
                node.type = node.head.get_head().type

    def remove_jumps(self):
        for node in self.nodes:
            if len(node.content.block.ins) == 0: 
                for suc in node.succs:
                    suc.preds.remove(node)
                    for pred in node.preds:
                        pred.succs.remove(node)
                        pred.add_node(suc)
                self.nodes.remove(node)

    def get_nodes_reversed(self):
        return sorted(self.nodes, key=lambda x: x.num, reverse=True)

    def first_node(self):
        return sorted(self.nodes, key=lambda x: x.num)[0]

    def __repr__(self):
        r = 'GRAPHNODE :\n'
        for node in self.nodes:
            r += '\tNODE :\t' + str(node) + '\n'
            for child in node.succs:
                r += '\t\t\tCHILD : ' + str(child) + '\n'
        return r

    def draw(self, dname, name):
        if len(self.nodes) < 3:
            return
        digraph = 'Digraph %s {\n' % dname
        digraph += 'graph [bgcolor=white];\n'
        digraph += 'node [color=lightgray, style=filled shape=box '\
                   'fontname=\"Courier\" fontsize=\"8\"];\n'
        slabel = ''
        for node in self.nodes:
            val = 'green'
            lenSuc = len(node.succs)
            if lenSuc > 1:
                val = 'red'
            elif lenSuc == 1:
                val = 'blue'
            for child in node.succs:
                digraph += '"%s" -> "%s" [color="%s"];\n' % (node, child, val)
                if val == 'red':
                    val = 'green'
            slabel += '"%s" [ label = "%s" ];\n' % (node, str(node))
        dir = 'graphs2'
        digraph += slabel + '}'
        pydot.graph_from_dot_data(digraph).write_png('%s/%s.png' % (dir, name))


class AST( ):
    def __init__(self, root, doms):
        self.succs = [root]
      #  else:
      #      self.root = root
      #      self.childs = root.succs
      #  print 'Root :', root,
      #  if root.looptype:
      #      print ['LOOP_PRETEST', 'LOOP_POSTTEST', 'LOOP_ENDLESS'][root.looptype]
      #  else:
      #      print 'not loop'
      #  print 'childs :', self.childs
        self.build(root, doms)
      #  print 'childs after build :', self.childs
      #  self.childs = [AST(child, False) for child in self.childs]

    def build(self, node, doms):
        if node.type == NODE_RETURN:
            child = None
        else:
            child = node.get_next()
      #      if child is None and len(node.succs) > 0:
      #          self.childs = node.succs
      #          return
      #  node.set_next(None)
        if child is not None:
            for pred in child.preds:
                if child in pred.succs:
                    pred.succs.remove(child)
            child.preds = []
            self.succs.append(child)
            self.build(child, doms)

    def draw(self, dname, name):
        if len(self.succs) < 2:
            return
        def slabel(node, done):
            done.add(node)
            val = 'green'
            lenSuc = len(node.succs)
            if lenSuc > 1:
                val = 'red'
            elif lenSuc == 1:
                val = 'blue'
            label = ''
            for child in node.succs:
                label += '"%s" -> "%s" [color="%s"];\n' % (node, child, val)
                if val == 'red':
                    val = 'green'
                if not (child in done):
                    label += slabel(child, done)
            label += '"%s" [ label = "%s" ];\n' % (node, str(node))
            return label
            
        digraph = 'Digraph %s {\n' % dname
        digraph += 'graph [bgcolor=white];\n'
        digraph += 'node [color=lightgray, style=filled shape=box '\
                   'fontname=\"Courier\" fontsize=\"8\"];\n'
        done = set()
        label = slabel(self, done)
        dir = 'graphs2/ast'
        digraph += label + '}'
        pydot.graph_from_dot_data(digraph).write_png('%s/%s.png' % (dir, name))


class Interval(Node):
    def __init__(self, head, nodes, num):
        super(Interval, self).__init__()
        self.content = nodes
        self.head = head
        self.end = None
        self.internum = num
        for node in nodes:
            node.interval = self
    
    def __contains__(self, item):
        for n in self.content:
            if item in n:
                return True
        return False

    def add(self, node):
        self.content.append(node)
        node.interval = self

    def compute_end(self):
        for node in self.content:
            for suc in node.succs:
                if suc not in self.content:
                        self.end = node

    def get_end(self):
        return self.end.get_end()

    def type(self):
        return self.get_head().type

    def set_next(self, next):
        self.head.set_next(next.get_head())

    def set_loop_type(self, type):
        self.looptype = type
        self.get_head().set_loop_type(type)

    def set_loophead(self, head):
        self.loophead = head
        for n in self.content:
            n.set_loophead(head)

    def set_loopend(self, end):
        self.loopend = end
        self.get_head().set_loopend(end)

    def set_startloop(self):
        self.head.set_startloop()

    def get_head(self):
        return self.head.get_head()

    def loop_head(self):
        return self.head.loop_head()

    def __repr__(self):
        return 'Interval(%d)=%s' % (self.internum, self.head.get_head())


def Construct(node, block):
#    if block.exception_analysis:
#        currentblock = TryBlock(node, block)
#    else:
    last_ins = block.ins[-1].op_name
    if last_ins.startswith('return'):
        node.type = NODE_RETURN
        currentblock = StatementBlock(node, block)
    elif last_ins.endswith('switch'):
        node.type = NODE_SWITCH
        currentblock = SwitchBlock(node, block)
    elif last_ins.startswith('if'):
        node.type = NODE_IF
        currentblock = IfBlock(node, block)
    else:
        if last_ins.startswith('goto'):
            block.ins = block.ins[:-1]
        node.type = NODE_STMT
        currentblock = StatementBlock(node, block)
    return currentblock


def process_block(block, memory, tabsymb, vars, ind):
    lins = []
    memory['heap'] = None
    for ins in block.get_ins():
        Util.log('Name : %s, Operands : %s' % (ins.get_name(),
                                               ins.get_operands()), 'debug')
        _ins = Instruction.INSTRUCTION_SET.get(ins.get_name().lower())
        if _ins is None:
            Util.log('Unknown instruction : %s.' % _ins.get_name().lower(),
                                                                    'error')
        else:
            newIns = _ins[1]
        newIns = newIns(ins)
        newIns.symbolic_process(memory, tabsymb, vars)
        #if _ins[0] in (Instruction.INST, Instruction.COND):
        lins.append(newIns)
        if memory['heap'] is True:
            memory['heap'] = newIns
        Util.log('---> newIns : %s. varName : %s.\n' % (ins.get_name(),
                                                        newIns), 'debug')
    return lins


def BFS(start):
    from Queue import Queue
    Q = Queue()
    Q.put(start)
    nodes = []
    nodes.append(start)
    while not Q.empty():
        node = Q.get()
        for child in node.childs:
            if child[-1] not in nodes:
                nodes.append(child[-1])
                Q.put(child[-1])
    return nodes


def NumberGraph(v, interval, num, visited = None):
    if visited is None:
        visited = set()
    v.num = num
    visited.add(v)
    for suc in v.succs:
        if suc not in visited:
            if suc in interval:
                toVisit = True
                for pred in suc.preds:
                    if pred not in visited and \
                        pred.interval.internum < suc.interval.internum:
                        toVisit = False
                if toVisit:
                    num = NumberGraph(suc, interval, num + 1, visited)
            else:
                toVisit = True
                for pred in suc.preds:
                    if pred not in visited:
                        toVisit = False
                if toVisit:
                    num = NumberGraph(suc, interval, num + 1, visited)
    return num


def Intervals(num, G):
    I = []
    H = [G.nodes[0]]
    L = {}
    processed = dict([(i, -1) for i in G.nodes])
    while H:
        n = H.pop(0)
        if processed[n] == -1:
            processed[n] = 1
            L[n] = Interval(n, [n], num)
            num += 1
            change = True
            while change:
                change = False
                for m in G.nodes:
                    add = True
                    if len(m.preds) > 0:
                        for p in m.preds:
                            if p not in L[n].content:
                                add = False
                        if add and m not in L[n].content:
                            L[n].add(m)
                            change = True
            for m in G.nodes:
                add = False
                if m not in H and m not in L[n].content:
                    for p in m.preds:
                        if p in L[n].content:
                            add = True
                    if add:
                        H.append(m)
            L[n].compute_end()
            I.append(L[n])
    return I, L, num


def DerivedSequence(G):
    I, L, nInterv = Intervals(1, G)
    NumberGraph(G.nodes[0], L, 1)
    derivSeq = []
    derivInterv = []
    different = True
    while different:
        derivSeq.append(G)
        derivInterv.append(L)
        for interval in I:
            for pred in interval.head.preds:
                if interval is not pred.interval:
                    pred.interval.add_node(interval)
            for node in interval.content:
                for suc in node.succs:
                    if interval is not suc.interval:
                        interval.add_node(suc.interval)
        G = Graph(I, None)
        I, L, nInterv = Intervals(nInterv, G)
        NumberGraph(G.nodes[0], L, 1)
        if len(I) == 1 and len(I[0].content) == 1:
            derivSeq.append(G)
            derivInterv.append(L)
            different = False
    return derivSeq, derivInterv


def InLoop(node, nodesInLoop):
    for n in nodesInLoop:
        if node in n:
            return True
    return False


def MarkLoop(G, root, end, L):
    print 'MARKLOOP :', root, 'END :', end
    def MarkLoopRec(end):
        if not InLoop(end, nodesInLoop):
            nodesInLoop.append(end)
            end.set_loophead(headnode)
            for node in end.preds:
                if node.num > headnode.num and node.num <= end.num:
                    if InLoop(node, L[root].content):
                        MarkLoopRec(node)
    headnode = root.get_head()
    endnode = end.get_end()
    nodesInLoop = [headnode]
    root.set_loophead(headnode)
    root.set_loopend(endnode)
    root.set_startloop()
    for pred in root.get_head().preds:
        if pred.num > headnode.num:
            pred.set_endloop()
    endnode.set_endloop()
    MarkLoopRec(endnode)
    return nodesInLoop


def LoopType(G, root, end, nodesInLoop):
    for pred in root.get_head().preds:
        if pred.interval is end:
            end = pred
    if end.type == NODE_IF:
        if root.type == NODE_IF:
            succs = root.succs
            if len(succs) == 1 and InLoop(succs[0].get_head(), nodesInLoop):
                root.set_loop_type(LOOP_POSTTEST)
            elif InLoop(succs[0], nodesInLoop) and InLoop(succs[1], nodesInLoop):
                root.set_loop_type(LOOP_POSTTEST)
            else:
                root.set_loop_type(LOOP_PRETEST)
        else:
            root.set_loop_type(LOOP_POSTTEST)
    else:
        if root.type == NODE_IF:
            succs = root.succs
            if len(succs) == 1 and InLoop(succs[0].get_head(), nodesInLoop):
                root.set_loop_type(LOOP_PRETEST)
            elif InLoop(succs[0], nodesInLoop) and InLoop(succs[1], nodesInLoop):
                root.set_loop_type(LOOP_ENDLESS)
            else:
                root.set_loop_type(LOOP_PRETEST)
        else:
            root.set_loop_type(LOOP_ENDLESS)


def LoopFollow(G, root, end, nodesInLoop):
    for pred in root.get_head().preds:
        if pred.interval is end:
            end = pred
    if root.looptype == LOOP_PRETEST:
        succ = root.get_head()
        if InLoop(succ.succs[0], nodesInLoop):
            root.set_next(succ.succs[1])
        else:
            root.set_next(succ.succs[0])
    elif root.looptype == LOOP_POSTTEST:
        succ = end.get_end()
        if InLoop(succ.succs[0], nodesInLoop):
            root.set_next(succ.succs[1])
        else:
            root.set_next(succ.succs[0])
    else:
        numNext = 10**10 #FIXME?
        for node in nodesInLoop:
            if node.type == NODE_IF:
                succs = node.succs
                if not InLoop(succs[0], nodesInLoop) and succs[0].num < numNext:
                    next = succs[0]
                    numNext = next.num
                elif not InLoop(succs[1], nodesInLoop) \
                                            and succs[1].num < numNext:
                    next = succs[1]
                    numNext = next.num
        if numNext != 10**10:
            root.set_next(next)


def LoopStruct(G, Gi, Li):
    if len(Li) < 0:
        return
    for i, G in enumerate(Gi):
        loops = set()
        L = Li[i]
        for head in sorted(L.keys(), key=lambda x: x.num):
            for node in head.preds:
                if node.interval == head.interval:
                    loops.update(MarkLoop(G, head, node, L))
                    LoopType(G, head, node, loops)
                    LoopFollow(G, head, node, loops)


def IfStruct(G, immDom):
    unresolved = set()
    for node in G.get_nodes_reversed():
        if node.type == NODE_IF and not (node.start_loop() or node.end_loop()):
            ldominates = []
            for n, dom in immDom.iteritems():
                if node is dom and len(n.preds) > 1:
                    ldominates.append(n)
            if len(ldominates) > 0:
                n = max(ldominates, key=lambda x: x.num)
                node.set_next(n)
                for x in unresolved:
                    x.set_next(n)
                unresolved = set()
            else:
                unresolved.add(node)


def SwitchStruct(G, immDom):
    unresolved = set()
    for node in G.get_nodes_reversed():
        if node.type == NODE_SWITCH:
            for suc in node.succs:
                if immDom[suc] is not node:
                    n = commonImmedDom(node.succs, immDom) #TODO
                else:
                    n = node
                ldominates = []
                for n, dom in immDom.iteritems():
                    if node is dom and len(n.preds) >= 2:
                        ldominates.append(n)
                if len(ldominates) > 0:
                    j = max(ldominates, key=lambda x: len(x.preds))
                    node.set_next(j)
                    for x in unresolved:
                        x.set_next(j)
                    unresolved = set()
                else:
                    unresolved.add(node)


def ShortCircuitStruct(G):
    def MergeNodes(node1, node2, isAnd, isNot):
        G.nodes.remove(node1)
        G.nodes.remove(node2)
        done.add(node2)
        newNode = Node()
        block = ShortCircuitBlock(newNode, Condition(node1, node2, isAnd, isNot))
        newNode.set_content(block)
        block.update()
        G.nodes.append(newNode)
    change = True
    while change:
        G.nodes = sorted(G.nodes, key=lambda x: x.num)
        change = False
        done = set()
        for node in G.nodes[:]: # work on copy
            if node.type == NODE_IF and node not in done and \
                                    not node.end_loop():#(node.start_loop() or node.end_loop()):
                then = node.succs[1]
                els = node.succs[0]
                if then.type is NODE_IF and len(then.preds) == 1 and \
                                                        not then.end_loop():
                    if then.succs[0] is els: # !node && t
                        MergeNodes(node, then, True, True)
                        change = True
                    elif then.succs[1] is els: # node || t
                        MergeNodes(node, then, False, False)
                        change = True
                elif els.type is NODE_IF and len(els.preds) == 1 and \
                                                        not els.end_loop():
                    if els.succs[0] is then: # !node && e
                        MergeNodes(node, els, True, True)
                        change = True
                    elif els.succs[1] is then: # node || e
                        MergeNodes(node, els, False, False)
                        change = True
            done.add(node)


def WhileBlockStruct(G):
    for node in G.nodes:
        if node.start_loop():
            cnt = node.content
            block = WhileBlock(node, cnt)
            block.next = cnt.next
            if node.type == NODE_IF:
                print 'NODE :', node
                print 'CNT :', cnt
                print 'TRUE :', cnt.true
                print 'FALSE :', cnt.false
                block.true = node.content.true
                block.false = node.content.false
            node.set_content(block)


def Dominators(G):
    dom = {}
    dom[G.nodes[0]] = set([G.nodes[0]])
    for n in G.nodes[1:]:
        dom[n] = set(G.nodes)
    changes = True
    while changes:
        changes = False
        for n in G.nodes[1:]:
            old = len(dom[n])
            for p in n.preds:
                dom[n].intersection_update(dom[p])
            dom[n] = dom[n].union([n])
            if old != len(dom[n]):
                changes = True
    return dom


def BuildImmediateDominator_old(G):
    immDom = {}
    dominators = Dominators(G)
    for dom in dominators:
        dom_set = dominators[dom] - set([dom])
        if dom_set:
            immDom[dom] = max(dom_set, key=lambda x: x.num)
        else:
            immDom[dom] = None
    return immDom


def BuildImmediateDominator(G):
    def commonDom(cur, pred):
        if not cur: return pred
        if not pred: return cur
        while cur and pred and cur is not pred:
            if cur.num < pred.num:
                pred = immDom[pred]
            else:
                cur = immDom[cur]
        return cur
    immDom = dict([(n, None) for n in G.nodes])
    for node in sorted(G.nodes, key=lambda x: x.num):
        for pred in node.preds:
            if pred.num < node.num:
                immDom[node] = commonDom(immDom[node], pred)
    return immDom


def ConstructAST(basicblocks, exceptions):
    def build_node_from_bblock(bblock):
        node = Node()
        nodeBlock = Construct(node, bblock)
        bblockToNode[bblock] = node
        node.set_content(nodeBlock)
        nodegraph.append(node)
#        if bblock.exception_analysis:
#            Util.log("BBLOCK == %s" % bblock.name, 'debug')
#            build_exception(node, bblock)
        return node
        
    def build_exception(node, bblock):
        Util.log('Exceptions :', 'debug')
        for exception in bblock.exception_analysis.exceptions:
            Util.log('  => %s' % exception, 'debug')
            catchNode = bblockToNode.get(exception[-1])
            if catchNode is None:
                catchNode = Node()
                catchBlock = CatchBlock(catchNode, exception[-1],
                                        exception[0])
                bblockToNode[exception[-1]] = catchNode
                catchNode.set_content(catchBlock)
                nodegraph.append(catchNode)
            catchNode.num += 1
            node.content.add_catch(catchNode)
            node.add_node(catchNode)

    # Native methods,... no blocks.
    if len(basicblocks) < 1:
        return
    graph = BFS(basicblocks[0]) # Needed for now because of exceptions
    nodegraph = []

    # Construction of a mapping of basic blocks into Nodes
    bblockToNode = {}
    for bblock in graph:
        node = bblockToNode.get(bblock)
        if node is None:
            node = build_node_from_bblock(bblock)
        for child in bblock.childs: #[::-1] for rev post order right to left
            childNode = bblockToNode.get(child[-1])
            if childNode is None:
                childNode = build_node_from_bblock(child[-1]) 
            node.add_node(childNode)

    G = Graph(nodegraph, bblockToNode) 

    G.remove_jumps()

    Gi, Li = DerivedSequence(G)
    
    immdoms = BuildImmediateDominator(G)

    SwitchStruct(G, immdoms)

    LoopStruct(G, Gi, Li)

    IfStruct(G, immdoms)

    ShortCircuitStruct(G)

    WhileBlockStruct(G)

    if False:
    #if True:
        import string
        mmeth = basicblocks[0].get_method()
        dname = filter(lambda x: x in string.letters + string.digits,
                                                        mmeth.get_name())
        mname = mmeth.get_class_name().split('/')[-1][:-1] + '#' + dname
        for i, g in enumerate(Gi, 1):
            name = mname + '-%d' % i
            g.draw(dname, name)
    
    for node in G.nodes:
        for pred in node.preds:
            if node in pred.succs and node.num <= pred.num:
                pred.succs.remove(node)
    
    #ast = AST(G.first_node(), None)#invdoms)
    
    #if False:
    ##if True:
    #    import string
    #    mmeth = basicblocks[0].get_method()
    #    dname = filter(lambda x: x in string.letters + string.digits,
    #                                                    mmeth.get_name())
    #    mname = mmeth.get_class_name().split('/')[-1][:-1] + '#' + dname
    #    ast.draw(dname, mname)

    #return ast
    return G

