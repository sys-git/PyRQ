'''
Created on 17 Sep 2012

@author: francis
'''

class LinkageError(Exception):
    r"""
    @summary: Raised when an error is encountered creating a Linkage object.
    """
    def __str__(self):
        return "PyRQErrors.LinkageError"
