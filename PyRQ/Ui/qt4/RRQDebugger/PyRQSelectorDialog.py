'''
Created on 10 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails
from PyRQ.RRQ.Debugger.PING import PING
from PyRQ.Ui.qt4.RRQDebugger.RRQTab import RRQTab

class PyRQSelectorDialog(QtGui.QDialog):
    RESOURCE_NAME = "PyRQSelectorDialog.ui"
    STATE_TESTING = "testing"
    STATE_OK = "ok"
    STATE_FAIL = "fail"
    def __init__(self, debugger, quiet, parent, *args, **kwargs):
        self.debugger = debugger
        self._details = None
        self.state = PyRQSelectorDialog.STATE_TESTING
        self.quiet = quiet
        super(PyRQSelectorDialog, self).__init__(parent=parent)
    def details(self):
        return self._details
    def setupUi(self, host="127.0.0.1", port=10000):
        self.lineEdit_host.setText(host)
        self.pushButton_Test.setText("Test")
        self.spinBox_port.setValue(int(port))
        self.connect(self.pushButton_Test, Qt.SIGNAL('pressed()'), self._onButton, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Cancel, Qt.SIGNAL('pressed()'), QtCore.SLOT('reject()'), QtCore.Qt.QueuedConnection)
    def closeEvent(self, event):
        self._details = self._getDetails()
        event.accept()
    def _getDetails(self):
        try:
            host = str(self.lineEdit_host.text().toAscii())
            port = int(self.spinBox_port.value())
            details = QueueServerDetails(host, port)
        except:
            details = None
        return details
    def _onButton(self):
        if self.state in [PyRQSelectorDialog.STATE_TESTING, PyRQSelectorDialog.STATE_FAIL]:
            self._checkPyrq()
        elif self.state==PyRQSelectorDialog.STATE_OK:
            self.accept()
    def _checkPyrq(self):
        try:
            self.pushButton_Test.setText("testing")
            details = self._getDetails()
            iface = RRQTab.staticConnect(self.debugger, details, PING())
        except Exception, e:
            reason = e.message
            if (reason==None) or (reason==""):
                reason = str(e)
                self.state = PyRQSelectorDialog.STATE_FAIL
                self.pushButton_Test.setText("FAIL - retest")
        else:
            self._details = details
            self.state = PyRQSelectorDialog.STATE_OK
            self.pushButton_Test.setText("OK - continue")
            iface.close()
