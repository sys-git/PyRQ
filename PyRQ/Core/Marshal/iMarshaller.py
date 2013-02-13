'''
Created on 13 Sep 2012

@author: francis
'''

class iMarshaller(object):
    r"""
    @summary: The interface all Marshallers should implement.
    """
    def package(self, data):
        r"""
        @summary: Package the data for sending across the wire.
        @param data: The raw data to package.
        @return: The packaged data.
        """
        raise NotImplementedError("iMarshaller.package")
    def receive(self, data):
        r"""
        @summary: Receive data from the wire.
        @attention: The data may contain one or more items to place onto the queue.
        @attention: is an generator.
        """
        raise NotImplementedError("iMarshaller.receive")
