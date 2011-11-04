import Util
import Instruction
from start import Register

class Block(object):
    def __init__(self, node, block):
        self.block = block
        self.node = node

    def get_next(self):
        return self.next

    def process_cfg(self, succ, pred):
        self.next = succ.get(self.node)

    def process(self, memory, vars):
        #print 'Process not done :', self
        pass


class StatementBlock(Block):
    def __init__(self, node, block):
        super(StatementBlock, self).__init__(node, block)

    def process(self, memory, vars):
        lins, memory, res = process_block_ins(memory, vars, self.block)
        return res.dump() #get_value()

    def process_cfg(self, succ, pred):
        self.next = succ.get(self.node)
        if self.next:
            self.next = self.next[0]


class WhileBlock(Block):
    def __init__(self, node, block):
        super(WhileBlock, self).__init__(node, block)


class DoWhileBlock(Block):
    def __init__(self, node, block):
        super(DoWhileBlock, self).__init__(node, block)


class SwitchBlock(Block):
    def __init__(self, node, block):
        super(SwitchBlock, self).__init__(node, block)
        self.case = []
        for child in block.childs:
            self.case.append(Construct(node, child[-1]))


class TryBlock(Block):
    def __init__(self, node, block):
        super(TryBlock, self).__init__(node, block)
        self.catch = []
        for exception in block.exception_analysis.exceptions:
            self.catch.append(CatchBlock(node, exception[-1]))


class CatchBlock(Block):
    def __init__(self, node, block):
        super(CatchBlock, self).__init__(node, block)


def get_branch(node, succ, nodes=None):
    if nodes is None:
        nodes = set()
    nodes.add(node)
    for child in succ.get(node, []):
        if not child in nodes:
            nodes.update(get_branch(child, succ, nodes))
    return nodes


class IfBlock(Block):
    def __init__(self, node, block):
        super(IfBlock, self).__init__(node, block)
        self.true = None
        self.false = None

    def process_cfg(self, succ, pred):
        trueblocks = get_branch(succ.get(self.node)[1], succ)
        falseblocks = get_branch(succ.get(self.node)[0], succ)

        truebranch = trueblocks - falseblocks
        falsebranch = falseblocks - trueblocks
        
        Util.log('TRUEBRANCH : %s' % truebranch, 'debug')
        Util.log('FALSEBRANCH : %s' % falsebranch, 'debug')

        nextblock = None
        if len(truebranch) == 0:
            nextblock = succ.get(self.node)[1]
        elif len(falsebranch) == 0:
            nextblock = succ.get(self.node)[0]
        else:
            child = succ.get(self.node)[1]
            while truebranch and nextblock is None :
                for ch in succ.get(child):
                    if ch not in truebranch:
                        nextblock = ch
                    else:
                        truebranch.remove(ch)
                child = succ.get(child)[0]

        self.next = nextblock

        print "BLOCK:", self.block.name
        print "\tTRUE :",
        for node in truebranch:
            print node.content.block.name,
        print
        print "\tFALSE:",
        for node in falsebranch:
            print node.content.block.name,
        print
        print "NEXT:", self.next.content.block.name

#        ifblocks = trueblocks.union(falseblocks)
#        ifblocks.add(self.block)
        truebranch = trueblocks - falseblocks
        falsebranch = falseblocks - trueblocks
#        for block in ifblocks:
#            lsucc = [b for b in succ.get(block, [])]
#            for s in lsucc:
#                if s not in truebranch and s not in falsebranch:
#                    succ.get(block).remove(s)
#                    pred.get(s).remove(block)

        if len(truebranch) > 0:
            self.true = succ.get(self.node)[1]
        if len(falsebranch) > 0:
            self.false = succ.get(self.node)[0]

    def get_next(self):
        return self.next

    def process(self, memory, vars):
        indent = 1
        if self.true and self.false:
            lins, mem, res = process_block_ins(memory, vars, self.block)
            ins = 'if( %s ) {\n' % res.get_value()
            indent += 1
            vars.startBlock()
            res = self.true.process(memory, vars)
            vars.endBlock()
            ins += '    ' * indent + '%s' % res
            indent -= 1
            ins += '\n' + '    ' * indent + '} else {\n'
            indent += 1
            ins += '    ' * indent 
            vars.startBlock()
            res = self.false.process(memory, vars)
            vars.endBlock()
            ins += '%s' % res
            indent -= 1
            vars.endBlock()
        elif self.true:
            lins, mem, res = process_block_ins(memory, vars, self.block)
            ins = 'if( %s ) {\n' % res.get_value()
            res = self.true.process(memory, vars)
        else:
            lins, mem, res = process_block_ins(memory, vars, self.block)
            ins = 'if( !(%s) ) {\n' % res.get_value()
            res = self.false.process(memory, vars)
            indent += 1
            ins += '    ' * indent + '%s' % res
            indent -= 1
        ins += '\n' + '    ' * indent + '}'
        return ins


