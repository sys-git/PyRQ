'''
Created on 19 Sep 2012

@summary: Use PyRQTimeUtils.set_getTime/set_delayTime as required.

@author: francis
'''

import time

@staticmethod
def _getTime():
    r"""
    @summary: Get the current time.
    """
    return time.time()

@staticmethod
def _delayTime(howLong):
    r"""
    @summary: Sleep for the given time.
    """
    if (howLong!=None) and (howLong>=0):
        time.sleep(howLong)

class _timeUtils(object):
    GET_TIME = _getTime
    TIME_SLEEP = _delayTime
    @classmethod
    def getTime(cls):
        return _timeUtils.GET_TIME()
    @classmethod
    def delayTime(cls, value):
        return cls.TIME_SLEEP(value)
    @classmethod
    def set_getTime(cls, func):
        _timeUtils.GET_TIME = staticmethod(func)
    @classmethod
    def set_delayTime(cls, func):
        _timeUtils.TIME_SLEEP = staticmethod(func)

PyRQTimeUtils = _timeUtils()
