
from PyRQ import PyRQServer
from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails
from PyRQ.Ui.qt4.RRQDebugger.RRQDebugger import RRQDebugger
from optparse import OptionParser
import os
import subprocess
import sys

def RunRRQDebugger(quiet=True, details=[], host="127.0.0.1"):
    #    Launch the simple UI.
    from PyQt4 import QtGui, uic
    resourcesPath = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources"))
    path = os.path.join(resourcesPath, RRQDebugger.RESOURCE_NAME)
    app = QtGui.QApplication(sys.argv)
    inst = RRQDebugger(resourcesPath, details=details, quiet=quiet, host=host)
    uic.loadUi(path, baseinstance = inst)
    print "UI Show..."
    inst.show()
    print "UI Execute..."
    app.exec_() # Run the UI

def subprocessRRQDebugger(quiet=True, details=[], host="127.0.0.1", cwd=os.getcwd()):
    q = ""
    if quiet==True:
        q = "-q"
    args = ["%(Q)s"%{"Q":q}]
    args.append("--host %(H)s"%{"H":host})
    for detail in details:
        args.append("-d %(H)s:%(P)s"%{"H":detail.host(), "P":detail.port()})
    cmd = "python %(F)s %(A)s"%{"F":__file__, "A":" ".join(args)}
    process = subprocess.Popen(
                                 cmd,
                                 stdout=subprocess.PIPE,
                                 shell=True,
                                 #    FYI: Won't work on *indows
                                 preexec_fn=os.setsid,
                                 cwd=cwd
                                 )

def getOptions(args=sys.argv[1:]):
    #    This is where we run from another process etc via the subprocess module.
    parser = OptionParser()
    parser.add_option("--host", action="store", dest="host", type="str",
        metavar="HOST", default="127.0.0.1", help="Specify a host, Default is: '127.0.0.1'.")
    parser.add_option("-d", action="append", dest="details", type="str", 
        metavar="PYRQ_DETAILS", help="Specify a PyRQ, Default is '[]'.")
    parser.add_option("-q", action="store_true", dest="quiet", 
        metavar="QUIET", default=False, help="specify quiet, default is: 'False'")
    options, _args = parser.parse_args(args=args)
    return options

if __name__ == '__main__':
#    import pydevd
#    pydevd.settrace(stdoutToServer = True, stderrToServer = True)
    options = getOptions(sys.argv[1:])
    quiet = options.quiet
    host = options.host
    details = options.details
    allDetails = []
    for detail in details:
        params = detail.split(":")
        allDetails.append(QueueServerDetails(params[0], port=int(params[1])))
    print "quiet: %(Q)s"%{"Q":quiet}
    print "host: %(Q)s"%{"Q":host}
    print "details: %(Q)s"%{"Q":allDetails}
    debugger = RunRRQDebugger(quiet=quiet, details=allDetails, host=host)
