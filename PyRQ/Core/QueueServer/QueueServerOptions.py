'''
Created on 14 Sep 2012

@author: francis
'''

class QueueServerOptions(object):
    r"""
    @summary: Command-line arguments used by BootQueueServer to instantiate a
    PyRQ.
    """
    ACKHOST = "ackHost"
    ACKPORT = "ackPort"
    HOST = "host"
    PORT = "port"
    CLAZZPATH = "clazzpath"
    CLAZZ = "clazz"
    MARSHALLER_TYPE = "marshaller"
    HANDLERCLAZZ = "handlerclazz"
    MAX_CLIENTS = "max-clients"
    QUIET = "quiet"
    SERVICES_CLAZZPATH = "services-clazzpath"
    SERVICES_CLAZZ = "services-clazz"
    SOCKET_RECV_CHUNK_SIZE = "socket-recv-chunk-size"
    SOCKET_READ_TIMEOUT = "socket-read-timeout"
    LOGGING_MODULE = "logging-module"
