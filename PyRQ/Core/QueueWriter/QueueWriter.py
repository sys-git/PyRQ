'''
Created on 12 Sep 2012

@author: francis
'''
import PyRQ.Core.Errors as Errors
from PyRQ.Core.Marshal.NoMarshallerError import NoMarshallerError
from PyRQ.Core.Marshal.iMarshaller import iMarshaller
from PyRQ.Core.QueueServer.iQueueServerDetails import iQueueServerDetails
from PyRQ.Core.QueueWriter.iQueueWriter import iQueueWriter
from Queue import Full
from multiprocessing.synchronize import RLock
import socket
import sys
import traceback
import uuid

class QueueWriter(iQueueWriter):
    DEFAULT_QUIET = False
    r"""
    @summary: Presents a queue-like interface to allow sending data to the queue.
    """
    def __init__(self,
                 target=None,
                 quiet=False,
                 marshaller=None,
                 autoConnect=False,
                 sockTimeout=None):
        r"""
        @param target: QueueServer details to connect to.
        @param quiet: Silence stderr.
        @param marshaller: The marshaller to use.
        """
        self.quiet(quiet)
        self._autoConnect = autoConnect
        self._sockTimeout = sockTimeout
        self._marshaller = marshaller
        self._uuid = uuid.uuid4()
        self._name = "QueueWriter_%(U)s"%{"U":self._uuid}
        self._lock = RLock()
        self._target = target
        self._sock = None
        if target!=None:
            self.setTarget(target)
    def quiet(self, enabler):
        try:
            self._quiet = bool(enabler)
        except Exception, _e:
            self._quiet = QueueWriter.DEFAULT_QUIET
        return self._quiet
    def start(self):
        if self._sock!=None:
            raise Errors.AlreadyStartedError()
        if self._target==None:
            raise Errors.ConfigurationError("Target not configured.")
        #    Create the connection to the remote Queue:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self._sockTimeout)
        host = self._target.host()
        port = self._target.port()
        if not self._quiet: sys.stderr.write("%(N)s connecting to: %(H)s:%(P)s\r\n"%{"N":self._name, "H":host, "P":port})
        sock.connect((host, port))
        self._sock = sock
        return self
    def close(self):
        try:
            self._sock.close()
        except Exception, _e:
            pass
        else:
            if not self._quiet: sys.stderr.write("%(N)s closed.\r\n"%{"N":self._name})
        self._sock = None
    def setMarshaller(self, marshaller=None):
        if not isinstance(marshaller, iMarshaller):
            raise ValueError("%(N)s marshaller of incorrect type: <%(T)s>, expecting one of: [iMarshaller]"%{"N":self._name, "T":marshaller})
        with self._lock:
            if self._marshaller != marshaller:
                self._marshaller = marshaller
                if not self._quiet: sys.stderr.write("%(N)s marshaller changed to: %(T)s\r\n"%{"N":self._name, "T":marshaller})
    def setTarget(self, target=None):
        if not isinstance(target, iQueueServerDetails):
            raise ValueError("%(N)s target of incorrect type: <%(T)s>, expecting iQueueServerDetails"%{"N":self._name, "T":target})
        with self._lock:
            if self._target != target:
                self._target = target
                if not self._quiet: sys.stderr.write("%(N)s target changed to: %(T)s\r\n"%{"N":self._name, "T":target})
    def put(self, data, block=True, timeout=None):
        if self._sock==None:
            if self._autoConnect:
                self.start()
        with self._lock:
            target = self._target
            marshaller = self._marshaller
        if not target:
            raise Errors.ClosedError()
        if not marshaller:
            raise NoMarshallerError()
        if not self._quiet: sys.stderr.write("%(N)s PUT(%(B)s, %(T)s) onto target: %(G)s, data: %(D)s"%{"B":block, "T":timeout, "U":self._uuid, "G":target, "N":self._name, "D":data})
        try:
            self._sock.setblocking(bool(block))
            self._sock.sendall(marshaller.package(data))
        except socket.error, _e:
            if not self._quiet: sys.stderr.write("%(N)s Socket error sending data:\r\n%(T)s\r\n"%{"N":self._name, "T":traceback.format_exc()})
            self.close()
            raise Full()
        except Exception, _e:
            if not self._quiet: sys.stderr.write("%(N)s Error sending data:\r\n%(T)s\r\n"%{"N":self._name, "T":traceback.format_exc()})
            self.close()
            raise Errors.ClosedError()
        else:
            pass

if __name__ == '__main__':
    pass
