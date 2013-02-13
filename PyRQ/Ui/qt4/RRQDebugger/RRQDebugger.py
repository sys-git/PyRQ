'''
Created on 2 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, QtCore, uic, Qt
from PyRQ.Core.QueueServer.QueueServerDetails import QueueServerDetails
from PyRQ.Ui.qt4.RRQDebugger.AboutDialog import AboutDialog
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
from PyRQ.Ui.qt4.RRQDebugger.GlobalActionsModel import GlobalActionsModel
from PyRQ.Ui.qt4.RRQDebugger.InternalState import InternalState
from PyRQ.Ui.qt4.RRQDebugger.PyRQSelectorDialog import PyRQSelectorDialog
from PyRQ.Ui.qt4.RRQDebugger.RRQTab import RRQTab
from PyRQ.Ui.qt4.RRQDebugger.Scripter import Scripter
from PyRQ.Ui.qt4.RRQDebugger.SetHostDialog import SetHostDialog
from Queue import Empty
from multiprocessing.synchronize import Semaphore, RLock
import logging
import os
import pickle
import shutil
import threading
import time
import traceback

class RRQDebugger(QtGui.QMainWindow):
    RESOURCE_NAME = "MainWindow.ui"
    DEFAULT_SIZE_WIDTH = 1268
    DEFAULT_SIZE_HEIGHT = 648
    r"""
    Setup and configure a remote PyRQ debugging.
    """
    def __init__(self, resourcesPath, details=[], quiet=True, host="127.0.0.1"):
        super(RRQDebugger, self).__init__()
        self.resourcesPath = resourcesPath
        self.settings = QtCore.QSettings()
        self.settings.setPath(Qt.QSettings.IniFormat, Qt.QSettings.UserScope, "RRQDebugger")
        self.state = InternalState(self.settings)
        self.loggingLevel = logging.DEBUG
        self.logger = self._getLogger("Debugger", self.loggingLevel)
        self.tabs = []
        self._backupDetails = QueueServerDetails(host, 11223)
        self.author = "root"
        self.lock = RLock()
        self.qReader = None    #    threading.Thread: Multiplex over the queues and emit their results into the qt4-evt-loop.
        self.terminateQReader = False
        self.details = details
        self.quiet = quiet
        self.host = host
        self.globalActions = None
        self._createDir()
    def _createDir(self):
        self.path = os.path.realpath(".RRQDebugger")
        try:    shutil.rmtree(self.path)
        except: pass
        os.mkdir(self.path)
    def show(self):
        super(RRQDebugger, self).show()
        self.connect(self, QtCore.SIGNAL('Initialized()'), self._onMainWindowReady, QtCore.Qt.QueuedConnection)
        self.connect(self, QtCore.SIGNAL('data(PyQt_PyObject)'), self._onData, QtCore.Qt.QueuedConnection)
        #    Connect Menu items:
        self.connect(self.actionSet_Host, QtCore.SIGNAL('triggered()'), self._onSetHost, QtCore.Qt.QueuedConnection)
        self.connect(self.actionE_Xit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'), QtCore.Qt.QueuedConnection)
        self.connect(self.action_Save, QtCore.SIGNAL('triggered()'), self._onSave, QtCore.Qt.QueuedConnection)
        self.connect(self.action_Load, QtCore.SIGNAL('triggered()'), self._onLoad, QtCore.Qt.QueuedConnection)
        self.connect(self.action_Clear, QtCore.SIGNAL('triggered()'), self._onClearSettings, QtCore.Qt.QueuedConnection)
        self.connect(self.action_add, QtCore.SIGNAL('triggered()'), self._onAdd, QtCore.Qt.QueuedConnection)
        self.connect(self.action_remove, QtCore.SIGNAL('triggered()'), self._onRemove, QtCore.Qt.QueuedConnection)
        self.connect(self.action_About, QtCore.SIGNAL('triggered()'), self._onAbout, QtCore.Qt.QueuedConnection)
        self.connect(self.action_Create, QtCore.SIGNAL('triggered()'), self._onActionCreate, QtCore.Qt.QueuedConnection)
        self.connect(self.action_Close, QtCore.SIGNAL('triggered()'), self._onActionClose, QtCore.Qt.QueuedConnection)
        self.connect(self.action_Put, QtCore.SIGNAL('triggered()'), self._onActionPut, QtCore.Qt.QueuedConnection)
        self.connect(self.action_Get, QtCore.SIGNAL('triggered()'), self._onActionGet, QtCore.Qt.QueuedConnection)
        self.connect(self.action_QSize, QtCore.SIGNAL('triggered()'), self._onActionQSize, QtCore.Qt.QueuedConnection)
        self.connect(self.action_MaxQSize, QtCore.SIGNAL('triggered()'), self._onActionMaxQSize, QtCore.Qt.QueuedConnection)
        #    DBus:
        iconPath = os.path.join(self.resourcesPath, "icons", "app.png")
        self.setWindowIcon(QtGui.QIcon(iconPath))
        self.showHostAddress()
        self._createGlobalActions()
        self._createScripter()
        self.tabWidget = QtGui.QTabWidget(self)
        self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter2.addWidget(self.globalActions)
        self.splitter2.addWidget(self.scripter)
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitter1.addWidget(self.splitter2)
        self.splitter1.addWidget(self.tabWidget)
        self.splitter1.setOpaqueResize(False)
        self.splitter1.show()
        self.setCentralWidget(self.splitter1)
        self._loadUi()
        self._checkMenu()
        #    Asynchronously start the app - allows welcome screen to be shown etc.
        self.emit(QtCore.SIGNAL('Initialized()'))
    def _createScripter(self):
        self.scripter = Scripter(self)
        path = os.path.join(self.resourcesPath, Scripter.RESOURCE_NAME)
        uic.loadUi(path, self.scripter)
        self.scripter.show()
    def _createGlobalActions(self):
        self.globalActions = GlobalActionsModel(self)
        path = os.path.join(self.resourcesPath, GlobalActionsModel.RESOURCE_NAME)
        uic.loadUi(path, self.globalActions)
        self.globalActions.show()
    def _onActionCreate(self):
        tab = self.tabWidget.currentWidget()
        if tab!=None:
            tab._showActionDialog(Enablers.CREATE_START)
    def _onActionClose(self):
        tab = self.tabWidget.currentWidget()
        if tab!=None:
            tab._showActionDialog(Enablers.CLOSE_START)
    def _onActionPut(self):
        tab = self.tabWidget.currentWidget()
        if tab!=None:
            tab._showActionDialog(Enablers.PUT_START)
    def _onActionGet(self):
        tab = self.tabWidget.currentWidget()
        if tab!=None:
            tab._showActionDialog(Enablers.GET_START)
    def _onActionQSize(self):
        tab = self.tabWidget.currentWidget()
        if tab!=None:
            tab._showActionDialog(Enablers.QSIZE_START)
    def _onActionMaxQSize(self):
        tab = self.tabWidget.currentWidget()
        if tab!=None:
            tab._showActionDialog(Enablers.MAXQSIZE_START)
    def showHostAddress(self):
        self.statusbar.showMessage("host: %(H)s"%{"H":self.host})
    def closeEvent(self, event):
        if self.state.isDirty():
            #   Ask to save the details.
            mb = QtGui.QMessageBox()
            mb.setText("PyRQ config has changed.")
            mb.setInformativeText("Do you want to save the changes?")
            mb.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            mb.setDefaultButton(QtGui.QMessageBox.Save)
            result = mb.exec_()
            if result==QtGui.QMessageBox.Save:
                self._save()
                self.state.notDirty()
            elif result==QtGui.QMessageBox.Discard:
                pass
            elif result==QtGui.QMessageBox.Cancel:
                return
        self._teardown()
        event.accept()
    def _onMainWindowReady(self):
        self._onLoad()
#        import pydevd
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        if len(self.details)>0:
            for details in self.details:
                self._doAdd(details)
    def _onSetHost(self):
        mb = SetHostDialog(self.host, parent=self)
        path = os.path.join(self.resourcesPath, SetHostDialog.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=mb)
        mb.setupUi()
        result = mb.exec_()
        if result==QtGui.QDialog.Rejected:
            return
        host = mb.host()
        if host and len(host)>0:
            self.host = host
            self.showHostAddress()
    def _onAbout(self):
        details = []
        with self.lock:
            for tab in self.tabs:
                details.append((tab.getQueueServerDetails(), tab.getName(), (tab.iface!=None)))
        mb = AboutDialog(self.resourcesPath, self.host, details, parent=self)
        path = os.path.join(self.resourcesPath, AboutDialog.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=mb)
        mb.setupUi()
        mb.exec_()
    def _onAdd(self):
        try:
            details = self.tabWidget.currentWidget().getDetails()
        except:
            details = self._backupDetails
        mb = PyRQSelectorDialog(self, self.quiet, parent=self)
        path = os.path.join(self.resourcesPath, PyRQSelectorDialog.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=mb)
        mb.setupUi(port=int(details.port())+1, host=details.host())
        result = mb.exec_()
        if result==QtGui.QDialog.Rejected:
            return
        details = mb.details()
        if self._backupDetails==None:
            self.details = details
        self._doAdd(details)
    def _onRemove(self):
        #    Remove the currently selected tab.
        index = self.tabWidget.currentIndex()
        tab = self.tabWidget.currentWidget()
        self.tabs.remove(tab)
        self.tabWidget.removeTab(index)
        self.state.remove(tab.getDetails())
        if len(self.tabs)==0:
            self.globalActions.pushButton_Execute.setEnabled(False)
        tab.close()
        self._checkMenu()
    def _doAdd(self, details):
#        import pydevd
#        pydevd.settrace(stdoutToServer = True, stderrToServer = True)
        try:
            self.state.add(details)
        except PyRQSelectorDialog.Failed:
            return False
        else:
            self._createTab(details)
            self.globalActions.pushButton_Execute.setEnabled(True)
            return True
    def _onLoad(self):
        #    Teardown everything and rebuild.
        self._teardown()
        self._doLoad()
    def _onClearSettings(self):
        self.settings.clear()
    def _doLoad(self):
        self._load()
        self._build()
    def _onSave(self):
        self._save()
    def _save(self):
        self.state.store()
    def _load(self):
        self.state.retrieve()
    def _saveUi(self, settings=None):
        if settings==None:
            settings = self.settings
        settings.beginGroup("ui")
        try:
            settings.setValue("backupDetails", bytearray(pickle.dumps(self._backupDetails)))
            settings.setValue("size", self.size())
            settings.setValue("pos", self.pos())
            settings.setValue("state", self.saveState())
            settings.setValue("tabIndex", self.tabWidget.currentIndex())
            settings.setValue("splitter1", self.splitter1.saveState())
            settings.setValue("splitter2", self.splitter2.saveState())
            settings.beginGroup("tabs")
            try:
                for tab in self.tabs:
                    tab.saveUi(settings)
            finally:
                self.settings.endGroup()
            settings.beginGroup("actions")
            try:
                self.globalActions.saveUi(settings)
            finally:
                settings.endGroup()
            settings.beginGroup("scripter")
            try:
                self.scripter.saveUi(settings)
            finally:
                settings.endGroup()
            settings.setValue("author", self.author)
        finally:
            settings.endGroup()
    def _loadUi(self, settings=None):
        if settings==None:
            settings = self.settings
        settings.beginGroup("ui")
        try:
            try:
                value = settings.value("backupDetails", type=bytearray)
                value = str(value)
                details = pickle.loads(value)
            except Exception, _e:
                details = self._backupDetails
            self._backupDetails = details
            self.restoreState(self.settings.value("state").toByteArray())
            self.resize(settings.value("size", defaultValue=QtCore.QSize(RRQDebugger.DEFAULT_SIZE_WIDTH, RRQDebugger.DEFAULT_SIZE_HEIGHT)).toSize())
            self.move(settings.value("pos", QtCore.QPoint(0, 0)).toPoint())
            (index, isValid) = settings.value("tab1Index", 0).toInt()
            if isValid:
                self.tabWidget.setCurrentIndex(index)
            self._restoreSplitter("splitter1")
            self._restoreSplitter("splitter2")
            settings.beginGroup("actions")
            try:
                self.globalActions.loadUi(settings)
            finally:
                settings.endGroup()
            settings.beginGroup("scripter")
            try:
                self.scripter.loadUi(settings)
            finally:
                settings.endGroup()
            self.author = settings.value("author", self.author).toString()
        finally:
            settings.endGroup()
    def _restoreSplitter(self, name):
        value = self.settings.value(name)
        if value.isValid():
            getattr(self, name).restoreState(value.toByteArray())
    def _teardown(self):
        #    Save the window dims, etc:
        self._saveUi()
        #    remove all tabs, tearing down their QueueServer.
        for tab in self.tabs:
            tab.close()
        self.tabs = []
        #    Close our QueueServer receptor multiplexer:
        try:
            self.terminateQReader = True
            self.qReader.join()
        except Exception, _e:
            pass
        self.qReader = None
        self.tabWidget.clear()
    def _build(self):
        #    based on the self.state, rebuild the UI.
        for details in self.state.getIterator():
            self._createTab(details)
    def _createTab(self, details):
        #    Create a new RRQTab
        tab = RRQTab(self, details)
        path = os.path.join(self.resourcesPath, RRQTab.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=tab)
        tab.show()
        self.tabs.append(tab)
        self.tabWidget.insertTab(0, tab, tab.getName())
        self.tabWidget.setCurrentIndex(0)
        self._startQReader()
        self._checkMenu()
    def _startQReader(self):
        if self.qReader==None:
            self.terminateQReader = False
            startMutex = Semaphore(0)
            self.qReader = threading.Thread(target=self.run, args=[startMutex, self._getLogger("QReader.thread", self.loggingLevel)])
            self.qReader.setName("qReader")
            self.qReader.setDaemon(True)
            self.qReader.start()
            startMutex.acquire()
    def _getLogger(self, name, loggingLevel):
        logger = logging.getLogger("%(R)s"%{"R":name})
        try:
            if len(logger.handlers)==0:
                loggerHandler = logging.StreamHandler()
                loggerHandler.setLevel(loggingLevel)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                loggerHandler.setFormatter(formatter)
                logger.addHandler(loggerHandler)
            logger.setLevel(loggingLevel)
        except Exception, _e:
            pass
        return logger
    def run(self, startMutex, logger):
        logger.warn("Starting")
        startMutex.release()
        def process(name, data):
            #logger.info("Got debugging data: %(D)s"%{"D":data})
            return (name, data)
        try:
            while self.terminateQReader==False:
                events = []
                with self.lock:
                    for tab in self.tabs:
                        q = tab.getQ()
                        name = tab.getName()
                        try:
                            data =  q.get(block=False)
                        except Empty:
                            pass
                        except Exception, _e:
                            pass
                        else:
                            events.append(process(name, data))
                if len(events)>0:
                    self.emit(QtCore.SIGNAL("data(PyQt_PyObject)"), events)
                else:
                    time.sleep(0.1)
        except Exception, _e:
            logger.exception("d'oh:\r\n%(T)s"%{"T":traceback.format_exc()})
        finally:
            logger.warn("Terminating")
    def _onData(self, events):
        #self.logger.info("Got debugging data for %(N)s events..."%{"N":len(events)})
        for (clientName, data) in events:
            self.__onData(clientName, data)
    def __onData(self, clientName, data):
        with self.lock:
            for tab in self.tabs:
                if tab.getName()==clientName:
                    tab.data(data)
                    return
        self.logger.warn("Received data for a stale PyRQ: %(N)s"%{"N":clientName})
    def _checkMenu(self):
        #    FIXME: This doesn't work!!!
        if len(self.tabs)>0:
            self.menu_Queue.setEnabled(True)
        else:
            self.menu_Queue.setEnabled(False)
