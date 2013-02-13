'''
Created on 17 Sep 2012

@author: francis
'''

from Mock.Debugger.MockDebugger import MockDebugger
from Mock.Debugger.PING import PING
from PyRQ.Core.Utils.PyRQTimeUtils import PyRQTimeUtils
from PyRQ.RRQ.RRQPackage import RRQPackage
from PyRQ.RRQ.RRQType import RRQType
from Queue import Empty, Full
from multiprocessing.synchronize import RLock
import PyRQ.Core.Errors as Errors
import PyRQ.Core.Messages as Messages
import SocketServer
import copy
import pickle
import socket
import threading
import traceback
import uuid

#from PyRQ.Core.Messages.DEBUG import DEBUG, DEBUG_STOP, DEBUG_START, \
#    DEBUG_SOMETHING, DEBUG_QUERY
#from PyRQ.Core.Messages.PUT import PUT
#import pydevd
#pydevd.settrace(stdoutToServer = True, stderrToServer = True)

class _Ping(object):
    def __init__(self, data):
        self.data = data

class _CLOSE(object):   pass

class MockRegistrar(object):
    def __init__(self, namespace=None):
        self.namespace = namespace
        self.data = {"queues":{}, "stale-queues":[], "stall":{}}
    def terminate(self):
        pass

class MockQueue(object):
    DEFAULT_POLL_INTERVAL = 0.25
    def __init__(self, namespace, getLogger, maxsize=0, pollInterval=None, quiet=True):
        self._logger = getLogger("Queue.%(NS)s"%{"NS":namespace})
        self._quiet = quiet
        self._maxsize = maxsize
        self._lock = RLock()
        self._data = []
        self._closed = False
        self._totalPut = 0
        self._totalGot = 0
        if pollInterval==None:
            pollInterval = MockQueue.DEFAULT_POLL_INTERVAL
        self._pollInterval = pollInterval
    def _testPickleability(self, data):
        try:
            pickle.dumps(data)
        except Exception, _e:
            self._logger.error("Failed to pickle the following data for putting onto the queue: <%(R)s>"%{"R":data})
            raise
    def put(self, data, block=True, timeout=None):
        self._testPickleability(data)
        with self._lock:
            if self._closed==True:
                raise Errors.ClosedError()
            #    FYI - always called with block==False.
            if (self._maxsize!=0) and (len(self._data)==self._maxsize):
                raise Full()
            else:
                self._data.append(data)
                l = len(self._data)
                self._totalPut += 1
            if not self._quiet: self._logger.debug("PUT Queue contains %(NS)s items, total-PUT: %(T)s.\r\n"%{"NS":l, "T":self._totalPut})
    def get(self, block=True, timeout=None):
        data = None
        #    Calculate the maxTime:
        pollInterval = self._pollInterval
        timeStart = PyRQTimeUtils.getTime()
        maxTime = None
        if block==True:
            try:    maxTime = timeStart + timeout
            except: pass
        try:
            while True:
                timeDelay = None
                with self._lock:
                    if self._closed==True:
                        break
                    if block==False:
                        if len(self._data)==0:
                            raise Empty()
                        data = self._data.pop(0)
                        break
                    else:
                        if len(self._data)==0:
                            timeNow = PyRQTimeUtils.getTime()
                            #    Calculate the maxTime:
                            if maxTime==None:
                                remainingTime = pollInterval
                            else:
                                remainingTime = maxTime-timeNow
                            if remainingTime<=0:
                                raise Empty()
                            else:
                                #    Wait for minPeriod and try again:
                                timeDelay = min(pollInterval, min(pollInterval, remainingTime))
                        else:
                            data = self._data.pop(0)
                            break
                if timeDelay!=None:
                    PyRQTimeUtils.delayTime(timeDelay)
        except Exception, _e:
#            self._logger.error("EEEEEEEERRRRRRRRROOOOOOOOORRRRRRRR.total: %(T)s.\r\n%(NS)s\r\n"%{"T":self._totalGot, "NS":traceback.format_exc()})
            raise
        finally:
            if self._closed==True:
                raise Errors.ClosedError()
        with self._lock:
            l = len(self._data)
            self._totalGot += 1
            if not self._quiet: self._logger.debug("Messages.GET Queue contains %(NS)s items, total-Messages.GOT: %(T)s.\r\n"%{"NS":l, "T":self._totalGot})
        return data
    def qsize(self):
        with self._lock:
            if self._closed==True:
                raise Errors.ClosedError()
            return len(self._data)
    def close(self):
        with self._lock:
            if self._closed==True:
                raise Errors.ClosedError()
            self._closed=True

