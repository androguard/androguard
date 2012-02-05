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
import sys, hashlib, os
from optparse import OptionParser

PATH_INSTALL = "./"																																																			   
sys.path.append(PATH_INSTALL + "./")

import androguard, apk, dvm, analysis, ganalysis, androconf 

option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input (dex, apk)', 'nargs' : 1 }
option_1 = { 'name' : ('-o', '--output'), 'help' : 'filename output of the apk graphml', 'nargs' : 1 }

options = [option_0, option_1]

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
    def __init__(self, a, output) :
        self.a = a
        self.output = output

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
        
    def export_to_gml(self) :
        fd = open(self.output, "w")
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

        av = ApkViewer( a, options.output )
        av.export_to_gml()

        #vmx = analysis.VMAnalysis( vm )
        #gvmx = ganalysis.GVMAnalysis( vmx, a )

        #gvmx.export_to_gmf()

if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
	  param = option['name']
	  del option['name']
	  parser.add_option(*param, **option)

	  
   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)	
