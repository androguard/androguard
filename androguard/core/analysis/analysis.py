from __future__ import print_function
from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
import re
import collections
import multiprocessing
import queue
import time
from androguard.core.androconf import is_ascii_problem
from androguard.core.bytecodes import dvm
import logging

log = logging.getLogger("androguard.analysis")


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

        self.__cached_instructions = None

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
            if self.start <= idx < self.end:
                yield i
            idx += i.get_length()

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
        # print self, self.start, self.end, values
        if not values:
            next_block = self.context.get_basic_block(self.end + 1)
            if next_block is not None:
                self.childs.append((self.end - self.get_last_length(), self.end,
                                    next_block))
        else:
            for i in values:
                if i != -1:
                    next_block = self.context.get_basic_block(i)
                    if next_block is not None:
                        self.childs.append((self.end - self.get_last_length(),
                                            i, next_block))

        for c in self.childs:
            if c[2] is not None:
                c[2].set_fathers((c[1], c[0], self))

    def push(self, i):
        self.nb_instructions += 1
        idx = self.end
        self.last_length = i.get_length()
        self.end += self.last_length

        op_value = i.get_op_value()

        if op_value == 0x26 or (0x2b <= op_value <= 0x2c):
            code = self.method.get_code().get_bc()
            self.special_ins[idx] = code.get_ins_off(idx + i.get_ref_off() * 2)

    def get_special_ins(self, idx):
        """
            Return the associated instruction to a specific instruction (for example a packed/sparse switch)

            :param idx: the index of the instruction

            :rtype: None or an Instruction
        """
        if idx in self.special_ins:
            return self.special_ins[idx]
        else:
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
                if self.patterns[i][1].search(method.get_class()) is not None:
                    self.tags.add(i)

    def emit_by_classname(self, classname):
        for i in self.patterns:
            if self.patterns[i][0] == 0:
                if self.patterns[i][1].search(classname) is not None:
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
            if i.get_start() <= idx < i.get_end():
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
            if i[2] is None:
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

    def __init__(self, vm, method):
        """
        This class analyses in details a method of a class/dex file

        :type vm: a :class:`DalvikVMFormat` object
        :type method: a :class:`EncodedMethod` object
        """
        self.__vm = vm
        self.method = method

        self.basic_blocks = BasicBlocks(self.__vm)
        self.exceptions = Exceptions(self.__vm)

        self.code = self.method.get_code()
        if self.code:
            self._create_basic_block()

    def _create_basic_block(self):
        current_basic = DVMBasicBlock(0, self.__vm, self.method, self.basic_blocks)
        self.basic_blocks.push(current_basic)

        bc = self.code.get_bc()
        l = []
        h = {}
        idx = 0

        log.debug("Parsing instructions")
        for i in bc.get_instructions():
            for j in BasicOPCODES:
                if j.match(i.get_name()) is not None:
                    v = dvm.determineNext(i, idx, self.method)
                    h[idx] = v
                    l.extend(v)
                    break

            idx += i.get_length()

        log.debug("Parsing exceptions")
        excepts = dvm.determineException(self.__vm, self.method)
        for i in excepts:
            l.extend([i[0]])
            for handler in i[2:]:
                l.append(handler[1])

        log.debug("Creating basic blocks in %s" % self.method)
        idx = 0
        for i in bc.get_instructions():
            # index is a destination
            if idx in l:
                if current_basic.get_nb_instructions() != 0:
                    current_basic = DVMBasicBlock(current_basic.get_end(), self.__vm, self.method, self.basic_blocks)
                    self.basic_blocks.push(current_basic)

            current_basic.push(i)

            # index is a branch instruction
            if idx in h:
                current_basic = DVMBasicBlock(current_basic.get_end(), self.__vm, self.method, self.basic_blocks)
                self.basic_blocks.push(current_basic)

            idx += i.get_length()

        if current_basic.get_nb_instructions() == 0:
            self.basic_blocks.pop(-1)

        log.debug("Settings basic blocks childs")

        for i in self.basic_blocks.get():
            try:
                i.set_childs(h[i.end - i.get_last_length()])
            except KeyError:
                i.set_childs([])

        log.debug("Creating exceptions")

        # Create exceptions
        self.exceptions.add(excepts, self.basic_blocks)

        for i in self.basic_blocks.get():
            # setup exception by basic block
            i.set_exception_analysis(self.exceptions.get_exception(i.start, i.end - 1))

    def get_basic_blocks(self):
        """
            :rtype: a :class:`BasicBlocks` object
        """
        return self.basic_blocks

    def get_length(self):
        """
            :rtype: an integer which is the length of the code
        """
        return self.code.get_length() if self.code else 0

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

    def __repr__(self):
        return "<analysis.MethodAnalysis {}>".format(self.method)