class MockQObject(object):
    def __init__(self, queueType, getLogger, namespace, maxsize=0, pollInterval=None, quiet=True):
        self.namespace = namespace
        self.maxsize = maxsize
        if queueType==RRQType.LOCKED_LIST:
            q = MockQueue(namespace, getLogger, maxsize=maxsize, pollInterval=pollInterval, quiet=quiet)
        else:
            from multiprocessing.queues import Queue
            q = Queue(maxsize=maxsize)
        self._q = q
    def q(self):
        return self._q
    def qsize(self):
        return self._q.qsize()
    def maxQSize(self):
        return self.maxsize
    def close(self):
        try:
            self._q.close()
        except Exception, _e:
            pass

class FinishedWithSocket(Exception): pass

class MockHandler(object, SocketServer.BaseRequestHandler):
    #    TODO: Use a logger, put the loggerModule into the Factory and subprocess.
    def __init__(self, *args, **kwargs):
        self._clients = {}  #    {namespace:[socks]}
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)
    def _doResponse(self, request, response):
        try:
            pickle.dumps(response)
        except Exception, _e:
            self.logger.error("Failed to pickle the following response: <%(R)s>"%{"R":response})
        request.sendall(response)
    def closeClients(self, namespace, clientData, marshaller, quiet):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.closeClients_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
        with self.getClientLock():
            numClients = len(self._clients)
            if namespace in self._clients:
                #    Close clients in parallel:
                while len(self._clients[namespace])>0:
                    client = self._clients[namespace].pop()
                    if not quiet: self.logger.debug("Closing client for namespace: %(Q)s\r\n"%{"Q":namespace})
                    def closeClient(c):
                        try:
                            self._doResponse(c.request, marshaller.package(Messages.CLOSED(namespace=namespace)))
                            PyRQTimeUtils.delayTime(1)
                            c.request.shutdown(socket.SHUT_WR)
                            c.request.close()
                            del c
                        except Exception, _e:
                            pass
                    t = threading.Timer(0, closeClient, args=[client])
                    t.setDaemon(True)
                    t.setName("ClientCloser_%(U)s_%(C)s"%{"U":namespace, "C":client})
                    t.start()
                del self._clients[namespace]
            #    Now discard the buffer and queue:
            try:
                qData = clientData["queues"][namespace]
            except Exception, _e:
                pass
            else:
                #    Tell each Messages.GET client to close:
                q = qData.q()
                for _ in xrange(numClients):
                    try:
                        q.put(_CLOSE(), block=False)
                    except Exception, _e:
                        pass
                PyRQTimeUtils.delayTime(1)
                qData.close()
                del clientData["queues"][namespace]
                clientData["stale-queues"].append(namespace)
        if debugger:
            debugger.closeClients_end(self.peerName, PyRQTimeUtils.getTime(), uu=uu)
    def _getPeerName(self):
        name = self.request.getpeername()
        return ":".join([str(name[0]), str(name[1])])
    def setup(self):
        self.peerName = self._getPeerName()
        debugger = self.getDebugger(inst=MockDebugger())
        if debugger:
            uu = debugger.setup_start(self.peerName, PyRQTimeUtils.getTime())
        quiet = self.getQuiet()
        self.logger = self.getNewLogger(self.peerName)
        if not quiet: self.logger.debug(">> SETUP start @ %(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
            def setClient(getter, setter):
                data = getter()
                if data==None:
                    setter(self._getDefaultClientData())
            self.client = self.newClient(self, setClientData=setClient)
        except Errors.TooManyClientsError, _e:
            self.abort = True
        if not quiet: self.logger.debug(">> SETUP end @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        if debugger:
            debugger.setup_end(self.peerName, PyRQTimeUtils.getTime(), uu=uu)
    def _getDefaultClientData(self):
        return {"queues":{}, "stale-queues":[], "stall":{}}
    def finish(self):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.finish_start(self.peerName, PyRQTimeUtils.getTime())
        try:
            self.clientFinished(self.client)
        except Exception, _e:
            pass
        if debugger:
            debugger.finish_end(self.peerName, PyRQTimeUtils.getTime(), uu=uu)
    def handle(self):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.handle_start(self.peerName, PyRQTimeUtils.getTime())
        quiet = self.getQuiet()
        response = None
        if not quiet: self.logger.debug(">> HANDLE start @%(T)s\r\n"%{"T":PyRQTimeUtils.getTime()})
        try:
            marshaller = self.getMarshaller()
            if self.abort:
                response = Errors.TooManyClientsError()
                self._doResponse(self.request, marshaller.package(response))
                return
            target = self.getTarget()
            if not quiet: self.logger.info("Serving new client [%(C)s]\r\n"%{"C":self.client})
            while True:
                try:
                    self._work(target, marshaller)
                except FinishedWithSocket, _e:
                    if not quiet: self.logger.debug("Finished with socket for client: %(C)s\r\n"%{"C":self.client})
                    return
                except Exception, _e:
                    #    This is fatal, so just return.
                    self.logger.error("Error in work for client: %(C)s\r\n%(T)s"%{"C":self.client, "T":traceback.format_exc()})
                    return
        finally:
            if debugger:
                debugger.handle_end(self.peerName, PyRQTimeUtils.getTime(), response, uu=uu)
            if not quiet: self.logger.debug(">> HANDLE end @%(T)s"%{"T":PyRQTimeUtils.getTime()})
    def _getMaxQueueSize(self):
        return 0
    def _work(self, target, marshaller):
        debugger = self.getDebugger()
        tOut = self.getReadTimeout()
#        tOut = 1
        self.request.setblocking(True)
        self.request.settimeout(tOut)
        clientData = self.getClientData()
        while self.getTerminate()==False:
            #    Receive the data from the socket:
            quiet = self.getQuiet()
            try:
                data = self.request.recv(self.getRecvChunkSize())
            except socket.timeout, _e:
                print ">"
            else:
                if data=='':
                    raise FinishedWithSocket()
                #    Pump the data into the marshaller, piping the packages onto the target:
                for p in marshaller.receive(data):
                    if not quiet: self.logger.debug("WORK %(P)s for: %(C)s\r\n"%{"P":p, "C":self.client_address})
                    if isinstance(p, RRQPackage):
                        pp = p.data
                        namespace = p.namespace
                        if debugger:
                            uu = debugger.work_start(self.peerName, PyRQTimeUtils.getTime(), pp)
                        if not quiet: self.logger.info("WORK data: %(P)s for: %(C)s\r\n"%{"P":pp, "C":self.client_address})
                        if isinstance(pp, Messages.CREATE):
                            namespace = uuid.uuid4().hex
                            with self.getClientLock():
                                #    There is a remote chance that the uuids will be identical so:
                                if namespace in clientData["queues"].keys():
                                    namespace += namespace
                                queueType = pp.queueType
                                maxsize = pp.maxsize
                                pollInterval = pp.pollInterval
                                q = MockQObject(queueType,
                                                self.getNewLogger,
                                                namespace,
                                                maxsize=maxsize,
                                                pollInterval=pollInterval,
                                                quiet=quiet)
                                clientData["queues"][namespace] = q
                            self._addClient(self, namespace)
                            self._stall("Messages.CREATE", clientData, quiet)
                            self._doResponse(self.request, marshaller.package(Messages.ACK(namespace)))
                        elif isinstance(pp, Messages.CLOSE):
                            with self.getClientLock():
                                alreadyClosed = (namespace in clientData["stale-queues"])
                            if alreadyClosed==True:
                                #    Subsequent close already!
                                self._doResponse(self.request, marshaller.package(Messages.CLOSED(result=False, namespace=namespace)))
                                return
                            self._addClient(self, namespace)
                            self._stall("Messages.CLOSE", clientData, quiet)
                            self.closeClients(namespace, clientData, marshaller, quiet)
                            raise FinishedWithSocket()
                        elif isinstance(pp, Messages.PUT):
                            self._addClient(self, namespace)
                            self._stall("PUT", clientData, quiet)
                            self._put(namespace, pp, clientData, marshaller, quiet)
                        elif isinstance(pp, Messages.GET):
                            self._addClient(self, namespace)
                            self._stall("Messages.GET", clientData, quiet)
                            self._get(namespace, pp, clientData, marshaller, quiet)
                        elif isinstance(pp, Messages.QSIZE):
                            self._addClient(self, namespace)
                            self._qSize(namespace, clientData, marshaller)
                        elif isinstance(pp, Messages.MAXQSIZE):
                            self._addClient(self, namespace)
                            self._maxQSize(namespace, clientData, marshaller)
                        elif isinstance(pp, Messages.DEBUG):
                            self._debug(pp, marshaller, clientData, quiet)
                        if debugger:
                            debugger.work_end(self.peerName, PyRQTimeUtils.getTime(), uu=uu)
    def _addClient(self, who, namespace):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.addClient_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
        with self.getClientLock():
            if namespace not in self._clients:
                self._clients[namespace] = []
            self._clients[namespace].append(who)
        if debugger:
            debugger.addClient_end(self.peerName, PyRQTimeUtils.getTime(), namespace, uu=uu)
    def _put(self, namespace, pp, clientData, marshaller, quiet, pollDelay=0.1):
        #    Add the data onto the queue for namespace:
        debugger = self.getDebugger()
        socketDetails = self.client_address
        q = self._getQ(namespace, clientData, marshaller)
        if q!=None:
            #    Now loop every 'pollDelay' seconds, checking if we're closed.
            block = pp.block
            timeout = pp.timeout
            if debugger:
                uu = debugger.put_start(self.peerName, PyRQTimeUtils.getTime(), namespace, block, timeout)
            result = Messages.ACK(namespace)
            try:
                data = pp.data
                if not quiet: self.logger.debug("-PUT - %(D)s"%{"D":data})
                if block==False:
                    if not quiet: self.logger.debug("-PUT start (non-blocking) @%(T)s - %(D)s"%{"D":data, "T":namespace})
                    q.put(data, block=False)
                else:
                    if not quiet: self.logger.debug("-PUT start (blocking) @%(T)s - %(D)s"%{"D":data, "T":namespace})
                    maxTime=None
                    if timeout!=None:
                        maxTime = PyRQTimeUtils.getTime()+timeout
                    while True:
                        with self.getClientLock():
                            try:
                                q = clientData["queues"][namespace].q()
                            except Exception, _e:
                                raise Errors.ClosedError()
                            else:
                                try:
                                    q.put(data, block=False)
                                except Full, _e:
                                    pass
                                else:
                                    break
                        #    Manual queue delay:
                        PyRQTimeUtils.delayTime(pollDelay)
                        if (maxTime!=None) and (PyRQTimeUtils.getTime()>=maxTime):
                            #    timeout!
                            raise Full()
            except (Full, Errors.ClosedError), result:
                if not quiet: self.logger.error("-PUT - %(D)s Exception[0] from %(C)s"%{"D":data, "C":socketDetails})
                pass
            if isinstance(result, Exception):
                if not quiet: self.logger.debug("-PUT - %(D)s Exception[1] from %(C)s"%{"D":data, "C":socketDetails})
            if debugger:
                debugger.put_end(self.peerName, PyRQTimeUtils.getTime(), result, uu=uu)
            if not quiet: self.logger.info("-PUT - %(D)s result: %(R)s from %(C)s\r\n"%{"R":result, "D":data, "C":socketDetails})
            self._doResponse(self.request, marshaller.package(result))
            if not quiet: self.logger.debug("-PUT end @%(T)s\r\n"%{"T":PyRQTimeUtils.getTime()})
    def _getQ(self, namespace, clientData, marshaller):
        result = None
        with self.getClientLock():
            if not namespace in clientData["queues"]:
                result = Errors.NoSuchQueue(namespace)
                if namespace in clientData["stale-queues"]:
                    result = Errors.ClosedError()
            else:
                q = clientData["queues"][namespace].q()
                return q
        if result!=None:
            self._doResponse(self.request, marshaller.package(result))
    def _get(self, namespace, pp, clientData, marshaller, quiet):
        #    Get the data from the queue:
        debugger = self.getDebugger()
        q = self._getQ(namespace, clientData, marshaller)
        if q!=None:
            block=pp.block
            timeout=pp.timeout
            if debugger:
                uu = debugger.get_start(self.peerName, PyRQTimeUtils.getTime(), namespace, block, timeout)
            result = None
            r"""
            FYI: if block=True, make the timeout=1 and loop
            --> allows us to abort when another client closes this 'Queue'.
            """
            try:
                data = q.get(block=block, timeout=timeout)
            except Empty, result:
                if not quiet: self.logger.debug("Queue empty for [%(NS)s].\r\n"%{"NS":namespace})
            except Errors.ClosedError, result:
                pass
            else:
                if isinstance(data, _CLOSE):
                    #    Now we manually close otherwise we have thread-leakage!
                    if not quiet: self.logger.info("Manual close detected, performing clean-close, propagating Errors.ClosedError back to client.\r\n")
                    result = Errors.ClosedError()
                else:
                    result = Messages.GOT(data)
                    if not quiet: self.logger.debug("Messages.GOT DATA for %(NS)s - %(D)s"%{"D":data, "NS":namespace})
            if debugger:
                debugger.get_end(self.peerName, PyRQTimeUtils.getTime(), result, uu=uu)
            if not quiet: self.logger.info("Messages.GET result for %(NS)s - %(D)s"%{"D":result, "NS":namespace})
            self._doResponse(self.request, marshaller.package(result))
            if not quiet: self.logger.debug("Returning result: %(R)s for %(NS)s"%{"R":result, "NS":namespace})
    def _qSize(self, namespace, clientData, marshaller):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.qsize_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
        with self.getClientLock():
            if not namespace in clientData["queues"]:
                result = Errors.NoSuchQueue(namespace)
                if namespace in clientData["stale-queues"]:
                    result = Errors.ClosedError()
            else:
                size = clientData["queues"][namespace].qsize()
                result = Messages.QSIZE(size)
        if debugger:
            debugger.qsize_end(self.peerName, PyRQTimeUtils.getTime(), result, uu=uu)
        self._doResponse(self.request, marshaller.package(result))
    def _maxQSize(self, namespace, clientData, marshaller):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.maxqsize_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
        with self.getClientLock():
            if not namespace in clientData["queues"]:
                result = Errors.NoSuchQueue(namespace)
                if namespace in clientData["stale-queues"]:
                    result = Errors.ClosedError()
            else:
                size = clientData["queues"][namespace].maxQSize()
                result = Messages.MAXQSIZE(size)
        if debugger:
            debugger.maxqsize_end(self.peerName, PyRQTimeUtils.getTime(), result, uu=uu)
        self._doResponse(self.request, marshaller.package(result))
    def _stall(self, where, clientData, quiet):
        if not quiet: self.logger.debug("STALL %(W)s.\r\n"%{"W":where})
        try:
            t = clientData["stall"][where]
            if not quiet: self.logger.info("STALL time: %(W)s\r\n"%{"W":t})
            debugger = self.getDebugger()
            if (t!=None) and (t>0):
                if debugger:
                    uu = debugger.delay_start(self.peerName, PyRQTimeUtils.getTime(), t, where)
            PyRQTimeUtils.delayTime(t)
            if (t!=None) and (t>0):
                if debugger:
                    uu = debugger.delay_end(self.peerName, PyRQTimeUtils.getTime(), uu=uu)
        except Exception, _e:
            pass
    def _debug(self, cmd, marshaller, clientData, quiet):
        r"""
        @summary: Configure the debug.
        """
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        debugger = self.getDebugger()
        if isinstance(cmd, Messages.DEBUG_START):
            try:
                result = debugger.start(self.peerName, PyRQTimeUtils.getTime(), cmd.filename, cmd.server)
            except Exception, e:
                self.logger.error("DEBUG_START filename: <%(F)s>, server: <%(S)s>...\r\n%(E)s.\r\n"%{"E":e, "S":cmd.server, "F":cmd.filename})
        elif isinstance(cmd, Messages.DEBUG_STOP):
            result = debugger.stop()
        elif isinstance(cmd, Messages.DEBUG_SOMETHING):
            result = PING()
        elif isinstance(cmd, Messages.DEBUG_QUERY):
            result = PING()
            with self.getClientLock():
                staleNamespaces = copy.deepcopy(clientData["stale-queues"])
                namespaces = copy.deepcopy(clientData["queues"].keys())
            debugger.query(self.peerName, PyRQTimeUtils.getTime(), namespaces, staleNamespaces)
        else:
            self.logger.error("UNKNOWN DEBUG command: <%(C)s>."%{"C":cmd})
            return
        if not quiet: self.logger.error("result: <%(C)s>."%{"C":result})
        self._doResponse(self.request, marshaller.package(result))

class TimeoutMockHandler(MockHandler):
    def _getDefaultClientData(self):
        #    FYI - These timeouts affect the TestRRWReader directly.
        return {"queues":{}, "stale-queues":[], "stall":{"Messages.GET":5, "PUT":5, "Messages.CREATE":4, "Messages.CLOSE":0}}
