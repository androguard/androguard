from androguard.core.bytecodes.dvm_types import TypeMapItem

import unittest

class LoadOrderTest(unittest.TestCase):
    def testLoadOrder(self):
        load_order = TypeMapItem.determine_load_order()
        ordered = sorted(load_order, key=lambda i: load_order[i])

        dependencies = TypeMapItem._get_dependencies()

        treated = []

        for item in ordered:
            for dependency in dependencies[item]:
                self.assertIn(dependency, treated)
            treated.append(item)

if __name__ == '__main__':
    unittest.main()