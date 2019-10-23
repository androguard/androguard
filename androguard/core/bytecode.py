import hashlib
from xml.sax.saxutils import escape
from struct import pack
import textwrap
import json
import logging

from androguard.core.androconf import CONF, color_range
from androguard.core.bytecodes.dvm_types import Kind, Operand

log = logging.getLogger("androguard.bytecode")


def _PrintBanner():
    print_fct = CONF["PRINT_FCT"]
    print_fct("*" * 75 + "\n")


def _PrintSubBanner(title=None):
    print_fct = CONF["PRINT_FCT"]
    if title is None:
        print_fct("#" * 20 + "\n")
    else:
        print_fct("#" * 10 + " " + title + "\n")


def _PrintNote(note, tab=0):
    print_fct = CONF["PRINT_FCT"]
    note_color = CONF["COLORS"]["NOTE"]
    normal_color = CONF["COLORS"]["NORMAL"]
    print_fct("\t" * tab + "{}# {}{}".format(note_color, note, normal_color) + "\n")


def _Print(name, arg):
    """Print arg into a correct format"""
    buff = name + " "

    if type(arg).__name__ == 'int':
        buff += "0x%x" % arg
    elif type(arg).__name__ == 'long':
        buff += "0x%x" % arg
    elif type(arg).__name__ == 'str':
        buff += "%s" % arg

    print(buff)


def PrettyShowEx(exceptions):
    if len(exceptions) > 0:
        CONF["PRINT_FCT"]("Exceptions:\n")
        for i in exceptions:
            CONF["PRINT_FCT"]("\t%s%s%s\n" %
                              (CONF["COLORS"]["EXCEPTION"], i.show_buff(),
                               CONF["COLORS"]["NORMAL"]))


def _PrintXRef(tag, items):
    print_fct = CONF["PRINT_FCT"]
    for i in items:
        print_fct("%s: %s %s %s %s\n" %
                  (tag, i[0].get_class_name(), i[0].get_name(),
                   i[0].get_descriptor(), ' '.join("%x" % j.get_idx()
                                                   for j in i[1])))


def _PrintDRef(tag, items):
    print_fct = CONF["PRINT_FCT"]
    for i in items:
        print_fct("%s: %s %s %s %s\n" %
                  (tag, i[0].get_class_name(), i[0].get_name(),
                   i[0].get_descriptor(), ' '.join("%x" % j for j in i[1])))


def _PrintDefault(msg):
    print_fct = CONF["PRINT_FCT"]
    print_fct(msg)


def _colorize_operands(operands, colors):
    """
    Return strings with color coded operands
    """
    for operand in operands:
        if operand[0] == Operand.REGISTER:
            yield "{}v{}{}".format(colors["registers"], operand[1], colors["normal"])

        elif operand[0] == Operand.LITERAL:
            yield "{}{}{}".format(colors["literal"], operand[1], colors["normal"])

        elif operand[0] == Operand.RAW:
            yield "{}{}{}".format(colors["raw"], operand[1], colors["normal"])

        elif operand[0] == Operand.OFFSET:
            yield "%s%d%s" % (colors["offset"], operand[1], colors["normal"])

        elif operand[0] & Operand.KIND:
            if operand[0] == (Operand.KIND + Kind.STRING):
                yield "{}{}{}".format(colors["string"], operand[2], colors["normal"])
            elif operand[0] == (Operand.KIND + Kind.METH):
                yield "{}{}{}".format(colors["meth"], operand[2], colors["normal"])
            elif operand[0] == (Operand.KIND + Kind.FIELD):
                yield "{}{}{}".format(colors["field"], operand[2], colors["normal"])
            elif operand[0] == (Operand.KIND + Kind.TYPE):
                yield "{}{}{}".format(colors["type"], operand[2], colors["normal"])
            else:
                yield "{}".format(repr(operands[2]))
        else:
            yield "{}".format(repr(operands[1]))


