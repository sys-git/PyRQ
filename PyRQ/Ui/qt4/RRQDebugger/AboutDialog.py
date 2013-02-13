'''
Created on 10 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.version import getVersionString, getVersionDate
import os
import platform

class AboutDialog(QtGui.QDialog):
    RESOURCE_NAME = "about.ui"
    TEXT_HEADER = "About PyRQ Debugger"
    IMAGE_FILENAME = "icon.png"
    def __init__(self, resourcesPath, host, details, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)
        self.resourcesPath = resourcesPath
        self.host = host
        self.details = details
    def setupUi(self):
        path = os.path.join(self.resourcesPath, "icons", AboutDialog.IMAGE_FILENAME)
        pm = QtGui.QPixmap(path)
        self.label_image.setText("")
        self.label_image.setPixmap(pm)
        args = {"PLAT":platform.platform(),
                "PROC":platform.processor(),
                "S": platform.system(),
                "R":platform.release(),
                "P":platform.python_version(),
                "NODE":platform.node(),
                "MACH":platform.machine(),
                "I":platform.python_implementation()}
        t = ["System info:"]
        t.append("OS: %(PLAT)s %(R)s"%args)
        t.append("CPU: %(NODE)s %(PROC)s"%args)
        t.append("Python info:")
        t.append("%(I)s %(P)s"%args)
        tt = "\n".join(t)
        self.plainTextEdit_System.setPlainText(tt)
        self.setWindowTitle(AboutDialog.TEXT_HEADER)
        args = {"VS":getVersionString(), "D":getVersionDate(), "S":len(self.details), "H":self.host}
        tHeader = ["PyRQ debugger", "Version: %(VS)s"%args, "Date: %(D)s"%args, "Host: %(H)s"%args]
        tBody =   ["Number of sessions: %(S)s"%args]
        for index, (detail, name, isConnected) in enumerate(self.details):
            k = index+1
            host = detail.host()
            port = detail.port()
            connectionStatus = ""
            if isConnected==False:
                connectionStatus = " (disconnected)"
            tBody.append("Session %(K)s: listening on: %(H)s:%(P)s to PyRQ: %(N)s%(CON)s"%{"H":host, "K":k, "P":port, "N":name, "CON":connectionStatus})
        tFooter = ["", "Have a nice day!"]
        tt = "\n".join(tHeader+tBody+tFooter)
        self.plainTextEdit_body.setPlainText(tt)
        self.connect(self.pushButton_Ok, Qt.SIGNAL('pressed()'), QtCore.SLOT('accept()'), QtCore.Qt.QueuedConnection)
