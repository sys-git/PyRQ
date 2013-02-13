'''
Created on 12 Sep 2012

@author: francis
'''

class LostDataReceived(Exception):
    r"""
    @summary: Raised when stale data in found in the Marshaller's internal buffer.
    Just prior to this has being raised, the Marshaller will empty it's internal
    buffer ready for new data, although there is no guarantee that this will be
    able to be decoded. 
    """
    def __init__(self, data):
        super(LostDataReceived, self).__init__(data)
        self._data = data
    def data(self):
        return self._data
    def __str__(self):
        if self._data!=None:
            return "PyRQErrors.LostDataReceived: <%(D)s>"%{"D":self._data[:min(256, len(self._data))]}
        return "PyRQErrors.LostDataReceived."
