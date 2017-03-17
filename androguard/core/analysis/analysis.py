from __future__ import print_function

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
import re, collections
import threading, queue, time


from androguard.core.androconf import error, warning, debug, is_ascii_problem,\
    load_api_specific_resource_module
from androguard.core.bytecodes import dvm
from androguard.core.bytecodes.api_permissions import DVM_PERMISSIONS_BY_PERMISSION, DVM_PERMISSIONS_BY_ELEMENT

class DVMBasicBlock(object):
    """
        A simple basic block of a dalvik method
    """

    def __init__(self, start, vm, method, context):
        self.__vm = vm
        self.method = method
        self.context = context

        self.last_length = 0
        self.nb_instructions = 0

        self.fathers = []
        self.childs = []

        self.start = start
        self.end = self.start

        self.special_ins = {}

        self.name = "%s-BB@0x%x" % (self.method.get_name(), self.start)
        self.exception_analysis = None

        self.notes = []

    def get_notes(self):
        return self.notes

    def set_notes(self, value):
        self.notes = [value]

    def add_note(self, note):
        self.notes.append(note)

    def clear_notes(self):
        self.notes = []

    def get_instructions(self):
        """
        Get all instructions from a basic block.

        :rtype: Return all instructions in the current basic block
      """
        tmp_ins = []
        idx = 0
        for i in self.method.get_instructions():
            if idx >= self.start and idx < self.end:
                tmp_ins.append(i)

            idx += i.get_length()
        return tmp_ins

    def get_nb_instructions(self):
        return self.nb_instructions

    def get_method(self):
        return self.method

    def get_name(self):
        return "%s-BB@0x%x" % (self.method.get_name(), self.start)

    def get_start(self):
        return self.start

    def get_end(self):
        return self.end

    def get_last(self):
        return self.get_instructions()[-1]

    def get_next(self):
        """
            Get next basic blocks

            :rtype: a list of the next basic blocks
        """
        return self.childs

    def get_prev(self):
        """
            Get previous basic blocks

            :rtype: a list of the previous basic blocks
        """
        return self.fathers

    def set_fathers(self, f):
        self.fathers.append(f)

    def get_last_length(self):
        return self.last_length

    def set_childs(self, values):
        #print self, self.start, self.end, values
        if values == []:
            next_block = self.context.get_basic_block(self.end + 1)
            if next_block != None:
                self.childs.append((self.end - self.get_last_length(), self.end,
                                    next_block))
        else:
            for i in values:
                if i != -1:
                    next_block = self.context.get_basic_block(i)
                    if next_block != None:
                        self.childs.append((self.end - self.get_last_length(),
                                            i, next_block))

        for c in self.childs:
            if c[2] != None:
                c[2].set_fathers((c[1], c[0], self))

    def push(self, i):
        self.nb_instructions += 1
        idx = self.end
        self.last_length = i.get_length()
        self.end += self.last_length

        op_value = i.get_op_value()

        if op_value == 0x26 or (op_value >= 0x2b and op_value <= 0x2c):
            code = self.method.get_code().get_bc()
            self.special_ins[idx] = code.get_ins_off(idx + i.get_ref_off() * 2)

    def get_special_ins(self, idx):
        """
            Return the associated instruction to a specific instruction (for example a packed/sparse switch)

            :param idx: the index of the instruction

            :rtype: None or an Instruction
        """
        try:
            return self.special_ins[idx]
        except:
            return None

    def get_exception_analysis(self):
        return self.exception_analysis

    def set_exception_analysis(self, exception_analysis):
        self.exception_analysis = exception_analysis

    def show(self):
        print(self.get_name(), self.get_start(), self.get_end())


class Enum(object):

    def __init__(self, names):
        self.names = names
        for value, name in enumerate(self.names):
            setattr(self, name.upper(), value)

    def tuples(self):
        return tuple(enumerate(self.names))


