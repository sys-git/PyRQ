'''
Created on 12 Sep 2012

@author: francis
'''

class AlreadyStartedError(Exception):
    r"""
    @summary: Raised when multiple attempts are made to start a QueueReader or
    QueueWriter instance.
    """
    def __str__(self):
        return "PyRQErrors.AlreadyStartedError"
