'''
Created on 17 Sep 2012

@author: francis
'''

class Finished(Exception):
    r"""
    @summary: Raised when a socket connection is closed (ie: EOF is received).
    """
    def __str__(self):
        return "PyRQErrors.Finished"
