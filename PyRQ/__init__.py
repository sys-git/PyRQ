r"""
    PyRQ
    A pure python remote queue implementation.
    Conceptually, a series of multiprocessing-queues sit behind a socketserver 
    which acts as a proxy to them.
    The proxy resides in a separate Python Process launched by the subprocess
    module.
    Queue can be created and destroyed (freeing all resources).
    The proxy is referenced by it's host:port details.
    The queue is referenced by it's namespace (uuid4) returned when created.
    All methods contain a timeout value, this allows for network latency.
    At the moment, the mock implementation is also the real one!
    The proxy is accessed using the PyRQIface which holds the PyRQ host:port and
    namespace details for the desired queue.
"""

from Core.Linkage.Linkage import Linkage
from Core.QueueServer.SubprocessQueueServer import \
    SubprocessQueueServer as PyRQServer
from Core.Utils.PyRQTimeUtils import PyRQTimeUtils
from Iface.PyRQIface import PyRQIface
from Iface.PyRQIfaceFactory import PyRQIfaceFactory
from Iface.PyRQIfaceType import PyRQIfaceType
from version import *
import Core.Errors as PyRQErrors
import traceback

try:
    from Ui.qt4.RRQDebugger import RunRRQDebugger as RRQDebugger
    from Ui.qt4.RRQDebugger import subprocessRRQDebugger as SubprocessRRQDebugger
except Exception, _e:
    import sys
    sys.stderr.write("Debugger disabled.")#\r\n%(T)s"%{"T":traceback.format_exc()})
