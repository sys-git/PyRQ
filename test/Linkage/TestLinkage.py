'''
Created on 17 Sep 2012

@author: francis
'''

import unittest
from PyRQ.Core.Linkage.Linkage import Linkage
from test.testArtefacts.ModuleName import Classicname

class TestLinkage(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test(self):
        result = Linkage.create(Classicname)
        assert isinstance(result, Linkage)
        assert result.clazz()=="Classicname"
        assert result.clazzpath()=="test.testArtefacts.ModuleName"

if __name__ == '__main__':
    unittest.main()