def PrettyShow(basic_blocks, notes={}):
    idx = 0

    offset_color = CONF["COLORS"]["OFFSET"]
    offset_addr_color = CONF["COLORS"]["OFFSET_ADDR"]
    instruction_name_color = CONF["COLORS"]["INSTRUCTION_NAME"]
    branch_false_color = CONF["COLORS"]["BRANCH_FALSE"]
    branch_true_color = CONF["COLORS"]["BRANCH_TRUE"]
    branch_color = CONF["COLORS"]["BRANCH"]
    exception_color = CONF["COLORS"]["EXCEPTION"]
    bb_color = CONF["COLORS"]["BB"]
    normal_color = CONF["COLORS"]["NORMAL"]
    print_fct = CONF["PRINT_FCT"]

    colors = CONF["COLORS"]["OUTPUT"]

    for nb, i in enumerate(basic_blocks):
        print_fct("{}{}{} : \n".format(bb_color, i.get_name(), normal_color))
        instructions = list(i.get_instructions())
        for ins in instructions:
            if nb in notes:
                for note in notes[nb]:
                    _PrintNote(note, 1)

            print_fct("\t%s%-3d%s(%s%08x%s) " %
                      (offset_color, nb, normal_color, offset_addr_color, idx,
                       normal_color))
            print_fct("%s%-20s%s" %
                      (instruction_name_color, ins.get_name(), normal_color))

            operands = ins.get_operands()
            print_fct(
                "%s" %
                ", ".join(_colorize_operands(operands, colors)))

            op_value = ins.get_op_value()
            if ins == instructions[-1] and i.childs:
                print_fct(" ")

                # packed/sparse-switch
                if (op_value == 0x2b or op_value == 0x2c) and len(i.childs) > 1:
                    values = i.get_special_ins(idx).get_values()
                    print_fct("%s[ D:%s%s " %
                              (branch_false_color, i.childs[0][2].get_name(),
                               branch_color))
                    print_fct(' '.join("%d:%s" % (
                        values[j], i.childs[j + 1][2].get_name()) for j in
                                       range(0, len(i.childs) - 1)) + " ]%s" %
                              normal_color)
                else:
                    if len(i.childs) == 2:
                        print_fct("{}[ {}{} ".format(branch_false_color,
                                                     i.childs[0][2].get_name(),
                                                     branch_true_color))
                        print_fct(' '.join("%s" % c[2].get_name(
                        ) for c in i.childs[1:]) + " ]%s" % normal_color)
                    else:
                        print_fct("%s[ " % branch_color + ' '.join(
                            "%s" % c[2].get_name() for c in i.childs) + " ]%s" %
                                  normal_color)

            idx += ins.get_length()

            print_fct("\n")

        if i.get_exception_analysis():
            print_fct("\t%s%s%s\n" %
                      (exception_color, i.exception_analysis.show_buff(),
                       normal_color))

        print_fct("\n")


