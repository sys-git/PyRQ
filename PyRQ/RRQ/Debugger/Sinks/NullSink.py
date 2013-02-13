'''
Created on 2 Oct 2012

@author: francis
'''

from PyRQ.RRQ.Debugger.iRRQDebuggerSink import iRRQDebuggerSink

class NullSink(iRRQDebuggerSink):
    def __init__(self, methods=None):
        self._methods = []
        methods = iRRQDebuggerSink()._getMethods()
        self._methods = methods
    def start(self):
        return "null.sink.started"
    def close(self):
        return "null.sink.closed"
    def waitUntilRunning(self):
        return self
    def __getattribute__(self, name):
        if name in object.__getattribute__(self, "_methods"):
            return lambda *args, **kwargs: 123
        return object.__getattribute__(self, name)
