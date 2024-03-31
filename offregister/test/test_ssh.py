# -*- coding: utf-8 -*-
from unittest import TestCase
from unittest import main as unittest_main

from offutils import obj_to_d, pp
from offutils_strategy_register import list_nodes


class TestSSH(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = list_nodes()
        if not len(cls.nodes):
            raise AssertionError("No nodes found to process")

    def test_(self):
        for node_name in self.nodes:
            node = self.nodes[node_name]
            pp(obj_to_d(node))


if __name__ == "__main__":
    unittest_main()