TAG_ANDROID = Enum(
    ['ANDROID', 'TELEPHONY', 'SMS', 'SMSMESSAGE', 'ACCESSIBILITYSERVICE',
     'ACCOUNTS', 'ANIMATION', 'APP', 'BLUETOOTH', 'CONTENT', 'DATABASE',
     'DEBUG', 'DRM', 'GESTURE', 'GRAPHICS', 'HARDWARE', 'INPUTMETHODSERVICE',
     'LOCATION', 'MEDIA', 'MTP', 'NET', 'NFC', 'OPENGL', 'OS', 'PREFERENCE',
     'PROVIDER', 'RENDERSCRIPT', 'SAX', 'SECURITY', 'SERVICE', 'SPEECH',
     'SUPPORT', 'TEST', 'TEXT', 'UTIL', 'VIEW', 'WEBKIT', 'WIDGET',
     'DALVIK_BYTECODE', 'DALVIK_SYSTEM', 'JAVA_REFLECTION'])

TAG_REVERSE_ANDROID = dict((i[0], i[1]) for i in TAG_ANDROID.tuples())

TAGS_ANDROID = {
    TAG_ANDROID.ANDROID: [0, "Landroid"],
    TAG_ANDROID.TELEPHONY: [0, "Landroid/telephony"],
    TAG_ANDROID.SMS: [0, "Landroid/telephony/SmsManager"],
    TAG_ANDROID.SMSMESSAGE: [0, "Landroid/telephony/SmsMessage"],
    TAG_ANDROID.DEBUG: [0, "Landroid/os/Debug"],
    TAG_ANDROID.ACCESSIBILITYSERVICE: [0, "Landroid/accessibilityservice"],
    TAG_ANDROID.ACCOUNTS: [0, "Landroid/accounts"],
    TAG_ANDROID.ANIMATION: [0, "Landroid/animation"],
    TAG_ANDROID.APP: [0, "Landroid/app"],
    TAG_ANDROID.BLUETOOTH: [0, "Landroid/bluetooth"],
    TAG_ANDROID.CONTENT: [0, "Landroid/content"],
    TAG_ANDROID.DATABASE: [0, "Landroid/database"],
    TAG_ANDROID.DRM: [0, "Landroid/drm"],
    TAG_ANDROID.GESTURE: [0, "Landroid/gesture"],
    TAG_ANDROID.GRAPHICS: [0, "Landroid/graphics"],
    TAG_ANDROID.HARDWARE: [0, "Landroid/hardware"],
    TAG_ANDROID.INPUTMETHODSERVICE: [0, "Landroid/inputmethodservice"],
    TAG_ANDROID.LOCATION: [0, "Landroid/location"],
    TAG_ANDROID.MEDIA: [0, "Landroid/media"],
    TAG_ANDROID.MTP: [0, "Landroid/mtp"],
    TAG_ANDROID.NET: [0, "Landroid/net"],
    TAG_ANDROID.NFC: [0, "Landroid/nfc"],
    TAG_ANDROID.OPENGL: [0, "Landroid/opengl"],
    TAG_ANDROID.OS: [0, "Landroid/os"],
    TAG_ANDROID.PREFERENCE: [0, "Landroid/preference"],
    TAG_ANDROID.PROVIDER: [0, "Landroid/provider"],
    TAG_ANDROID.RENDERSCRIPT: [0, "Landroid/renderscript"],
    TAG_ANDROID.SAX: [0, "Landroid/sax"],
    TAG_ANDROID.SECURITY: [0, "Landroid/security"],
    TAG_ANDROID.SERVICE: [0, "Landroid/service"],
    TAG_ANDROID.SPEECH: [0, "Landroid/speech"],
    TAG_ANDROID.SUPPORT: [0, "Landroid/support"],
    TAG_ANDROID.TEST: [0, "Landroid/test"],
    TAG_ANDROID.TEXT: [0, "Landroid/text"],
    TAG_ANDROID.UTIL: [0, "Landroid/util"],
    TAG_ANDROID.VIEW: [0, "Landroid/view"],
    TAG_ANDROID.WEBKIT: [0, "Landroid/webkit"],
    TAG_ANDROID.WIDGET: [0, "Landroid/widget"],
    TAG_ANDROID.DALVIK_BYTECODE: [0, "Ldalvik/bytecode"],
    TAG_ANDROID.DALVIK_SYSTEM: [0, "Ldalvik/system"],
    TAG_ANDROID.JAVA_REFLECTION: [0, "Ljava/lang/reflect"],
}


