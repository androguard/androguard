import sys
sys.path.append('./')
import androguard
import analysis
import copy
import Instruction
import Util
#import Findloop
import Structure

class This():
    def __init__(self, cls):
        self.cls = cls

    def get_content(self):
        return self

    def get_type(self):
        return self.cls.name

    def get_value(self):
        return 'this'


class Register():
    def __init__(self, content, num):
        self.content = content
        self.nbuses = 0
        self.used = False
        self.num = num
        self.isPair = False

    def modify(self, ins):
        if self.used:
            self.dump(ins)
        self.content = ins
        self.nbuses = 0
        self.used = False

    def get_content(self):
        self.nbuses += 1
        if self.nbuses >= 1 and self.content.get_content():
            self.used = True
            Util.log('GET CONTENT -> USED TRUE (%s)' % self.content, 'debug')
        return self.content

    def get_content_dbg(self):
        return self.content

    def dump(self, ins):
        Util.log("""Register #%d Dump :
                ---------------
                Old value :
                %s
                -> %s
                -------
                New value :
                %s
                -> %s
                ---------------""" % (self.num, str(self.content),
                self.content.get_value(), str(ins), ins.get_value()), 'debug')

    def __deepcopy__(self, dic=None):
        d = dic.get(self, None)
        if d is None:
            r = Register(self.content, self.num)
            r.nbuses = self.nbuses
            r.used = self.used
            r.num = self.num
            r.isPair = self.isPair
            dic[self] = r
            return r
        return d

    def __str__(self):
        return 'Register number %d :\n\tused : %s\n\tcontent : %s\t\tvalue : %s.' % (
                self.num, self.used, str(self.content), str(self.content.get_value()))

    def __repr__(self):
        return repr(self.content)


class DvMethod():
    def __init__(self, methanalysis, this):
        self.memory = {}
        self.method = methanalysis.get_method()
        self.name = self.method.get_name()
        self.lparams = []
        self.variables = Instruction.Variable()
        
        if self.name == '<init>':
            self.name = self.method.get_class_name()[1:-1].split('/')[-1]
        self.basic_blocks = methanalysis.basic_blocks.bb
        code = self.method.get_code()

        access = self.method.get_access()
        self.access = [flag for flag in Util.ACCESS_FLAGS_METHODS if flag & access]
        desc = self.method.get_descriptor()
        self.type = Util.get_type(desc.split(')')[-1])
        self.paramsType = Util.get_params_type(desc)

        #Util.log('Searching loops in method %s' % self.name, 'debug')
        """
        Findloop.loopCounter = 0
        cfg = Findloop.CFG()
        lsg = Findloop.LSG()
        self.cfg = cfg
        self.lsg = lsg
        Findloop.AddEdges(cfg, self)
        nbLoops = Findloop.FindLoops(cfg, lsg)
        
        if nbLoops > 1:
            Util.log('==================', 'debug')
            Util.log('==== DUMP CFG ====', 'debug')
            cfg.dump()
            Util.log('==================', 'debug')
            Findloop.ShowBlocks(lsg, 0)
            Util.log('==== DUMP LSG ====', 'debug')
            lsg.dump()
            Util.log('==================', 'debug')
        """
        lsg = None
        blocks = []
        exceptions = methanalysis.exceptions.exceptions
        print "METHOD :", self.name
        self.graph = Structure.ConstructCFG(lsg, self.basic_blocks, exceptions, blocks)
        print

        #androguard.bytecode.method2png('graphs/%s#%s.png' % (self.method.get_class_name().split('/')[-1][:-1], self.name), methanalysis)

        if code is None:
            Util.log('CODE NONE : %s %s' % (self.name, self.method.get_class_name()), 'debug')
        else:
            start = code.registers_size.get_value() - code.ins_size.get_value()
            # 0x8 == Static case : this is not passed as a parameter
            if 0x8 in self.access:
                self._add_parameters(start)
            else:
                self.memory[start] = Register(this, start)
                #print 'THIS ( %s ) : %d' % (self.name, start)
                self._add_parameters(start + 1)
        self.ins = []
        self.cur = 0

    def _add_parameters(self, start):
        i = 1
        size = 0
        for paramType in self.paramsType:
            param = self.variables.newVar(paramType)
            param.param = True
            self.memory[start + size] = Register(param, start + size)
            self.lparams.append(param)
            size += param.size
            i += 1

    def process(self):
        startBlock = self.graph.getBlock(self.basic_blocks[0])
        firstNode = startBlock.node
        if firstNode is None:
            print "ARRRRRRRRRRRRRR"

        print "\nMETHOD :", self.name
        print "FIRSTNODE :", firstNode, firstNode.content, firstNode.content.block, firstNode.content.block.name
        next = firstNode.get_next()
        print "NEXT :", firstNode.content , '=>', next
        self.ins.append(firstNode.process(self.memory, self.variables))
        while next:
            self.ins.append(next.process(self.memory, self.variables))
            next = next.get_next()
            if next:
                print "=NEXT :", next, next.content.block.name#, [n.content.block.name for n in next]

        return self.debug()

    def debug(self, code=None):
        print "TEST :"
        for var in self.variables.vars:
            print "VAR ::", var
        if code is None:
            code = []
        Util.log('Dump of method :', 'debug')
        for j in self.memory.values():
            Util.log(j, 'debug')
        Util.log('Dump of ins :', 'debug')
        acc = []
        for i in self.access:
            if i == 0x10000:
                self.type = None
            else:
                acc.append(Util.ACCESS_FLAGS_METHODS.get(i))
        if self.type:
            proto = '%s %s %s(' % (' '.join(acc), self.type, self.name)
        else:
            proto = '%s %s(' % (' '.join(acc), self.name)
        if self.paramsType:
            proto += ', '.join(['%s' % param.decl() for param in self.lparams])
        proto += ') {'
        Util.log(proto, 'debug')
        code.append(proto)
        for var in self.variables.vars:
            if var.used and not var.param:
                code.append('    %s;' % var.decl())
        for i in self.ins:
            Util.log('%s' % i, 'debug')
            code.append('    %s' % i)
        Util.log('}', 'debug')
        code.append('}')
        return '\n'.join(code)

    def __repr__(self):
        return 'Method %s' % self.name


