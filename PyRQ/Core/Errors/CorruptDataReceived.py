'''
Created on 12 Sep 2012

@author: francis
'''

class CorruptDataReceived(Exception):
    r"""
    @summary: Raised when the Marshaller encounter corrupt
    data in it's input stream.
    """
    def __init__(self, data):
        super(CorruptDataReceived, self).__init__(data)
        self._data = data
    def data(self):
        return self._data
    def __str__(self):
        if self._data!=None:
            return "PyRQErrors.CorruptDataReceived: <%(D)s>"%{"D":self._data[:min(256, len(self._data))]}
        return "PyRQErrors.CorruptDataReceived."
