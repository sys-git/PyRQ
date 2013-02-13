'''
Created on 12 Sep 2012

@author: francis
'''

class ConfigurationError(Exception):
    r"""
    @summary: Raised when a QueueReader or QueueWriter fails to start in
    the given timeout.
    """
    def __str__(self):
        return "PyRQErrors.ConfigurationError"