class ElseBlock(Block):
    def __init__(self, block):
        super(ElseBlock, self).__init__(block)


class Graph( ):
    def __init__(self, nodes, succ, preds, bblock):
        self.nodes = nodes
        self.succ = succ
        self.preds = preds
        self.tradBlock = bblock

    def getBlock(self, basicblock):
        return self.tradBlock.get(basicblock)

class Node( ):
    def __init__(self):
        self.content = None

    def add_node(self, node, succ, pred):
        succ.setdefault(self, []).append(node)
        pred.setdefault(node, []).append(self)

    def set_content(self, block):
        if self.content is None:
            self.content = block
        else:
            print "ERRRRRRRRR"
            exit()

    def process(self, memory, vars):
        return self.content.process(memory, vars)

    def get_next(self):
        return self.content.get_next()


def Construct(node, block):
    if block.exception_analysis:
        currentblock = TryBlock(node, block)
    else:
        #lastins = block.ins[-1]
        #if 'switch' in lastins.op_name
        if len(block.childs) > 2:
            currentblock = SwitchBlock(node, block)
        #elif 'if' in lastins.op_name:
        elif len(block.childs) == 2:
            currentblock = IfBlock(node, block)
        else:
            currentblock = StatementBlock(node, block)
    return currentblock

def process_block_ins(memory, variables, block):
    res = []
    for ins in block.get_ins():
#        heap = memory.get('heap')
        Util.log('Name : %s, Operands : %s' % (ins.get_name(), ins.get_operands()), 'debug')
        _ins = Instruction.INSTRUCTION_SET.get(ins.get_name().lower())
        if _ins == Instruction.Goto:
            continue
        else:
            newIns = _ins
        if newIns is None:
            Util.log('Unknown instruction : %s.' % ins.get_name().lower(), 'error')
            return res, memory, newIns
        newIns = newIns(ins.get_operands())
        #newIns.set_dest_dump([])
        newIns.emulate(memory)
        regnum = newIns.get_reg()
        if regnum is None:
            regnum = []
        newIns = variables.newVar(newIns.get_type(), newIns)
        if regnum:
            register = memory.get(regnum[0])
            if register is None:
                memory[regnum[0]] = Register(newIns, regnum[0])
                #if self.memory[regnum[0]].used:
                #    self.ins.append(newIns.dump())
            else:
                register.modify(newIns)
                # Case len(regnum) == 2 ?
        Util.log('---> newIns : %s, register : %s.\n' % (ins.get_name(), regnum), 'debug')
#        heapaft = memory.get('heap')
#        if heap is not None and heapaft is not None:
#            Util.log('Append : %s' % heap.get_value(), 'debug')
#            res.append(heap.get_value())
#            if heap == heapaft:
#                Util.log('HEAP = %s' % heap, 'debug')
#                Util.log('HEAPAFT = %s' % heapaft, 'debug')
#                memory['heap'] = None
    return res, memory, newIns

from Queue import Queue
def BFS(start):
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


def ConstructCFG(lsg, basicblocks, exceptions, blocks):
    graph = BFS(basicblocks[0])
    nodegraph = set()
    nodesucc = {}
    nodepred = {}

    bblockToBlock = {}
    for bblock in graph:
        nodeBlock = bblockToBlock.get(bblock)
        if nodeBlock is None:
            node = Node()
            nodeBlock = Construct(node, bblock)
            bblockToBlock[bblock] = nodeBlock
            node.set_content(nodeBlock)
            nodegraph.add(node)
        else:
            node = nodeBlock.node
        for child in bblock.childs:
            nodeBlock = bblockToBlock.get(child[-1])
            if nodeBlock is None:
                childnode = Node()
                nodeBlock = Construct(childnode, child[-1])
                bblockToBlock[child[-1]] = nodeBlock
                childnode.set_content(nodeBlock)
                nodegraph.add(childnode)
            node.add_node(nodeBlock.node, nodesucc, nodepred)

    print 'GRAPHNODE :'
    for node in nodegraph:
        print '\tNODE :\t', node.content.block.name, '(', node.content, ')'
        for child in nodesucc.get(node,[]):
            print '\t\t\tCHILD :', child.content.block.name, '(', child.content, ')'

#    print '============= PRED ==============='
#    for n in PRED.keys():
#        print '%s -> %s' % (n.name, [b.name for b in PRED[n]])
#    print '=================================='

#    if len(lsg.loops) > 1:
        # cfg loop
#        firstNode = None
#    else:
        # cfg normal
        
    for node in nodegraph:
        node.content.process_cfg(nodesucc, nodepred)

#    print '============= SUCC ==============='
#    for n in SUCC.keys():
#        print '%s -> %s' % (n.name, [b.name for b in SUCC[n]])
#    print '=================================='


    G = Graph(nodegraph, nodesucc, nodepred, bblockToBlock)
#    print 'STARTBLOCK :', firstNode, '(', firstNode.block, ')'
#    print 'NEXT :', bblockToBlock.get(firstNode.block.get_next())

    return G

