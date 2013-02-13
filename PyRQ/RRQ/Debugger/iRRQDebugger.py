'''
Created on 2 Oct 2012

@author: francis
'''

import itertools

class iRRQDebugger(object):
    _uId = itertools.count()
    def start(self, filename=None, server=None):
        raise NotImplementedError("iRRQDebugger.start")
    def waitUntilRunning(self):
        raise NotImplementedError("iRRQDebugger.waitUntilRunning")
    def stop(self):
        raise NotImplementedError("iRRQDebugger.stop")
    def newUid(self):
        return iRRQDebugger._uId.next()
