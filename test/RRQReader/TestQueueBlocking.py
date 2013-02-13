'''
Created on 20 Sep 2012

@author: francis
'''

from Mock.mock import MockHandler
from PyRQ.Core.Errors.ClosedError import ClosedError
from PyRQ.Core.Errors.Finished import Finished
from PyRQ.Core.Linkage.Linkage import Linkage
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.SubprocessQueueServer import SubprocessQueueServer
from PyRQ.Iface.PyRQIface import PyRQIface
from Queue import Full, Empty
from multiprocessing.queues import Queue
from random import Random
import sys
import threading
import time
import unittest
#from PyRQ.Core.Linkage.Linkage import Linkage

class TestBlockingMethods(unittest.TestCase):
    def setUp(self):
        self.quiet=True
        self.random = Random()
        self._timers = []
        self.namespaces = []
        self.iface = PyRQIface(quiet=self.quiet, ref="test")
        self.dummyQueue = Queue()
        self.marshaller = MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=self.quiet)
        desiredPort = "19001"
        self.r = SubprocessQueueServer(
                                       desiredPort=desiredPort,
                                       handlerClazz=Linkage.create(MockHandler),
                                       quiet=self.quiet
#           includePydevd="/home/francis/.eclipse/org.eclipse.platform_3.7.0_155965261/plugins/org.python.pydev.debug_2.5.0.2012040618/pysrc"
           )
        PyRQIface.setGlobalPYRQ(self.r.details())
        self.r.start().waitUntilRunning()
        pass
    def tearDown(self):
        try:
            self.dummyQueue.close()
            del self.dummyQueue
        except Exception, _e:
            pass
        for namespace in self.namespaces:
            self.iface.setNamespace(namespace)
        try:    self.iface.close()
        except ClosedError, _e:
            pass
        try:    self.r.close()
        except: pass
        for i in self._timers:
            try:    i.cancel()
            except: pass
    def _createInterface(self, maxsize=1):
        namespace = self.iface.create(maxsize=maxsize)
        self.namespaces.append(namespace)
        return namespace
    def _closeQueue(self, namespace, delay=0, name="Closer"):
        iface = PyRQIface(namespace=namespace, quiet=self.quiet, ref=name)
        def close(d):
            if delay!=None:
                time.sleep(delay)
            sys.stderr.write("Closing interface\r\n")
            iface.close()
            sys.stderr.write("Interface closed\r\n")
        t = threading.Timer(0, close, args=[delay])
        t.setDaemon(True)
        t.setName("Closer")
        t.start()
    def testDelayedGetThenClosed(self, maxsize=1):
        r"""
        @summary: Test what happens to a q.get(block=True, timeout=lots)
        when the socket is remotely closed.
        """
        iface = PyRQIface(quiet=self.quiet, ref="creator-testDelayedGetWithTimeoutThenClosed")
        namespace = iface.create(maxsize=maxsize)
        self._closeQueue(namespace, delay=2, name="closer-testDelayedGetThenClosed")
        iface = PyRQIface(namespace=namespace, quiet=self.quiet, ref="testDelayedGetThenClosed")
        try:
            data = iface.get(block=True, timeout=None)
        except (ClosedError, Finished):
            assert True
        else:
            print "got data in eror: ", data
            assert False
    def testDelayedGetWithTimeoutThenClosed(self, maxsize=1):
        r"""
        @summary: Test what happens to a q.get(block=True, timeout=lots)
        when the socket is remotely closed.
        """
        iface = PyRQIface(quiet=self.quiet, ref="creator-testDelayedGetWithTimeoutThenClosed")
        namespace = iface.create(maxsize=maxsize)
        self._closeQueue(namespace, delay=1, name="closer-testDelayedGetWithTimeoutThenClosed")
        iface = PyRQIface(namespace=namespace, quiet=self.quiet, ref="testDelayedGetWithTimeoutThenClosed")
        try:
            iface.get(block=True, timeout=10)
        except (ClosedError, Empty):
            assert True
        else:
            assert False
    def testDelayedPutThenClosed(self, maxsize=1):
        #    Put 2 items, second one should block forever, then we close the q.
        iface = PyRQIface(quiet=self.quiet, ref="creator-testDelayedPutThenClosed")
        namespace = iface.create(maxsize=maxsize)
        iface = PyRQIface(namespace=namespace, quiet=self.quiet, ref="testDelayedPutThenClosed")
        iface.put("hello.world.1", block=True, timeout=None)
        self._closeQueue(namespace, delay=1, name="closer-testDelayedPutThenClosed")
        #    Queue should now be full.
        try:
            iface.put("hello.world.2", block=True, timeout=None)
        except (ClosedError, Finished):
            assert True
        else:
            assert False
    def testDelayedWithTimeoutPutThenClosed(self, maxsize=1):
        #    Put 2 items, second one should block forever, then we close the q.
        iface = PyRQIface(quiet=self.quiet, ref="creator-testDelayedWithTimeoutPutThenClosed")
        namespace = iface.create(maxsize=maxsize)
        iface = PyRQIface(namespace=namespace, quiet=self.quiet, ref="testDelayedWithTimeoutPutThenClosed")
        iface.put("hello.world.1", block=True, timeout=None)
        #    Queue should now be full.
        self._closeQueue(namespace, delay=2, name="closer-testDelayedWithTimeoutPutThenClosed")
        try:
            iface.put("hello.world.2", block=True, timeout=5)
        except (ClosedError, Full):
            assert True
        else:
            assert False
    def testPutOnFullQueueWithTimeout(self, maxsize=1):
        #    Put 2 items, second one should block forever, then we close the q.
        iface = PyRQIface(quiet=self.quiet, ref="creator-testDelayedWithTimeoutPutThenClosed")
        namespace = iface.create(maxsize=maxsize)
        iface = PyRQIface(namespace=namespace, quiet=self.quiet, ref="testDelayedWithTimeoutPutThenClosed")
        iface.put("hello.world.1", block=True, timeout=None)
        #    Queue should now be full.
        try:
            iface.put("hello.world.2", block=True, timeout=2)
        except Full, _e:
            assert True
        else:
            assert False

if __name__ == '__main__':
    unittest.main()
