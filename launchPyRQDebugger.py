'''
Created on 2 Oct 2012

@author: francis
'''

from PyRQ import PyRQServer
import PyRQ
import os

def getIpOfHost():
    result = None
    try:
        try:
            import platform
            p = platform.platform()
            if p[1:].startswith("indows"):
                import socket
                result = socket.gethostbyname(socket.gethostname())
            else:
                import subprocess
                result = subprocess.check_output('ifconfig').split('\n')[1].split()[1][5:]
        except Exception, _e:
            import commands
            op = commands.getoutput("ifconfig")
            result = op.split("\n")[1].split()[1][5:]
    finally:
        print "Determined local host: %(H)s"%{"H":result}
        return result
__defaultHostAddress = getIpOfHost()

def getHost():
    return (__defaultHostAddress)

def LaunchPyRQDebugger(details=[], quiet=True, host=getHost()):
    #    Host = where the debugger listens.
    debugger = PyRQ.RRQDebugger(quiet=quiet, details=details, host=host)
    return debugger

def SubprocessPyRQDebugger(details=[], quiet=True, host=getHost(), cwd=os.getcwd()):
    #    Host = where the debugger listens.
    debugger = PyRQ.SubprocessRRQDebugger(quiet=quiet, details=details, host=host, cwd=cwd)
    return debugger

if __name__ == '__main__':
    noTestQueue=True
    host=getHost()
    quiet = True
    details = []
    if noTestQueue==False:
        qs = PyRQServer(
                        desiredHost=host,
                        quiet=quiet,
                        )
        details = [qs.details()]
    LaunchPyRQDebugger(details=details, quiet=quiet, host=host)
    if noTestQueue==False:
        qs.close()
    print "done"
