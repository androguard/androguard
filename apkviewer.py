#!/usr/bin/env python

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

from networkx import DiGraph                                                                                                                                                                     
from xml.sax.saxutils import escape, unescape
import sys, hashlib, os
from optparse import OptionParser

PATH_INSTALL = "./"																																																			   
sys.path.append(PATH_INSTALL + "./")

import androguard, apk, dvm, analysis, ganalysis, androconf 

option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input (dex, apk)', 'nargs' : 1 }
option_1 = { 'name' : ('-o', '--output'), 'help' : 'directory output', 'nargs' : 1 }

options = [option_0, option_1]

def create_directory( class_name, output ) :
    output_name = output
    if output_name[-1] != "/" :
        output_name = output_name + "/"

    try :
        os.makedirs( output_name + class_name )
    except OSError :
        pass

def create_directories( vm, output ) :
    for class_name in vm.get_classes_names() :
        z = os.path.split( class_name )[0]
        create_directory( z[1:], output )

class DexViewer :
    def __init__(self, vm, vmx, gvmx) :
        self.vm = vm
        self.vmx = vmx
        self.gvmx = gvmx
    
    def add_method_node(self, i, id_i) :
        buff = "<node id=\"%d\">\n" % id_i
        buff += "<data key=\"d6\">\n"
        buff += "<y:ShapeNode>\n"
        
        height = 2 
        width = 2
        label = ""
        
        label += i.get_name()
        label += i.get_descriptor()
        
        buff += "<y:Geometry height=\"%f\" width=\"%f\"/>\n" % (16 * height, 7 * width)
        buff += "<y:Fill color=\"#%s\" transparent=\"false\"/>\n" % "FF0000"

        buff += "<y:NodeLabel alignment=\"left\" autoSizePolicy=\"content\" fontFamily=\"Dialog\" fontSize=\"13\" fontStyle=\"plain\" hasBackgroundColor=\"false\" hasLineColor=\"false\" modelName=\"internal\" modelPosition=\"c\" textColor=\"#000000\" visible=\"true\">\n"

        buff += escape(label)

        buff += "</y:NodeLabel>\n"
        buff += "</y:ShapeNode>\n"
        buff += "</data>\n"

        buff += "</node>\n"

        return buff

    def add_node(self, i, id_i) :
        buff = "<node id=\"%d\">\n" % id_i
        buff += "<data key=\"d6\">\n"
        buff += "<y:ShapeNode>\n"
        
        height = 0
        width = 0
        idx = i.start
        label = ""
        for ins in i.ins :
            c_label = "%x %s\n" % (idx, self.vm.dotbuff(ins, idx))
            idx += ins.get_length()
            label += c_label
            width = max(width, len(c_label)) 
            height += 1

        if height < 10 :
            height += 3 
            
        buff += "<y:Geometry height=\"%f\" width=\"%f\"/>\n" % (16 * height, 7 * width)
        buff += "<y:Fill color=\"#%s\" transparent=\"false\"/>\n" % "FFCC00"

        buff += "<y:NodeLabel alignment=\"left\" autoSizePolicy=\"content\" fontFamily=\"Dialog\" fontSize=\"13\" fontStyle=\"plain\" hasBackgroundColor=\"false\" hasLineColor=\"false\" modelName=\"internal\" modelPosition=\"c\" textColor=\"#000000\" visible=\"true\">\n"

        buff += escape(label)

        buff += "</y:NodeLabel>\n"
        buff += "</y:ShapeNode>\n"
        buff += "</data>\n"

        buff += "</node>\n"

        return buff

    def add_edge(self, i, id_i, j, id_j, l_eid, val) :
        buff = "<edge id=\"%d\" source=\"%d\" target=\"%d\">\n" % (len(l_eid), id_i, id_j)
        
        buff += "<data key=\"d9\">\n"
        buff += "<y:PolyLineEdge>\n"
        buff += "<y:Arrows source=\"none\" target=\"standard\"/>\n"

        if val == 0 :
            buff += "<y:LineStyle color=\"#00FF00\" type=\"line\" width=\"1.0\"/>\n"
        elif val == 1 :
            buff += "<y:LineStyle color=\"#FF0000\" type=\"line\" width=\"1.0\"/>\n"
        else :
            buff += "<y:LineStyle color=\"#0000FF\" type=\"line\" width=\"1.0\"/>\n"

        buff += "</y:PolyLineEdge>\n"
        buff += "</data>\n"

        buff += "</edge>\n"

        l_eid[ "%d+%d" % (id_i, id_j) ] = len(l_eid)
        return buff

    def new_id(self, i, l) :
        try :
            return l[i]
        except KeyError :
            l[i] = len(l)
            return l[i]

    def export_to_gml(self, output) :
        self.gvmx.export_to_gml( output + "/" + "methodcalls.graphml" )

        for _class in self.vm.get_classes() :
            name = _class.get_name()
            name = name[1:-1]
            fd = open(output + "/" + name + ".graphml", "w")
            fd.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n")
            fd.write("<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:y=\"http://www.yworks.com/xml/graphml\" xmlns:yed=\"http://www.yworks.com/xml/yed/3\" xsi:schemaLocation=\"http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd\">\n")
        
            fd.write("<key attr.name=\"description\" attr.type=\"string\" for=\"node\" id=\"d5\"/>\n")
            fd.write("<key for=\"node\" id=\"d6\" yfiles.type=\"nodegraphics\"/>\n")
            fd.write("<key for=\"edge\" id=\"d9\" yfiles.type=\"edgegraphics\"/>\n")
        
            fd.write("<graph edgedefault=\"directed\" id=\"G\">\n")

            print name

            buff_nodes = ""
            buff_edges = ""
            l_id = {}
            l_eid = {}

            for method in _class.get_methods() :
                mx = self.vmx.get_method( method )
                
                id_method = self.new_id(method, l_id)
                buff_nodes += self.add_method_node(method, id_method)

                for i in mx.basic_blocks.get() :
                    
                    id_i = self.new_id(i, l_id)
                    print i, id_i
                    buff_nodes += self.add_node( i, id_i )
                    
                    val = 0
                    if len(i.childs) > 1 :
                        val = 1
                    elif len(i.childs) == 1 :
                        val = 2

                    for j in i.childs :
                        print "\t", j

                        id_j = self.new_id(j[-1], l_id)
                        buff_edges += self.add_edge(i, id_i, j[-1], id_j, l_eid, val)
                        if val == 1 :
                            val = 0

                buff_edges += self.add_edge(None, id_method, None, id_method+1, l_eid, 2)

            fd.write(buff_nodes)
            fd.write(buff_edges)

            fd.write("</graph>\n")
            fd.write("</graphml>\n")
            fd.close()

