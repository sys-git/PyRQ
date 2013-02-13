'''
Created on 2 Oct 2012

@author: francis
'''

class iMockDebuggerSink(object):
    @staticmethod
    def _getMethods():
        methods = []
        for what in dir(iMockDebuggerSink):
            if not what.startswith("_"):
                methods.append(what)
        return methods
    def setup_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.setup_start")
    def setup_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.setup_end")
    def finish_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.finish_start")
    def finish_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.finish_end")
    def handle_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.handle_start")
    def handle_end(self, peerName, relativeTime, response, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.handle_end")
    def work_start(self, peerName, relativeTime, data, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.work_start")
    def work_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.work_end")
    def addClient_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.addClient_start")
    def addClient_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.addClient_end")
    def put_start(self, peerName, relativeTime, namespace, block, timeout, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.put_start")
    def put_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.put_end")
    def get_start(self, peerName, relativeTime, namespace, block, timeout, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.get_start")
    def get_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.get_end")
    def closeClients_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.closeClients_start")
    def closeClients_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.closeClients_end")
    def qsize_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.qsize_start")
    def qsize_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.qsize_end")
    def maxqsize_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.maxqsize_start")
    def maxqsize_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.maxqsize_end")
    def delay_start(self, peerName, relativeTime, where, t, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.delay_start")
    def delay_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.delay_end")
    def create_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.create_start")
    def create_end(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.create_end")
    def query(self, namespaces, staleNamespaces, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.size")




