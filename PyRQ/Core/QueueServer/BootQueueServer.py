'''
Created on 17 Sep 2012

@summary: This module is called by the SubprocessQueueServer to bootstrap a
PyRQ instance.

@author: francis
'''

from PyRQ.Core.Linkage.Linkage import Linkage
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.QueueServer import QueueServer, ServerHandlerFactory
from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails
from PyRQ.Core.QueueServer.QueueServerOptions import QueueServerOptions
from PyRQ.Core.Utils.ImportUtils import _getClass, _importModule, \
    _importModuleName
from optparse import OptionParser
import sys
import traceback

def _getOptions(args=sys.argv[1:]):
    #    This is where we run from another process etc via the subprocess module.
    parser = OptionParser()
    #    For the ack:
    parser.add_option("-x", "--%(OAH)s"%{"OAH":QueueServerOptions.ACKHOST}, action="store", dest="ackHost", type="str", 
        metavar="ACK_HOST", default="%(DHA)s"%{"DHA":QueueServer.DEFAULT_HOST}, help="specify"
        "a host to send our server details to. Default is '%(DHA)s'"%{"DHA":QueueServer.DEFAULT_HOST})
    parser.add_option("-y", "--%(OAP)s"%{"OAP":QueueServerOptions.ACKPORT}, action="store", dest="ackPort", type="int", 
        metavar="ACK_PORT", default=None, help="specify"
        "a port to send our server details to. Default is 'None'.")
    #    For the server:
    parser.add_option("-a", "--%(P)s"%{"P":QueueServerOptions.PORT}, action="store", dest="port", type="int", 
        metavar="PORT", default=QueueServer.DEFAULT_PORT, help="specify a different "
        "TCP listener port. Default is '%(P)d'"%{"P":QueueServer.DEFAULT_PORT})
    parser.add_option("-b", "--%(H)s"%{"H":QueueServerOptions.HOST}, action="store", dest="host", type="str", 
        metavar="HOST", default="%(DHA)s"%{"DHA":QueueServer.DEFAULT_HOST}, help="specify a different "
        "host to bind to. Default is '%(DHA)s'"%{"DHA":QueueServer.DEFAULT_HOST})
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.MARSHALLER_TYPE}, action="store", dest="marshallerType", type="int", 
        metavar="MARSHALLER_TYPE", default=MarshallerFactory.DEFAULT, help="Type of the Queue's marshaller."
        "Default is '%(D)s'."%{"D":MarshallerFactory.DEFAULT})
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.CLAZZPATH}, action="store", dest="clazzpath", type="str", 
        metavar="CLAZZPATH", default=None, help="specify a classpath "
        "to launch this queue with. Default is 'None'.")
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.CLAZZ}, action="store", dest="clazz", type="str", 
        metavar="CLAZZ", default=None, help="specify a class from the given clazzpath"
        "to launch this queue with. Default is 'None'.")
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.HANDLERCLAZZ}, action="store", dest="handlerClazz", type="str", 
        metavar="HANDLER_CLAZZ", default=None, help="The handler clazz to execute for new socket connections."
        "Default is 'None'")
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.MAX_CLIENTS}, action="store", dest="maxClients", type="str", 
        metavar="MAX_CLIENTS", default=None, help="Max number of clients."
        "Default is 'None'")
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.QUIET}, action="store_true", dest="quiet", 
        metavar="QUIET", default=False, help="Non-verbose output."
        "Default is 'False'")
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.SERVICES_CLAZZPATH}, action="store", dest="servicesClazzpath", type="str", 
        metavar="SERVICES_CLAZZPATH", default=None, help="specify a classpath for the plugin services object"
        "Default is 'None'.")
    parser.add_option("--%(H)s"%{"H":QueueServerOptions.SERVICES_CLAZZ}, action="store", dest="servicesClazz", type="str", 
        metavar="CLAZZ", default=None, help="specify a class from the given servicesClazzpath"
        "Default is 'None'.")
    parser.add_option("--%(OAP)s"%{"OAP":QueueServerOptions.SOCKET_RECV_CHUNK_SIZE}, action="store", dest="socketRecvChunkSize", type="int", 
        metavar="SOCKET_RECV_CHUNK_SIZE", default=ServerHandlerFactory.DEFAULT_RECV_CHUNK_SIZE, help="specify "
        "a recv chunk size for the socket. Default is '%(D)s'."%{"D":ServerHandlerFactory.DEFAULT_RECV_CHUNK_SIZE})
    parser.add_option("--%(OAP)s"%{"OAP":QueueServerOptions.SOCKET_READ_TIMEOUT}, action="store", dest="socketReadTimeout", type="int", 
        metavar="SOCKET_RECV_CHUNK_SIZE", default=ServerHandlerFactory.DEFAULT_SOCKET_READ_TIMEOUT, help="specify "
        "a read timeout for the socket. Default is '%(D)s'."%{"D":ServerHandlerFactory.DEFAULT_SOCKET_READ_TIMEOUT})
    parser.add_option("--%(OAH)s"%{"OAH":QueueServerOptions.LOGGING_MODULE}, action="store", dest="loggingModule", type="str", 
        metavar="LOGGING_MODULE", default=None, help="specify a logging module to use. Default is 'None'")
    options, _args = parser.parse_args(args=args)
    return options

