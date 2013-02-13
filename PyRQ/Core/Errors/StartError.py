'''
Created on 12 Sep 2012

@author: francis
'''

class StartError(Exception):
    r"""
    @summary: Raised when the SubprocessQueueServer fails to start in the given
    timeout.
    """
    def __str__(self):
        return "PyRQErrors.StartError"