class StringAnalysis(object):
    def __init__(self, value):
        """
        StringAnalysis contains the XREFs of a string.

        As Strings are only used as a source, they only contain
        the XREF_FROM set, i.e. where the string is used.

        This Array stores the information in which method the String is used.
        """
        self.value = value
        self.orig_value = value
        self.xreffrom = set()

    def AddXrefFrom(self, classobj, methodobj):
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
            data += "%s:%s\n" % (ref_class.get_vm_class().get_name(), ref_method)
        return data

    def __repr__(self):
        # TODO should remove all chars that are not pleasent. e.g. newlines
        if len(self.get_value()) > 20:
            s = "'{}'...".format(self.get_value()[:20])
        else:
            s = "'{}'".format(self.get_value())
        return "<analysis.StringAnalysis {}>".format(s)


class MethodClassAnalysis(object):
    def __init__(self, method):
        """
        MethodClassAnalysis contains the XREFs for a given method.

        Both referneces to other methods (XREF_TO) as well as methods calling
        this method (XREF_FROM) are saved.

        :param method: `dvm.EncodedMethod`
        """
        self.method = method
        self.xrefto = set()
        self.xreffrom = set()

    def AddXrefTo(self, classobj, methodobj, offset):
        self.xrefto.add((classobj, methodobj, offset))

    def AddXrefFrom(self, classobj, methodobj, offset):
        self.xreffrom.add((classobj, methodobj, offset))

    def get_xref_from(self):
        return self.xreffrom

    def get_xref_to(self):
        return self.xrefto

    def get_method(self):
        return self.method

    def __str__(self):
        data = "XREFto for %s\n" % self.method
        for ref_class, ref_method, offset in self.xrefto:
            data += "in\n"
            data += "%s:%s @0x%x\n" % (ref_class.get_vm_class().get_name(), ref_method, offset)

        data += "XREFFrom for %s\n" % self.method
        for ref_class, ref_method, offset in self.xreffrom:
            data += "in\n"
            data += "%s:%s @0x%x\n" % (ref_class.get_vm_class().get_name(), ref_method, offset)

        return data

    def __repr__(self):
        return "<analysis.MethodClassAnalysis {}{}>".format(self.method,
                " EXTERNAL" if isinstance(self.method, ExternalMethod) else "")


class FieldClassAnalysis(object):
    def __init__(self, field):
        """
        FieldClassAnalysis contains the XREFs for a class field.

        Instead of using XREF_FROM/XREF_TO, this object has methods for READ and
        WRITE access to the field.

        That means, that it will show you, where the field is read or written.

        :param field: `dvm.EncodedField`
        """
        self.field = field
        self.xrefread = set()
        self.xrefwrite = set()

    def AddXrefRead(self, classobj, methodobj):
        self.xrefread.add((classobj, methodobj))

    def AddXrefWrite(self, classobj, methodobj):
        self.xrefwrite.add((classobj, methodobj))

    def get_xref_read(self):
        return self.xrefread

    def get_xref_write(self):
        return self.xrefwrite

    def get_field(self):
        return self.field

    def __str__(self):
        data = "XREFRead for %s\n" % self.field
        for ref_class, ref_method in self.xrefread:
            data += "in\n"
            data += "%s:%s\n" % (ref_class.get_vm_class().get_name(), ref_method)

        data += "XREFWrite for %s\n" % self.field
        for ref_class, ref_method in self.xrefwrite:
            data += "in\n"
            data += "%s:%s\n" % (ref_class.get_vm_class().get_name(), ref_method)

        return data

    def __repr__(self):
        return "<analysis.FieldClassAnalysis {}->{}>".format(self.field.class_name, self.field.name)


