'''
Created on 10 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, QtCore, Qt
from PyRQ.Core.Messages.CLOSE import CLOSE
from PyRQ.Core.Messages.CREATE import CREATE
from PyRQ.Core.Messages.PUT import PUT
from PyRQ.RRQ.RRQType import RRQType
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
from Queue import Full
import copy
import random

class QueueActionDialog(QtGui.QDialog):
    RESOURCE_NAME = "QueueActionDialog.ui"
    def __init__(self, resourcesPath, parent, action, *args, **kwargs):
        super(QueueActionDialog, self).__init__(parent=parent)
        self.resourcesPath = resourcesPath
        self.parent = parent
        self.action = action
        self.queues = []
        self.indexMap = {
                         Enablers.CREATE_START:0,
                         Enablers.CLOSE_START:1,
                         Enablers.PUT_START:2,
                         Enablers.GET_START:3,
                         Enablers.QSIZE_START:4,
                         Enablers.MAXQSIZE_START:5,
                         }
    def show(self):
        super(QueueActionDialog, self).show()
        self.connect(self, QtCore.SIGNAL("changeTab(PyQt_PyObject)"), self._onChangeTab, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Ok, Qt.SIGNAL('pressed()'), QtCore.SLOT('accept()'), QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Create, Qt.SIGNAL('pressed()'), self._onCreate, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Refresh, Qt.SIGNAL('pressed()'), self._onRefresh, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Close, Qt.SIGNAL('pressed()'), self._onClose, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_CloseAll, Qt.SIGNAL('pressed()'), self._onCloseAll, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Put, Qt.SIGNAL('pressed()'), self._onPut, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Get, Qt.SIGNAL('pressed()'), self._onGet, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_QSize, Qt.SIGNAL('pressed()'), self._onQSize, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_MaxQSize, Qt.SIGNAL('pressed()'), self._onMaxQSize, QtCore.Qt.QueuedConnection)
        self.tabWidget.setCurrentIndex(self.indexMap[self.action])
        self._onRefresh()
    def _onChangeTab(self, action):
        self.tabWidget.setCurrentIndex(self.indexMap[action])
    def _onRefresh(self):
        #   Now populate the tabs:
        self.queues = copy.deepcopy(self.parent.allQueues["active"])
        for cb in [self.comboBox_QueueClose, self.comboBox_QueuePut, self.comboBox_QueueGet, self.comboBox_QueueQSize, self.comboBox_QueueMaxQSize]:
            cb.clear()
            for namespace in self.queues:
                cb.addItem(namespace)
    def _onCreate(self):
        count = self.spinBox_CreateCount.value()
        maxSize = self.spinBox_CreateMaxsize.value()
        timeout = self._getTimeout(self.spinBox_CreateTimeout)
        iface = self.parent.getIface()
        typeMap = {
                   0:RRQType.LOCKED_LIST,
                   1:RRQType.MULTIPROCESSING_QUEUE,
                   2:None,
                   3:-1,
                   }
        ns = []
        ran = random
        for _ in xrange(count):
            queueType = typeMap[self.comboBox_CreateQueueType.currentIndex()]
            if queueType==-1:
                queueType = ran.sample([RRQType.LOCKED_LIST, RRQType.MULTIPROCESSING_QUEUE], 1)[0]
            ns.append(iface.create(maxsize=maxSize, timeout=timeout, queueType=queueType))
        result = ", ".join(ns)
        self.lineEdit_Create.setText(result)
    def _onClose(self):
        namespace = self._getNamespace(self.comboBox_QueueClose)
        if namespace!=None:
            self.parent._sendUnique(CLOSE(), namespace)
    def _onCloseAll(self):
        for namespace in self.queues:
            if namespace!=None:
                self.parent._sendUnique(CLOSE(), namespace)
    def _onPut(self):
        data = str(self.lineEdit_Content.text())
        namespace = self._getNamespace(self.comboBox_QueuePut)
        block = self._getBlock(self.checkBox_PutBlock)
        timeout = self._getTimeout(self.spinBox_PutTimeout)
        iface = self.parent.getIface(namespace)
        iface.put(data, block=block, timeout=timeout)
    def _onGet(self):
        self.lineEdit_Get.clear()
        namespace = self._getNamespace(self.comboBox_QueueGet)
        block = self._getBlock(self.checkBox_GetBlock)
        timeout = self._getTimeout(self.spinBox_GetTimeout)
        iface = self.parent.getIface(namespace)
        try:
            result = iface.get(block=block, timeout=timeout)
        except Full, _e:
            result = "Full"
        except Exception, e:
            result = str(e)
        self.lineEdit_Get.setText("GET = <"+str(result)+">")
    def _onQSize(self):
        self.lineEdit_QSize.clear()
        namespace = self._getNamespace(self.comboBox_QueueQSize)
        timeout = self._getTimeout(self.spinBox_QSizeTimeout)
        iface = self.parent.getIface(namespace)
        try:
            result = iface.qsize(timeout=timeout)
        except Exception, e:
            result = str(e)
        self.lineEdit_QSize.setText("QSize = "+str(result))
    def _onMaxQSize(self):
        self.lineEdit_QSize.clear()
        namespace = self._getNamespace(self.comboBox_QueueMaxQSize)
        timeout = self._getTimeout(self.spinBox_MaxQSizeTimeout)
        iface = self.parent.getIface(namespace)
        try:
            result = iface.qsize(timeout=timeout)
        except Exception, e:
            result = str(e)
        self.lineEdit_MaxQSize.setText("MaxQSize = "+str(result))
    def _getBlock(self, item):
        return item.isChecked()
    def _getTimeout(self, item):
        timeout = self.spinBox_PutTimeout.value()
        if timeout==-1:
            timeout = None
        return timeout
    def _getNamespace(self, item):
        namespace = str(item.currentText())
        if namespace and len(namespace)>0:
            return namespace









