'''
Created on 12 Sep 2012

@author: francis
'''

class NoMarshallerError(Exception): 
    r"""
    @summary: Raised at runtime by a QueueWriter if a marshaller is not
    provided.
    """
    pass
