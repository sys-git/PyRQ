'''
Created on 13 Sep 2012

@author: francis
'''

class iQueueServer(object):
    r"""
    @summary: The interface that all QueueServer's must implement.
    """
    def start(self):
        r"""
        Start the QueueServer.
        """
        raise NotImplementedError("iQueueServer.start")
    def close(self, block=True, timeout=None):
        r"""
        @summary: Close the QueueServer. This is permanent.
        @param block: True=Block until the server closes, False=otherwise.
        @param timeout: Timeout in seconds to wait for the server to close in.
        timeout can be None (indefinite).
        @return: True=Closed successfully, False=Not closed - may close
        asynchronously.
        """
        raise NotImplementedError("iQueueServer.close")
    def waitUntilRunning(self, block=True, timeout=None):
        r"""
        Wait until the server is running and serving.
        """
        raise NotImplementedError("iQueueServer.waitUntilRunning")
    def details(self):
        r"""
        @return: The server's details.
        @see: iQueueServerDetails
        """
        raise NotImplementedError("iQueueServer.details")
    def setRecvChunkSize(self, recvChunkSize):
        r"""
        @return: Set the RecvChunkSize.
        """
        raise NotImplementedError("iQueueServer.setRecvChunkSize")
    def setMaxClients(self, maxClients):
        r"""
        @return: Set the MaxClients.
        """
        raise NotImplementedError("iQueueServer.setMaxClients")
    def setNamespace(self, namespace):
        r"""
        @return: Set the namespace.
        """
        raise NotImplementedError("iQueueServer.setNamespace")
    def setClientData(self, clientData):
        r"""
        @return: Set the ClientData.
        """
        raise NotImplementedError("iQueueServer.setClientData")
    def setHunt(self, hunt):
        r"""
        @return: Set the Hunt.
        """
        raise NotImplementedError("iQueueServer.setHunt")
    def setHost(self, host):
        r"""
        @return: Set the Host.
        """
        raise NotImplementedError("iQueueServer.setHost")
    def setPort(self, port):
        r"""
        @return: Set the Port.
        """
        raise NotImplementedError("iQueueServer.setPort")
    def setQuiet(self, quiet):
        r"""
        @return: Set the Quiet.
        """
        raise NotImplementedError("iQueueServer.setQuiet")
    def setHandlerClazz(self, clazz):
        r"""
        @return: Set the HandlerClazz.
        """
        raise NotImplementedError("iQueueServer.setHandlerClazz")
    def setTarget(self, target):
        r"""
        @return: Set the Target.
        """
        raise NotImplementedError("iQueueServer.setTarget")
    def getTarget(self):
        r"""
        @return: Get the Target.
        """
        raise NotImplementedError("iQueueServer.getTarget")
    def setMarshaller(self, marshaller):
        r"""
        @return: Set the Marshaller.
        """
        raise NotImplementedError("iQueueServer.setMarshaller")
    def setReadTimeout(self, readTimeout):
        r"""
        @return: Set the ReadTimeout.
        """
        raise NotImplementedError("iQueueServer.setReadTimeout")
