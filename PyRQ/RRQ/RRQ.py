'''
Created on 9 Oct 2012

@author: francis
'''

from PyRQ.Core.Messages.DEBUG import UnknownDebuggerCommand
from PyRQ.Core.Utils.PyRQTimeUtils import PyRQTimeUtils
from PyRQ.RRQ.Debugger.PING import PING
from PyRQ.RRQ.Debugger.RRQDebugger import RRQDebugger
from PyRQ.RRQ.RQueue.RQueueWrapper import RQueueWrapper
from PyRQ.RRQ.RRQPackage import RRQPackage
from Queue import Full, Empty
import PyRQ.Core.Errors as Errors
import PyRQ.Core.Messages as Messages
import SocketServer
import copy
import pickle
import socket
import threading
import traceback
import uuid

class _CLOSE(object):   pass

class RRQHandler(object, SocketServer.BaseRequestHandler):
    MAX_CLOSE_THREADS = 10
    class FinishedWithSocket(Exception): pass
    def __init__(self, *args, **kwargs):
        self._clients = {}  #    {namespace:[socks]}
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)
    def _doResponse(self, request, response):
        try:
            pickle.dumps(response)
        except Exception, _e:
            self.logger.error("Failed to pickle the following response: <%(R)s>"%{"R":response})
        try:
            request.sendall(response)
        except Exception, _e:
            #    We don't care if the remote side has disconnected: fire-and-forget!
            pass
    def _packageClients(self, clients, maxPackages):
        #    Now package up the clients into 'n' packages.
        size = len(clients)
        packages = []
        (minCountPerPackage, _remainder) = divmod(size, maxPackages)
        if minCountPerPackage==0:
            return [clients]
        minCountPerPackage += 1
        numPackages = ((size/minCountPerPackage)+1)
        for _ in xrange(numPackages):
            packages.append([])
        index = 0
        while len(clients)>0:
            client = clients.pop()
            packages[index].append(client)
            index += 1
            if index==len(packages):
                index = 0
        return packages
    def closeClients(self, namespace, clientData, marshaller, quiet):
        debugger = self.getDebugger()
        if debugger:
            uu = debugger.closeClients_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
        with self.getClientLock():
            numClients = len(self._clients)
            if namespace in self._clients:
                #    Close clients in parallel:
                def closeClient(clients):
                    while len(clients)>0:
                        c = clients.pop()
                        try:
                            self._doResponse(c.request, marshaller.package(Messages.CLOSED(namespace=namespace)))
                            PyRQTimeUtils.delayTime(1)
                            c.request.shutdown(socket.SHUT_WR)
                            c.request.close()
                            del c
                        except Exception, _e:
                            pass
                maxPackages = RRQHandler.MAX_CLOSE_THREADS
                if len(self._clients[namespace])>0:
                    packages = self._packageClients(self._clients[namespace], maxPackages)
                    #    Now farm out the work packages:
                    for index, clients in enumerate(packages):
                        if not quiet: self.logger.debug("Closing client for namespace: %(Q)s\r\n"%{"Q":namespace})
                        t = threading.Timer(0, closeClient, args=[clients])
                        t.setDaemon(True)
                        t.setName("ClientCloser_%(U)s_%(I)s"%{"U":namespace, "I":index})
                        t.start()
                del self._clients[namespace]
            #    Now discard the buffer and queue:
            try:
                qData = clientData["queues"][namespace]
            except Exception, _e:
                pass
            else:
                #    Tell each GET client to close:
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
        debugger = self.getDebugger(inst=RRQDebugger())
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
                except RRQHandler.FinishedWithSocket, _e:
                    if not quiet: self.logger.debug("Finished with socket for client: %(C)s\r\n"%{"C":self.client})
                    return
                except socket.error, _e:
                    self.logger.warn("Socket error in work for client: %(C)s\r\n"%{"C":self.client})
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
                    raise RRQHandler.FinishedWithSocket()
                #    Pump the data into the marshaller, piping the packages onto the target:
                for p in marshaller.receive(data):
                    if not quiet: self.logger.debug("WORK %(P)s for: %(C)s\r\n"%{"P":p, "C":self.client_address})
                    if isinstance(p, RRQPackage):
                        pp = p.data
                        namespace = p.namespace
                        if debugger:
                            uu = debugger.work_start(self.peerName, PyRQTimeUtils.getTime(), pp)
                        if not quiet: self.logger.debug("WORK data: %(P)s for: %(C)s\r\n"%{"P":pp, "C":self.client_address})
                        if isinstance(pp, Messages.CREATE):
                            self._addClient(self, namespace)
                            self._stall("CREATE", clientData, quiet)
                            self._create(marshaller, pp, clientData, quiet)
                        elif isinstance(pp, Messages.CLOSE):
                            self._addClient(self, namespace)
                            self._stall("CLOSE", clientData, quiet)
                            self._close(marshaller, namespace, clientData, quiet)
                        elif isinstance(pp, Messages.PUT):
                            self._addClient(self, namespace)
                            self._stall("PUT", clientData, quiet)
                            self._put(namespace, pp, clientData, marshaller, quiet)
                        elif isinstance(pp, Messages.GET):
                            self._addClient(self, namespace)
                            self._stall("GET", clientData, quiet)
                            self._get(namespace, pp, clientData, marshaller, quiet)
                        elif isinstance(pp, Messages.QSIZE):
                            self._addClient(self, namespace)
                            self._stall("QSIZE", clientData, quiet)
                            self._qSize(namespace, clientData, marshaller, quiet)
                        elif isinstance(pp, Messages.MAXQSIZE):
                            self._addClient(self, namespace)
                            self._stall("MAXQSIZE", clientData, quiet)
                            self._maxQSize(namespace, clientData, marshaller, quiet)
                        elif isinstance(pp, Messages.DEBUG):
                            self._debug(pp, marshaller, clientData, quiet)
                        if debugger:
                            debugger.work_end(self.peerName, PyRQTimeUtils.getTime(), uu=uu)
    def _close(self, marshaller, namespace, clientData, quiet):
        if not quiet: self.logger.debug("CLOSE - START @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
            debugger = self.getDebugger()
            if debugger:
                uu = debugger.close_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
            try:
                with self.getClientLock():
                    alreadyClosed = (namespace in clientData["stale-queues"])
                if alreadyClosed==True:
                    #    Subsequent close already!
                    self._doResponse(self.request, marshaller.package(Messages.CLOSED(result=False, namespace=namespace)))
                    return
                self.closeClients(namespace, clientData, marshaller, quiet)
                raise RRQHandler.FinishedWithSocket()
            finally:
                if debugger:
                    debugger.close_end(self.peerName, PyRQTimeUtils.getTime(), namespace, uu=uu)
        finally:
            if not quiet: self.logger.debug("CLOSE - END @%(T)s"%{"T":PyRQTimeUtils.getTime()})
    def _create(self, marshaller, pp, clientData, quiet):
        if not quiet: self.logger.debug("CREATE - START @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
            debugger = self.getDebugger()
            socketDetails = self.client_address
            queueType = pp.queueType
            maxsize = pp.maxsize
            pollInterval = pp.pollInterval
            if debugger:
                uu = debugger.create_start(self.peerName, PyRQTimeUtils.getTime(), queueType, maxsize, pollInterval)
            namespace = uuid.uuid4().hex
            with self.getClientLock():
                #    There is a remote chance that the uuids will be identical so:
                if namespace in clientData["queues"].keys():
                    namespace += namespace
                q = RQueueWrapper(queueType,
                                  self.getNewLogger,
                                  namespace,
                                  maxsize=maxsize,
                                  pollInterval=pollInterval,
                                  quiet=quiet)
                clientData["queues"][namespace] = q
            if debugger:
                uu = debugger.create_end(self.peerName, PyRQTimeUtils.getTime(), namespace, uu=uu)
            if not quiet: self.logger.info("CREATE - namespace: %(R)s from %(C)s\r\n"%{"R":namespace, "C":socketDetails})
            self._doResponse(self.request, marshaller.package(Messages.ACK(namespace)))
        finally:
            if not quiet: self.logger.debug("CREATE - END @%(T)s"%{"T":PyRQTimeUtils.getTime()})
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
        if not quiet: self.logger.debug("PUT - START @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
            #    Add the data onto the queue for namespace:
            debugger = self.getDebugger()
            socketDetails = self.client_address
            q = self._getQ(namespace, clientData, marshaller)
            if q!=None:
                #    Now loop every 'pollDelay' seconds, checking if we're closed.
                block = pp.block
                timeout = pp.timeout
                data = pp.data
                if debugger:
                    uu = debugger.put_start(self.peerName, PyRQTimeUtils.getTime(), namespace, block, timeout, data)
                result = Messages.ACK(namespace)
                try:
                    if not quiet: self.logger.debug("PUT - %(D)s"%{"D":data})
                    if block==False:
                        if not quiet: self.logger.debug("PUT start (non-blocking) @%(T)s - %(D)s"%{"D":data, "T":namespace})
                        q.put(data, block=False)
                    else:
                        if not quiet: self.logger.debug("PUT start (blocking) @%(T)s - %(D)s"%{"D":data, "T":namespace})
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
                    if not quiet: self.logger.error("PUT - %(D)s Exception[0] from %(C)s"%{"D":data, "C":socketDetails})
                    pass
                if isinstance(result, Exception):
                    if not quiet: self.logger.debug("PUT - %(D)s Exception[1] from %(C)s"%{"D":data, "C":socketDetails})
                if debugger:
                    debugger.put_end(self.peerName, PyRQTimeUtils.getTime(), namespace, result, uu=uu)
                if not quiet: self.logger.info("PUT - %(D)s result: %(R)s from %(C)s\r\n"%{"R":result, "D":data, "C":socketDetails})
                self._doResponse(self.request, marshaller.package(result))
        finally:
            if not quiet: self.logger.debug("PUT end @%(T)s"%{"T":PyRQTimeUtils.getTime()})
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
        if not quiet: self.logger.debug("GET - START @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
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
                        if not quiet: self.logger.info("Manual close detected, performing clean-close, propagating ClosedError back to client.\r\n")
                        result = Errors.ClosedError()
                    else:
                        result = Messages.GOT(data)
                        if not quiet: self.logger.debug("GOT DATA for %(NS)s - %(D)s"%{"D":data, "NS":namespace})
                if debugger:
                    debugger.get_end(self.peerName, PyRQTimeUtils.getTime(), namespace, result, uu=uu)
                if not quiet: self.logger.info("GET result for %(NS)s - %(D)s"%{"D":result, "NS":namespace})
                self._doResponse(self.request, marshaller.package(result))
        finally:
            if not quiet: self.logger.debug("GET - END @%(T)s"%{"T":PyRQTimeUtils.getTime()})
    def _qSize(self, namespace, clientData, marshaller, quiet):
        if not quiet: self.logger.debug("QSIZE - START @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
            debugger = self.getDebugger()
            if debugger:
                uu = debugger.qsize_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
            if not quiet: self.logger.debug("QSIZE - ns = %(D)s"%{"D":namespace})
            with self.getClientLock():
                if not namespace in clientData["queues"]:
                    result = Errors.NoSuchQueue(namespace)
                    if namespace in clientData["stale-queues"]:
                        result = Errors.ClosedError()
                else:
                    size = clientData["queues"][namespace].qsize()
                    result = Messages.QSIZE(size)
            if debugger:
                debugger.qsize_end(self.peerName, PyRQTimeUtils.getTime(), namespace, result, uu=uu)
            if not quiet: self.logger.info("QSIZE result for %(NS)s - %(D)s"%{"D":result, "NS":namespace})
            self._doResponse(self.request, marshaller.package(result))
        finally:
            if not quiet: self.logger.debug("QSIZE - END @%(T)s"%{"T":PyRQTimeUtils.getTime()})
    def _maxQSize(self, namespace, clientData, marshaller, quiet):
        if not quiet: self.logger.debug("MAXQSIZE - START @%(T)s"%{"T":PyRQTimeUtils.getTime()})
        try:
            debugger = self.getDebugger()
            if debugger:
                uu = debugger.maxqsize_start(self.peerName, PyRQTimeUtils.getTime(), namespace)
            if not quiet: self.logger.debug("MAXQSIZE - ns = %(D)s"%{"D":namespace})
            with self.getClientLock():
                if not namespace in clientData["queues"]:
                    result = Errors.NoSuchQueue(namespace)
                    if namespace in clientData["stale-queues"]:
                        result = Errors.ClosedError()
                else:
                    size = clientData["queues"][namespace].maxQSize()
                    result = Messages.MAXQSIZE(size)
            if debugger:
                debugger.maxqsize_end(self.peerName, PyRQTimeUtils.getTime(), namespace, result, uu=uu)
            if not quiet: self.logger.info("MAXQSIZE result for %(NS)s - %(D)s"%{"D":result, "NS":namespace})
            self._doResponse(self.request, marshaller.package(result))
        finally:
            if not quiet: self.logger.debug("MAXQSIZE - END @%(T)s"%{"T":PyRQTimeUtils.getTime()})
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
        @summary: Configure the debug mechanism.
        """
        debugger = self.getDebugger()
        try:
            if isinstance(cmd, Messages.DEBUG_START):
                if not quiet: self.logger.info("DEBUG_START filename: <%(F)s>, server: <%(S)s>...\r\n"%{"S":cmd.server, "F":cmd.filename})
                try:
                    result = debugger.start(self.peerName, PyRQTimeUtils.getTime(), cmd.filename, cmd.server)
                except Exception, result:
                    if not quiet: self.logger.error("Unable to start debugger!")
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
                if not quiet: self.logger.error("UNKNOWN DEBUG command: <%(C)s>."%{"C":cmd})
                raise UnknownDebuggerCommand(cmd)
        except Exception, result:
            pass
        finally:
            if not quiet: self.logger.error("result: <%(C)s>."%{"C":result})
        self._doResponse(self.request, marshaller.package(result))
