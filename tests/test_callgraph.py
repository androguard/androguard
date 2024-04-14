from androguard.misc import AnalyzeAPK
from androguard.core.analysis.analysis import ExternalMethod

import os
import unittest

test_dir = os.path.dirname(os.path.abspath(__file__))

class TestCallgraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_apk_path = os.path.join(test_dir, 'data/APK/TestActivity.apk')
        cls.a, cls.d, cls.dx = AnalyzeAPK(test_apk_path)

    def _get_num_nodes(self, callgraph):
        num_external = 0
        num_internal = 0

        for n in callgraph:
            if isinstance(n, ExternalMethod):
                num_external+=1
            else:
                num_internal+=1

        return callgraph.number_of_nodes(), num_external, num_internal

    def testCallgraphTotalNodesEdges(self):
        """test callgraph generated with default parameter values"""
        callgraph = self.dx.get_call_graph()

        total_nodes, total_external_nodes, total_internal_nodes = self._get_num_nodes(callgraph)

        # ensure total of internal and external nodes equals the total nodes
        self.assertEqual(total_nodes, total_external_nodes + total_internal_nodes)

        # total num nodes
        self.assertEqual(total_nodes, 3600)

        # num external nodes
        self.assertEqual(total_external_nodes, 1000)

        # num internal nodes
        self.assertEqual(total_internal_nodes, 2600)

        # total num edges
        self.assertEqual(callgraph.number_of_edges(), 4490)


    def testCallgraphFilterClassname(self):
        """test callgraph with classname filter parameter"""
        callgraph = self.dx.get_call_graph(classname='Ltests/androguard/*')

        total_nodes, total_external_nodes, total_internal_nodes = self._get_num_nodes(callgraph)
        
        self.assertEqual(total_nodes, 165)
        self.assertEqual(total_external_nodes, 41)
        self.assertEqual(total_internal_nodes, 124)

        self.assertEqual(callgraph.number_of_edges(), 197)

    def testCallgraphFilterMethodname(self):
        """test callgraph with methodname filter parameter"""
        callgraph = self.dx.get_call_graph(methodname='Test*')

        total_nodes, total_external_nodes, total_internal_nodes = self._get_num_nodes(callgraph)
        
        self.assertEqual(total_nodes, 36)
        self.assertEqual(total_external_nodes, 12)
        self.assertEqual(total_internal_nodes, 24)
        self.assertEqual(callgraph.number_of_edges(), 42)

    def testCallgraphFilterDescriptor(self):
        """test callgraph with descriptor filter parameter"""
        callgraph = self.dx.get_call_graph(descriptor='\(LTestDefaultPackage;\sI\sI\sLTestDefaultPackage\$TestInnerClass;\)V')

        total_nodes, total_external_nodes, total_internal_nodes = self._get_num_nodes(callgraph)
        
        self.assertEqual(total_nodes, 2)
        self.assertEqual(total_external_nodes, 0)
        self.assertEqual(total_internal_nodes, 2)
        self.assertEqual(callgraph.number_of_edges(), 1)

        # since this is a small graph, let's check some additional values

        # get the source and destination node of the only edge
        src_node, dst_node = list(callgraph.edges)[0]

        # check source node
        self.assertEqual(src_node.get_class_name(), 'LTestDefaultPackage$TestInnerClass;')
        self.assertEqual(src_node.get_name(), '<init>')
        self.assertEqual(src_node.get_access_flags_string(), 'synthetic constructor')
        self.assertEqual(src_node.get_descriptor(), '(LTestDefaultPackage; I I LTestDefaultPackage$TestInnerClass;)V')

        # check dest node
        self.assertEqual(dst_node.get_class_name(), 'LTestDefaultPackage$TestInnerClass;')
        self.assertEqual(dst_node.get_name(), '<init>')
        self.assertEqual(dst_node.get_access_flags_string(), 'private constructor')
        self.assertEqual(dst_node.get_descriptor(), '(LTestDefaultPackage; I I)V')

if __name__ == '__main__':
    unittest.main()