def _get_operand_html(operand, registers_colors, colors):
    """
    Return a HTML representation of the operand.
    The HTML should be compatible with pydot/graphviz to be used
    inside a node label.

    This is solely used in :func:`~androguard.core.bytecodes.method2dot`

    :param operand: tuple containing the operand type and operands
    :param dict register_colors: key: register number, value: register color
    :param dict colors: dictionary containing the register colors
    :returns: HTML code of the operands
    """
    if operand[0] == Operand.REGISTER:
        return '<FONT color="{}">v{}</FONT>'.format(registers_colors[operand[1]], operand[1])

    if operand[0] == Operand.LITERAL:
        return '<FONT color="{}">0x{:x}</FONT>'.format(colors["literal"], operand[1])

    if operand[0] == Operand.RAW:
        wrapped_adjust = '<br />'.join(escape(repr(i)[1:-1]) for i in textwrap.wrap(operand[1], 64))
        return '<FONT color="{}">{}</FONT>'.format(colors["raw"], wrapped_adjust)

    if operand[0] == Operand.OFFSET:
        return '<FONT FACE="Times-Italic" color="{}">@0x{:x}</FONT>'.format(colors["offset"], operand[1])

    if operand[0] & Operand.KIND:
        if operand[0] == (Operand.KIND + Kind.STRING):
            wrapped_adjust = "&quot; &#92;<br />&quot;".join(map(escape, textwrap.wrap(operand[2], 64)))
            return '<FONT color="{}">&quot;{}&quot;</FONT>'.format(colors["string"], wrapped_adjust)

        if operand[0] == (Operand.KIND + Kind.METH):
            return '<FONT color="{}">{}</FONT>'.format(colors["method"], escape(operand[2]))
        if operand[0] == (Operand.KIND + Kind.FIELD):
            return '<FONT color="{}">{}</FONT>'.format(colors["field"], escape(operand[2]))
        if operand[0] == (Operand.KIND + Kind.TYPE):
            return '<FONT color="{}">{}</FONT>'.format(colors["type"], escape(operand[2]))

        return escape(str(operand[2]))

    return escape(str(operand[1]))


