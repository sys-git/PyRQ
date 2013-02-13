'''
Created on 2 Oct 2012

@author: francis
'''

from Mock.Debugger.iMockDebuggerSink import iMockDebuggerSink
from Queue import Empty
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Semaphore
import threading

class FileSink(iMockDebuggerSink):
    def __init__(self, peerName, theTime, filename, quiet):
        self._peerName = peerName
        self._fp = open(filename, "w")
        self.fp.write("File debugger started at: %(T)s for client: %(C)s"%{"T":theTime, "C":peerName})
        self.fp.flush()
        self._methods = []
        methods = iMockDebuggerSink()._getMethods()
        self._methods = methods
        self._terminate = False
        self.quiet=  quiet
        self._startMutex = Semaphore(0)
        self._q = Queue()
        self.thread = None
    def start(self):
        t = threading.Thread(target=self.run, args=[self._startMutex])
        t.setName("FileSink.%(P)s"%{"P":self._peerName})
        t.setDaemon(True)
        self.thread = t
        self.thread.start()
        return "file.sink.started"
    def close(self):
        self._terminate = True
        try:    self.thread.join()
        except: pass
        try:    self._fp.close()
        except: pass
        try:    self._fp.close()
        except: pass
        try:    self._q.close()
        except: pass
        self._fp = None
        return "file.sink.closed"
    def waitUntilRunning(self, block=True, timeout=None):
        self._startMutex.acquire(block=block, timeout=timeout)
        return self
    def __getattribute__(self, name):
        if name in object.__getattribute__(self, "_methods"):
            q = self._q
            def wrapper(self, *args, **kwargs):
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
                try:
                    (methodName, args, kwargs) = data
                    peerName = args[0]
                    relativeTime = args[1]
                    args = args[2:]
                    ss = ["PEER:", peerName, "REL-TIME:", relativeTime, "METHOD", methodName, "ARGS:", str(args), "KWARGS", str(kwargs)]
                    s = "\n".join(ss)
                except: pass
                else:
                    try:
                        self._fp.write(s)
                    except:
                        break
