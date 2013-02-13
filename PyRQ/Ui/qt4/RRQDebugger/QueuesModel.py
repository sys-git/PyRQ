'''
Created on 17 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore, uic
from PyRQ.Core.Messages.CLOSE import CLOSE
from PyRQ.Core.Messages.DEBUG import DEBUG_QUERY
import os

class QueuesModel(QtGui.QFrame):
    RESOURCE_NAME = "QueuesHolder.ui"
#    RESOURCE_NAME = "Queues.ui"
    TEXT_OBSERVED_QUEUES = "Observed queues:"
    TEXT_ALL_QUEUES = "All queues:"
    def __init__(self, parent, *args, **kwargs):
        super(QueuesModel, self).__init__(parent)
        self._parent = parent
        self._resourcePath = self._parent.debugger.resourcesPath
    def show(self, isconnected):
        self.observedQueues = uic.loadUi(os.path.join(self._resourcePath, "ObservedQueues.ui"))
        self.allQueues = uic.loadUi(os.path.join(self._resourcePath, "AllQueues.ui"))
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.splitter1.addWidget(self.allQueues)
        self.splitter1.addWidget(self.observedQueues)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.splitter1)
        self.frame_QueuesHolder.setLayout(self.layout)
        self.splitter1.show()
        self.connect(self.pushButton_Query, Qt.SIGNAL('pressed()'), self._onQuery, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL('queryRequested()'), self._onRequestQuery)
        self.connect(self.observedQueues.tableWidget_qNamespaces, Qt.SIGNAL('customContextMenuRequested(QPoint)'), self._onPopup_QNamespaces, QtCore.Qt.QueuedConnection)
        self.connect(self.allQueues.tableWidget_qAllNamespaces, Qt.SIGNAL('customContextMenuRequested(QPoint)'), self._onPopup_QAllNamespaces, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL('connectionState(int)'), self._onConnectionStateChange, QtCore.Qt.QueuedConnection)
    def _onConnectionStateChange(self, bState):
        self.pushButton_Query.setEnabled(bState)
        if bState==True:
            self.emit(Qt.SIGNAL("queryRequested()"))
    def _onRequestQuery(self):
        self._onQuery()
    def _showPopupMenu(self, table, pos, col):
        item = table.itemAt(pos)
        screenPos = table.mapToGlobal(pos)
        row = table.row(item)
        col = 0
        item = table.item(row, col)
        if item!=None:
            text =  str(item.text())
            if text not in self._parent.allQueues["defunct"]:
                menu = QtGui.QMenu(self)
                closeAction = menu.addAction("Close q: %(T)s"%{"T":text})
                action = menu.exec_(screenPos)
                if action == closeAction:
                    self._parent._sendUnique(CLOSE(), text)
            else:
                self._parent._actionMainPopup(screenPos)
        else:
            self._parent._actionMainPopup(screenPos)
    def _onPopup_QNamespaces(self, pos):
        self._showPopupMenu(self.observedQueues.tableWidget_qNamespaces, pos, 1)
    def _onPopup_QAllNamespaces(self, pos):
        self._showPopupMenu(self.allQueues.tableWidget_qAllNamespaces, pos, 1)
    def addNewQueue(self, ns, nsId):
        table = self.observedQueues.tableWidget_qNamespaces
        row = 0
        table.insertRow(row)
        for col, what in enumerate([str(nsId), str(ns)]):
            item = QtGui.QTableWidgetItem(what)
            table.setItem(row, col, item)
        table.resizeColumnsToContents()
#        table.sortItems(0)
        table.horizontalHeader().setStretchLastSection(True)
    def updateNumAllQueues(self):
        l1 = self._parent.allQueues["active"]
        l2 = self._parent.allQueues["defunct"]
        a = len(l1)
        d = len(l2)
        t = " ".join([QueuesModel.TEXT_ALL_QUEUES, "Active: %(A)s"%{"A":a}, "Defunct: %(D)s"%{"D":d}])
        self.allQueues.label_allQueues.setText(t)
    def updateNumObservedQueues(self):
        l = len(self._parent.qIds.keys())
        t = " ".join([QueuesModel.TEXT_OBSERVED_QUEUES, "Total: %(L)s"%{"L":l}])
        self.observedQueues.label_observedQueues.setText(t)
    def populateAllNamespaces(self):
        table = self.allQueues.tableWidget_qAllNamespaces
        table.setRowCount(0)
        #    Defunct queues:
        queues = self._parent.allQueues["defunct"]
        for row, what in enumerate(queues):
            table.insertRow(row)
            item = QtGui.QTableWidgetItem(QtCore.QString(what))
            table.setItem(row, 0, item)
            item = QtGui.QTableWidgetItem("DEFUNCT")
            table.setItem(row, 1, item)
        #    Active queues (all that aren't in: self._parent.qIds):
        queues = self._parent.allQueues["active"]
        row = 0
        for what in queues:
            if what not in self._parent.qIds:
                table.insertRow(row)
                item = QtGui.QTableWidgetItem(what)
                table.setItem(row, 0, item)
                item = QtGui.QTableWidgetItem("ACTIVE")
                table.setItem(row, 1, item)
        table.resizeColumnsToContents()
#        table.sortItems(0)
        table.horizontalHeader().setStretchLastSection(True)
    def _onQuery(self):
        self._parent._send(DEBUG_QUERY())
    def setNumQueues(self, l):
        self.lcdNumber_numQueues.display(l)
    def saveUi(self, settings):
        settings.beginGroup("queues")
        try:
            #    Save the value of the splitters
            settings.setValue("splitter1/position", self.splitter1.saveState())
        finally:
            settings.endGroup()
    def loadUi(self, settings):
        settings.beginGroup("queues")
        try:
            #    Save the value of the splitters
            value = settings.value("splitter1/position")
            if value.isValid():
                self.splitter1.restoreState(value.toByteArray())
        finally:
            settings.endGroup()