def _loadLoggingModule(loggingModule):
    if loggingModule!=None:
        m = _importModuleName(loggingModule)
        return m

def _loadHost(options, handlerClazz, **kwargs):
    servicesClazzpath = options.servicesClazzpath
    servicesClazz = options.servicesClazz
    quiet = options.quiet
    if (servicesClazzpath!=None) and (len(servicesClazzpath)>0) and (servicesClazz!=None) and (len(servicesClazz)>0):
        services = _importModule(options.servicesClazzpath, options.servicesClazz)
        from PyRQ import PyRQTimeUtils
        PyRQTimeUtils.set_getTime(services.getSystemUptimeInteger)
        PyRQTimeUtils.set_delayTime(services.timeSleep)
        b = PyRQTimeUtils.getTime()
        if not quiet: sys.stderr.write("subprocess getTime()...%(T)s\r\n"%{"T":b})
    if options.handlerClazz!=None:
        handlerClazz = _getClass(options.handlerClazz)
        hC = Linkage.create(handlerClazz)
    else:
        msg = "No HandlerClazz specified!!!"
        sys.stderr.write(msg)
        raise Exception(msg)
#        hC = Linkage.create(RRQHandler)
#        handlerClazz = _getClass(".".join([hC.clazzpath(), hC.clazz()]))
    if not quiet: sys.stderr.write("BootQueueServer::handlerClazz... %(H)s  .  %(P)s\r\n"%{"H":hC.clazzpath(), "P":hC.clazz()})
    from multiprocessing.queues import Queue
    mt = options.marshallerType
    mt = int(mt)
    target=Queue()
    kwargs["maxClients"] = options.maxClients
    kwargs["quiet"] = quiet
    kwargs["recvChunkSize"] = int(options.socketRecvChunkSize)
    kwargs["readTimeout"] = int(options.socketReadTimeout)
    kwargs["loggerModule"] = _loadLoggingModule(options.loggingModule)
    qs = QueueServer(host=options.host,
                     port=options.port,
                     marshaller=MarshallerFactory.get(mt, quiet=quiet),
                     target=target,
                     handlerClazz=handlerClazz,
                     **kwargs)
    qs.start().waitUntilRunning()
    if options.ackHost and options.ackPort:
        #    Send the ack back!
        if not quiet: sys.stderr.write("BootQueueServer::load...[0.1]: %(H)s:%(P)s[1]\r\n"%{"H":options.ackHost, "P":options.ackPort})
        from PyRQ.Core.QueueWriter.QueueWriter import QueueWriter
#        import pydevd
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        qw = QueueWriter(target=QueueServerDetails(options.ackHost, options.ackPort),
                        marshaller=MarshallerFactory.get(mt, quiet=quiet),
                        autoConnect=True,
                        sockTimeout=10,
                        quiet=quiet
                        )
        if not quiet: sys.stderr.write("BootQueueServer::load...[1.0]\r\n")
        qw.start()
        details = qs.details()
        if not quiet: sys.stderr.write("BootQueueServer::load...[1.2]: %(D)s\r\n"%{"D":details})
        qw.put(details)
        if not quiet: sys.stderr.write("BootQueueServer::load...[1.2]\r\n")
    #    Now we have a queue which we can use to receive messages on:    'target'.
    importedModule = None
    if options.clazzpath!=None and options.clazz!=None:
        if not quiet: sys.stderr.write("BootQueueServer::load...Launching %(P)s.%(C)s with target queue: %(Q)s\r\n"%{"P":options.clazzpath, "C":options.clazz, "Q":target})
        try:
            importedModule = _importModule(options.clazzpath, options.clazz)(qs)
        except Exception, _e:
            sys.stderr.write("Error Launching %(P)s.%(C)s with target queue: %(Q)s\r\n%(T)s\r\n"%{"P":options.clazzpath, "C":options.clazz, "Q":target, "T":traceback.format_exc()})
    return (qs, target, importedModule)

def BootQueueServer(args=sys.argv[1:], handlerClazz=None, **kwargs):
    sys.stderr.write("BootQueueServer...args: %(A)s\r\n"%{"A":args})
    sys.stderr.write("BootQueueServer...handlerClazz: %(A)s\r\n"%{"A":handlerClazz})
    sys.stderr.write("BootQueueServer...kwargs: %(A)s\r\n"%{"A":kwargs})
    options = _getOptions(args=args)
    (qs, _target, _importedModule) = _loadHost(options, handlerClazz, **kwargs)
    sys.stderr.write("BootQueueServer waiting for completion...\r\n"%{"A":args})
    qs.join()
    sys.stderr.write("BootQueueServer completed!\r\n"%{"A":args})

def RunQueueServer(args=sys.argv[1:], handlerClazz=None, **kwargs):
    options = _getOptions(args=args)
    (qs, _target, _importedModule) = _loadHost(options, handlerClazz, **kwargs)
    sys.stderr.write("RunQueueServer completed!\r\n"%{"A":args})
    return (qs, _target, _importedModule)

if __name__ == '__main__':
    BootQueueServer()