def method2dot(mx, colors=None):
    """
    Export analysis method to dot format.

    A control flow graph is created by using the concept of BasicBlocks.
    Each BasicBlock is a sequence of opcode without any jumps or branch.

    :param mx: :class:`~androguard.core.analysis.analysis.MethodAnalysis`
    :param colors: dict of colors to use, if colors is None the default colors are used

    :returns: a string which contains the dot graph
    """

    font_face = "monospace"

    if not colors:
        colors = {
            "true_branch": "green",
            "false_branch": "red",
            "default_branch": "purple",
            "jump_branch": "blue",
            "bg_idx": "lightgray",
            "idx": "blue",
            "bg_start_idx": "yellow",
            "bg_instruction": "lightgray",
            "instruction_name": "black",
            "instructions_operands": "yellow",
            "raw": "red",
            "string": "red",
            "literal": "green",
            "offset": "#4000FF",
            "method": "#DF3A01",
            "field": "#088A08",
            "type": "#0000FF",
            "registers_range": ("#999933", "#6666FF")
        }

    node_tpl = """
    struct_%s [label=<
        <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="3">
            %s
        </TABLE>
    >];
    """
    label_tpl = """
    <TR>
        <TD ALIGN="LEFT" BGCOLOR="%s">
            <FONT FACE="{font_face}" color="%s">%04x</FONT>
        </TD>
        <TD ALIGN="LEFT" BGCOLOR="%s">
            <FONT FACE="{font_face}" color="%s">%s</FONT> %s
        </TD>
    </TR>
    """.format(font_face=font_face)

    link_tpl = '<TR><TD PORT="{}"></TD></TR>\n'

    edges_html = ""
    blocks_html = ""

    method = mx.get_method()

    # This is used as a seed to create unique hashes for the nodes
    sha256 = hashlib.sha256(
        mx.get_method().get_class_name() + mx.get_method().get_name() + mx.get_method().get_descriptor()).digest()

    # Collect all used Registers and create colors
    if method.get_code() and method.get_code().get_registers_size() != 0:
        registers = {i: c for i, c in enumerate(color_range(colors["registers_range"][0], colors["registers_range"][1],
                                                            method.get_code().get_registers_size()))}
    else:
        registers = dict()

    new_links = []

    # Go through all basic blocks and create the CFG
    for basic_block in mx.basic_blocks:
        ins_idx = basic_block.start
        block_id = hashlib.md5(sha256 + basic_block.get_name()).hexdigest()

        content = link_tpl.format('header')

        for instruction in basic_block.get_instructions():
            if instruction.get_op_value() in (0x2b, 0x2c):
                new_links.append((basic_block, ins_idx, instruction.get_ref_off() * 2 + ins_idx))
            elif instruction.get_op_value() == 0x26:
                new_links.append((basic_block, ins_idx, instruction.get_ref_off() * 2 + ins_idx))

            operands = instruction.get_operands(ins_idx)
            output = ", ".join(_get_operand_html(i, registers, colors) for i in operands)

            bg_idx = colors["bg_idx"]
            if ins_idx == 0 and "bg_start_idx" in colors:
                bg_idx = colors["bg_start_idx"]

            content += label_tpl % (
                bg_idx, colors["idx"], ins_idx, colors["bg_instruction"],
                colors["instruction_name"],
                instruction.get_name(), output)

            ins_idx += instruction.get_length()

        # all blocks from one method parsed
        # updating dot HTML content
        content += link_tpl.format('tail')
        blocks_html += node_tpl % (block_id, content)

        # Block edges color treatment (conditional branchs colors)
        val = colors["true_branch"]
        if len(basic_block.childs) > 1:
            val = colors["false_branch"]
        elif len(basic_block.childs) == 1:
            val = colors["jump_branch"]

        values = None
        # The last instruction is important and still set from the loop
        # FIXME: what if there is no instruction in the basic block?
        if instruction.get_op_value() in (0x2b, 0x2c) and len(basic_block.childs) > 1:
            val = colors["default_branch"]
            values = ["default"]
            values.extend(basic_block.get_special_ins(ins_idx - instruction.get_length()).get_values())

        # updating dot edges
        for DVMBasicMethodBlockChild in basic_block.childs:
            label_edge = ""

            if values:
                label_edge = values.pop(0)

            child_id = hashlib.md5(sha256 + DVMBasicMethodBlockChild[-1].get_name()).hexdigest()
            edges_html += "struct_{}:tail -> struct_{}:header  [color=\"{}\", label=\"{}\"];\n".format(block_id,
                                                                                                       child_id, val,
                                                                                                       label_edge)

            # color switch
            if val == colors["false_branch"]:
                val = colors["true_branch"]
            elif val == colors["default_branch"]:
                val = colors["true_branch"]

        exception_analysis = basic_block.get_exception_analysis()
        if exception_analysis:
            for exception_elem in exception_analysis.exceptions:
                exception_block = exception_elem[-1]
                if exception_block:
                    exception_id = hashlib.md5(sha256 + exception_block.get_name()).hexdigest()
                    edges_html += "struct_{}:tail -> struct_{}:header  [color=\"{}\", label=\"{}\"];\n".format(
                        block_id, exception_id, "black", exception_elem[0])

    for link in new_links:
        basic_block = link[0]
        DVMBasicMethodBlockChild = mx.basic_blocks.get_basic_block(link[2])

        if DVMBasicMethodBlockChild:
            block_id = hashlib.md5(sha256 + basic_block.get_name()).hexdigest()
            child_id = hashlib.md5(sha256 + DVMBasicMethodBlockChild.get_name()).hexdigest()

            edges_html += "struct_{}:tail -> struct_{}:header  [color=\"{}\", label=\"data(0x{:x}) to @0x{:x}\", style=\"dashed\"];\n".format(
                block_id, child_id, "yellow", link[1], link[2])

    method_label = method.get_class_name() + "." + method.get_name() + "->" + method.get_descriptor()

    method_information = method.get_information()
    if method_information:
        method_label += "\\nLocal registers v{} ... v{}".format(*method_information["registers"])
        if "params" in method_information:
            for register, rtype in method_information["params"]:
                method_label += "\\nparam v%d = %s" % (register, rtype)
        method_label += "\\nreturn = %s" % (method_information["return"])

    return {'name': method_label, 'nodes': blocks_html, 'edges': edges_html}


