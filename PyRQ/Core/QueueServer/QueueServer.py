'''
Created on 12 Sep 2012

@author: francis
'''

from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails
from PyRQ.Core.QueueServer.QueueServerHandler import QueueServerHandler
from PyRQ.Core.QueueServer.iQueueServer import iQueueServer
from multiprocessing.synchronize import Semaphore, RLock
import PyRQ.Core.Errors as Errors
import SocketServer
import itertools
import socket
import sys
import threading
import weakref
#import pydevd

class ServerHandlerFactory(object):
    DEFAULT_SOCKET_READ_TIMEOUT = 1
    DEFAULT_RECV_CHUNK_SIZE = 128
    DEFAULT_MAX_CLIENTS = 1
    __uId = itertools.count(0)
    def __init__(self, clientData=None,
                 handlerClazz=None,
                 maxClients=None,
                 recvChunkSize=None,
                 readTimeout=None,
                 target=None, 
                 marshallerType=None,
                 quiet=False,
                 debugInterface=None,
                 loggerModule=None,
                 debugger=None
                 ):
        self._clients = {}
        self._lock = RLock()
        self.setLoggerModule(loggerModule)
        self.clientData(clientData)
        self.handlerClazz(handlerClazz)
        self.target(target)
        self.marshallerType(marshallerType)
        self.readTimeout(readTimeout)
        self.recvChunkSize(recvChunkSize)
        self.maxClients(maxClients)
        self.quiet(quiet)
        self.debugInterface(debugInterface)
        self.setDebugger(debugger)
        self.terminate(False)
    def setDebugger(self, debugger):
        self.debugger = debugger
    def setLoggerModule(self, loggerModule):
        self.loggerModule = loggerModule
    def debugInterface(self, iface):
        self._debugInterface = iface
    def getQuiet(self):
        return self._quiet
    def quiet(self, quiet):
        self._quiet = quiet
    def clientData(self, clientData):
        self._clientData = clientData
    def getClientData(self, *args, **kwargs):
        return self._clientData
    def handlerClazz(self, handlerClazz):
        self._handlerClazz = handlerClazz
    def getTarget(self):
        return self._target
    def target(self, target):
        self._target = target
    def marshallerType(self, marshallerType):
        self._marshallerType = marshallerType
    def getMarshaller(self):
        return MarshallerFactory.get(self._marshallerType, quiet=self._quiet)
    def readTimeout(self, readTimeout):
        self._readTimeout = readTimeout
    def getReadTimeout(self):
        return self._readTimeout
    def recvChunkSize(self, recvChunkSize):
        self._recvChunkSize = recvChunkSize
    def getRecvChunkSize(self):
        return self._recvChunkSize
    def maxClients(self, maxClients):
        self._maxClients = maxClients
    def getTerminate(self):
        return (self._terminateAllClients==True)
    def terminate(self, enabler=True):
        #    Terminates all clients:
        self._terminateAllClients = enabler
    def getClientlock(self):
        return self._lock
    def getDebugInterface(self):
        return self._debugInterface
    def getNewLogger(self, name):
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        logger = self.loggerModule.getLogger(name)
        try:
            #    Remove existing logger handlers:
            for handler in logger.handlers[:]:
                try:    logger.removeHandler(handler)
                except: pass
        except:
            pass
        #    FIXME: Pass in the logging level!
        loggingLevel = self.loggerModule.DEBUG
        logger.setLevel(loggingLevel)
        try:
            logger.setQuiet(False)
        except:
            pass
        try:
            loggerHandler = self.loggerModule.StreamHandler()
            loggerHandler.setLevel(loggingLevel)
            formatter = self.loggerModule.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            loggerHandler.setFormatter(formatter)
            logger.addHandler(loggerHandler)
        except:
            self._loggerHandler = None
        return logger
    def getDebugger(self, inst=None):
        with self._lock:
            if self.debugger==None:
                self.debugger = inst
            return self.debugger
    def __call__(self, *args, **kwargs):
        #    Factory function called by the SocketServer for each new client to create the handler:
        #    Oh, fun and games required here!:
        if not self._quiet: sys.stderr.write("Handler clazz: %(C)s\r\n"%{"C":self._handlerClazz})
        handler = type("QueueServer_Handler_%(C)s"%{"C":self._handlerClazz}, (self._handlerClazz, ), dict(
                        abort = False,
                        newClient = self._handlerNewClient,
                        clientFinished = self._handlerClientFinished,
                        #    Dynamic parameter usage in the handler...!!!
                        getTarget = self.getTarget,
                        getMarshaller = self.getMarshaller,
                        getReadTimeout = self.getReadTimeout,
                        getRecvChunkSize = self.getRecvChunkSize,
                        getTerminate = self.getTerminate,
                        getClientData = self.getClientData,
                        getClientLock = self.getClientlock,
                        getQuiet = self.getQuiet,
                        getDebugInterface = self.getDebugInterface,
                        getNewLogger = self.getNewLogger,
                        getDebugger = self.getDebugger,
                        )
                       )
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        handler(*args, **kwargs)
    def _handlerNewClient(self, client, **kwargs):
        #    Called by the handler from the setup().
        uuid = ServerHandlerFactory.__uId.next()
        with self._lock:
            if (self._maxClients!=None) and (len(self._clients)+1)>self._maxClients:
                msg = "Too many existing clients, rejecting new client connection.\r\n"
                sys.stderr.write(msg)
                raise Errors.TooManyClientsError(msg)
            self._clients[uuid] = weakref.proxy(client)
            if ("setClientData" in kwargs):
                #    Set the client data:
                kwargs["setClientData"](self.getClientData, self.clientData)
        return uuid
    def _handlerClientFinished(self, client):
        #    Called by the handler from the finish().
        with self._lock:
            del self._clients[client]

