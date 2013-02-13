'''
Created on 20 Sep 2012

@author: francis
'''

from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory

class iPyRQIface(object):
    r"""
    @summary: Always set the queue namespace either in the constructor or via
    setNamespace().
    @summary: Always set the RRQ details via setPYRQ().
    """
    def __init__(self, namespace=None, marshaller=MarshallerFactory.DEFAULT, sockTimeout=10, quiet=False):
        r"""
        Create an interface to a PYRQ.
        @param namespace: The namespace on the queue which may already have been created.
        If None, then setNamespace() will need to be called before this instance
        can be used, alternatively use create().
        @param marshaller: The marshaller type to use, see: MarshallerFactory.
        @param sockTimeout: The timeout to use for every connection attempt to the PYRQ.
        @param quiet: True - minimise sys.stderr output, False - verbose output.
        """
        raise NotImplementedError("iPyRQIface.__init__()")
    @staticmethod
    def setGlobalPYRQ(details):
        r"""
        @summary: Set the PYRQ into the interface, used for all interfaces in this Process.
        @param details: See iQueueServerDetails.
        @raise None.
        @return: None.
        """
        raise NotImplementedError("iPyRQIface.setGlobalPYRQ()")
    def setPYRQ(self, details):
        r"""
        @summary: Set the PYRQ into the interface, used for this interface instance only.
        @param details: See iQueueServerDetails.
        @raise None.
        @return: None.
        """
        raise NotImplementedError("iPyRQIface.setPYRQ()")
    def close(self, timeout=None):
        r"""
        @summary: Close the remote 'Queue', any further use of the queue will result
        in ClosedError being raised by any of [get(), put(), close()]
        @raise PyRQError: Failed to connect to the PYRQ.
        @raise ClosedError: Queue already closed.
        """
        raise NotImplementedError("iPyRQIface.close()")
    def create(self, maxsize=0, timeout=None):
        r"""
        @summary: Create a new queue.
        @attention: Allocates finite resource on the PYRQ.
        @return: The queue's namespace which can be passed around with the PyRQIface's
        details.
        @param maxsize: See: multiprocessing.Queue.__init__. 0=unlimited, >0=otherwise.
        @param timeout: timeout in seconds in which to create the new queue.
        @raise PyRQError: Failed to connect to the PYRQ.
        @raise PyRQError: Failed to create the queue in the given timeout.
        """
        raise NotImplementedError("iPyRQIface.create()")
    def get(self, block=True, timeout=None):
        r"""
        @summary: Get an item from the queue.
        @param timeout: timeout in seconds in which to get the item from the queue.
        @raise PyRQError: Failed to connect to the PYRQ.
        @raise ClosedError: Queue already closed.
        @raise Empty: Failed to get an item from the queue in the given timeout.
        @param block: The call blocks until the operation completes.
        @param timeout: The timeout in which to get the data in.
        @attention: The timeout parameter works even if block=False.
        @return: Data extracted from the queue.
        """
        raise NotImplementedError("iPyRQIface.get()")
    def get_no_wait(self, timeout=None):
        r"""
        @equivalent to: get_nowait
        """
    def get_nowait(self, timeout=None):
        r"""
        @summary: Get an item from the queue, equivalent to get(block=False, timeout=timeout).
        @raise PyRQError: Failed to connect to the PYRQ.
        @raise ClosedError: Queue already closed.
        @raise Empty: Failed to get an item from the queue.
        @attention: The call blocks at most 'timeout' for the network.
        @param timeout: network timeout in seconds.
        @return: Data extracted from the queue.
        """
        raise NotImplementedError("iPyRQIface.get()")
    def put(self, data, block=True, timeout=None):
        r"""
        @summary: Put an item onto the queue.
        @param timeout: timeout in seconds in which to put the item onto the queue.
        @raise PyRQError: Failed to connect to the PYRQ.
        @raise ClosedError: Queue already closed.
        @raise Full: Failed to put an item onto the queue in the given timeout.
        @param block: True: The call blocks for 'timeout' seconds until the
        operation completes. False: The call blocks for 'timeout' until the
        operation completes with Empty.
        @param timeout: The timeout in which to get the data in.
        @attention: The timeout parameter works even if block=False.
        @return: None.
        """
        raise NotImplementedError("iPyRQIface.put()")
    def put_nowait(self, data, timeout=None):
        r"""
        @summary: Put an item onto the queue, equivalent to put(data, block=False, timeout=timeout).
        @raise PyRQError: Failed to connect to the PYRQ.
        @raise ClosedError: Queue already closed.
        @raise Full: Failed to put an item onto the queue.
        @param timeout: network timeout in seconds.
        @attention: The call blocks at most 'timeout' for the network.
        @return: None.
        """
    def qsize(self, timeout=None):
        r"""
        @summary: Query the queue size (approx number of items on the queue).
        @param timeout: timeout in seconds in which to query the queue size.
        @raise PyRQError: Failed to connect to the PYRQ.
        @return: The number of items on the queu. 
        @see: multiprocessing.Queue.qsize()
        """
        raise NotImplementedError("iPyRQIface.qsize()")
    def maxQSize(self, timeout=None):
        r"""
        @summary: Query the maximum allowed queue size (the value the queue was
        created with).
        @param timeout: timeout in seconds in which to query the queue size.
        @raise PyRQError: Failed to connect to the PYRQ.
        @return: The size of the queue.
        @see: multiprocessing.Queue.__init__()
        """
        raise NotImplementedError("iPyRQIface.qsize()")
    def getFixedTimeout(self):
        r"""
        @summary: Get the fixed timeout (which is added to all socket receive operations).
        @return: timeout in seconds.
        """
        raise NotImplementedError("iPyRQIface.setFixedTimeout()")
    def setFixedTimeout(self, value):
        r"""
        @summary: Set the fixed timeout added to all socket receive operations.
        @attention: Increase this value if the logger indicates that:
        'TIMEOUT on socket operation'. Depends on network/cpu load.
        @param timeout: timeout in seconds.
        @raise ValueError: value must be integer/float > 0.
        """
        raise NotImplementedError("iPyRQIface.setFixedTimeout()")
    def allowIfaceTimeouts(self, enabler=True):
        r"""
        @summary: Allow interface actions to time-out.
        @param timeout: bool(enabler).
        """
        raise NotImplementedError("iPyRQIface.allowIfaceTimeouts()")
    def keepAlive(self, enabler=True):
        r"""
        @summary: Prevent the interface from voluntarily dropping the
        socket connection to the PyRQ.
        @param enabler: bool(enabler)=True - keepAlive, False - drop connection.
        """
        raise NotImplementedError("iPyRQIface.keepAlive()")