class Tags(object):
    """
      Handle specific tags

      :param patterns:
      :params reverse:
  """

    def __init__(self, patterns=TAGS_ANDROID, reverse=TAG_REVERSE_ANDROID):
        self.tags = set()

        self.patterns = patterns
        self.reverse = TAG_REVERSE_ANDROID

        for i in self.patterns:
            self.patterns[i][1] = re.compile(self.patterns[i][1])

    def emit(self, method):
        for i in self.patterns:
            if self.patterns[i][0] == 0:
                if self.patterns[i][1].search(method.get_class()) != None:
                    self.tags.add(i)

    def emit_by_classname(self, classname):
        for i in self.patterns:
            if self.patterns[i][0] == 0:
                if self.patterns[i][1].search(classname) != None:
                    self.tags.add(i)

    def get_list(self):
        return [self.reverse[i] for i in self.tags]

    def __contains__(self, key):
        return key in self.tags

    def __str__(self):
        return str([self.reverse[i] for i in self.tags])

    def empty(self):
        return self.tags == set()


class BasicBlocks(object):
    """
        This class represents all basic blocks of a method
    """

    def __init__(self, _vm):
        self.__vm = _vm
        self.bb = []

    def push(self, bb):
        self.bb.append(bb)

    def pop(self, idx):
        return self.bb.pop(idx)

    def get_basic_block(self, idx):
        for i in self.bb:
            if idx >= i.get_start() and idx < i.get_end():
                return i
        return None

    def get(self):
        """
            :rtype: return each basic block (:class:`DVMBasicBlock` object)
        """
        for i in self.bb:
            yield i

    def gets(self):
        """
            :rtype: a list of basic blocks (:class:`DVMBasicBlock` objects)
        """
        return self.bb

    def get_basic_block_pos(self, idx):
        return self.bb[idx]


class ExceptionAnalysis(object):

    def __init__(self, exception, bb):
        self.start = exception[0]
        self.end = exception[1]

        self.exceptions = exception[2:]

        for i in self.exceptions:
            i.append(bb.get_basic_block(i[1]))

    def show_buff(self):
        buff = "%x:%x\n" % (self.start, self.end)

        for i in self.exceptions:
            if i[2] == None:
                buff += "\t(%s -> %x %s)\n" % (i[0], i[1], i[2])
            else:
                buff += "\t(%s -> %x %s)\n" % (i[0], i[1], i[2].get_name())

        return buff[:-1]

    def get(self):
        d = {"start": self.start, "end": self.end, "list": []}

        for i in self.exceptions:
            d["list"].append({"name": i[0], "idx": i[1], "bb": i[2].get_name()})

        return d


class Exceptions(object):

    def __init__(self, _vm):
        self.__vm = _vm
        self.exceptions = []

    def add(self, exceptions, basic_blocks):
        for i in exceptions:
            self.exceptions.append(ExceptionAnalysis(i, basic_blocks))

    def get_exception(self, addr_start, addr_end):
        for i in self.exceptions:
            #            print hex(i.start), hex(i.end), hex(addr_start), hex(addr_end), i.start >= addr_start and i.end <= addr_end, addr_end <= i.end and addr_start >= i.start
            if i.start >= addr_start and i.end <= addr_end:
                return i

            elif addr_end <= i.end and addr_start >= i.start:
                return i

        return None

    def gets(self):
        return self.exceptions

    def get(self):
        for i in self.exceptions:
            yield i


BasicOPCODES = []
for i in dvm.BRANCH_DVM_OPCODES:
    BasicOPCODES.append(re.compile(i))


