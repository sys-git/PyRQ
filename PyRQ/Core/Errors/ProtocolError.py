'''
Created on 17 Sep 2012

@author: francis
'''

class ProtocolError(Exception):
    r"""
    @summary: Raised when unexpected data is received from the PyRQ or PyRQIface.
    """
    def __init__(self, desc, received):
        self._description = desc
        self._actuallyReceived = received
        super(ProtocolError, self).__init__(desc)
    def description(self):
        return self._description
    def actuallyReceived(self):
        return self._actuallyReceived
    def __str__(self):
        return " ".join(["ProtocolError:", self._description, "\r\n", self._actuallyReceived])
