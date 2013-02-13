'''
Created on 17 Sep 2012

@author: francis
'''

class TooManyClientsError(Exception):
    r"""
    @summary: Raised when too many simultaneous clients attempt connection
    to the PyRQ instance.
    """
    def __str__(self):
        return "PyRQErrors.TooManyClientsError"