class QueueServer(iQueueServer, threading.Thread):
    r"""
    @summary: Serves a client talking to a queue.
    @attention: This class is NOT thread-safe.
    """
    MINIMUM_PORT = 1000
    DEFAULT_PORT = 40000
    DEFAULT_HOST = "127.0.0.1"
    def __init__(self,
                 clientData=None,
                 handlerClazz=QueueServerHandler,
                 host="127.0.0.1",
                 port=None,
                 target=None,
                 marshaller=None,
                 hunt=True,
                 quiet=False,
                 maxClients=ServerHandlerFactory.DEFAULT_MAX_CLIENTS,
                 recvChunkSize=ServerHandlerFactory.DEFAULT_RECV_CHUNK_SIZE,
                 readTimeout=ServerHandlerFactory.DEFAULT_SOCKET_READ_TIMEOUT,
                 debugInterface=None,
                 loggerModule=None
                 ):
#        sys.stderr.write("QueueServer on %(P)s is quiet: %(Q)s\r\n"%{"Q":quiet, "P":port})
        self._startMutex = Semaphore(0)
        super(QueueServer, self).__init__()
        self.setClientData(clientData)
        self.setReadTimeout(readTimeout)
        self.setMaxClients(maxClients)
        self.setRecvChunkSize(recvChunkSize)
        self.setMarshaller(marshaller)
        self.setTarget(target)
        self.setQuiet(quiet)
        self.setHost(host)
        self.setPort(port)
        self.setNamespace(None)
        self.setLoggerModule(loggerModule)
        self.setDebugInterface(debugInterface)
        self.setHandlerClazz(handlerClazz)
        self.setName("ThreadedQueueServer_%(H)s_%(P)s"%{"H":self._host, "P":self._port})
        self.setDaemon(True)
        self._server = None
        self.setHunt(hunt)
        self._factory = None
        self._createResources()
    def setLoggerModule(self, loggerModule):
        if loggerModule==None:
            import logging
            loggerModule = logging
        self._loggerModule = loggerModule
    def setNamespace(self, namespace):
        self._namespace = namespace
    def setClientData(self, clientData):
        self._clientData = clientData
    def setHunt(self, hunt):
        self._hunt = hunt
    def setHost(self, host):
        self._host = host
    def setPort(self, port):
        if port!=None:
            threshold = QueueServer.MINIMUM_PORT
            if port<threshold:
                raise ValueError("Port value below minimum threshold: %(M)s"%{"M":threshold})
        self._port = port
    def setDebugInterface(self, iface):
        self._debugInterface = iface
    def setQuiet(self, quiet):
        self._quiet = quiet
    def setHandlerClazz(self, clazz):
        self._handlerClazz = clazz
    def setTarget(self, target):
        self._target = target
    def getTarget(self):
        return self._target
    def setMarshaller(self, marshaller):
        self._marshaller = marshaller
    def setReadTimeout(self, readTimeout):
        self._readTimeout = readTimeout
    def setMaxClients(self, maxClients):
        self._maxClients = maxClients
    def setRecvChunkSize(self, recvChunkSize):
        self._recvChunkSize = recvChunkSize
    def _createResources(self):
        if (self._host!=None) and (self._port!=None) and (self._target!=None) and (self._marshaller!=None):
            self._port = int(self._port)
            self._create(self._host, self._port, hunt=self._hunt, target=self._target)
        return (self._server!=None)
    def _create(self, host, port, hunt=True, target=None):
        try:
            mt = self._marshaller.type_()
        except:
            mt = None
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        factory = ServerHandlerFactory(clientData=self._clientData,\
                                       handlerClazz=self._handlerClazz,\
                                       maxClients=self._maxClients,\
                                       recvChunkSize=self._recvChunkSize,\
                                       readTimeout=self._readTimeout,\
                                       target=target,\
                                       marshallerType=mt,\
                                       quiet=self._quiet,\
                                       debugInterface=self._debugInterface,\
                                       loggerModule=self._loggerModule,\
                                       )
        iPort = port
        while True:
            try:
                server = SocketServer.ThreadingTCPServer((host, port), factory)
            except socket.error, _e:
                if not hunt:
                    raise
                port += 1
                if port==65535:
                    port = QueueServer.MINIMUM_PORT
                elif port==iPort:
                    raise
            else:
                server.allow_reuse_address = True
                self._factory = factory
                self._server = server
                self._port = port
                sys.stderr.write("listening on %(H)s:%(P)s...\r\n"%{"H":self._host, "P":self._port})
                break
    def start(self):
        if self.isAlive():
            raise Errors.AlreadyStartedError()
        threading.Thread.start(self)
        return self
    def close(self, block=True, timeout=None):
        host = self._host
        port = self._port
        if not self._quiet: sys.stderr.write("queue server closing on %(H)s:%(P)s...\r\n"%{"H":host, "P":port})
        self._factory.terminate()
        closeMutex = Semaphore(0)
        try:
            t = threading.Timer(0, self._closeServer, args=[closeMutex])
            t.setName("CloseTimer")
            t.setDaemon(True)
            t.start()
        except Exception, _e:
            pass
        acquired = closeMutex.acquire(block=block, timeout=timeout)
        if not self._quiet: sys.stderr.write("...queue server closed.\r\n")
        return acquired
    def _closeServer(self, closeMutex):
        if self._server!=None:
            if not self._quiet: sys.stderr.write("queue server closing asynchronously...\r\n")
            self._server.shutdown()
            if not self._quiet: sys.stderr.write("...queue server closed asynchronously.\r\n")
            self._server = None
        closeMutex.release()
    def waitUntilRunning(self, block=True, timeout=None):
        if not self._startMutex.acquire(block=block, timeout=timeout):
            raise Errors.ConfigurationError()
        return self
    def run(self):
        self._startMutex.release()
        if not self._quiet: sys.stderr.write("queue server listening on %(H)s:%(P)s...\r\n"%{"H":self._host, "P":self._port})
        self._server.serve_forever()
        if not self._quiet: sys.stderr.write("...finished serving\r\n")
        try:    self._server.close()
        except: pass
    def details(self):
        return QueueServerDetails(self._host, self._port, namespace=self._namespace)

