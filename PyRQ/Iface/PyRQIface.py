'''
Created on 12 Sep 2012

@author: francis
'''
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.Messages.ACK import ACK
from PyRQ.Core.Messages.CLOSE import CLOSE
from PyRQ.Core.Messages.CLOSED import CLOSED
from PyRQ.Core.Messages.CREATE import CREATE
from PyRQ.Core.Messages.GET import GET
from PyRQ.Core.Messages.GOT import GOT
from PyRQ.Core.Messages.MAXQSIZE import MAXQSIZE
from PyRQ.Core.Messages.PUT import PUT
from PyRQ.Core.Messages.QSIZE import QSIZE
from PyRQ.Core.Utils.PyRQTimeUtils import PyRQTimeUtils
from PyRQ.Iface.iPyRQIface import iPyRQIface
from PyRQ.RRQ.RRQPackage import RRQPackage
from PyRQ.RRQ.RRQType import RRQType
from Queue import Full, Empty
from multiprocessing.synchronize import RLock
import PyRQ.Core.Errors as Errors
import socket
import threading

class _Timeout(Exception):   pass

class PyRQIface(iPyRQIface):
    r"""
    @summary: A physical interface to a PyRQ.
    The PyRQ must be reachable on the network or loopback adaptor.
    To make all interfaces use the same PyRQ instance, set it's details: setGlobalPYRQ().
    To make each interface use a different PyRQ instance, override it with: setPYRQ().
    """
    closedQueues = {}
    PyRqDetails = None
    loggingModule = None
    NOT_CONNECTED = "NOT_CONNECTED"
    MINIMUM_SOCKET_LATENCY = 3
    DEFAULT_QUEUETYPE = RRQType.LOCKED_LIST
    def __init__(self,
                 namespace=None,
                 marshaller=MarshallerFactory.DEFAULT,
                 sockTimeout=10,
                 quiet=False,
                 PyRqDetails=None,
                 ref="",
                 loggingModule=None,
                 loggingLevel=None,
                 allowIfaceTimeouts=True,
                 keepAlive=False,
                 maxDataSize=None,
                 ):
        if loggingModule==None:
            if PyRQIface.loggingModule==None:
                import logging
                loggingModule = logging
            else:
                loggingModule = PyRQIface.loggingModule
        self._loggingModule = loggingModule
        self.setFixedTimeout(PyRQIface.MINIMUM_SOCKET_LATENCY)
        if loggingLevel==None:
            loggingLevel=self._loggingModule.INFO
        self._loggingLevel = loggingLevel
        self._ref = ref
        self.setNamespace(namespace)
        self._quiet = quiet
        self.keepAlive(keepAlive)
        self._maxDataSize = maxDataSize
        self._marshaller = MarshallerFactory.get(marshaller, quiet=self._quiet, maxsize=self._maxDataSize)
        self._sockTimeout = sockTimeout
        self._sock = None
        self._closed = False
        self.allowIfaceTimeouts(allowIfaceTimeouts)
        self._lastSockname = PyRQIface.NOT_CONNECTED
        self._PyRqDetails = PyRqDetails
    def keepAlive(self, enabler):
        self._keepAlive = enabler
    def getFixedTimeout(self):
        return self._minimumSocketLatency
    def setFixedTimeout(self, value):
        if (not isinstance(value, (int, float))) or (value<=0):
            raise ValueError("timeout must be float or int and > 0, got: <%(V)s>"%{"V":value})
        self._minimumSocketLatency = value
    @staticmethod
    def setGlobalPYRQ(details):
        PyRQIface.PyRqDetails = details
    @staticmethod
    def setGlobalLoggingModule(loggingModule):
        PyRQIface.loggingModule = loggingModule
    def setPYRQ(self, details):
        self._PyRqDetails = details
    def getDescription(self):
        conn = self._getConn()
        return "%(H)s:%(P)s"%{"H":conn.host(), "P":conn.port()}
    def _getConn(self):
        #    If our instance details are available use them, otherwise use the global ones.
        #    FIXME: Breaks OO, use __str__ as a method name instead.
        #    Only usd by SlaveServiceWorker anyway!
        if self._PyRqDetails!=None:
            return self._PyRqDetails
        return PyRQIface.PyRqDetails
    def allowIfaceTimeouts(self, enabler=True):
        self._allowIfaceTimeouts = enabler
    def unClose(self):
        self._closed = False
        self._logger
    def setNamespace(self, namespace):
        self._namespace = namespace
        self._getLogger(namespace)
    def _getLogger(self, namespace):
        try:    del self._logger
        except: pass
        try:    self._loggerHandler.close()
        except: pass
        try:    self._logger.removeHandler(self._loggerHandler)
        except: pass
        try:    del self._loggerHandler
        except: pass
        self._logger = self._loggingModule.getLogger("%(R)s.%(N)s"%{"R":self._ref, "N":namespace})
        try:
            #    Remove existing logger handlers:
            for handler in self._logger.handlers[:]:
                try:    self._logger.removeHandler(handler)
                except: pass
        except:
            pass
        self._logger.setLevel(self._loggingLevel)
        try:
            self._loggerHandler = self._loggingModule.StreamHandler()
            self._loggerHandler.setLevel(self._loggingLevel)
            formatter = self._loggingModule.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self._loggerHandler.setFormatter(formatter)
            self._logger.addHandler(self._loggerHandler)
        except:
            self._loggerHandler = None
    def close(self, timeout=None):
        r"""
        @summary: Close the remote 'Queue', no further actions are possible.
        """
        namespace = self._namespace
        if not self._quiet: self._logger.debug("close START")
        try:
            if (self._closed==True) or (self._namespace in PyRQIface.closedQueues.keys()):
                if not self._quiet: self._logger.error("close already closed")
                raise Errors.ClosedError(namespace=self._namespace)
            c = self._connect()
            try:
                c._write(CLOSE(), timeout=timeout)
            except (_Timeout, Errors.Finished), _e:
                if not self._quiet: self._logger.info("close OK apparently")
            except Errors.ClosedError, e:
                #    Excellent, closed?
                if e.result==False:
                    #    No - already closed!
                    if not self._quiet: self._logger.error("close closed already")
                    raise
                if not self._quiet: self._logger.info("close OK")
        except Exception, e:
            if not self._quiet: self._logger.error("close raising: %(E)s"%{"E":e})
            raise
        finally:
            self._setClosed(namespace)
            self._logger.debug("close END")
    def create(self, maxsize=0, timeout=None, queueType=None, pollInterval=None):
        r"""
        @summary: Open a connection to the RRQ and ask it to create a new 'Q'.
        """
        if not self._quiet: self._logger.debug("create START")
        try:
            if self._closed==True:
                if not self._quiet: self._logger.error("create already closed")
                raise Errors.ClosedError(namespace=self._namespace)
            c = self._connect()
            sockDetails = self._sock.getsockname()
            try:
                ack = c._write(CREATE(maxsize=maxsize, queueType=queueType, pollInterval=pollInterval), timeout=timeout)
            except Errors.ClosedError, e:
                if not self._quiet: self._logger.error("create CLOSED: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                self._closed=True
                raise Errors.PyRQError(e)
            except (_Timeout, Errors.Finished), e:
                self._logger.error("create unable to create: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                raise Errors.PyRQError(e)
            else:
                self._namespace = namespace = ack.namespace
                if not self._quiet: self._logger.info("create OK: %(NS)s from: %(W)s"%{"NS":namespace, "W":sockDetails})
                return namespace
        except Exception, e:
            if not self._quiet: self._logger.error("create raising: %(E)s"%{"E":e})
            raise
        finally:
            self._logger.debug("create END")
    def get_nowait(self, block=True, timeout=None):
        return self.get(block=False, timeout=timeout)
    def get_no_wait(self, block=True, timeout=None):
        return self.get(block=False, timeout=timeout)
    def get(self, block=True, timeout=None):
        if not self._quiet: self._logger.debug("get START")
        sockDetails = None
        try:
            if (self._closed==True) or (self._namespace in PyRQIface.closedQueues.keys()):
                if not self._quiet: self._logger.error("get already closed")
                raise Errors.ClosedError(namespace=self._namespace)
            namespace = self._namespace
            c = self._connect()
            sockDetails = self._sock.getsockname()
            if not self._quiet: self._logger.info("get from: %(W)s"%{"W":sockDetails})
            msg = GET(block=block, timeout=timeout)
            try:
                result = c._write(msg, timeout=timeout)
            except (_Timeout, Errors.Finished), e:
                if not self._quiet: self._logger.debug("get EMPTY from %(W)s"%{"W":sockDetails})
                raise Empty(e)
            except Errors.ClosedError, e:
                if not self._quiet: self._logger.error("get CLOSED: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                self._setClosed(namespace)
                raise
            else:
                if not self._quiet: self._logger.info("get OK %(D)s"%{"D":result})
                return result
        except Exception, e:
            if not self._quiet: self._logger.error("get RAISING: %(E)s from: %(W)s"%{"E":type(e), "W":sockDetails})
            raise
        finally:
            if not self._quiet: self._logger.debug("get END from: %(W)s"%{"W":sockDetails})
    def put_nowait(self, data, timeout=None):
        return self.put(data, block=False, timeout=timeout)
    def put(self, data, block=True, timeout=None):
        self._logger.debug("put START")
        sockDetails = None
        try:
            if (self._closed==True) or (self._namespace in PyRQIface.closedQueues.keys()):
                if not self._quiet: self._logger.error("put already closed")
                raise Errors.ClosedError(namespace=self._namespace)
            namespace = self._namespace
            c = self._connect()
            sockDetails = self._sock.getsockname()
            if not self._quiet: self._logger.debug("put from: %(W)s - %(D)s"%{"W":sockDetails, "D":data})
            msg = PUT(data, block=block, timeout=timeout)
            try:
                c._write(msg, timeout=timeout)
            except Errors.ClosedError, e:
                if not self._quiet: self._logger.error("put CLOSED: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                self._setClosed(namespace)
                raise
            except (_Timeout, Errors.Finished), e:
                if not self._quiet: self._logger.info("put FINISHED: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                raise Full(e)
            else:
                if not self._quiet: self._logger.info("put OK")
        except Exception, e:
            if not self._quiet: self._logger.error("put RAISING: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
            raise
        finally:
            self._logger.debug("put END")
    def qsize(self, timeout=None):
        self._logger.debug("qsize START")
        sockDetails = None
        try:
            if (self._closed==True) or (self._namespace in PyRQIface.closedQueues.keys()):
                if not self._quiet: self._logger.error("qsize already closed")
                raise Errors.ClosedError(namespace=self._namespace)
            namespace = self._namespace
            c = self._connect()
            sockDetails = self._sock.getsockname()
            msg = QSIZE()
            try:
                qSize = c._write(msg, timeout=timeout)
            except Errors.ClosedError, e:
                if not self._quiet: self._logger.error("qsize CLOSED: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                self._setClosed(namespace)
                raise
            except Exception, e:
                if not self._quiet: self._logger.error("qsize unable to qsize: %(E)s from %(W)s"%{"E":e, "W":sockDetails})
                raise Errors.PyRQError(e)
            else:
                if not self._quiet: self._logger.info("qsize OK %(S)s"%{"S":qSize})
                return qSize
        except Exception, e:
            if not self._quiet: self._logger.error("qsize RAISING: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
            raise
        finally:
            if not self._quiet: self._logger.debug("qsize END")
    def maxQSize(self, timeout=None):
        self._logger.debug("maxQSize START")
        sockDetails = None
        try:
            if (self._closed==True) or (self._namespace in PyRQIface.closedQueues.keys()):
                if not self._quiet: self._logger.error("maxQSize already closed")
                raise Errors.ClosedError(namespace=self._namespace)
            namespace = self._namespace
            c = self._connect()
            sockDetails = self._sock.getsockname()
            msg = MAXQSIZE()
            try:
                maxQSize = c._write(msg, timeout=timeout)
            except Errors.ClosedError, e:
                if not self._quiet: self._logger.error("maxQSize CLOSED: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                self._setClosed(namespace)
                raise
            except Exception, e:
                if not self._quiet: self._logger.error("maxQSize unable to maxQSize: %(E)s from %(W)s"%{"E":e, "W":sockDetails})
                raise Errors.PyRQError(e)
            else:
                if not self._quiet: self._logger.info("maxQSize OK %(S)s"%{"S":maxQSize})
                return maxQSize
        except Exception, e:
            if not self._quiet: self._logger.error("maxQSize RAISING: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
            raise
        finally:
            if not self._quiet: self._logger.debug("maxQSize END")
    def _sendData(self, data):
        try:
            d = self._marshaller.package(RRQPackage(self._namespace, data))
        except Exception, e:
            self._logger.error("_sendData[0]: %(E)s from: %(W)s"%{"E":e, "W":self._sock.getsockname()})
            raise Errors.PyRQError(e)
        try:
            self._sock.sendall(d)
        except Exception, e:
            self._logger.error("_sendData[1]: %(E)s from: %(W)s"%{"E":e, "W":self._sock.getsockname()})
            self._closeSocket()
            raise Errors.PyRQError(e)
    def _write(self, data, timeout=None):
        timer = None
        error = {"err":[], "lock":RLock()}
        try:
            sockDetails = self._sock.getsockname()
        except:
            sockDetails = ""
        try:
            try:
                try:
                    #    Send the actual data:
                    self._sendData(data)
                    #    Wait for the response in the given 'timeout':
#                    maxTime = None
#                    if timeout!=None:
#                        maxTime = PyRQTimeUtils.getTime()+timeout
                    #    Always have a socket timeout so we don't wait indefinitely.
                    currentSocketTimeout = 1
                    try:
                        self._sock.settimeout(currentSocketTimeout)
                    except AttributeError, _e:
                        self._logger.error("socket remotely closed already from: %(W)s"%{"W":sockDetails})
                        raise Errors.Finished()
                    r"""
                    If timeout==None then the user wants to wait indefinitely until either
                    the socket is shutdown/closed or a response is received.
                    """
                    if timeout!=None:
                        def operationTimeout(err):
                            #    Set the exception override...
#                            with err["lock"]:
#                                err["err"].append(_Timeout())
                            self._logger.warn("TIMEOUT on socket operation from: %(W)s"%{"W":sockDetails})
                            if self._allowIfaceTimeouts==True:
                                #    ...and close the socket:
                                self._closeSocket()
                        #    Start the 'timeout' timer - in-case the RRQ timeout fails to return in time:
                        tOut = self._minimumSocketLatency + timeout
                        timer = threading.Timer(tOut, operationTimeout, args=[error])
                        timer.setDaemon(True)
                        timer.setName("Timer_Write_%(T)s_q_%(Q)s"%{"T":timeout, "Q":self._namespace})
                        if not self._quiet: self._logger.error("WRITE: tOut: %(T)s, timeout: %(TO)s"%{"T":tOut, "TO":timeout})
                        timer.start()
                    while True:
                        #    Now wait from a response (always expected):
                        try:
                            data = self._sock.recv(1048576)
                        except socket.timeout, e:
                            pass
                        except AttributeError, _e:
                            if not self._quiet: self._logger.error("socket closed already when waiting for receive from: %(W)s"%{"W":sockDetails})
                            raise Errors.Finished()
                        except Exception, e:
                            #    Need to close!
                            self._logger.error("socket Exception: %(E)s from: %(W)s"%{"E":e, "W":sockDetails})
                            raise e
                        else:
                            if data=='':
                                #    Socket has been remotely shutdown:
                                if not self._quiet: self._logger.error("socket remotely closed already when processing data from: %(W)s"%{"W":sockDetails})
                                raise Errors.Finished()
                            marshaller = self._marshaller
                            for p in marshaller.receive(data):
                                if isinstance(p, Exception):
                                    #    Propagate directly:
                                    if not self._quiet: self._logger.error("received EXCEPTION: %(E)s from: %(W)s"%{"E":type(p), "W":sockDetails})
                                    raise p
                                elif isinstance(p, CLOSED):
                                    if not self._quiet: self._logger.warn("received REMOTE_CLOSE from: %(W)s"%{"W":sockDetails})
                                    raise Errors.ClosedError(result=p.result, namespace=p.namespace)
                                elif isinstance(p, ACK):
                                    if not self._quiet: self._logger.debug("received ACK from: %(W)s"%{"W":sockDetails})
                                    return p
                                elif isinstance(p, (QSIZE, MAXQSIZE)):
                                    if not self._quiet: self._logger.debug("received %(P)s from: %(W)s"%{"P":p, "W":sockDetails})
                                    return p.size
                                elif isinstance(p, GOT):
                                    if not self._quiet: self._logger.debug("received GOT from: %(W)s"%{"W":sockDetails})
                                    return p.data
                                else:
                                    if not self._quiet: self._logger.error("received unknown response: %(P)s from: %(W)s"%{"P":p, "W":sockDetails})
                                    raise Errors.ProtocolError("Unknown response received from RRQ", p)
                except Errors.ClosedError, _e:
                    #    The other-side directly told us that our Q is closed.
                    if not self._quiet: self._logger.info("We discovered socket remotely closed from: %(W)s"%{"W":sockDetails})
                    self._closed = True
                    raise
            except Exception, e:
                #    Log all exceptions, we're only interested in the first one.
                with error["lock"]:
                    err = error["err"].append(e)
                raise e
        except Exception, e:
            #    Obtain the first exception generated and raise it:
            with error["lock"]:
                if not self._quiet: self._logger.info("Exceptions(%(L)s): %(E)s from: %(W)s"%{"E":error["err"], "L":len(error["err"]), "W":sockDetails})
                err = error["err"][0]
            raise err
        finally:
            try:    timer.cancel()
            except: pass
            if self._keepAlive==False:
                self._closeSocket()
    def _setClosed(self, namespace):
        PyRQIface.closedQueues[namespace]=PyRQTimeUtils.getTime()
        self._logger.error("Q now closed.")
        self._closed=True
    def _connect(self):
        host = ""
        port = ""
        try:
            if self._sock==None:
                self._lastSockname = PyRQIface.NOT_CONNECTED
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setblocking(True)
                sock.settimeout(self._sockTimeout)
                con = self._getConn()
                host = con.host()
                port = con.port()
                sock.connect((host, port))
                self._sock = sock
                self._lastSockname = sock.getsockname()
            return self
        except Exception, e:
            self._logger.error("Unable to connect to PyRQ at: %(H)s:%(P)s"%{"H":host, "P":port})
            raise Errors.PyRQError(e)
    def _closeSocket(self):
        try:
            sockDetails = self._sock.getsockname()
            self._sock.shutdown(socket.SHUT_WR)
            self._sock.close()
            self._sock = None
        except Exception, _e:
            #    Don't care!
            pass
        else:
            if not self._quiet: self._logger.debug("socket closed to: %(H)s"%{"H":sockDetails})
    def getLastSockDetails(self):
        try:
            return self._lastSockname
        except:
            return PyRQIface.NOT_CONNECTED
