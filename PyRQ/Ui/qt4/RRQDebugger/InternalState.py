'''
Created on 10 Oct 2012

@author: francis
'''

from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails
from PyRQ.Ui.qt4.RRQDebugger.Failed import Failed
import pickle

class InternalState(object):
    def __init__(self, settings):
        self.filename = ".state"
        self.details = {}       #    {'host:port':{"qs":iQueueServerDetails}}
        self.dirty = False
        self.settings = settings
    def save(self):
        return pickle.dumps(self)
    def add(self, details):
        d = str(details)
        if d in self.details.keys():
            raise Failed(details)
        self.details[d] = details
        self.dirty = True
    def remove(self, details):
        d = str(details)
        if d not in self.details.keys():
            raise Failed(details)
        del self.details[d]
        self.dirty = True
    def getIterator(self):
        return self.details.values()
    def isDirty(self):
        return self.dirty
    def notDirty(self):
        self.dirty = False
    def store(self):
        #   Store our state to the registry (remove existing state first!!):
        print self.settings.group()
        self.settings.remove("sessions")
        self.settings.beginGroup("sessions")
        try:
            for (key, details) in self.details.items():
                host = details.host()
                port = details.port()
                self.settings.beginGroup(key)
                try:
                    self.settings.setValue("host", host)
                    self.settings.setValue("port", port)
                    self.settings.setValue("enabled", True)
                finally:
                    self.settings.endGroup()
        finally:
            self.settings.endGroup()
        self.notDirty()
    def retrieve(self):
        print self.settings.group()
        self.details = {}
        #   Retrieve our state from the registry:
        self.settings.beginGroup("sessions")
        try:
            for key in self.settings.childGroups():
                key = str(key)
                self.settings.beginGroup(key)
                try:
                    if self.settings.value("enabled", False).toBool():
                        host = self.settings.value("host")
                        port = self.settings.value("port")
                        if host.isValid() and port.isValid():
                            host = str(host.toString())
                            (port, isValid) = port.toUInt()
                            if isValid:
                                self.details[key] = QueueServerDetails(host, int(port))
                finally:
                    self.settings.endGroup()
        finally:
            self.settings.endGroup()
        self.notDirty()
