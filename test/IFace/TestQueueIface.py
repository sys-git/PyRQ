'''
Created on 17 Oct 2012

@author: francis
'''

from PyRQ.Iface.QIface import QIface
import unittest

class TestCreate(unittest.TestCase):
    def setUp(self):
        self.iface = QIface()
        assert self.iface._namespace==None
    def tearDown(self):
        try:
            self.iface.close()
        except: pass
        QIface._cache = {}
    def testCreate(self):
        namespace = self.iface._namespace
        iface = self.iface.create()
        assert not isinstance(iface, QIface)
        assert isinstance(iface, basestring)
        iface = QIface(iface)
        assert self.iface._namespace==namespace
        assert iface._namespace!=namespace
        assert len(QIface._cache.keys())==1
    def testCreateMultiple(self):
        namespace = self.iface._namespace
        for count in xrange(1, 100):
            iface = self.iface.create()
            assert not isinstance(iface, QIface)
            assert isinstance(iface, basestring)
            assert self.iface._namespace==namespace
            iface = QIface(iface)
            assert iface._namespace!=namespace
            assert len(QIface._cache.keys())==count
            iface.close()

class TestQueueIfaceNoUnderlyingQueue(unittest.TestCase):
    def setUp(self):
        self.iface = QIface()
        assert self.iface._namespace==None
    def tearDown(self):
        pass
    def testClose(self):
        try:
            self.iface.close()
        except KeyError, _e:
            assert True
        else:
            assert False
    def testGet(self):
        try:
            self.iface.get()
        except KeyError, _e:
            assert True
        else:
            assert False
    def testPut(self):
        try:
            self.iface.put("")
        except KeyError, _e:
            assert True
        else:
            assert False
    def testQSize(self):
        try:
            self.iface.qsize()
        except KeyError, _e:
            assert True
        else:
            assert False
    def testMaxQSize(self):
        try:
            self.iface.maxQSize()
        except KeyError, _e:
            assert True
        else:
            assert False
    def testSetNamespace(self):
        namespace=self.iface._namespace
        iface = self.iface.create()
        iface = QIface(iface)
        self.iface.setNamespace(iface._namespace)
        assert iface._namespace==self.iface._namespace
        assert iface._namespace!=namespace



if __name__ == '__main__':
    unittest.main()