class MethodAnalysis(object):
    """
        This class analyses in details a method of a class/dex file

        :type vm: a :class:`DalvikVMFormat` object
        :type method: a :class:`EncodedMethod` object
    """

    def __init__(self, vm, method):
        self.__vm = vm
        self.method = method

        self.basic_blocks = BasicBlocks(self.__vm)
        self.exceptions = Exceptions(self.__vm)

        code = self.method.get_code()
        if code == None:
            return

        current_basic = DVMBasicBlock(0, self.__vm, self.method, self.basic_blocks)
        self.basic_blocks.push(current_basic)

        ##########################################################

        bc = code.get_bc()
        l = []
        h = {}
        idx = 0

        debug("Parsing instructions")
        instructions = [i for i in bc.get_instructions()]
        for i in instructions:
            for j in BasicOPCODES:
                if j.match(i.get_name()) != None:
                    v = dvm.determineNext(i, idx, self.method)
                    h[idx] = v
                    l.extend(v)
                    break

            idx += i.get_length()

        debug("Parsing exceptions")
        excepts = dvm.determineException(self.__vm, self.method)
        for i in excepts:
            l.extend([i[0]])
            for handler in i[2:]:
                l.append(handler[1])

        debug("Creating basic blocks in %s" % self.method)
        idx = 0
        for i in instructions:
            # index is a destination
            if idx in l:
                if current_basic.get_nb_instructions() != 0:
                    current_basic = DVMBasicBlock(current_basic.get_end(),
                                                  self.__vm, self.method,
                                                  self.basic_blocks)
                    self.basic_blocks.push(current_basic)

            current_basic.push(i)

            # index is a branch instruction
            if idx in h:
                current_basic = DVMBasicBlock(current_basic.get_end(),
                                              self.__vm, self.method,
                                              self.basic_blocks)
                self.basic_blocks.push(current_basic)

            idx += i.get_length()

        if current_basic.get_nb_instructions() == 0:
            self.basic_blocks.pop(-1)

        debug("Settings basic blocks childs")

        for i in self.basic_blocks.get():
            try:
                i.set_childs(h[i.end - i.get_last_length()])
            except KeyError:
                i.set_childs([])

        debug("Creating exceptions")

        # Create exceptions
        self.exceptions.add(excepts, self.basic_blocks)

        for i in self.basic_blocks.get():
            # setup exception by basic block
            i.set_exception_analysis(self.exceptions.get_exception(i.start,
                                                                   i.end - 1))

        del instructions
        del h, l

    def get_basic_blocks(self):
        """
            :rtype: a :class:`BasicBlocks` object
        """
        return self.basic_blocks

    def get_length(self):
        """
            :rtype: an integer which is the length of the code
        """
        return self.get_code().get_length()

    def get_vm(self):
        return self.__vm

    def get_method(self):
        return self.method

    def show(self):
        print("METHOD", self.method.get_class_name(), self.method.get_name(
        ), self.method.get_descriptor())

        for i in self.basic_blocks.get():
            print("\t", i)
            i.show()
            print("")

    def show_methods(self):
        print("\t #METHODS :")
        for i in self.__bb:
            methods = i.get_methods()
            for method in methods:
                print("\t\t-->", method.get_class_name(), method.get_name(
                ), method.get_descriptor())
                for context in methods[method]:
                    print("\t\t\t |---|", context.details)

    def get_tags(self):
        """
          Return the tags of the method

          :rtype: a :class:`Tags` object
      """
        return self.tags


class StringAnalysis(object):

    def __init__(self, value):
        self.value = value
        self.orig_value = value
        self.xreffrom = set()

    def AddXrefFrom(self, classobj, methodobj):
        #debug("Added strings xreffrom for %s to %s" % (self.value, methodobj))
        self.xreffrom.add((classobj, methodobj))

    def get_xref_from(self):
        return self.xreffrom

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_orig_value(self):
        return self.orig_value

    def __str__(self):
        data = "XREFto for string %s in\n" % repr(self.get_value())
        for ref_class, ref_method in self.xreffrom:
            data += "%s:%s\n" % (ref_class.get_vm_class().get_name(), ref_method
                                )
        return data


class MethodClassAnalysis(object):

    def __init__(self, method):
        self.method = method
        self.xrefto = set()
        self.xreffrom = set()

    def AddXrefTo(self, classobj, methodobj, offset):
        #debug("Added method xrefto for %s [%s] to %s" % (self.method, classobj, methodobj))
        self.xrefto.add((classobj, methodobj, offset))

    def AddXrefFrom(self, classobj, methodobj, offset):
        #debug("Added method xreffrom for %s [%s] to %s" % (self.method, classobj, methodobj))
        self.xreffrom.add((classobj, methodobj, offset))

    def get_xref_from(self):
        return self.xreffrom

    def get_xref_to(self):
        return self.xrefto

    def __str__(self):
        data = "XREFto for %s\n" % self.method
        for ref_class, ref_method, offset in self.xrefto:
            data += "in\n"
            data += "%s:%s @0x%x\n" % (ref_class.get_vm_class().get_name(), ref_method, offset
                                )

        data += "XREFFrom for %s\n" % self.method
        for ref_class, ref_method, offset in self.xreffrom:
            data += "in\n"
            data += "%s:%s @0x%x\n" % (ref_class.get_vm_class().get_name(), ref_method, offset
                                )

        return data


