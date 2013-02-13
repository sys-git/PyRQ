'''
Created on 17 Sep 2012

@author: francis
'''

from PyRQ.Core.Errors.TooManyClientsError import TooManyClientsError
import SocketServer
import socket
import sys
import traceback

class QueueServerHandler(object, SocketServer.BaseRequestHandler):
    r"""
    A socketserver handler which marshals data from the socket connection
    onto a target with a method: 'put(data)'
    """
    def __init__(self, *args, **kwargs):
        SocketServer.BaseRequestHandler.__init__(self, *args, **kwargs)
    def setup(self):
        try:
            self.client = self.newClient(self)
        except TooManyClientsError, _e:
            self.abort = True
    def finish(self):
        try:
            self.clientFinished(self.client)
        except Exception, _e:
            pass
    def handle(self):
        if self.abort:
            return
        target = self.getTarget()
        marshaller = self.getMarshaller()
        quiet = self.getQuiet()
        if not quiet: sys.stderr.write("Serving new client [%(C)s] from %(CON)s\r\n"%{"C":self.client, "CON":self.request.getpeername()})
        try:
            self._work(target, marshaller, quiet)
        except Exception, _e:
            #    This is fatal, so just return.
            sys.stderr.write("Error in work for client: %(C)s\r\n%(T)s\r\n"%{"C":self.client, "T":traceback.format_exc()})
    def _work(self, target, marshaller, quiet):
        self.request.settimeout(self.getReadTimeout())
        while self.getTerminate()==False:
            #    Receive the data from the socket:
            try:
                data = self.request.recv(self.getRecvChunkSize())
            except socket.timeout, _e:
                pass
            else:
                if data=='':
                    self.abort = True
                    break
                #    Pump the data into the marshaller, piping the packages onto the target:
                for p in marshaller.receive(data):
                    target = self.getTarget()
                    if target!=None:
                        if not quiet: sys.stderr.write("q'd data: <%(D)s>\r\n"%{"D":p})
                        target.put(p)
