# This file is part of Androguard.
#
# Copyright (C) 2012 Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
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

import random

from androconf import error
import jvm

class Automaton :
    def __init__(self, _analysis) :
        self.__analysis = _analysis

        try :
            from networkx import DiGraph
            from networkx import draw_graphviz, write_dot
        except ImportError :
            error("module networkx not found")

        self.__G = DiGraph()

        for m in self.__analysis.get_methods() :
            for bb in m.basic_blocks.get() :
                for trace in bb.stack_traces.get() :
                    for mre in jvm.MATH_JVM_RE :
                        if mre[0].match( trace[2].get_name() ) :
                            for i in trace[3].gets() :
                                self._add( str(i) )

    def _add(self, elem) :
        l = []
        x = ""
        for i in elem :
            if i not in jvm.MATH_JVM_OPCODES.values() :
                x += i
            else :
                l.append( x )
                l.append( i )
                x = ""

        if len(l) > 1 :
            l.append( x )

        self._add_expr( l )

    def _add_expr(self, l) :
        if l == [] :
            return
        i = 0
        while i < (len(l)-1) :
            self.__G.add_edge( self._transform(l[i]), self._transform(l[i+1]) )

            i += 1

    def _transform(self, i) :
        if "VARIABLE" in i :
            return "V"
        return i

    def new(self, loop) :
        expr = []

        l = list( self.__G.node )

        init = l[ random.randint(0, len(l) - 1) ]
        while init in jvm.MATH_JVM_OPCODES.values() :
            init = l[ random.randint(0, len(l) - 1) ]

        expr.append( init )

        i = 0
        while i <= loop :
            l = list( self.__G.edge[ init ] )
            if l == [] :
                break

            init =  l[ random.randint(0, len(l) - 1) ]
            expr.append( init )

            i += 1

        return expr

    def show(self) :
        print self.__G.node
        print self.__G.edge

        #draw_graphviz(self.__G)
        #write_dot(self.__G,'file.dot')

class JVMGenerate :
    def __init__(self, _vm, _analysis) :
        self.__vm = _vm
        self.__analysis = _analysis

        self.__automaton = Automaton( self.__analysis )
        self.__automaton.show()

    def create_affectation(self, method_name, desc) :
        l = []

        if desc[0] == 0 :
            l.append( [ "aload_0" ] )
            l.append( [ "bipush", desc[2] ] )
            l.append( [ "putfield", desc[1].get_name(), desc[1].get_descriptor() ] )

        return l

    def write(self, method, offset, field) :
        print method, offset, field
        expr = self.__automaton.new( 5 )

        print field.get_name(), "EXPR ->", expr

        self._transform( expr )


    def _transform(self, expr) :
        if len(expr) == 1 :
            return

        x = [ expr.pop(0), expr.pop(1), expr.pop(0) ]

#      while expr != [] :
