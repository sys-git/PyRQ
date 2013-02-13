'''
Created on 9 Oct 2012

@author: francis
'''
from PyRQ.Core.Utils.PyRQTimeUtils import PyRQTimeUtils
from Queue import Empty, Full
from multiprocessing.synchronize import RLock
import PyRQ.Core.Errors as Errors
import pickle

class RQueueImpl(object):
    DEFAULT_POLL_INTERVAL = 0.25
    def __init__(self, namespace, getLogger, maxsize=0, pollInterval=None, quiet=True):
        self._logger = getLogger("Queue.%(NS)s"%{"NS":namespace})
        self._quiet = quiet
        self._maxsize = maxsize
        self._lock = RLock()
        self._data = []
        self._closed = False
        self._totalPut = 0
        self._totalGot = 0
        if pollInterval==None:
            pollInterval = RQueueImpl.DEFAULT_POLL_INTERVAL
        self._pollInterval = pollInterval
    def _testPickleability(self, data):
        try:
            pickle.dumps(data)
        except Exception, _e:
            self._logger.error("Failed to pickle the following data for putting onto the queue: <%(R)s>"%{"R":data})
            raise
    def put(self, data, block=True, timeout=None):
        self._testPickleability(data)
        with self._lock:
            if self._closed==True:
                raise Errors.ClosedError()
            #    FYI - always called with block==False.
            if (self._maxsize!=0) and (len(self._data)==self._maxsize):
                raise Full()
            else:
                self._data.append(data)
                l = len(self._data)
                self._totalPut += 1
            if not self._quiet: self._logger.debug("PUT Queue contains %(NS)s items, total-PUT: %(T)s.\r\n"%{"NS":l, "T":self._totalPut})
    def get(self, block=True, timeout=None):
        data = None
        #    Calculate the maxTime:
        pollInterval = self._pollInterval
        timeStart = PyRQTimeUtils.getTime()
        maxTime = None
        if block==True:
            try:    maxTime = timeStart + timeout
            except: pass
            if not self._quiet: self._logger.debug("GET blocking, maxTime: %(MT)s, timeStart: %(TS)s"%{"MT":maxTime, "TS":timeStart, "TO":timeout})
        else:
            if not self._quiet: self._logger.debug("GET non-blocking")
        try:
            while True:
                timeDelay = None
                with self._lock:
                    if self._closed==True:
                        break
                    if block==False:
                        if len(self._data)==0:
                            raise Empty()
                        data = self._data.pop(0)
                        break
                    else:
                        if len(self._data)==0:
                            timeNow = PyRQTimeUtils.getTime()
                            #    Calculate the maxTime:
                            if maxTime==None:
                                remainingTime = pollInterval
                            else:
                                remainingTime = maxTime-timeNow
                            if not self._quiet: self._logger.debug("GET blocking, maxTime: %(MT)s, timeStart: %(TS)s, timeNow: %(TN)s, remainingTime: %(RT)s"%{"TN":timeNow, "MT":maxTime, "TS":timeStart, "TO":timeout, "RT":remainingTime})
                            if remainingTime<=0:
                                raise Empty()
                            else:
                                #    Wait for minPeriod and try again:
                                timeDelay = min(pollInterval, min(pollInterval, remainingTime))
                        else:
                            data = self._data.pop(0)
                            break
                if timeDelay!=None:
                    PyRQTimeUtils.delayTime(timeDelay)
        except Exception, _e:
            raise
        finally:
            if self._closed==True:
                raise Errors.ClosedError()
        with self._lock:
            l = len(self._data)
            self._totalGot += 1
            if not self._quiet: self._logger.debug("GET Queue contains %(NS)s items, total-GOT: %(T)s.\r\n"%{"NS":l, "T":self._totalGot})
        return data
    def qsize(self):
        with self._lock:
            if self._closed==True:
                raise Errors.ClosedError()
            return len(self._data)
    def close(self):
        with self._lock:
            if self._closed==True:
                raise Errors.ClosedError()
            self._closed=True
