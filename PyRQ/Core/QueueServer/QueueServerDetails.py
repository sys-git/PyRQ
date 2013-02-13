
'''
Created on 13 Sep 2012

@author: francis
'''

from PyRQ.Core.QueueServer.iQueueServerDetails import iQueueServerDetails

class QueueServerDetails(iQueueServerDetails):
    def __init__(self, host, port=None, namespace=None):
        self._host = host
        if port!=None:
            port = int(port)
        self._port = port
        self._namespace = namespace
    def host(self):
        return self._host
    def port(self):
        return self._port
    def namespace(self):
        return self._namespace
    def setNamespace(self, namespace):
        self._namespace = namespace
    def __eq__(self, other):
        if isinstance(other, iQueueServerDetails):
            if other.host()==self.host():
                if other.port()==self.port():
                    return True
        return False
    def __neq__(self, other):
        return not self.__eq__(other)
    def __str__(self):
        ns = ""
        if self._namespace!=None:
            ns = " with ns: <%(N)s>"%{"N":self._namespace}
        return "Server on %(H)s:%(P)s %(N)s"%{"H":self._host, "P":self._port, "N":ns}
