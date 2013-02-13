'''
Created on 10 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.Core.Utils.NetworkUtils import get_ipv4_address

class SetHostDialog(QtGui.QDialog):
    RESOURCE_NAME = "SetHostDialog.ui"
    def __init__(self, host, *args, **kwargs):
        self._host = None
        self._oldHost = host
        super(SetHostDialog, self).__init__(*args, **kwargs)
    def host(self):
        return self._host
    def setupUi(self):
        self.connect(self.pushButton_Accept, Qt.SIGNAL('pressed()'), self._onAccept, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Cancel, Qt.SIGNAL('pressed()'), QtCore.SLOT('reject()'), QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Refresh, Qt.SIGNAL('pressed()'), self._onRefresh, QtCore.Qt.QueuedConnection)
        self.lineEdit_existingHost.setText("%(H)s"%{"H":self._oldHost})
        self._onRefresh()
    def _onAccept(self):
        self._host = self._getHost()
        self.accept()
    def _getHost(self):
        #    Find out which interface is selected:
        return self.listWidget_Hosts.currentItem().text()
    def _onRefresh(self):
        self.listWidget_Hosts.clear()
        (localHost, hosts) = self._getAllHosts()
        self.listWidget_Hosts.addItem(QtGui.QListWidgetItem(localHost))
        for host in hosts:
            self.listWidget_Hosts.addItem(QtGui.QListWidgetItem(host))
        self.listWidget_Hosts.setCurrentRow(0)
    def _getAllHosts(self):
        hosts = get_ipv4_address()
        try:
            localHost = hosts.pop(hosts.index("127.0.0.1"))
        except Exception, _e:
            localHost = None
        return (localHost, hosts)
