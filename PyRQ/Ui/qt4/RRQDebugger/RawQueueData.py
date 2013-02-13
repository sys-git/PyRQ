'''
Created on 17 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.Messages.DEBUG import DEBUG_SOMETHING, DEBUG_START
from PyRQ.Core.QueueWriter.QueueWriter import QueueWriter

class RawQueueData(QtGui.QFrame):
    RESOURCE_NAME = "RawQueueData.ui"
    def __init__(self, parent, *args, **kwargs):
        super(RawQueueData, self).__init__(parent)
        self._parent = parent
        self._state = False
    def show(self, isConnected):
        self.connect(self.pushButton_Test, Qt.SIGNAL('pressed()'), self._onTest, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Clear, Qt.SIGNAL('pressed()'), self._onClear, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Connect, Qt.SIGNAL('pressed()'), self._onConnect, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL('connectionState(int)'), self._onConnectionStateChange, QtCore.Qt.QueuedConnection)
        self._onConnectionStateChange(isConnected)
    def _onTest(self):
        quiet=self._parent.debugger.quiet
        iface = QueueWriter( target=self._parent.details,
                             autoConnect=True,
                             marshaller=MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=quiet),
                             quiet=quiet)
        iface.start()
        iface.put(DEBUG_SOMETHING())
        iface.close()
    def _onClear(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
    def _onConnect(self):
        if self._state==False:
            self.pushButton_Connect.setText("Connecting")
            self.pushButton_Connect.setEnabled(False)
            self._parent._connect(DEBUG_START(server=self._parent.qs.details()))
        else:
            #    Pointless really:
            self._parent._disconnect()
    def saveUi(self, settings):
        pass
    def loadUi(self, settings):
        pass
    def _onConnectionStateChange(self, bState):
        self._state = bState
        self.checkBox_Enabled.setChecked(bState)
        self.pushButton_Test.setEnabled(bState)
        if bState==True:
            self.pushButton_Connect.setText("Disconnect")
        else:
            self.pushButton_Connect.setText("Connect")
        self.pushButton_Connect.setEnabled(True)


