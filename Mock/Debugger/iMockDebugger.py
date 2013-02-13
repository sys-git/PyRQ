'''
Created on 2 Oct 2012

@author: francis
'''

import itertools

class iMockDebugger(object):
    _uId = itertools.count()
    def start(self, filename=None, server=None):
        raise NotImplementedError("iMockDebugger.start")
    def waitUntilRunning(self):
        raise NotImplementedError("iMockDebuggerSink.waitUntilRunning")
    def stop(self):
        raise NotImplementedError("iMockDebugger.stop")
    def newUid(self):
        return iMockDebugger._uId.next()