REF_NEW_INSTANCE = 0
REF_CLASS_USAGE = 1


class ExternalClass:
    def __init__(self, name):
        """
        The ExternalClass is used for all classes that are not defined in the
        DEX file, thus are external classes.
        """
        self.name = name
        self.methods = {}

    def get_methods(self):
        return self.methods.values()

    def GetMethod(self, name, descriptor):
        key = name + str(descriptor)
        if key not in self.methods:
            self.methods[key] = ExternalMethod(self.name, name, descriptor)

        return self.methods[key]

    def get_name(self):
        """
        Returns the name of the ExternalClass object
        """
        return self.name

    def __repr__(self):
        return "<analysis.ExternalClass {}>".format(self.name)


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

    def get_access_flags_string(self):
        # TODO can we assume that external methods are always public?
        # they can also be static...
        # or constructor...
        return ""

    def __str__(self):
        return "%s->%s%s" % (self.class_name, self.name, ''.join(self.descriptor))

    def __repr__(self):
        return "<analysis.ExternalMethod {}>".format(self.__str__())


class ClassAnalysis(object):
    def __init__(self, classobj, internal=False):
        """
        ClassAnalysis contains the XREFs from a given Class.

        Also external classes will generate xrefs, obviously only XREF_FROM are
        shown for external classes.
        """

        self.orig_class = classobj
        self._inherits_methods = {}
        self._methods = {}
        self._fields = {}
        self.internal = internal

        self.xrefto = collections.defaultdict(set)
        self.xreffrom = collections.defaultdict(set)

    def get_methods(self):
        """
        Return all `MethodClassAnalysis` objects of this class
        """
        return list(self._methods.values())

    def get_fields(self):
        """
        Return all `FieldClassAnalysis` objects of this class
        """
        return self._fields.values()

    def get_nb_methods(self):
        """
        Get the number of methods in this class
        """
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

    def __repr__(self):
        return "<analysis.ClassAnalysis {}{}>".format(self.orig_class.get_name(),
                " EXTERNAL" if isinstance(self.orig_class, ExternalClass) else "")

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
    def __init__(self, vm=None):
        """
        Analysis Object

        The Analysis contains a lot of information about (multiple) DalvikVMFormat objects
        Features are for example XREFs between Classes, Methods, Fields and Strings.

        Multiple DalvikVMFormat Objects can be added using the function `add`

        XREFs are created for:
        * classes (`ClassAnalysis`)
        * methods (`MethodClassAnalysis`)
        * strings (`StringAnalyis`)
        * fields (`FieldClassAnalysis`)

        :param vm: inital DalvikVMFormat object (default None)
        """
        self.vms = []
        self.classes = {}
        self.strings = {}
        self.methods = {}

        if vm:
            self.add(vm)

    def add(self, vm):
        """
        Add a DalvikVMFormat to this Analysis

        :param vm:
        """
        self.vms.append(vm)
        for current_class in vm.get_classes():
            self.classes[current_class.get_name()] = ClassAnalysis(current_class, True)

        for method in vm.get_methods():
            self.methods[method] = MethodAnalysis(vm, method)

    def _get_all_classes(self):
        """
        Returns all Class objects of all VMs in this Analysis
        Used by create_xref().
        """
        for vm in self.vms:
            for current_class in vm.get_classes():
                yield current_class

    def create_xref(self):
        log.debug("Creating XREF/DREF")
        started_at = time.time()

        # TODO multiprocessing
        for c in  self._get_all_classes():
            self._create_xref(c)

        diff = time.time() - started_at
        log.info("End of creating XREF/DREF {:.0f}:{:.2f}".format(*divmod(diff, 60)))

    def _create_xref(self, current_class):
        """
        Create the xref for `current_class`
        """
        cur_cls_name = current_class.get_name()

        log.debug("Creating XREF/DREF for %s" % cur_cls_name)
        for current_method in current_class.get_methods():
            log.debug("Creating XREF for %s" % current_method)

            code = current_method.get_code()
            if code is None:
                continue

            off = 0
            for instruction in code.get_bc().get_instructions():
                op_value = instruction.get_op_value()

                if op_value in [0x1c, 0x22]:
                    idx_type = instruction.get_ref_kind()
                    type_info = instruction.cm.vm.get_cm_type(idx_type)

                    # Internal xref related to class manipulation
                    if type_info in self.classes and type_info != cur_cls_name:
                        if op_value == 0x22:
                            # new instance
                            self.classes[cur_cls_name].AddXrefTo(REF_NEW_INSTANCE, self.classes[type_info], current_method, off)
                            self.classes[type_info].AddXrefFrom(REF_NEW_INSTANCE, self.classes[cur_cls_name], current_method, off)
                        else:
                            # class reference
                            self.classes[cur_cls_name].AddXrefTo(REF_CLASS_USAGE, self.classes[type_info], current_method, off)
                            self.classes[type_info].AddXrefFrom(REF_CLASS_USAGE, self.classes[cur_cls_name], current_method, off)

                elif ((0x6e <= op_value <= 0x72) or (0x74 <= op_value <= 0x78)):
                    idx_meth = instruction.get_ref_kind()
                    method_info = instruction.cm.vm.get_cm_method(idx_meth)
                    if method_info:
                        class_info = method_info[0]

                        method_item = instruction.cm.vm.get_method_descriptor(method_info[0], method_info[1], ''.join(method_info[2]))

                        if not method_item:
                            # Seems to be an external classes, create it first
                            if method_info[0] not in self.classes:
                                self.classes[method_info[0]] = ClassAnalysis(ExternalClass(method_info[0]), False)
                            method_item = self.classes[method_info[0]].GetFakeMethod(method_info[1], method_info[2])

                        self.classes[cur_cls_name].AddMXrefTo(current_method, self.classes[class_info], method_item, off)
                        self.classes[class_info].AddMXrefFrom(method_item, self.classes[cur_cls_name], current_method, off)

                        # Internal xref related to class manipulation
                        if class_info in self.classes and class_info != cur_cls_name:
                            self.classes[cur_cls_name].AddXrefTo(REF_CLASS_USAGE, self.classes[class_info], method_item, off)
                            self.classes[class_info].AddXrefFrom(REF_CLASS_USAGE, self.classes[cur_cls_name], current_method, off)

                elif 0x1a <= op_value <= 0x1b:
                    string_value = instruction.cm.vm.get_cm_string(instruction.get_ref_kind())
                    if string_value not in self.strings:
                        self.strings[string_value] = StringAnalysis(string_value)

                    self.strings[string_value].AddXrefFrom(self.classes[cur_cls_name], current_method)

                elif 0x52 <= op_value <= 0x6d:
                    idx_field = instruction.get_ref_kind()
                    field_info = instruction.cm.vm.get_cm_field(idx_field)
                    field_item = instruction.cm.vm.get_field_descriptor(field_info[0], field_info[2], field_info[1])
                    if field_item:
                        if (0x52 <= op_value <= 0x58) or (0x60 <= op_value <= 0x66):
                            # read access to a field
                            self.classes[cur_cls_name].AddFXrefRead(current_method, self.classes[cur_cls_name], field_item)
                        else:
                            # write access to a field
                            self.classes[cur_cls_name].AddFXrefWrite(current_method, self.classes[cur_cls_name], field_item)

                off += instruction.get_length()

    def get_method(self, method):
        """
        :param method:
        :return: `MethodAnalysis` object for the given method
        """
        if method in self.methods:
            return self.methods[method]
        else:
            return None

    def get_method_by_name(self, class_name, method_name, method_descriptor):
        if class_name in self.classes:
            for method in self.classes[class_name].get_vm_class().get_methods():
                if method.get_name() == method_name and method.get_descriptor(
                ) == method_descriptor:
                    return method
        return None

    def get_method_analysis(self, method):
        """
        :param method:
        :return: `MethodClassAnalysis` for the given method
        """
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
        """
        Returns all external classes, that means all classes that are not
        defined in the given set of `DalvikVMObjects`.

        :rtype: generator of `ClassAnalysis`
        """
        for i in self.classes:
            if not self.classes[i].internal:
                yield self.classes[i]

    def get_strings_analysis(self):
        return self.strings

    def get_strings(self):
        """
        Returns a list of `StringAnalysis` objects

        :rtype: list of `StringAnalysis`
        """
        return self.strings.values()

    def get_classes(self):
        """
        Returns a list of `ClassAnalysis` objects

        :rtype: list of `ClassAnalysis`
        """
        return self.classes.values()

    def get_methods(self):
        """
        Returns a list of `MethodClassAnalysis` objects

        """
        for c in self.classes.values():
            for m in c.get_methods():
                yield m

    def get_fields(self):
        """
        Returns a list of `FieldClassAnalysis` objects

        """
        for c in self.classes.values():
            for f in c.get_fields():
                yield f

    def find_classes(self, name=".*", no_external=False):
        """
        Find classes by name, using regular expression
        This method will return all ClassAnalysis Object that match the name of
        the class.

        :param name: regular expression for class name (default ".*")
        :param no_external: Remove external classes from the output (default False)
        :rtype: generator of `ClassAnalysis`
        """
        for cname, c in self.classes.items():
            if no_external and isinstance(c.get_vm_class(), ExternalClass):
                continue
            if re.match(name, cname):
                yield c

    def find_methods(self, classname=".*", methodname=".*", descriptor=".*",
            accessflags=".*", no_external=False):
        """
        Find a method by name using regular expression.
        This method will return all MethodClassAnalysis objects, which match the
        classname, methodname, descriptor and accessflags of the method.

        :param classname: regular expression for the classname
        :param methodname: regular expression for the method name
        :param descriptor: regular expression for the descriptor
        :param accessflags: regular expression for the accessflags
        :param no_external: Remove external method from the output (default False)
        :rtype: generator of `MethodClassAnalysis`
        """
        for cname, c in self.classes.items():
            if re.match(classname, cname):
                for m in c.get_methods():
                    z = m.get_method()
                    # TODO is it even possible that an internal class has
                    # external methods? Maybe we should check for ExternalClass
                    # instead...
                    if no_external and isinstance(z, ExternalMethod):
                        continue
                    if re.match(methodname, z.get_name()) and \
                       re.match(descriptor, z.get_descriptor()) and \
                       re.match(accessflags, z.get_access_flags_string()):
                        yield m

    def find_strings(self, string=".*"):
        """
        Find strings by regex

        :param string: regular expression for the string to search for
        :rtype: generator of `StringAnalysis`
        """
        for s, sa in self.strings.items():
            if re.match(string, s):
                yield sa

    def find_fields(self, classname=".*", fieldname=".*", fieldtype=".*",
            accessflags=".*"):
        """
        find fields by regex

        :param classname: regular expression of the classname
        :param fieldname: regular expression of the fieldname
        :param fieldtype: regular expression of the fieldtype
        :param accessflags: regular expression of the access flags
        :rtype: generator of `FieldClassAnalysis`
        """
        for cname, c in self.classes.items():
            if re.match(classname, cname):
                for f in c.get_fields():
                    z = f.get_field()
                    if re.match(fieldname, z.get_name()) and \
                       re.match(fieldtype, z.get_descriptor()) and \
                       re.match(accessflags, z.get_access_flags_string()):
                           yield f

    def __repr__(self):
        return "<analysis.Analysis VMs: {}, Classes: {}, Strings: {}>".format(len(self.vms), len(self.classes), len(self.strings))


def is_ascii_obfuscation(vm):
    """
    Tests if any class inside a DalvikVMObject
    uses ASCII Obfuscation (e.g. UTF-8 Chars in Classnames)

    :param vm: `DalvikVMObject`
    :return: True if ascii obfuscation otherwise False
    """
    for classe in vm.get_classes():
        if is_ascii_problem(classe.get_name()):
            return True
        for method in classe.get_methods():
            if is_ascii_problem(method.get_name()):
                return True
    return False