def method2format(output, _format="png", mx=None, raw=None):
    """
    Export method structure as a graph to a specific file format using dot from the graphviz package.
    The result is written to the file specified via :code:`output`.

    There are two possibilites to give input for this method:

    1) use :code:`raw` argument and pass a dictionary containing the keys
    :code:`name`, :code:`nodes` and :code:`edges`.
    This can be created using :func:`method2dot`.
    2) give a :class:`~androguard.core.analysis.analysis.MethodAnalysis`.

    This function requires pydot!

    There is a special format :code:`raw` which saves the dot buffer before it
    is handled by pydot.

    :param str output: output filename
    :param str _format: format type (png, jpg ...). Can use all formats which are understood by pydot.
    :param androguard.core.analysis.analysis.MethodAnalysis mx: specify the MethodAnalysis object
    :param dict raw: use directly a dot raw buffer if None
    """
    # pydot is optional!
    import pydot

    if raw:
        data = raw
    else:
        data = method2dot(mx)

    buff = """
    digraph {{
        graph [rankdir=TB]
        node [shape=plaintext]

        subgraph cluster_{clustername}
        {{
            label="{classname}"
            {nodes}
        }}

        {edges}
    }}
    """.format(clustername=hashlib.md5(output.encode("UTF-8")).hexdigest(),
               classname=data['name'],
               nodes=data['nodes'],
               edges=data['edges'],
               )

    # NOTE: In certain cases the graph_from_dot_data function might fail.
    # There is a bug in the code that certain html strings are interpreted as comment
    # and therefore the dot buffer which is passed to graphviz is invalid.
    # We can not really do anything here to prevent this (except for heavily
    # escaping and replacing all characters).
    # We hope, that this issue get's fixed in pydot, so we do not need to patch
    # stuff here.
    # In order to be able to debug the problems better, we will write the dot
    # data here if the format `raw` is requested, instead of creating the graph
    # and then writing the dot data.
    # If you have problems with certain data, export it as dot and then run
    # graphviz manually to see if the problem persists.
    if _format == "raw":
        with open(output, "w") as fp:
            fp.write(buff)
    else:
        d = pydot.graph_from_dot_data(buff)
        if len(d) > 1:
            # Not sure what to do in this case?!
            log.warnig("The graph generated for '{}' has too many subgraphs! "
                       "Only plotting the first one.".format(output))
        for g in d:
            getattr(g, "write_" + _format.lower())(output)
            break


def method2png(output, mx, raw=False):
    """
    Export method to a png file format

    :param output: output filename
    :type output: string
    :param mx: specify the MethodAnalysis object
    :type mx: :class:`MethodAnalysis` object
    :param raw: use directly a dot raw buffer
    :type raw: string
    """
    buff = raw
    if not raw:
        buff = method2dot(mx)

    method2format(output, "png", mx, buff)


def method2jpg(output, mx, raw=False):
    """
    Export method to a jpg file format

    :param output: output filename
    :type output: string
    :param mx: specify the MethodAnalysis object
    :type mx: :class:`MethodAnalysis` object
    :param raw: use directly a dot raw buffer (optional)
    :type raw: string
    """
    buff = raw
    if not raw:
        buff = method2dot(mx)

    method2format(output, "jpg", mx, buff)


def vm2json(vm):
    """
    Get a JSON representation of a DEX file

    :param vm: :class:`~androguard.core.bytecodes.dvm.DalvikVMFormat`
    :return:
    """
    d = {"name": "root", "children": []}

    for _class in vm.get_classes():
        c_class = {"name": _class.get_name(), "children": []}

        for method in _class.get_methods():
            c_method = {"name": method.get_name(), "children": []}

            c_class["children"].append(c_method)

        d["children"].append(c_class)

    return json.dumps(d)


class TmpBlock:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name


def method2json(mx, directed_graph=False):
    """
    Create directed or undirected graph in the json format.

    :param mx: :class:`~androguard.core.analysis.analysis.MethodAnalysis`
    :param directed_graph: True if a directed graph should be created (default: False)
    :return:
    """
    if directed_graph:
        return method2json_direct(mx)
    return method2json_undirect(mx)


