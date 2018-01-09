from __future__ import division
from __future__ import print_function

from builtins import hex
from builtins import object
from networkx import DiGraph
import os
from xml.sax.saxutils import escape


class DexViewer(object):
    def __init__(self, vm, vmx, gvmx):
        self.vm = vm
        self.vmx = vmx
        self.gvmx = gvmx

    def _create_node(self, i, height, width, color, label):
        buff = "<node id=\"%d\">\n" % i
        buff += "<data key=\"d6\">\n"
        buff += "<y:ShapeNode>\n"

        buff += "<y:Geometry height=\"%f\" width=\"%f\"/>\n" % (16 * height, 7.5 * width)
        buff += "<y:Fill color=\"#%s\" transparent=\"false\"/>\n" % color

        buff += "<y:NodeLabel alignment=\"left\" autoSizePolicy=\"content\" fontFamily=\"Dialog\" fontSize=\"13\" fontStyle=\"plain\" hasBackgroundColor=\"false\" hasLineColor=\"false\" modelName=\"internal\" modelPosition=\"c\" textColor=\"#000000\" visible=\"true\">\n"

        buff += escape(label)

        buff += "</y:NodeLabel>\n"
        buff += "</y:ShapeNode>\n"
        buff += "</data>\n"

        buff += "</node>\n"

        return buff

    def add_exception_node(self, exception, id_i):
        buff = ""
        # 9933FF
        height = 2
        width = 0
        label = ""

        label += "%x:%x\n" % (exception.start, exception.end)
        for i in exception.exceptions:
            c_label = "\t(%s -> %x %s)\n" % (i[0], i[1], i[2].get_name())
            label += c_label

            width = max(len(c_label), width)
            height += 1

        return self._create_node(id_i, height, width, "9333FF", label)

    def add_method_node(self, i, id_i):
        height = 0
        width = 0
        label = ""

        label += i.get_name() + "\n"
        label += i.get_descriptor()

        height = 3
        width = len(label)

        return self._create_node(id_i, height, width, "FF0000", label)

    def add_node(self, i, id_i):
        height = 0
        width = 0
        idx = i.start
        label = ""
        for ins in i.get_instructions():
            c_label = "%x %s %s\n" % (idx, ins.get_name(), ins.get_output(idx))
            idx += ins.get_length()
            label += c_label
            width = max(width, len(c_label))
            height += 1

        if height < 10:
            height += 3

        return self._create_node(id_i, height, width, "FFCC00", label)

    def add_edge(self, i, id_i, j, id_j, l_eid, val):
        buff = "<edge id=\"%d\" source=\"%d\" target=\"%d\">\n" % (len(l_eid), id_i, id_j)

        buff += "<data key=\"d9\">\n"
        buff += "<y:PolyLineEdge>\n"
        buff += "<y:Arrows source=\"none\" target=\"standard\"/>\n"

        if val == 0:
            buff += "<y:LineStyle color=\"#00FF00\" type=\"line\" width=\"1.0\"/>\n"
        elif val == 1:
            buff += "<y:LineStyle color=\"#FF0000\" type=\"line\" width=\"1.0\"/>\n"
        else:
            buff += "<y:LineStyle color=\"#0000FF\" type=\"line\" width=\"1.0\"/>\n"

        buff += "</y:PolyLineEdge>\n"
        buff += "</data>\n"

        buff += "</edge>\n"

        l_eid["%d+%d" % (id_i, id_j)] = len(l_eid)
        return buff

    def new_id(self, i, l):
        try:
            return l[i]
        except KeyError:
            l[i] = len(l)
            return l[i]

    def export_to_gml(self):
        H = {}

        for _class in self.vm.get_classes():
            name = _class.get_name()
            name = name[1:-1]

            buff = ""

            buff += "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n"
            buff += "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:y=\"http://www.yworks.com/xml/graphml\" xmlns:yed=\"http://www.yworks.com/xml/yed/3\" xsi:schemaLocation=\"http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd\">\n"

            buff += "<key attr.name=\"description\" attr.type=\"string\" for=\"node\" id=\"d5\"/>\n"
            buff += "<key for=\"node\" id=\"d6\" yfiles.type=\"nodegraphics\"/>\n"
            buff += "<key for=\"edge\" id=\"d9\" yfiles.type=\"edgegraphics\"/>\n"

            buff += "<graph edgedefault=\"directed\" id=\"G\">\n"

            print(name)

            buff_nodes = ""
            buff_edges = ""
            l_id = {}
            l_eid = {}

            for method in _class.get_methods():
                mx = self.vmx.get_method(method)
                exceptions = mx.exceptions

                id_method = self.new_id(method, l_id)
                buff_nodes += self.add_method_node(method, id_method)

                for i in mx.basic_blocks.get():
                    id_i = self.new_id(i, l_id)
                    print(i, id_i, i.exception_analysis)

                    buff_nodes += self.add_node(i, id_i)

                    # add childs nodes
                    val = 0
                    if len(i.childs) > 1:
                        val = 1
                    elif len(i.childs) == 1:
                        val = 2

                    for j in i.childs:
                        print("\t", j)

                        id_j = self.new_id(j[-1], l_id)
                        buff_edges += self.add_edge(i, id_i, j[-1], id_j, l_eid, val)
                        if val == 1:
                            val = 0

                    # add exceptions node
                    if i.exception_analysis is not None:
                        id_exceptions = self.new_id(i.exception_analysis, l_id)
                        buff_nodes += self.add_exception_node(i.exception_analysis, id_exceptions)
                        buff_edges += self.add_edge(None, id_exceptions, None, id_i, l_eid, 2)

                buff_edges += self.add_edge(None, id_method, None, id_method + 1, l_eid, 2)

            buff += buff_nodes
            buff += buff_edges

            buff += "</graph>\n"
            buff += "</graphml>\n"

            H[name] = buff
        return H


