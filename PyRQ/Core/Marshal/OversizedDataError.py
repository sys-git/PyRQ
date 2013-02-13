'''
Created on 12 Sep 2012

@author: francis
'''

class OversizedDataError(Exception):
    r"""
    @summary: Raised when too much data is pumped into a queue.
    """
    def __init__(self, size, maxsize):
        super(OversizedDataError, self).__init__()
        self._size = size
        self._maxsize = maxsize
    def __str__(self):
        return "OversizedDataError: %(L)s, limit: %(LI)s"%{"L":self._size, "LI":self._maxsize}
