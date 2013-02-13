'''
Created on 18 Sep 2012

@author: francis
'''
from PyRQ.RRQ.RRQType import RRQType

class CREATE(object):
    def __init__(self, maxsize=0, queueType=None, pollInterval=None):
        self.maxsize = maxsize
        if queueType==None:
            queueType = RRQType.LOCKED_LIST
        self.queueType = queueType
        self.pollInterval = pollInterval
    def __str__(self):
        return "CREATE(maxsize=%(M)s, queueType=%(Q)s, pollInterval=%(P)s)"%{"P":self.pollInterval, "M":self.maxsize, "Q":self.queueType}
