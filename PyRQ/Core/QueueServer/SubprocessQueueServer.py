'''
Created on 14 Sep 2012

@author: francis
'''

from PyRQ.Core.Linkage.Linkage import Linkage
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.QueueServer import QueueServer
from PyRQ.Core.QueueServer.QueueServerOptions import QueueServerOptions
from PyRQ.Core.QueueServer.iQueueServerDetails import iQueueServerDetails
from Queue import Empty
from multiprocessing.queues import Queue
import PyRQ.Core.Errors as Errors
import os
import signal
import subprocess
import sys
import unittest

class SubprocessQueueServer(object):
    r"""
    @summary: Run a PyRQ in another Python Process using the 'subprocess' module.
    """
    def _getCwd(self):
        import PyRQ
        import inspect
        dirname = os.path.dirname(inspect.getfile(PyRQ))
        cwd = os.sep.join(dirname.split(os.sep)[:-1])
        return cwd
    def _getBootable(self):
        import BootQueueServer
        import inspect
        filename = inspect.getfile(BootQueueServer)
        sExt = os.path.splitext(filename)
        if sExt[1]==".pyc":
            filename = sExt[0]+".py"
        
        return "\""+filename+"\""
    def __init__(self,
                 cwd=None,
                 desiredHost="127.0.0.1",
                 desiredPort=QueueServer.DEFAULT_PORT,
                 linkage=Linkage(),
                 timeout=None,
                 handlerClazz=Linkage(),
                 includePydevd=None,
                 quiet=False,
                 location=None,
                 servicesLinkage=Linkage(),
                 maxClients=None,
                 dbgIface=None,
#                 includePydevd="/home/francis/.eclipse/org.eclipse.platform_3.7.0_155965261/plugins/org.python.pydev.debug_2.5.0.2012040618/pysrc",
                 **kwargs
#                 socketRecvChunkSize=None,
#                 socketReadTimeout=None,
            ):
        if cwd==None:
            cwd = self._getCwd()
        if location==None:
            location = self._getBootable()
        (target, tQs, details) = self._createResources(cwd, timeout, quiet)
        try:
            #    Construct the command-line:
            hc = ".".join([handlerClazz.clazzpath(), handlerClazz.clazz()])
            sl = ".".join([servicesLinkage.clazzpath(), servicesLinkage.clazz()])
            if len(hc)==1:
                hc = ""
            if len(sl)==1:
                sl = ""
            srcs = ""
            srt = ""
            lm = ""
            if "loggingModule" in kwargs:
                lm = kwargs["loggingModule"]
            if "socketRecvChunkSize" in kwargs:
                srcs = kwargs["socketRecvChunkSize"]
            if "socketReadTimeout" in kwargs:
                srt = kwargs["socketReadTimeout"]
            args1 = {
                    "ODP":QueueServerOptions.PORT,
                    "ODH":QueueServerOptions.HOST,
                    "OC":QueueServerOptions.CLAZZ,
                    "OCP":QueueServerOptions.CLAZZPATH,
                    "OAH":QueueServerOptions.ACKHOST,
                    "OAP":QueueServerOptions.ACKPORT,
                    "OHC":QueueServerOptions.HANDLERCLAZZ,
                    "OSCP":QueueServerOptions.SERVICES_CLAZZPATH,
                    "OSC":QueueServerOptions.SERVICES_CLAZZ,
                    "OQ":QueueServerOptions.QUIET,
                    "OSRCS":QueueServerOptions.SOCKET_RECV_CHUNK_SIZE,
                    "OSRT":QueueServerOptions.SOCKET_READ_TIMEOUT,
                    "OLM":QueueServerOptions.LOGGING_MODULE,
                    "OMC":QueueServerOptions.MAX_CLIENTS,
                    "DH":desiredHost,
                    "DP":desiredPort,
                    "H":details.host(),
                    "P":details.port(),
                    "C":linkage.clazz(),
                    "CP":linkage.clazzpath(),
                    "SC":servicesLinkage.clazz(),
                    "SCP":servicesLinkage.clazzpath(),
                    "HC":hc,
                    "Q":quiet,
                    "SRCS":srcs,
                    "SRT":srt,
                    "LM":lm,
                    "MC":maxClients,
                    }
            ll = ".".join([linkage.clazzpath(), linkage.clazz()])
            if len(ll)==1:
                ll = ""
            args = " ".join([
                             "--%(ODH)s %(DH)s"%args1,
                             "--%(ODP)s %(DP)s"%args1,
                             "--%(OAH)s %(H)s"%args1,
                             "--%(OAP)s %(P)s"%args1,
                             "--%(OMC)s %(MC)s"%args1,
                             ])
            if hc!="":
                args = " ".join([args, "--%(OHC)s %(HC)s"%args1])
            if ll!="":
                args = " ".join([args, "--%(OCP)s %(CP)s"%args1, "--%(OC)s %(C)s"%args1])
            if sl!="":
                args = " ".join([args, "--%(OSCP)s %(SCP)s"%args1, "--%(OSC)s %(SC)s"%args1])
            if quiet==True:
                args = " ".join([args, "--%(OQ)s"%args1])
            if "socketRecvChunkSize" in kwargs:
                args = " ".join([args, "--%(OSRCS)s %(SRCS)s"%args1])
            if "socketReadTimeout" in kwargs:
                args = " ".join([args, "--%(OSRT)s %(SRT)s"%args1])
            if "loggingModule" in kwargs:
                args = " ".join([args, "--%(OLM)s %(LM)s"%args1])
            pydevdPath = ""
            if includePydevd!=None:
                pydevdPath = includePydevd
            opt = ""
            if "opt" in kwargs:
                opt = "-O"
            cmd = ";".join(["export PYTHONPATH=$PYTHONPATH:.:%(PDEVP)s"%{"PDEVP":pydevdPath}, "python %(OPT)s %(L)s %(A)s"%{"L":location, "A": args, "OPT":opt}])
            #    Start the external process, tell it where to send the 'ack(host, port)'.
            self._process = subprocess.Popen(
                                             cmd,
                                             stdout=subprocess.PIPE,
                                             shell=True,
                                             #    FYI: Won't work on *indows
                                             preexec_fn=os.setsid,
                                             cwd=cwd
                                             )
            try:
                d = target.get(block=True, timeout=timeout)
            except Empty, e:
                #    Failed to start the server in the given timeout.
                raise Errors.StartError(e)
            else:
                #    Should have received a iQueueServerDetails object!
                if isinstance(d, iQueueServerDetails):
                    self._details = d
                else:
                    if not self._quiet: sys.stderr.write("Protocol error, expecting iQueueServerDetails but received %(D)s\r\n"%{"D":d})
                    self.close()
                    raise Errors.ProtocolError("First item received should be of type: iQueueServerDetails.", d)
        finally:
            try:
                tQs.close()
            except Exception, _e:
                pass
            try:
                target.close()
                del target
            except Exception, _e:
                pass
    def start(self):
        return self
    def close(self, block=True, timeout=None):
        try:
            os.killpg(self._process.pid, signal.SIGKILL)
        except Exception, _e:
            return False
        else:
            return True
    def waitUntilRunning(self, block=True, timeout=None):
        return
    def details(self):
        return self._details
    @staticmethod
    def _createResources(cwd, timeout, quiet):
        #    Create our listener:
        target = Queue()
        marshaller = MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=quiet)
        tQs = QueueServer(host="127.0.0.1", port=54000, target=target, marshaller=marshaller, quiet=quiet).start().waitUntilRunning()
        details = tQs.details()
        return (target, tQs, details)


if __name__ == '__main__':
    unittest.main()