def method2json_undirect(mx):
    """

    :param mx: :class:`~androguard.core.analysis.analysis.MethodAnalysis`
    :return:
    """
    d = {}
    reports = []
    d["reports"] = reports

    for DVMBasicMethodBlock in mx.basic_blocks.gets():
        cblock = {"BasicBlockId": DVMBasicMethodBlock.get_name(),
                  "registers": mx.get_method().get_code().get_registers_size(), "instructions": []}

        ins_idx = DVMBasicMethodBlock.start
        for DVMBasicMethodBlockInstruction in DVMBasicMethodBlock.get_instructions():
            c_ins = {"idx": ins_idx, "name": DVMBasicMethodBlockInstruction.get_name(),
                     "operands": DVMBasicMethodBlockInstruction.get_operands(
                         ins_idx)}

            cblock["instructions"].append(c_ins)
            ins_idx += DVMBasicMethodBlockInstruction.get_length()

        cblock["Edge"] = []
        for DVMBasicMethodBlockChild in DVMBasicMethodBlock.childs:
            cblock["Edge"].append(DVMBasicMethodBlockChild[-1].get_name())

        reports.append(cblock)

    return json.dumps(d)


def method2json_direct(mx):
    """

    :param mx: :class:`~androguard.core.analysis.analysis.MethodAnalysis`
    :return:
    """
    d = {}
    reports = []
    d["reports"] = reports

    hooks = {}

    l = []
    for DVMBasicMethodBlock in mx.basic_blocks.gets():
        for index, DVMBasicMethodBlockChild in enumerate(DVMBasicMethodBlock.childs):
            if DVMBasicMethodBlock.get_name() == DVMBasicMethodBlockChild[-1].get_name():

                preblock = TmpBlock(DVMBasicMethodBlock.get_name() + "-pre")

                cnblock = {"BasicBlockId": DVMBasicMethodBlock.get_name() + "-pre",
                           "start": DVMBasicMethodBlock.start,
                           "notes": [],
                           "Edge": [DVMBasicMethodBlock.get_name()],
                           "registers": 0,
                           "instructions": [],
                           "info_bb": 0}

                l.append(cnblock)

                for parent in DVMBasicMethodBlock.fathers:
                    hooks[parent[-1].get_name()] = []
                    hooks[parent[-1].get_name()].append(preblock)

                    for idx, child in enumerate(parent[-1].childs):
                        if child[-1].get_name() == DVMBasicMethodBlock.get_name(
                        ):
                            hooks[parent[-1].get_name()].append(child[-1])

    for DVMBasicMethodBlock in mx.basic_blocks.gets():
        cblock = {"BasicBlockId": DVMBasicMethodBlock.get_name(),
                  "start": DVMBasicMethodBlock.start,
                  "notes": DVMBasicMethodBlock.get_notes(),
                  "registers": mx.get_method().get_code().get_registers_size(),
                  "instructions": []}

        ins_idx = DVMBasicMethodBlock.start
        last_instru = None
        for DVMBasicMethodBlockInstruction in DVMBasicMethodBlock.get_instructions():
            c_ins = {"idx": ins_idx,
                     "name": DVMBasicMethodBlockInstruction.get_name(),
                     "operands": DVMBasicMethodBlockInstruction.get_operands(ins_idx),
                     }

            cblock["instructions"].append(c_ins)

            if (DVMBasicMethodBlockInstruction.get_op_value() == 0x2b or
                    DVMBasicMethodBlockInstruction.get_op_value() == 0x2c):
                values = DVMBasicMethodBlock.get_special_ins(ins_idx)
                cblock["info_next"] = values.get_values()

            ins_idx += DVMBasicMethodBlockInstruction.get_length()
            last_instru = DVMBasicMethodBlockInstruction

        cblock["info_bb"] = 0
        if DVMBasicMethodBlock.childs:
            if len(DVMBasicMethodBlock.childs) > 1:
                cblock["info_bb"] = 1

            if (last_instru.get_op_value() == 0x2b or
                    last_instru.get_op_value() == 0x2c):
                cblock["info_bb"] = 2

        cblock["Edge"] = []
        for DVMBasicMethodBlockChild in DVMBasicMethodBlock.childs:
            ok = False
            if DVMBasicMethodBlock.get_name() in hooks:
                if DVMBasicMethodBlockChild[-1] in hooks[DVMBasicMethodBlock.get_name()]:
                    ok = True
                    cblock["Edge"].append(hooks[DVMBasicMethodBlock.get_name()][0].get_name())

            if not ok:
                cblock["Edge"].append(DVMBasicMethodBlockChild[-1].get_name())

        exception_analysis = DVMBasicMethodBlock.get_exception_analysis()
        if exception_analysis:
            cblock["Exceptions"] = exception_analysis.get()

        reports.append(cblock)

    reports.extend(l)

    return json.dumps(d)