class Directory(object):
    def __init__(self, name):
        self.name = name
        self.basename = os.path.basename(name)
        self.color = "FF0000"

        self.width = len(self.name)

    def set_color(self, color):
        self.color = color


class File(object):
    def __init__(self, name, file_type, file_crc):
        self.name = name
        self.basename = os.path.basename(name)
        self.file_type = file_type
        self.file_crc = file_crc

        self.color = "FFCC00"

        self.width = max(len(self.name), len(self.file_type))


def splitall(path, z):
    if len(path) == 0:
        return

    l = os.path.split(path)
    z.append(l[0])

    for i in l:
        return splitall(i, z)


class ApkViewer(object):
    def __init__(self, a):
        self.a = a

        self.G = DiGraph()
        self.all_files = {}
        self.ids = {}

        root = Directory("APK")
        root.set_color("00FF00")

        self.ids[root] = len(self.ids)
        self.G.add_node(root)

        for x, y, z in self.a.get_files_information():
            print(x, y, z, os.path.basename(x))

            l = []
            splitall(x, l)
            l.reverse()
            l.pop(0)

            last = root
            for i in l:
                if i not in self.all_files:
                    tmp = Directory(i)
                    self.ids[tmp] = len(self.ids)
                    self.all_files[i] = tmp
                else:
                    tmp = self.all_files[i]

                self.G.add_edge(last, tmp)
                last = tmp

            n1 = last
            n2 = File(x, y, z)
            self.G.add_edge(n1, n2)

            self.ids[n2] = len(self.ids)

    def export_to_gml(self):
        buff = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n"
        buff += "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:y=\"http://www.yworks.com/xml/graphml\" xmlns:yed=\"http://www.yworks.com/xml/yed/3\" xsi:schemaLocation=\"http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd\">\n"

        buff += "<key attr.name=\"description\" attr.type=\"string\" for=\"node\" id=\"d5\"/>\n"
        buff += "<key for=\"node\" id=\"d6\" yfiles.type=\"nodegraphics\"/>\n"

        buff += "<graph edgedefault=\"directed\" id=\"G\">\n"

        for node in self.G.nodes():
            print(node)

            buff += "<node id=\"%d\">\n" % self.ids[node]
            buff += "<data key=\"d6\">\n"
            buff += "<y:ShapeNode>\n"

            buff += "<y:Geometry height=\"%f\" width=\"%f\"/>\n" % (60.0, 7 * node.width)
            buff += "<y:Fill color=\"#%s\" transparent=\"false\"/>\n" % node.color

            buff += "<y:NodeLabel>\n"
            buff += "%s\n" % node.basename

            if isinstance(node, File):
                buff += "%s\n" % node.file_type
                buff += "%s\n" % hex(node.file_crc)

            buff += "</y:NodeLabel>\n"

            buff += "</y:ShapeNode>\n"
            buff += "</data>\n"

            buff += "</node>\n"

        nb = 0
        for edge in self.G.edges():
            buff += "<edge id=\"%d\" source=\"%d\" target=\"%d\">\n" % (nb, self.ids[edge[0]], self.ids[edge[1]])
            buff += "</edge>\n"
            nb += 1

        buff += "</graph>\n"
        buff += "</graphml>\n"

        return buff