class DvClass():
    def __init__(self, dvclass, bca):
        self.name = dvclass.get_name()[1:-1].split('/')[-1]
        self.package = dvclass.get_name().rsplit('/', 1)[0][1:].replace('/', '.')
        self.this = This(self)
        lmethods = [(method.get_idx(), DvMethod(bca.get_method(method), self.this))
                    for method in dvclass.get_methods()]
        self.methods = dict(lmethods)
        self.fields = {}
        for field in dvclass.get_fields():
            self.fields[field.get_name()] = field
        self.access = []
        self.prototype = None
        self.subclasses = {}
        self.code = []
        self.inner = False

        Util.log('Class : %s' % self.name, 'log')
        Util.log('Methods added :', 'log')
        for index, meth in self.methods.iteritems():
            Util.log('%s (%s, %s)' % (index, meth.method.get_class_name(),
                                   meth.name), 'log')
        Util.log('\n', 'log')

        access = dvclass.format.get_value().access_flags
        access = [flag for flag in Util.ACCESS_FLAGS_CLASSES if flag & access]
        for i in access:
            self.access.append(Util.ACCESS_FLAGS_CLASSES.get(i))
        
        self.prototype = '%s class %s' % (' '.join(self.access), self.name)
        
        self.interfaces = dvclass._interfaces
        self.superclass = dvclass._sname

    def add_subclass(self, innername, dvclass):
        self.subclasses[innername] = dvclass
        dvclass.inner = True

    def get_methods(self):
        meths = copy.copy(self.methods)
        for cls in self.subclasses.values():
            meths.update(cls.get_methods())
        return meths

    def select_meth(self, nb):
        if nb in self.methods:
            self.code.append(self.methods[nb].process())
        elif self.subclasses.values():
            for cls in self.subclasses.values():
                cls.select_meth(nb)
        else:
            Util.log('Method %s not found.' % nb, 'error')

    def show_code(self):
        if not self.inner and self.package:
            Util.log('package %s;\n' % self.package, 'log')

        if self.superclass is not None:
            self.superclass = self.superclass[1:-1].replace('/', '.')
            if self.superclass.split('.')[-1] == 'Object':
                self.superclass = None
            if self.superclass is not None:
                self.prototype += ' extends %s' % self.superclass
        if self.interfaces is not None:
            self.interfaces = self.interfaces[1:-1].split(' ')
            self.prototype += ' implements %s' % ', '.join(
                            [n[1:-1].replace('/', '.') for n in self.interfaces])

        Util.log('%s {' % self.prototype, 'log')
        for field in self.fields.values():
            access =  [Util.ACCESS_FLAGS_FIELDS.get(flag) for flag in
                        Util.ACCESS_FLAGS_FIELDS if flag & field.get_access()]
            type = Util.get_type(field.get_descriptor())
            name = field.get_name()
            Util.log('\t%s %s %s;' % (' '.join(access), type, name), 'log')

        Util.log('', 'log')
        for cls in self.subclasses.values():
            cls.show_code()

        for ins in self.code:
            Util.log(ins, 'log')
        Util.log('}', 'log')

    def process(self):
        Util.log('SUBCLASSES : %s' % self.subclasses, 'debug')
        for cls in self.subclasses.values():
            cls.process()
        Util.log('METHODS : %s' % self.methods, 'debug')
        for meth in self.methods:
            self.select_meth(meth)

    def __str__(self):
        return 'Class name : %s.' % self.name

    def __repr__(self):
        if self.subclasses == {}:
            return 'Class(%s)' % self.name
        return 'Class(%s) -- Subclasses(%s)' % (self.name, self.subclasses)