class Directory :
    def __init__(self, name) :
        self.name = name
        self.basename = os.path.basename(name)
        self.color = "FF0000"

        self.width = len(self.name)

    def set_color(self, color) :
        self.color = color

class File :
    def __init__(self, name, file_type, file_crc) :
        self.name = name
        self.basename = os.path.basename(name)
        self.file_type = file_type
        self.file_crc = file_crc
        
        self.color = "FFCC00"

        self.width = max(len(self.name), len(self.file_type))

def splitall(path, z) :
    if len(path) == 0 :
        return

    l = os.path.split( path )
    z.append(l[0])

    for i in l :
        return splitall( i, z )

class ApkViewer :
    def __init__(self, a) :
        self.a = a

        self.G = DiGraph()
        self.all_files = {}
        self.ids = {}

        root = Directory( "APK" )
        root.set_color( "00FF00" )

        self.ids[ root ] = len(self.ids)
        self.G.add_node( root )

        for x, y, z in self.a.get_files_information() :
            print x, y, z, os.path.basename(x)
            
            l = []
            splitall( x, l )
            l.reverse()
            l.pop(0)

            
            last = root
            for i in l :
                if i not in self.all_files :
                    tmp = Directory( i )
                    self.ids[ tmp ] = len(self.ids)
                    self.all_files[ i ] = tmp
                else :
                    tmp = self.all_files[ i ]

                self.G.add_edge(last, tmp)
                last = tmp

            n1 = last 
            n2 = File( x, y, z ) 
            self.G.add_edge(n1, n2)
            
            self.ids[ n2 ] = len(self.ids)
        
    def export_to_gml(self, output) :
        fd = open(output + "apk.graphml", "w")
        fd.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n")
        fd.write("<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:y=\"http://www.yworks.com/xml/graphml\" xmlns:yed=\"http://www.yworks.com/xml/yed/3\" xsi:schemaLocation=\"http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd\">\n")
        
        fd.write("<key attr.name=\"description\" attr.type=\"string\" for=\"node\" id=\"d5\"/>\n")
        fd.write("<key for=\"node\" id=\"d6\" yfiles.type=\"nodegraphics\"/>\n")

        
        fd.write("<graph edgedefault=\"directed\" id=\"G\">\n")

        
        for node in self.G.nodes() :
            print node

            fd.write("<node id=\"%d\">\n" % self.ids[node])
            fd.write("<data key=\"d6\">\n")
            fd.write("<y:ShapeNode>\n")
            
            fd.write("<y:Geometry height=\"%f\" width=\"%f\"/>\n" % (60.0, 7 * node.width))
            fd.write("<y:Fill color=\"#%s\" transparent=\"false\"/>\n" % node.color)

            fd.write("<y:NodeLabel>\n")
            fd.write("%s\n" % node.basename)

            if isinstance(node, File) :
                fd.write("%s\n" % node.file_type)
                fd.write("%s\n" % hex(node.file_crc))
            
            fd.write("</y:NodeLabel>\n")

            fd.write("</y:ShapeNode>\n")
            fd.write("</data>\n")

            fd.write("</node>\n")

        nb = 0
        for edge in self.G.edges() :
            fd.write("<edge id=\"%d\" source=\"%d\" target=\"%d\">\n" % (nb, self.ids[edge[0]], self.ids[edge[1]]))
            fd.write("</edge>\n")
            nb += 1

        fd.write("</graph>\n")
        fd.write("</graphml>\n")
        fd.close()



def main(options, arguments) :
    if options.input != None and options.output != None :

        ret_type = androconf.is_android( options.input )
        vm = None
        a = None
        if ret_type == "APK"  :
            a = apk.APK( options.input )
            if a.is_valid_APK() :
                print a.get_files_types()
                print a.get_files_crc32()

                #a.export_to_gml()
                vm = dvm.DalvikVMFormat( a.get_dex() )
            else :
                print "INVALID APK"
        elif ret_type == "DEX" :
            try :
                vm = dvm.DalvikVMFormat( open(options.input, "rb").read() )
            except Exception, e :
                print "INVALID DEX", e

        av = ApkViewer( a )
        av.export_to_gml( options.output )

        vmx = analysis.VMAnalysis( vm )
        gvmx = ganalysis.GVMAnalysis( vmx, a )
 
        create_directories( vm, options.output )

        dv = DexViewer( vm, vmx, gvmx )
        dv.export_to_gml( options.output )

if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
	  param = option['name']
	  del option['name']
	  parser.add_option(*param, **option)

	  
   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)	
