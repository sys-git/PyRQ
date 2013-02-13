'''
Created on 2 Oct 2012

@author: francis
'''

class iRRQDebuggerSink(object):
    @staticmethod
    def _getMethods():
        methods = []
        for what in dir(iRRQDebuggerSink):
            if not what.startswith("_"):
                methods.append(what)
        return methods
    def setup_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.setup_start")
    def setup_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.setup_end")
    def finish_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.finish_start")
    def finish_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.finish_end")
    def handle_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.handle_start")
    def handle_end(self, peerName, relativeTime, response, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.handle_end")
    def work_start(self, peerName, relativeTime, data, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.work_start")
    def work_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.work_end")
    def addClient_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.addClient_start")
    def addClient_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.addClient_end")
    def put_start(self, peerName, relativeTime, namespace, block, timeout, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.put_start")
    def put_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.put_end")
    def get_start(self, peerName, relativeTime, namespace, block, timeout, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.get_start")
    def get_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.get_end")
    def closeClients_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.closeClients_start")
    def closeClients_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.closeClients_end")
    def close_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.close_start")
    def close_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.close_end")
    def qsize_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.qsize_start")
    def qsize_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.qsize_end")
    def maxqsize_start(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.maxqsize_start")
    def maxqsize_end(self, peerName, relativeTime, result, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.maxqsize_end")
    def delay_start(self, peerName, relativeTime, where, t, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.delay_start")
    def delay_end(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.delay_end")
    def create_start(self, peerName, relativeTime, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.create_start")
    def create_end(self, peerName, relativeTime, namespace, *args, **kwargs):
        raise NotImplementedError("iMockDebugger.create_end")
    def query(self, namespaces, staleNamespaces, *args, **kwargs):
        raise NotImplementedError("iRRQDebuggerSink.size")