def object_to_bytes(obj):
    """
    Convert a object to a bytearray or call get_raw() of the object
    if no useful type was found.
    """
    if isinstance(obj, str):
        return bytearray(obj, "UTF-8")
    if isinstance(obj, bool):
        return bytearray()
    if isinstance(obj, int):
        return pack("<L", obj)
    if obj is None:
        return bytearray()
    if isinstance(obj, bytearray):
        return obj

    return obj.get_raw()


class BuffHandle:
    """
    BuffHandle is a wrapper around bytes.
    It gives the ability to jump in the byte stream, just like with BytesIO.
    """

    def __init__(self, buff):
        self.__buff = bytearray(buff)
        self.__idx = 0

    def __getitem__(self, item):
        """
        Get the byte at the position `item`

        :param int item: offset in the buffer
        :returns: byte at the position
        :rtype: int
        """
        return self.__buff[item]

    def __len__(self):
        return self.size()

    def size(self):
        """
        Get the total size of the buffer

        :rtype: int
        """
        return len(self.__buff)

    def length_buff(self):
        """
        Alias for :meth:`size`
        """
        return self.size()

    def set_idx(self, idx):
        """
        Set the current offset in the buffer

        :param int idx: offset to set
        """
        self.__idx = idx

    def get_idx(self):
        """
        Get the current offset in the buffer

        :rtype: int
        """
        return self.__idx

    def add_idx(self, idx):
        """
        Advance the current offset by `idx`

        :param int idx: number of bytes to advance
        """
        self.__idx += idx

    def tell(self):
        """
        Alias for :meth:`get_idx`.

        :rtype: int
        """
        return self.__idx

    def readNullString(self, size):
        """
        Read a String with length `size` at the current offset

        :param int size: length of the string
        :rtype: bytearray
        """
        data = self.read(size)
        return data

    def read_b(self, size):
        """
        Read bytes with length `size` without incrementing the current offset

        :param int size: length to read in bytes
        :rtype: bytearray
        """
        return self.__buff[self.__idx:self.__idx + size]

    def peek(self, size):
        """
        Alias for :meth:`read_b`
        """
        return self.read_b(size)

    def read_at(self, offset, size):
        """
        Read bytes from the given offset with length `size` without incrementing
        the current offset

        :param int offset: offset to start reading
        :param int size: length of bytes to read
        :rtype: bytearray
        """
        return self.__buff[offset:offset + size]

    def readat(self, off):
        """
        Read all bytes from the start of `off` until the end of the buffer

        This method can be used to determine a checksum of a buffer from a given
        point on.

        :param int off: starting offset
        :rtype: bytearray
        """
        return self.__buff[off:]

    def read(self, size):
        """
        Read from the current offset a total number of `size` bytes
        and increment the offset by `size`

        :param int size: length of bytes to read
        :rtype: bytearray
        """
        buff = self.__buff[self.__idx:self.__idx + size]
        self.__idx += size

        return buff

    def end(self):
        """
        Test if the current offset is at the end or over the buffer boundary

        :rtype: bool
        """
        return self.__idx >= len(self.__buff)

    def get_buff(self):
        """
        Return the whole buffer

        :rtype: bytearray
        """
        return self.__buff

    def set_buff(self, buff):
        """
        Overwrite the current buffer with the content of `buff`

        :param bytearray buff: the new buffer
        """
        self.__buff = buff

    def save(self, filename):
        """
        Save the current buffer to `filename`

        Exisiting files with the same name will be overwritten.

        :param str filename: the name of the file to save to
        """
        with open(filename, "wb") as fd:
            fd.write(self.__buff)


