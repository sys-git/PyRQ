'''
Created on 13 Sep 2012

@author: francis
'''

from Mock.Pinger import Pinger
from PyRQ.Core.Linkage.Linkage import Linkage
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.QueueServer import QueueServer
from PyRQ.Core.QueueServer.QueueServerHandler import QueueServerHandler
from PyRQ.Core.QueueServer.SubprocessQueueServer import SubprocessQueueServer
from PyRQ.Core.QueueWriter.QueueWriter import QueueWriter
from PyRQ.RRQ.Messages.Ping import Ping
from multiprocessing.queues import Queue
import unittest

class TestServer(unittest.TestCase):
    def setUp(self,
              host="127.0.0.1",
              port="11223",
              portReplyTo=44332,
              marshaller=MarshallerFactory.DEFAULT,
              quiet=True,
              maxClients=1,
              recvChunkSize=1024,
              readTimeout=1
              ):
        self.details = None
        self.quiet = quiet
        self.host = host
        self.port = port
        self.portReplyTo = portReplyTo
        self.maxClients = maxClients
        self.recvChunkSize = recvChunkSize
        self.readTimeout = readTimeout
        self.TIMEOUT = 2
        self.target = Queue()
        self.m = MarshallerFactory.get(marshaller, quiet=self.quiet)
        self._createQueueServer()
        #    Create the QueueWriter:
        self.qw = QueueWriter(target=self.details,
                              quiet=self.quiet,
                              marshaller=self.m,
                              autoConnect=True)
    def tearDown(self):
        try:
            self.qs.close()
        except Exception, _e:
            pass
        self.qw.close()
        self.target.close()
        del self.target

class TestSameProcessInlineServer(TestServer):
    def _createQueueServer(self):
        #    Create the QueueServer programatically in our Process (not vi a a shell-out (yet))...
        self.qs = QueueServer(host=self.host,
                              port=self.port,
                              target=self.target,
                              marshaller=self.m,
                              hunt=True,
                              quiet=self.quiet,
                              maxClients=self.maxClients,
                              recvChunkSize=self.recvChunkSize,
                              readTimeout=self.readTimeout,
                              )
        #    ...and set it serving:
        self.qs.start().waitUntilRunning()
        #    not forgetting to save it's connection details.
        self.details = self.qs.details()
    def testDoubleClose(self):
        assert self.qs.close()
        assert self.qs.close()
    def testSimpleSend(self):
        #    Send some data and check that it's put onto the target queue.
        eResult = {"hello.world!":{123:456}}
        self.qw.put(eResult)
        received = self.target.get(True, timeout=self.TIMEOUT)
        assert received==eResult

class TestSameProcessExternalServer(TestServer):
    def tearDown(self):
        try:    self.rqs.close()
        except: pass
        super(TestSameProcessExternalServer, self).tearDown()
    def testDoubleClose(self):
        assert self.qs.close()
        assert self.qs.close()
    def _createQueueServer(self):
        #    Create the QueueServer by using os.system or Subprocess.
        #    Create a reply-to Ping server:
        self.rqs= QueueServer(host=self.host,
                              port=self.portReplyTo,
                              target=self.target,
                              marshaller=self.m,
                              hunt=True,
                              quiet=self.quiet,
                              maxClients=self.maxClients,
                              recvChunkSize=self.recvChunkSize,
                              readTimeout=self.readTimeout,
                              )
        self.rqs.start().waitUntilRunning()
        #    Now create the subprocess server:
        desiredPort = 50001
        linkage = Linkage.create(Pinger)
        self.qs = SubprocessQueueServer(handlerClazz=Linkage.create(QueueServerHandler),
                                        desiredPort=desiredPort,
                                        linkage=linkage,
                                        quiet=self.quiet)
        self.details = self.qs.details()
    def testSimpleSendPingRoundtrip(self):
        details = self.rqs.details()
        eResult = Ping(replyTo=details, data={"hello.world!":{123:456}}, quiet=self.quiet)
        self.qw.put(eResult)
        received = self.target.get(True, timeout=self.TIMEOUT)
        assert received==eResult












