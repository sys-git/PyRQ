'''
Created on 2 Oct 2012

@author: francis
'''

from Mock.Debugger.iMockDebuggerSink import iMockDebuggerSink
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueWriter.QueueWriter import QueueWriter
from Queue import Empty
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Semaphore
import pickle
import threading

class ServerSink(iMockDebuggerSink):
    def __init__(self, peerName, theTime, details, quiet):
        self._peerName = peerName
        self._methods = []
        methods = iMockDebuggerSink()._getMethods()
        self._methods = methods
        self._terminate = False
        self._details = details
        self._qw = None
        self._startMutex = Semaphore(0)
        self._q = Queue()
        self.quiet= quiet
        self._marshaller = MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=quiet)
        self._qw = QueueWriter(target=details, autoConnect=True, marshaller=self._marshaller, quiet=quiet)
        self._qw.start()
        self.thread = None
    def start(self):
        t = threading.Thread(target=self.run, args=[self._startMutex])
        t.setName("ServerSink.%(P)s"%{"P":self._peerName})
        t.setDaemon(True)
        self.thread = t
        self.thread.start()
        return "server.sink.started"
    def close(self):
        self._terminate = True
        try:    self.thread.join()
        except: pass
        try:    self._qw.close()
        except: pass
        try:    self._q.close()
        except: pass
        return "server.sink.closed"
    def waitUntilRunning(self, block=True, timeout=None):
        self._startMutex.acquire(block=block, timeout=timeout)
        return self
    def __getattribute__(self, name):
        if name in object.__getattribute__(self, "_methods"):
            q = self._q
            def wrapper(self, *args, **kwargs):
                ServerSink._testPickleability((name, args, kwargs))
                q.put((name, args, kwargs))
            return wrapper
        return object.__getattribute__(self, name)
    def run(self, startMutex):
        startMutex.release()
        while self._terminate==False:
            try:
                data = self._q.get(block=True, timeout=1)
            except Empty:   pass
            else:
                ServerSink._testPickleability(data)
                try:
                    self._qw.put(data, block=True, timeout=10)
                except Exception, _e:
                    break
    @staticmethod
    def _testPickleability(data):
        pickle.dumps(data)
