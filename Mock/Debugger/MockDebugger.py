'''
Created on 2 Oct 2012

@author: francis
'''
from Mock.Debugger.Sinks.FileSink import FileSink
from Mock.Debugger.Sinks.NullSink import NullSink
from Mock.Debugger.Sinks.ServerSink import ServerSink
from Mock.Debugger.iMockDebugger import iMockDebugger
from Mock.Debugger.iMockDebuggerSink import iMockDebuggerSink
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.QueueServer import QueueServer
from multiprocessing.queues import Queue
from multiprocessing.synchronize import RLock

class MockDebugger(iMockDebugger, iMockDebuggerSink):
    def __init__(self, methods=None, quiet=True):
        self._methods = []
        methods = iMockDebuggerSink()._getMethods()
        self._methods = methods
        self._enabled = False
        self._quiet = quiet
        self._lock = RLock()
        self._sink = None
    def start(self, peerName, theTime, filename=None, server=None):
        #    Stop an existing debugger:
        with self._lock:
            self.stop()
            #    Create the new one:
            if filename!=None:
                self._sink = FileSink(peerName, theTime, filename, self._quiet)
            elif server!=None:
                self._sink = ServerSink(peerName, theTime, server, self._quiet)
            else:
                self._sink = NullSink()
            result = self._sink.start()
            self._sink.waitUntilRunning()
            self._enabled = True
            return result
    def stop(self):
        result = "sink.not.closed"
        with self._lock:
            if self._sink!=None:
                result = self._sink.close()  #    Must be synchronous!
                self._sink = None
            self._enabled = False
        return result
    def _getUid(self, **kwargs):
        if "uu" in kwargs:
            uu = kwargs["uu"]
            if uu!=None:
                return uu
        return MockDebugger.newUid(self)
    def __getattribute__(self, name):
        if name in object.__getattribute__(self, "_methods"):
            if self._sink==None:
                def MockHandler(*args, **kwargs):
                    pass
                return MockHandler
            def genericSinkMethod(peerName, relativeTime, *args, **kwargs):
                uu = self._getUid(**kwargs)
                kwargs["uu"] = uu
                #    Call the sink-method with modified args:
                attr = getattr(self._sink, name)
                attr(self, peerName, relativeTime, *args, **kwargs)
                return uu
            return genericSinkMethod
        return object.__getattribute__(self, name)

if __name__ == '__main__':
    md = MockDebugger()
    a = md.finish_end("peerName", "relativeTime")
    print a
    md.start(filename="mock.file")
    a = md.setup_start("peerName123", "relativeTime123")
    print a
    #    Start a dummyQueueServer:
    q = Queue()
    m = MarshallerFactory.get(MarshallerFactory.DEFAULT)
    QS = QueueServer(port=22334, target=q, quiet=True, marshaller=m)
    QS.start()
    details = QS.details()
    md.start(server=details)
    a = md.setup_start("peerName123", "relativeTime123")
    print a
    data = q.get(block=True, timeout=10)
    QS.close()