class FieldClassAnalysis(object):

    def __init__(self, field):
        self.field = field
        self.xrefread = set()
        self.xrefwrite = set()

    def AddXrefRead(self, classobj, methodobj):
        #debug("Added method xrefto for %s [%s] to %s" % (self.method, classobj, methodobj))
        self.xrefread.add((classobj, methodobj))

    def AddXrefWrite(self, classobj, methodobj):
        #debug("Added method xreffrom for %s [%s] to %s" % (self.method, classobj, methodobj))
        self.xrefwrite.add((classobj, methodobj))

    def get_xref_read(self):
        return self.xrefread

    def get_xref_write(self):
        return self.xrefwrite

    def __str__(self):
        data = "XREFRead for %s\n" % self.field
        for ref_class, ref_method in self.xrefread:
            data += "in\n"
            data += "%s:%s\n" % (ref_class.get_vm_class().get_name(), ref_method
                                )

        data += "XREFWrite for %s\n" % self.field
        for ref_class, ref_method in self.xrefwrite:
            data += "in\n"
            data += "%s:%s\n" % (ref_class.get_vm_class().get_name(), ref_method
                                )

        return data

REF_NEW_INSTANCE = 0
REF_CLASS_USAGE = 1

class ExternalClass(object):
    def __init__(self, name):
        self.name = name
        self.methods = {}

    def GetMethod(self, name, descriptor):
        key = name + str(descriptor)
        if key not in self.methods:
            self.methods[key] = ExternalMethod(self.name, name, descriptor)

        return self.methods[key]

class ExternalMethod(object):
    def __init__(self, class_name, name, descriptor):
        self.class_name = class_name
        self.name = name
        self.descriptor = descriptor

    def get_name(self):
        return self.name

    def get_class_name(self):
        return self.class_name

    def get_descriptor(self):
        return ''.join(self.descriptor)

    def __str__(self):
        return "%s->%s%s" % (self.class_name, self.name, ''.join(self.descriptor))

class ClassAnalysis(object):

    def __init__(self, classobj, internal=False):
        self.orig_class = classobj
        self._inherits_methods = {}
        self._methods = {}
        self._fields = {}
        self.internal = internal

        self.xrefto = collections.defaultdict(set)
        self.xreffrom = collections.defaultdict(set)

    def get_methods(self):
        return list(self._methods.values())

    def get_nb_methods(self):
        return len(self._methods)

    def get_method_analysis(self, method):
        return self._methods.get(method)

    def get_field_analysis(self, field):
        return self._fields.get(field)

    def GetFakeMethod(self, name, descriptor):
        if not self.internal:
            return self.orig_class.GetMethod(name, descriptor)

        # We are searching an unknown method in this class
        # It could be something that the class herits
        key = name + str(descriptor)
        if key not in self._inherits_methods:
            self._inherits_methods[key] = ExternalMethod(self.orig_class.get_name(), name, descriptor)
        return self._inherits_methods[key]

    def AddFXrefRead(self, method, classobj, field):
        if field not in self._fields:
            self._fields[field] = FieldClassAnalysis(field)
        self._fields[field].AddXrefRead(classobj, method)

    def AddFXrefWrite(self, method, classobj, field):
        if field not in self._fields:
            self._fields[field] = FieldClassAnalysis(field)
        self._fields[field].AddXrefWrite(classobj, method)

    def AddMXrefTo(self, method1, classobj, method2, offset):
        if method1 not in self._methods:
            self._methods[method1] = MethodClassAnalysis(method1)
        self._methods[method1].AddXrefTo(classobj, method2, offset)

    def AddMXrefFrom(self, method1, classobj, method2, offset):
        if method1 not in self._methods:
            self._methods[method1] = MethodClassAnalysis(method1)
        self._methods[method1].AddXrefFrom(classobj, method2, offset)

    def AddXrefTo(self, ref_kind, classobj, methodobj, offset):
        self.xrefto[classobj].add((ref_kind, methodobj, offset))

    def AddXrefFrom(self, ref_kind, classobj, methodobj, offset):
        self.xreffrom[classobj].add((ref_kind, methodobj, offset))

    def get_xref_from(self):
        return self.xreffrom

    def get_xref_to(self):
        return self.xrefto

    def get_vm_class(self):
        return self.orig_class

    def __str__(self):
        # Print only instanceiations from other classes here
        # TODO also method xref and field xref should be printed?
        data = "XREFto for %s\n" % self.orig_class
        for ref_class in self.xrefto:
            data += str(ref_class.get_vm_class().get_name()) + " "
            data += "in\n"
            for ref_kind, ref_method, ref_offset in self.xrefto[ref_class]:
                data += "%d %s 0x%x\n" % (ref_kind, ref_method, ref_offset)

            data += "\n"

        data += "XREFFrom for %s\n" % self.orig_class
        for ref_class in self.xreffrom:
            data += str(ref_class.get_vm_class().get_name()) + " "
            data += "in\n"
            for ref_kind, ref_method, ref_offset in self.xreffrom[ref_class]:
                data += "%d %s 0x%x\n" % (ref_kind, ref_method, ref_offset)

            data += "\n"

        return data


