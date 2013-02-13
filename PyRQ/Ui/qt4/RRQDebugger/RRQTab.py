'''
Created on 10 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore, uic
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.Messages.CLOSE import CLOSE
from PyRQ.Core.Messages.DEBUG import DEBUG_START, DEBUG_STOP, DEBUG_SOMETHING, \
    DEBUG_QUERY
from PyRQ.Core.QueueServer.QueueServer import QueueServer
from PyRQ.Core.QueueWriter.QueueWriter import QueueWriter
from PyRQ.Iface.PyRQIface import PyRQIface
from PyRQ.RRQ.Debugger.iRRQDebuggerSink import iRRQDebuggerSink
from PyRQ.RRQ.RRQPackage import RRQPackage
from PyRQ.Ui.qt4.RRQDebugger.ActionDecoder import ActionDecoder
from PyRQ.Ui.qt4.RRQDebugger.Failed import Failed
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
from PyRQ.Ui.qt4.RRQDebugger.FiltererModel import FiltererModel
from PyRQ.Ui.qt4.RRQDebugger.QueueActionDialog import QueueActionDialog
from PyRQ.Ui.qt4.RRQDebugger.QueuesModel import QueuesModel
from PyRQ.Ui.qt4.RRQDebugger.RawQueueData import RawQueueData
from Queue import Full
from multiprocessing.queues import Queue
import itertools
import os
import threading
import time

class RRQTab(QtGui.QWidget):
    RESOURCE_NAME = "RRQTab.ui"
    uId = itertools.count(0)
    dataCount = itertools.count(0)
    def __init__(self, parent, details):
        super(RRQTab, self).__init__(parent=parent)
        self._createFile(parent, details)
        self.allQueues = {"active":[], "defunct":[]}
        self.qIds = {}
        self._data = []
        self._actionDialog = None
        self.details = details
        self.debugger = parent
        self._connectPending = False
        #    self.iface is used to send commands to the PyRQ (we could use a new specific interface?!):
        self.iface = None
        #    self.q receives the debugging info on:
        self.q = Queue()
        #    self.qs receives all debugging for a particular PyRQ:
        self.qs = QueueServer(host=self.debugger.host,
                              port=32323,
                              marshaller=MarshallerFactory.get(MarshallerFactory.DEFAULT),
                              target = self.q,
                              quiet=self.debugger.quiet)
        self.qs.start().waitUntilRunning()
    def getData(self):
        return self._data
    def _createFile(self, parent, details):
        filename = "%(H)s.%(P)s"%{"H":details.host(), "P":details.port()}
        path = os.path.join(parent.path, filename)
        self.fp = open(path, "wb")
    def getName(self):
        return ":".join([self.details.host(), str(self.details.port())])
    def _disconnect(self):
        try:
            if self.iface!=None:
                self.iface.close()
        except: pass
        self.iface = None
        self.emit(Qt.SIGNAL("connectionState(int)"), False)
    def _connect(self, msg):
        if self._connectPending==True:
            return
        self._connectPending = True
        #    Run asynchronously
        try:
            if self.iface!=None:
                self.iface.close()
        except: pass
        self.iface = None
        def doConnect(debugger, details, msg):
            try:
                iface = RRQTab.staticConnect(debugger, details, msg)
                startTime = time.time()
                state = True
            except Exception, _e:
                iface = None
                startTime = None
                state = False
            self.emit(Qt.SIGNAL("connectionState(int, PyQt_PyObject, PyQt_PyObject)"), state, iface, startTime)
        t = threading.Thread(target=doConnect, args=[self.debugger, self.details, msg])
        t.setName("connect_%(D)s"%{"D":str(self.details)})
        t.setDaemon(True)
        t.start()
    @staticmethod
    def staticConnect(debugger, target, msg=None):
        if target:
            #    Now try and connect to this PyRQ.
            iface = QueueWriter( target=target,
                                 marshaller=MarshallerFactory.get(MarshallerFactory.DEFAULT),
                                 autoConnect=True,
                                 quiet=True)
            if msg!=None:
                debugger.logger.warn("Sending data: %(D)s"%{"D":msg})
                try:
                    RRQTab.staticSend(iface, msg)
                except Full:
                    #    Can't send!
                    iface.close()
                    iface = None
                    raise
            return iface
    def _send(self, data, iface=None):
        if self.iface!=None:
            try:
                return self.staticSend(self.iface, data)
            except Full:
                self.iface.close()
                self.iface = None
                raise
        else:
            raise Failed()
    def _sendUnique(self, data, namespace):
        try:
            return RRQTab.staticConnect(self.debugger, self.details).put(RRQPackage(namespace, data), block=False, timeout=1)
        except Exception, _e:
            raise
    def getIface(self, namespace=None):
        return PyRQIface(namespace=namespace,
                         quiet=True,
                         PyRqDetails=self.details,
                         keepAlive=True,
                         )
    @staticmethod
    def staticGetIface(details, namespace=None):
        return PyRQIface(namespace=namespace,
                         quiet=True,
                         PyRqDetails=details,
                         keepAlive=True,
                         )
    @staticmethod
    def staticSend(iface, data):
        return iface.put(RRQPackage("dummyNamespace", data), block=False, timeout=1)
    def close(self):
        self.theQueues.close()
        self.theFilterer.close()
        self.rawQueueData.close()
        #    Tell the PyRQ to stop debugging:
        try:    self._send(DEBUG_STOP())
        except: pass
        try:    self.iface.close()
        except Exception, _e: pass
        self.iface = None
        #    Close the QueueServer:
        try:
            qs = self.qs
            qs.close()
        except Exception, _e:
            pass
        self.qs = None
        #    Close the reception queue:
        try:
            q = self.q
            q.close()
        except Exception, _e:
            pass
        self.q = None
        if self.fp!=None:
            try:    self.fp.flush()
            except: pass
            try:    self.fp.close()
            except: pass
            self.fp = None
    def getQ(self):
        return self.q
    def _extractAll(self, data):
        (action, args, kwargs) = data
        peer = args[0]
        theTime = args[1]
        args = args[2:]
        row = 0
        nArgs = []
        try:
            for arg in args:
                nArgs.append(arg)
        except:
            nArgs = args
        params = self._extractDecode(action, nArgs, kwargs)
        query = params["query"]
        if query!=None:
            (namespaces, staleNamespaces) = query
            self._handleQuery(namespaces, staleNamespaces)
            return
        self.rawQueueData.tableWidget.insertRow(row)
        timeNow = time.time()
        timeOffset = timeNow - self.startTime
        dataCount = RRQTab.dataCount.next()
        return (dataCount, peer, theTime, action, timeOffset, params, nArgs, kwargs, row)
    def data(self, data):
        self._data.append(data)
        stuff = self._extractAll(data)
        if stuff==None:
            return
        (dataCount, peer, theTime, action, timeOffset, params, nArgs, kwargs, row) = stuff
        self._writeDataToFile(dataCount, peer, theTime, action, timeOffset, params)
        self.theFilterer.data(peer, theTime, action, nArgs, kwargs, timeOffset)
        nsId_ = params["nsId"]
        block_ = params["block"]
        timeout_ = params["timeout"]
        result_ = params["result"]
        response_ = params["response"]
        data_ = params["data"]
        uu_ = params["uu"]
        for col, what in enumerate([
                                    str(peer),
                                    str(theTime),
                                    str(action),
                                    str(nsId_),
                                    str(block_),
                                    str(timeout_),
                                    str(result_),
                                    str(response_),
                                    str(uu_),
                                    str(timeOffset),
                                    ]):
            item = QtGui.QTableWidgetItem(what)
            theData = ""
            if data_!=None:
                theData = "%(D)s"%{"D":data_}
            ttip = "%(A)s(%(D)s)"%{"A":action, "D":theData}
            item.setToolTip(ttip)
            self.rawQueueData.tableWidget.setItem(row, col, item)
            self.rawQueueData.tableWidget.resizeColumnsToContents()
        if action=="close_end":
            self.theQueues._onQuery()
    def _writeDataToFile(self, dataCount, peer, theTime, action, timeOffset, params):
        args = {"DC":dataCount, "PE":peer, "TT":theTime, "AC":action, "TO":timeOffset}
        args.update(params)
        lines = []
        lines.append("[%(DC)s] Peer: %(PE)s\n"%args)
        lines.append("[%(DC)s] Time: %(TT)s\n"%args)
        lines.append("[%(DC)s] TimeOffset: %(TO)s\n"%args)
        lines.append("[%(DC)s] Action: %(AC)s\n"%args)
        lines.append("[%(DC)s] Block: %(block)s\n"%args)
        lines.append("[%(DC)s] Timeout: %(timeout)s\n"%args)
        lines.append("[%(DC)s] Namespace: %(namespace)s\n"%args)
        lines.append("[%(DC)s] Data: %(data)s\n"%args)
        lines.append("[%(DC)s] Response: %(response)s\n"%args)
        lines.append("[%(DC)s] Result: %(result)s\n"%args)
        lines.append("[%(DC)s] UU: %(uu)s\n"%args)
        lines.append("[%(DC)s] Query: %(query)s\n"%args)
        lines.append("\n")
        self.fp.writelines(lines)
        self.fp.flush()
    def _addNewQ(self, ns):
        nsId = RRQTab.uId.next()
        self.theQueues.addNewQueue(ns, nsId)
        return nsId
    def _extractDecode(self, action, args, kwargs, decoderParams=None):
        params = ActionDecoder.decode(action, args, kwargs, params=decoderParams)
        ns = params["namespace"]
        nsId = ""
        if ns and len(ns)>0:
            if ns not in self.qIds:
                nsId = self._addNewQ(ns)
                self.qIds[ns] = nsId
                l = len(self.qIds.keys())
                self.theQueues.setNumQueues(l)
                self._updateNumObservedQueues()
            else:
                nsId = self.qIds[ns]
        params["nsId"] = nsId
        return params
    def show(self):
        super(RRQTab, self).show()
        self.connect(self, Qt.SIGNAL('customContextMenuRequested(QPoint)'), self._onPopupMain, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL('connectionState(int, PyQt_PyObject, PyQt_PyObject)'), self._onConnectionStateChange, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL('connectionState(int)'), self._onConnectionState, QtCore.Qt.QueuedConnection)

        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.theQueues = QueuesModel(self)
        path = os.path.join(self.debugger.resourcesPath, QueuesModel.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=self.theQueues)
        self.theFilterer = FiltererModel(self)
        path = os.path.join(self.debugger.resourcesPath, FiltererModel.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=self.theFilterer)
        self.rawQueueData = RawQueueData(self)
        path = os.path.join(self.debugger.resourcesPath, RawQueueData.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=self.rawQueueData)

        self.splitter1.addWidget(self.theQueues)
        self.splitter1.addWidget(self.theFilterer)
        self.splitter1.setOpaqueResize(False)
        self.splitter2 = QtGui.QSplitter()
        self.splitter2.setOrientation(QtCore.Qt.Vertical)
        self.splitter2.addWidget(self.rawQueueData)
        self.splitter2.addWidget(self.splitter1)
        self.splitter2.show()
        self.splitter2.setOpaqueResize(False)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.splitter2)

        for what in [self.theQueues, self.theFilterer, self.rawQueueData]:
            what.show(False)

        self.loadUi(self.debugger.settings, str(self.details))
        self.rawQueueData.pushButton_Connect.emit(Qt.SIGNAL("pressed()"))

        #    Tell theQueues to query!
#        self.theQueues.emit(Qt.SIGNAL("queryRequested()"))
    def _onConnectionState(self, state):
        pass
    def _onConnectionStateChange(self, *args, **kwargs):
        self._connectPending = False
        (state, iface, startTime) = args
        self.iface = iface
        self.startTime = startTime
        try:    self._updateButtons()
        except: pass
        self.emit(Qt.SIGNAL("connectionState(int)"), state)
    def _onPopupMain(self, pos):
        print "Main context menu !!!"
        screenPos = self.mapToGlobal(pos)
        self._actionMainPopup(screenPos)
    def _actionMainPopup(self, pos):
        menu = QtGui.QMenu(self.debugger)
        createAction = menu.addAction("Create q")
        closeAction = menu.addAction("Close q...")
        menu.addSeparator()
        getAction = menu.addAction("Get q...")
        putAction = menu.addAction("Put q...")
        qsizeAction = menu.addAction("QSize q...")
        maxqsizeAction = menu.addAction("MaxQSize q...")
        action = menu.exec_(pos)
        #    Show the non-modal QueueActionDialog:
        actionMap = {
                     createAction:Enablers.CREATE_START,
                     closeAction:Enablers.CLOSE_START,
                     putAction:Enablers.PUT_START,
                     getAction:Enablers.GET_START,
                     qsizeAction:Enablers.QSIZE_START,
                     maxqsizeAction:Enablers.MAXQSIZE_START,
                     }
        if action in actionMap.keys():
            self._showActionDialog(actionMap[action])
    def _showActionDialog(self, action):
        resourcesPath = self.debugger.resourcesPath
        if self._actionDialog==None:
            mb = QueueActionDialog(resourcesPath, self, action)
            path = os.path.join(resourcesPath, QueueActionDialog.RESOURCE_NAME)
            uic.loadUi(path, baseinstance=mb)
            mb.setModal(False)
            mb.show()
            self._actionDialog = mb
        else:
            self._actionDialog.emit(QtCore.SIGNAL("changeTab(PyQt_PyObject)"), action)
    def _updateButtons(self):
        self._updateNumObservedQueues()
        self._updateNumAllQueues()
    def _updateNumObservedQueues(self):
        self.theQueues.updateNumObservedQueues()
    def _updateNumAllQueues(self):
        self.theQueues.updateNumAllQueues()
    def getDetails(self):
        return self.details
    def getQueueServerDetails(self):
        return self.qs.details()
    def _handleQuery(self, namespaces, staleNamespaces):
        self.allQueues["active"] = namespaces
        self.allQueues["defunct"] = staleNamespaces
        self._updateNumObservedQueues()
        self._updateNumAllQueues()
        self._populateAllNamespaces()
    def _populateAllNamespaces(self):
        self.theQueues.populateAllNamespaces()
    def saveUi(self, settings=None):
        if settings==None:
            settings = self.debugger.settings
        where = str(self.details)
        settings.beginGroup(where)
        try:
            #    Save the value of the splitters
            settings.setValue("splitter1/position", self.splitter1.saveState())
            settings.setValue("splitter2/position", self.splitter2.saveState())
            #    Save the sub-models:
            self.theQueues.saveUi(settings)
            self.theFilterer.saveUi(settings)
            self.rawQueueData.saveUi(settings)
        finally:
            settings.endGroup()
    def loadUi(self, settings, where):
        settings.beginGroup("ui")
        try:
            settings.beginGroup("tabs")
            try:
                settings.beginGroup(where)
                try:
                    #    Load the value of the splitters
                    value = settings.value("splitter1/position")
                    if value.isValid():
                        self.splitter1.restoreState(value.toByteArray())
                    value = settings.value("splitter2/position")
                    if value.isValid():
                        self.splitter2.restoreState(value.toByteArray())
                    #    Load the sub-models:
                    self.theQueues.loadUi(settings)
                    self.theFilterer.loadUi(settings)
                    self.rawQueueData.loadUi(settings)
                finally:
                    settings.endGroup()
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()




