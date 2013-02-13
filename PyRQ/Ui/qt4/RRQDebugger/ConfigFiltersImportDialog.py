'''
Created on 11 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers

class ConfigFiltersImportDialog(QtGui.QDialog):
    RESOURCE_NAME = "ConfigFiltersImportDialog.ui"
    indicees = [
                  Enablers.GET_START,
                  Enablers.GET_END,
                  Enablers.PUT_START,
                  Enablers.PUT_END,
                  Enablers.CREATE_START,
                  Enablers.CREATE_END,
                  Enablers.CLOSE_START,
                  Enablers.CLOSE_END,
                  Enablers.QSIZE_START,
                  Enablers.QSIZE_END,
                  Enablers.MAXQSIZE_START,
                  Enablers.MAXQSIZE_END,
                  ]
    def __init__(self, parent, currentConfig, newConfig, *args, **kwargs):
        super(ConfigFiltersImportDialog, self).__init__(*args, **kwargs)
        self.parent = parent
        self.resourcesPath = parent.resourcesPath
        self.currentConfig = currentConfig
        self.newConfig = newConfig
        self._config = None
    def setupUi(self):
        self.connect(self.pushButton_Accept, Qt.SIGNAL('pressed()'), self._onAccept, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Reject, Qt.SIGNAL('pressed()'), self._onReject, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_SelectAll, Qt.SIGNAL('pressed()'), self._onSelectAll, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_SelectNone, Qt.SIGNAL('pressed()'), self._onSelectNone, QtCore.Qt.QueuedConnection)
        self.connect(self.listWidget_Items, Qt.SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self._onDoubleClick, QtCore.Qt.QueuedConnection)
        self._onSelectAll()
    def _onAccept(self):
        #    Build the config object from the appropriate keys.
        for row in xrange(self.listWidget_Items.count()):
            item = self.listWidget_Items.item(row)
            if item.checkState()==QtCore.Qt.Checked:
                #    Import this config...
                self.currentConfig.update(self.indicees[row], self.newConfig)
        self._config = self.currentConfig
        self.accept()
    def _onReject(self):
        self.reject()
    def _onDoubleClick(self, item):
        checkState = item.checkState()
        if checkState==QtCore.Qt.Checked:
            checkState = QtCore.Qt.Unchecked
        else:
            checkState = QtCore.Qt.Checked
        item.setCheckState(checkState)
        #    Now scroll the example list to the given index:
        action = str(item.text().toAscii()).lower()
        index = ConfigFiltersImportDialog.indicees.index(action)
        self.listWidget_Example.scrollToItem(self.listWidget_Example.item(index))
    def _onSelectAll(self):
        for row in xrange(self.listWidget_Items.count()):
            item = self.listWidget_Items.item(row)
            item.setCheckState(QtCore.Qt.Checked)
    def _onSelectNone(self):
        for row in xrange(self.listWidget_Items.count()):
            item = self.listWidget_Items.item(row)
            item.setCheckState(QtCore.Qt.Unchecked)
    def getConfig(self):
        #    Return the resultant config.
        return self._config
    