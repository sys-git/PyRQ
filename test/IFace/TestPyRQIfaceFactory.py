'''
Created on 17 Oct 2012

@author: francis
'''

from PyRQ.Iface.PyRQIface import PyRQIface
from PyRQ.Iface.PyRQIfaceFactory import PyRQIfaceFactory
from PyRQ.Iface.PyRQIfaceType import PyRQIfaceType
from PyRQ.Iface.QIface import QIface
from PyRQ.Iface.UnknownInterfaceError import UnknownInterfaceError
import unittest

class TestPyRQIfaceFactory(unittest.TestCase):
    def testPyRQ(self):
        q = PyRQIfaceFactory.get(type_=PyRQIfaceType.PYRQ)
        assert isinstance(q, PyRQIface)
    def testMultiprocessingQ(self):
        q = PyRQIfaceFactory.get(type_=PyRQIfaceType.MULTIPROCESSING_QUEUE)
        assert isinstance(q, QIface)
    def testUnknownQueueType(self):
        XYZ = "xyz"
        assert XYZ not in [PyRQIfaceType.PYRQ, PyRQIfaceType.MULTIPROCESSING_QUEUE]
        try:
            PyRQIfaceFactory.get(type_=XYZ)
        except UnknownInterfaceError, _e:
            assert True
        else:
            assert False






if __name__ == '__main__':
    unittest.main()
