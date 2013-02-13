'''
Created on 12 Sep 2012

@author: francis
'''

class UnknownMarshallerError(Exception):
    r"""
    @summary: Raised by the MarshallerFactory when an unknown Marshaller type
    is requested.
    """
    def __init__(self, marshaller):
        self._marshaller = marshaller
        super(UnknownMarshallerError, self).__init__()
    def __str__(self):
        return "UnknownMarshallerError: %(D)s"%{"D":self._marshaller}