class DvMachine():
    def __init__(self, name):
        vm = androguard.AndroguardS(name).get_vm()
        bca = analysis.VMAnalysis(vm)
        self.vm = vm
        self.bca = bca
        ldict = [(dvclass.get_name(), DvClass(dvclass, bca))
                 for dvclass in vm.get_classes()]
        self.classes = dict(ldict)
        Util.merge_inner(self.classes)

    def get_class(self, className):
        for name, cls in self.classes.iteritems():
            if className in name:
                return cls

    def process_class(self, cls):
        if cls is None:
            Util.log('No class to process.', 'error')
        else:
            cls.process()

    def process_method(self, cls, meth):
        if cls is None:
            Util.log('No class to process.', 'error')
        else:
            cls.select_meth(meth)

    def show_code(self, cls):
        if cls is None:
            Util.log('Class not found.', 'error')
        else:
            cls.show_code()


if __name__ == '__main__':
    try:
        TEST = open('examples/android/TestsAndroguard/bin/classes.dex')
    except IOError:
        TEST = open('../examples/android/TestsAndroguard/bin/classes.dex')
    TEST.close()

    Util.DEBUG_LEVEL = 'debug'

    MACHINE = DvMachine(TEST.name)

    from pprint import pprint
    temp = Util.wrap_stream()
    Util.log('===========================', 'log')
    Util.log('Classes :', 'log')
    pprint(MACHINE.classes, temp)
    Util.log(temp, 'log')
    Util.log('===========================', 'log')

    CLS = raw_input('Choose a class: ')
    if CLS == '*':
        for CLS in MACHINE.classes:
            Util.log('CLS : %s' % CLS, 'log')
            cls = MACHINE.get_class(CLS)
            if cls is None:
                Util.log('%s not found.' % CLS, 'error')
            else:
                MACHINE.process_class(cls)
        Util.log('\n\nDump of code:', 'log')
        Util.log('===========================', 'log')
        for CLS in MACHINE.classes:
            MACHINE.show_code(MACHINE.get_class(CLS))
            Util.log('===========================', 'log')
    else:
        cls = MACHINE.get_class(CLS)
        if cls is None:
            Util.log('%s not found.' % CLS, 'error')
        else:
            Util.log('======================', 'log')
            temp.clean()
            pprint(cls.get_methods(), temp)
            Util.log(temp, 'log')
            Util.log('======================', 'log')
            METH = raw_input('Method: ')
            if METH == '*':
                Util.log('CLASS = %s' % cls, 'log')
                MACHINE.process_class(cls)
            else:
                MACHINE.process_method(cls, int(METH))
            Util.log('\n\nDump of code:', 'log')
            Util.log('===========================', 'log')
            MACHINE.show_code(cls)
