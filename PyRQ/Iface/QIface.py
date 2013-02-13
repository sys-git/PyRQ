'''
Created on 16 Oct 2012

@author: francis
'''

from PyRQ.Iface.iPyRQIface import iPyRQIface
from multiprocessing.queues import Queue
import itertools
from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails

class QIface(iPyRQIface):
    uuId = itertools.count(0)
    _cache = {}         #    {namespace:(multiprocessing.Queue, maxsize)}
    def __init__(self, namespace=None, **kwargs):
        self._namespace = None
        if isinstance(namespace, basestring):
            #    uuId:
            self._namespace = namespace
        elif isinstance(namespace, QIface):
            #    Get the uuId:
            self._namespace = namespace._namespace
    def getDescription(self):
        return QueueServerDetails("multiprocessing.queue")
    def keepAlive(self, enabler):
        return
    def getFixedTimeout(self):
        return 0
    def setFixedTimeout(self, value):
        return
    def setGlobalPYRQ(self, details):
        return
    def setPYRQ(self, details):
        return
    def setGlobalLoggingModule(self, loggingModule):
        QIface.loggingModule = loggingModule
    def allowIfaceTimeouts(self, enabler=True):
        return
    def setNamespace(self, namespace):
        self._namespace = namespace
    def _getItemFromNamespace(self):
        ns = self._namespace
        return QIface._cache[ns]
    def _getQueue(self):
        (queue, _maxsize) = self._getItemFromNamespace()
        return queue
    def _getMaxsize(self):
        (_queue, maxsize) = self._getItemFromNamespace()
        return maxsize
    def close(self, timeout=None):
        return self._getQueue().close()
    def create(self, maxsize=0, timeout=None, queueType=None, pollInterval=None):
        #    Create a queue, cache it and return a new interface:
        q = Queue(maxsize=maxsize)
        uuId = str(QIface.uuId.next())
        QIface._cache[uuId] = (q, maxsize)
        return uuId
    def get_nowait(self, block=True, timeout=None):
        return self.get(block=False, timeout=timeout)
    def get_no_wait(self, block=True, timeout=None):
        return self.get(block=False, timeout=timeout)
    def get(self, block=True, timeout=None):
        return self._getQueue().get(block=block, timeout=timeout)
    def put_nowait(self, data, timeout=None):
        return self.put(data, block=False, timeout=timeout)
    def put(self, data, block=True, timeout=None):
        return self._getQueue().put(data, block=block, timeout=timeout)
    def qsize(self, timeout=None):
        return self._getQueue().qsize()
    def maxQSize(self, timeout=None):
        return self._getMaxsize()
