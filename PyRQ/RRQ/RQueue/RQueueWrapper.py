'''
Created on 9 Oct 2012

@author: francis
'''

from PyRQ.RRQ.RQueue.RQueueImpl import RQueueImpl
from PyRQ.RRQ.RRQType import RRQType

class RQueueWrapper(object):
    def __init__(self, queueType, getLogger, namespace, maxsize=0, pollInterval=None, quiet=True):
        self.namespace = namespace
        self.maxsize = maxsize
        if queueType==RRQType.LOCKED_LIST:
            q = RQueueImpl(namespace, getLogger, maxsize=maxsize, pollInterval=pollInterval, quiet=quiet)
        else:
            from multiprocessing.queues import Queue
            q = Queue(maxsize=maxsize)
        self._q = q
    def q(self):
        return self._q
    def qsize(self):
        return self._q.qsize()
    def maxQSize(self):
        return self.maxsize
    def close(self):
        try:
            self._q.close()
        except Exception, _e:
            pass