class Buff:
    def __init__(self, offset, buff):
        self.offset = offset
        self.buff = buff

        self.size = len(buff)


# Here for legacy reasons. Might get removed some day...
_Bytecode = BuffHandle


def FormatClassToJava(i):
    """
    Transform a java class name into the typed variant found in DEX files.

    example::

        >>> FormatClassToJava('java.lang.Object')
        'Ljava/lang/Object;'

    :param i: the input class name
    :rtype: str
    """
    return "L" + i.replace(".", "/") + ";"


def FormatClassToPython(i):
    """
    Transform a typed class name into a form which can be used as a python
    attribute

    example::

        >>> FormatClassToPython('Lfoo/bar/foo/Barfoo$InnerClass;')
        'Lfoo_bar_foo_Barfoo_InnerClass'

    :param i: classname to transform
    :rtype: str
    """
    i = i[:-1]
    i = i.replace("/", "_")
    i = i.replace("$", "_")

    return i


def get_package_class_name(name):
    """
    Return package and class name in a java variant from a typed variant name.

    If no package could be found, the package is an empty string.

    If the name is an array type, the array is discarded.

    example::

        >>> get_package_class_name('Ljava/lang/Object;')
        ('java.lang', 'Object')
        >>> get_package_class_name('[[Ljava/lang/Object;')
        ('java.lang', 'Object')
        >>> get_package_class_name('LSomeClass;')
        ('', 'SomeClass')

    :param name: the name
    :rtype: tuple
    :return:
    """
    # name is MUTF8, so make sure we get the string variant
    name = str(name)
    if name[-1] != ';':
        raise ValueError("The name '{}' does not look like a typed name!".format(name))

    # discard array types, there might be many...
    name = name.lstrip('[')

    if name[0] != 'L':
        raise ValueError("The name '{}' does not look like a typed name!".format(name))

    name = name[1:-1]
    if '/' not in name:
        return '', name

    package, clsname = name.rsplit('/', 1)
    package = package.replace('/', '.')

    return package, clsname


def FormatNameToPython(i):
    """
    Transform a (method) name into a form which can be used as a python
    attribute

    example::

        >>> FormatNameToPython('<clinit>')
        'clinit'

    :param i: name to transform
    :rtype: str
    """

    i = i.replace("<", "")
    i = i.replace(">", "")
    i = i.replace("$", "_")

    return i


def FormatDescriptorToPython(i):
    """
    Format a descriptor into a form which can be used as a python attribute

    example::

        >>> FormatDescriptorToPython('(Ljava/lang/Long; Ljava/lang/Long; Z Z)V')
        'Ljava_lang_LongLjava_lang_LongZZV

    :param i: name to transform
    :rtype: str
    """

    i = i.replace("/", "_")
    i = i.replace(";", "")
    i = i.replace("[", "")
    i = i.replace("(", "")
    i = i.replace(")", "")
    i = i.replace(" ", "")
    i = i.replace("$", "")

    return i


class Node:
    def __init__(self, n, s):
        self.id = n
        self.title = s
        self.children = []