class Analysis(object):

    def __init__(self, vm):
        self.vms = [vm]
        self.classes = {}
        self.strings = {}

        for current_class in vm.get_classes():
            self.classes[current_class.get_name()] = ClassAnalysis(
                current_class, True)

    def create_xref(self):
        debug("Creating XREF/DREF")
        started_at = time.time()

        instances_class_name = list(self.classes.keys())

        queue_classes = queue.Queue()
        last_vm = self.vms[-1]
        for current_class in last_vm.get_classes():
            queue_classes.put(current_class)

        threads = []
        # TODO maybe adjust this number by the 
        # number of cores or make it configureable?
        for n in range(2):
            thread = threading.Thread(target=self._create_xref, args=(instances_class_name, last_vm, queue_classes))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        debug("Waiting all threads")
        queue_classes.join()

        debug("")
        diff = time.time() - started_at
        debug("End of creating XREF/DREF {:.0f}:{:.2f}".format(*divmod(diff, 60)))

    def _create_xref(self, instances_class_name, last_vm, queue_classes):
        while not queue_classes.empty():
            current_class = queue_classes.get()
            debug("Creating XREF/DREF for %s" % current_class.get_name())
            for current_method in current_class.get_methods():
                debug("Creating XREF for %s" % current_method)

                code = current_method.get_code()
                if code == None:
                    continue

                off = 0
                bc = code.get_bc()
                try:
                    for instruction in bc.get_instructions():
                        op_value = instruction.get_op_value()
                        if op_value in [0x1c, 0x22]:
                            idx_type = instruction.get_ref_kind()
                            type_info = last_vm.get_cm_type(idx_type)

                            # Internal xref related to class manipulation
                            if type_info in instances_class_name and type_info != current_class.get_name(
                            ):
                                # new instance
                                if op_value == 0x22:
                                    self.classes[current_class.get_name(
                                    )].AddXrefTo(REF_NEW_INSTANCE,
                                                 self.classes[type_info],
                                                 current_method, off)
                                    self.classes[type_info].AddXrefFrom(
                                        REF_NEW_INSTANCE,
                                        self.classes[current_class.get_name()],
                                        current_method, off)
                                # class reference
                                else:
                                    self.classes[current_class.get_name(
                                    )].AddXrefTo(REF_CLASS_USAGE,
                                                 self.classes[type_info],
                                                 current_method, off)
                                    self.classes[type_info].AddXrefFrom(
                                        REF_CLASS_USAGE,
                                        self.classes[current_class.get_name()],
                                        current_method, off)

                        elif ((op_value >= 0x6e and op_value <= 0x72) or
                              (op_value >= 0x74 and op_value <= 0x78)):
                            idx_meth = instruction.get_ref_kind()
                            method_info = last_vm.get_cm_method(idx_meth)
                            if method_info:
                                class_info = method_info[0]

                                method_item = last_vm.get_method_descriptor(
                                    method_info[0], method_info[1],
                                    ''.join(method_info[2]))

                                # Seems to be an external classes
                                if not method_item:
                                    if method_info[0] not in self.classes:
                                        self.classes[method_info[0]] = ClassAnalysis(ExternalClass(method_info[0]), False)
                                    method_item = self.classes[method_info[0]].GetFakeMethod(method_info[1], method_info[2])


                                if method_item:
                                    self.classes[current_class.get_name(
                                    )].AddMXrefTo(current_method,
                                                  self.classes[class_info],
                                                  method_item,
                                                  off)
                                    self.classes[class_info].AddMXrefFrom(
                                        method_item,
                                        self.classes[current_class.get_name()],
                                        current_method,
                                        off)

                                    # Internal xref related to class manipulation
                                    if class_info in instances_class_name and class_info != current_class.get_name(
                                    ):
                                        self.classes[current_class.get_name(
                                        )].AddXrefTo(REF_CLASS_USAGE,
                                                     self.classes[class_info],
                                                     method_item, off)
                                        self.classes[class_info].AddXrefFrom(
                                            REF_CLASS_USAGE,
                                            self.classes[current_class.get_name()],
                                            current_method, off)

                        elif op_value >= 0x1a and op_value <= 0x1b:
                            string_value = last_vm.get_cm_string(
                                instruction.get_ref_kind())
                            if string_value not in self.strings:
                                self.strings[string_value] = StringAnalysis(
                                    string_value)
                            self.strings[string_value].AddXrefFrom(
                                self.classes[current_class.get_name()],
                                current_method)

                        elif op_value >= 0x52 and op_value <= 0x6d:
                            idx_field = instruction.get_ref_kind()
                            field_info = last_vm.get_cm_field(idx_field)
                            field_item = last_vm.get_field_descriptor(
                                field_info[0], field_info[2], field_info[1])
                            if field_item:
                                # read access to a field
                                if (op_value >= 0x52 and op_value <= 0x58) or (
                                        op_value >= 0x60 and op_value <= 0x66):
                                    self.classes[current_class.get_name(
                                    )].AddFXrefRead(
                                        current_method,
                                        self.classes[current_class.get_name()],
                                        field_item)
                                # write access to a field
                                else:
                                    self.classes[current_class.get_name(
                                    )].AddFXrefWrite(
                                        current_method,
                                        self.classes[current_class.get_name()],
                                        field_item)

                        off += instruction.get_length()
                except dvm.InvalidInstruction as e:
                    warning("Invalid instruction %s" % str(e))
            queue_classes.task_done()

    def get_method(self, method):
        for vm in self.vms:
            if method in vm.get_methods():
                return MethodAnalysis(vm, method)
        return None

    def get_method_by_name(self, class_name, method_name, method_descriptor):
        if class_name in self.classes:
            for method in self.classes[class_name].get_vm_class().get_methods():
                if method.get_name() == method_name and method.get_descriptor(
                ) == method_descriptor:
                    return method
        return None

    def get_method_analysis(self, method):
        class_analysis = self.get_class_analysis(method.get_class_name())
        if class_analysis:
            return class_analysis.get_method_analysis(method)
        return None

    def get_method_analysis_by_name(self, class_name, method_name, method_descriptor):
        method = self.get_method_by_name(class_name, method_name, method_descriptor)
        if method:
            return self.get_method_analysis(method)
        return None

    def get_field_analysis(self, field):
        class_analysis = self.get_class_analysis(field.get_class_name())
        if class_analysis:
            return class_analysis.get_field_analysis(field)
        return None

    def is_class_present(self, class_name):
        return class_name in self.classes

    def get_class_analysis(self, class_name):
        return self.classes.get(class_name)

    def get_external_classes(self):
        for i in self.classes:
            if not self.classes[i].internal:
                yield self.classes[i]

    def get_strings_analysis(self):
        return self.strings

    def add(self, vm):
        self.vms.append(vm)

        for current_class in vm.get_classes():
            if current_class.get_name() not in self.classes:
                self.classes[current_class.get_name()] = ClassAnalysis(
                    current_class, True)

def is_ascii_obfuscation(vm):
    for classe in vm.get_classes():
        if is_ascii_problem(classe.get_name()):
            return True
        for method in classe.get_methods():
            if is_ascii_problem(method.get_name()):
                return True
    return False
