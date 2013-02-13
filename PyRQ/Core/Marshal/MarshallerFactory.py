'''
Created on 12 Sep 2012

@author: francis
'''

from PyRQ.Core.Marshal.DefaultMarshaller import DefaultMarshaller
from PyRQ.Core.Marshal.UnknownMarshallerError import UnknownMarshallerError

class MarshallerFactory(object):
    r"""
    @summary: Obtain marshallers of a particular type.
    """
    DEFAULT = 0
    @staticmethod
    def get(name, **kwargs):
        if name==MarshallerFactory.DEFAULT:
            return DefaultMarshaller(name, **kwargs)
        raise UnknownMarshallerError(name)