'''
Created on 2 Oct 2012

@author: francis
'''

from Mock.Debugger.iMockDebuggerSink import iMockDebuggerSink

class NullSink(iMockDebuggerSink):
    def __init__(self, methods=None):
        self._methods = []
        methods = iMockDebuggerSink()._getMethods()
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
