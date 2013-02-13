'''
Created on 17 Sep 2012

@author: francis
'''

from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueWriter.QueueWriter import QueueWriter
from PyRQ.RRQ.Messages.Ping import Ping
from Queue import Empty
import sys
import threading
import traceback

class Pinger(threading.Thread):
    def __init__(self, qs):
        super(Pinger, self).__init__()
        self.setDaemon(False)
        self.setName("Pinger")
        self._qs = qs
        self._qRx = qs.getTarget()
        self.start()
    def run(self):
        host = self._qs.details().host()
        port = self._qs.details().port()
        sys.stderr.write("Pinger listening on %(H)s:%(P)s with q: %(Q)s...\r\n"%{"Q":self._qRx, "H":host, "P":port})
        try:
            while True:
                #   Ping everything back!
                try:
                    data = self._qRx.get(block=True, timeout=1)
                except Empty, _e:
                    pass
                else:
#                    pydevd.settrace(stdoutToServer = True, stderrToServer = True)
                    sys.stderr.write("Pinger got data: %(D)s...\r\n"%{"D":data})
                    if isinstance(data, Ping):
                        replyTo = data.replyTo()
                        host = replyTo.host()
                        port = replyTo.port()
                        quiet = data.quiet()
                        if not quiet: sys.stderr.write("Pinger pinging data back to %(H)s:%(P)s\r\n"%{"H":host, "P":port})
                        m = MarshallerFactory.get(MarshallerFactory.DEFAULT)
                        qw = QueueWriter(target=replyTo, autoConnect=True, marshaller=m)
                        qw.put(Ping(data=data.data()))
        except Exception, _e:
            sys.stderr.write("Pinger got error: %(D)s...\r\n"%{"D":traceback.format_exc()})
        finally:
            sys.stderr.write("Pinger completed!\r\n")