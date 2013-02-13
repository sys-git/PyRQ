'''
Created on 13 Sep 2012

@author: francis
'''

class iQueueWriter(object):
    r"""
    @summary: The interface all QueueWriter's must implement.
    """
    def setTarget(self, target):
        r"""
        @summary: Set the QueueServer details to use in all subsequent 'put' operations.
        """
        raise NotImplementedError("iQueueWriter.setTarget")
    def setMarshaller(self, marshaller):
        r"""
        @summary: Set the marshaller to use.
        """
        raise NotImplementedError("iQueueWriter.setMarshaller")
    def start(self):
        r"""
        @summary: Open the connection to the remote queue.
        """
        raise NotImplementedError("iQueueWriter.start")
    def close(self):
        r"""
        @summary: Close the connection to the remote queue.
        """
        raise NotImplementedError("iQueueWriter.close")
    def quiet(self, *args):
        r"""
        @summary: Return the current quiet status.
        @param args: If present, args[0]==bool(enabler): True=quiet, False:otherwise.
        """
        raise NotImplementedError("iQueueWriter.quiet")
    def put(self, data, block=True, timeout=None):
        r"""
        @summary: Put data onto the queue.
        @param data: Python data to be sent.
        @param block: See Queue.block.
        @param timeout: Not used.
        """
        raise NotImplementedError("iQueueWriter.quiet")

