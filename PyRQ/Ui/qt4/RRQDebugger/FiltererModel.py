'''
Created on 17 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore, uic
from PyRQ.Ui.qt4.RRQDebugger.ActionDecoder import ActionDecoder
from PyRQ.Ui.qt4.RRQDebugger.ConfigureFiltersDialog import \
    ConfigureFiltersDialog
from PyRQ.Ui.qt4.RRQDebugger.Filterer import Filterer
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
import copy
import os

class FiltererModel(QtGui.QFrame):
    RESOURCE_NAME = "Filterer.ui"
    def __init__(self, parent, *args, **kwargs):
        super(FiltererModel, self).__init__(parent)
        self._parent = parent
        self._paused = False
        self.filterer = None
    def show(self, isConnected):
        self.filterer = Filterer(self._parent, str(self._parent.details), font=None)
        self.connect(self.listView_FilteredItems, Qt.SIGNAL('customContextMenuRequested(QPoint)'), self._onPopup_FilteredItems, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Start, Qt.SIGNAL('pressed()'), self._onStart, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_End, Qt.SIGNAL('pressed()'), self._onEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Follow, Qt.SIGNAL('toggled(bool)'), self._onFollow, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Configure, Qt.SIGNAL('pressed()'), self._onConfigure, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_ClearFiltered, Qt.SIGNAL('pressed()'), self._onClearFiltered, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_PauseFiltered, Qt.SIGNAL('pressed()'), self._onPauseFiltered, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Put_Start, Qt.SIGNAL('toggled(bool)'), self._onToggled_PutStart, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Put_End, Qt.SIGNAL('toggled(bool)'), self._onToggled_PutEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Get_Start, Qt.SIGNAL('toggled(bool)'), self._onToggled_GetStart, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Get_End, Qt.SIGNAL('toggled(bool)'), self._onToggled_GetEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Create_Start, Qt.SIGNAL('toggled(bool)'), self._onToggled_CreateStart, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Create_End, Qt.SIGNAL('toggled(bool)'), self._onToggled_CreateEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Close_Start, Qt.SIGNAL('toggled(bool)'), self._onToggled_CloseStart, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Close_End, Qt.SIGNAL('toggled(bool)'), self._onToggled_CloseEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_QSize_Start, Qt.SIGNAL('toggled(bool)'), self._onToggled_QSizeStart, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_QSize_End, Qt.SIGNAL('toggled(bool)'), self._onToggled_QSizeEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_MaxQSize_Start, Qt.SIGNAL('toggled(bool)'), self._onToggled_MaxQSizeStart, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_MaxQSize_End, Qt.SIGNAL('toggled(bool)'), self._onToggled_MaxQSizeEnd, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_All, Qt.SIGNAL('toggled(bool)'), self._onToggled_All, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_Filter_Get_End, Qt.SIGNAL('customContextMenuRequested(QPoint)'), self._onPopup_GetEnd, QtCore.Qt.QueuedConnection)
        self.updatePauseResumeButton()
        self.pushButton_ClearFiltered.setText("")
        self.pushButton_ClearFiltered.setIcon(QtGui.QIcon(os.path.join(self._parent.debugger.resourcesPath, "icons", "icon_clear.png")))
        self.pushButton_Start.setText("")
        self.pushButton_End.setText("")
        self.checkBox_Follow.setText("")
        self.pushButton_Start.setIcon(QtGui.QIcon(os.path.join(self._parent.debugger.resourcesPath, "icons", "icon_start.png")))
        self.pushButton_End.setIcon(QtGui.QIcon(os.path.join(self._parent.debugger.resourcesPath, "icons", "icon_end.png")))
        self.checkBox_Follow.setIcon(QtGui.QIcon(os.path.join(self._parent.debugger.resourcesPath, "icons", "icon_follow.png")))
        self.pushButton_Configure.setText("")
        self.pushButton_Configure.setIcon(QtGui.QIcon(os.path.join(self._parent.debugger.resourcesPath, "icons", "icon_configure.png")))
        self.followCheckboxDetails = ("checkBox_Follow", "follow")
        self.enablerCheckboxes = [
                                  ("checkBox_Filter_All", "all"),        #    Must be first!
                                  ("checkBox_Filter_Put_Start", "Put_Start"),
                                  ("checkBox_Filter_Put_End", "Put_End"),
                                  ("checkBox_Filter_Get_Start", "Get_Start"),
                                  ("checkBox_Filter_Get_End", "Get_End"),
                                  ("checkBox_Filter_Create_Start", "Create_Start"),
                                  ("checkBox_Filter_Create_End", "Create_End"),
                                  ("checkBox_Filter_Close_Start", "Close_Start"),
                                  ("checkBox_Filter_Close_End", "Close_End"),
                                  ("checkBox_Filter_QSize_Start", "QSize_Start"),
                                  ("checkBox_Filter_QSize_End", "QSize_End"),
                                  ("checkBox_Filter_MaxQSize_Start", "MaxQSize_Start"),
                                  ("checkBox_Filter_MaxQSize_End", "MaxQSize_End"),
                                  ]
    def close(self):
        try:    self.filterer.dump()
        except: pass
    def _getFileSaveLocation(self, caption="Select a file to store the items in"):
        filename = QtGui.QFileDialog.getSaveFileName(parent=self, caption=caption)
        return filename
    def _onPopup_GetEnd(self, pos):
        screenPos = self.checkBox_Filter_Get_End.mapToGlobal(pos)
        menu = QtGui.QMenu(self)
        eState = self.filterer.isSuccessfullGetOnly()
        allowAction = None
        disallowAction = None
        if eState==True:
            allowAction = menu.addAction("Allow all Exceptions raised by GET.")
        else:
            disallowAction = menu.addAction("Disallow all Exceptions raised by GET.")
        action = menu.exec_(screenPos)
        if action!=None:
            if action==allowAction:
                self.filterer.successfullGetOnly(False)
            elif action==disallowAction:
                self.filterer.successfullGetOnly(True)
    def _onPopup_FilteredItems(self, pos):
        menu = QtGui.QMenu(self)
        saveAllAsTextAction = menu.addAction("Save all as text")
        saveFilteredAsTextAction = menu.addAction("Save filtered-only as text")
        screenPos = self.listView_FilteredItems.mapToGlobal(pos)
        action = menu.exec_(screenPos)
        if action==saveAllAsTextAction:
            filename = self._getFileSaveLocation()
            if filename!=None:
                fp = open(filename, "w")
                dd = self._parent._data
                fp.write("this many items: %(I)s\n"%{"I":len(dd)})
                for data in dd:
                    (_dataCount, peer, theTime, action, timeOffset, params, _nArgs, _kwargs, _row) = self._extractAll(data)
                    desc = Filterer.getDesc(peer, theTime, action, timeOffset, params)
                    fp.write(desc+"\n")
                    fp.flush()
                fp.close()
        elif action==saveFilteredAsTextAction:
            #    Get all from the widget:
            filename = self._getFileSaveLocation()
            if filename!=None:
                filename = str(filename)
                fp = open(filename, "w")
                for row in xrange(0, self.listView_FilteredItems.count()):
                    item = self.listView_FilteredItems.item(row)
                    fp.write(str(item.text())+"\n")
                    fp.flush()
                fp.close()
    def _onStart(self):
        self.listView_FilteredItems.scrollToTop()
    def _onEnd(self):
        self.listView_FilteredItems.scrollToBottom()
    def _onClearFiltered(self):
        self.listView_FilteredItems.clear()
    def _onFollow(self, state):
        self.filterer.follow(state)
    def _onPauseFiltered(self):
        self._paused = not self._paused
        self.updatePauseResumeButton()
    def _onConfigure(self):
        resourcesPath = self._parent.debugger.resourcesPath
        config = self.filterer.cloneConfig()
        mb = ConfigureFiltersDialog(self, config)
        path = os.path.join(resourcesPath, ConfigureFiltersDialog.RESOURCE_NAME)
        uic.loadUi(path, baseinstance=mb)
        mb.setupUi()
        result = mb.exec_()
        if result==QtGui.QDialog.Rejected:
            return
        elif result==QtGui.QDialog.Accepted:
            self.filterer.setConfig(mb.getConfig())
    def updatePauseResumeButton(self):
        resourcesPath = self._parent.debugger.resourcesPath
        if self._paused==True:
            self.pushButton_PauseFiltered.setText("")
            self.pushButton_PauseFiltered.setIcon(QtGui.QIcon(os.path.join(resourcesPath, "icons", "icon_resume.png")))
        else:
            self.pushButton_PauseFiltered.setText("")
            self.pushButton_PauseFiltered.setIcon(QtGui.QIcon(os.path.join(resourcesPath, "icons", "icon_pause.png")))
    def _onToggled_PutStart(self, state):
        self.filterer.enable(Enablers.PUT_START, state)
        self._checkAllCheckbox()
    def _onToggled_PutEnd(self, state):
        self.filterer.enable(Enablers.PUT_END, state)
        self._checkAllCheckbox()
    def _onToggled_GetStart(self, state):
        self.filterer.enable(Enablers.GET_START, state)
        self._checkAllCheckbox()
    def _onToggled_GetEnd(self, state):
        self.filterer.enable(Enablers.GET_END, state)
        self._checkAllCheckbox()
    def _onToggled_CreateStart(self, state):
        self.filterer.enable(Enablers.CREATE_START, state)
        self._checkAllCheckbox()
    def _onToggled_CreateEnd(self, state):
        self.filterer.enable(Enablers.CREATE_END, state)
        self._checkAllCheckbox()
    def _onToggled_CloseStart(self, state):
        self.filterer.enable(Enablers.CLOSE_START, state)
        self._checkAllCheckbox()
    def _onToggled_CloseEnd(self, state):
        self.filterer.enable(Enablers.CLOSE_END, state)
        self._checkAllCheckbox()
    def _onToggled_QSizeStart(self, state):
        self.filterer.enable(Enablers.QSIZE_START, state)
        self._checkAllCheckbox()
    def _onToggled_QSizeEnd(self, state):
        self.filterer.enable(Enablers.QSIZE_END, state)
        self._checkAllCheckbox()
    def _onToggled_MaxQSizeStart(self, state):
        self.filterer.enable(Enablers.MAXQSIZE_START, state)
        self._checkAllCheckbox()
    def _onToggled_MaxQSizeEnd(self, state):
        self.filterer.enable(Enablers.MAXQSIZE_END, state)
        self._checkAllCheckbox()
    def _onToggled_All(self, state):
        self.filterer.enableAll(state)
        for cb in self.enablerCheckboxes:
            (widgetName, _storeAsName) = cb
            widget = getattr(self, widgetName)
            if state==True:
                widget.setCheckState(QtCore.Qt.Checked)
            else:
                widget.setCheckState(QtCore.Qt.Unchecked)
    def data(self, peer, theTime, action, nArgs, kwargs, timeOffset):
        if self._paused==False:
            params = self._parent._extractDecode(action, nArgs, kwargs, decoderParams=copy.deepcopy(ActionDecoder.DEFFAULT_PARAMS__NONE))
            self.filterer.data(peer, theTime, action, timeOffset, params)
    def saveUi(self, settings):
        settings.beginGroup("filterer")
        try:
            settings.beginGroup("checkBoxes")
            try:
                #    Filter enablers:
                for cb in self.enablerCheckboxes[1:]:
                    self._saveCheckValue(settings, cb)
                #    Follow:
                self._saveCheckValue(settings, self.followCheckboxDetails)
            finally:
                settings.endGroup()
            settings.setValue("successfullGetOnly", self.filterer.isSuccessfullGetOnly())
            #    Paused:
            settings.setValue("paused", self._paused)
        finally:
            settings.endGroup()
    def _saveCheckValue(self, settings, cb):
        (widgetName, storeAsName) = cb
        settings.setValue(storeAsName, getattr(self, widgetName).checkState())
    def _loadCheckValue(self, settings, cb):
        (widgetName, storeAsName) = cb
        value = settings.value(storeAsName, QtCore.Qt.Unchecked)
        if value.isValid():
            (value, isValid) = value.toInt()
            if isValid:
                widget = getattr(self, widgetName)
                widget.setCheckState(value)
    def loadUi(self, settings):
        settings.beginGroup("filterer")
        try:
            settings.beginGroup("checkBoxes")
            try:
                #    Filter enablers:
                for cb in self.enablerCheckboxes[1:]:
                    self._loadCheckValue(settings, cb)
                #    Follow:
                self._loadCheckValue(settings, self.followCheckboxDetails)
            finally:
                settings.endGroup()
            self.filterer.successfullGetOnly(settings.value("successfullGetOnly", True).toBool())
            #    Paused:
            self._paused = settings.value("paused", False).toBool()
        finally:
            settings.endGroup()
        self._checkAllCheckbox()
        self.updatePauseResumeButton()
    def _checkAllCheckbox(self):
        checkState = None
        result = True
        for cb in self.enablerCheckboxes[1:]:
            (widgetName, _storeAsName) = cb
            widget = getattr(self, widgetName)
            currentCheckState = widget.checkState()
            if checkState==None:
                checkState = currentCheckState
            else:
                if currentCheckState!=checkState:
                    result = False
                    break
        if result:
            #    All check-boxes identical!
            (widgetName, _storeAsName) = self.enablerCheckboxes[0]
            widget = getattr(self, widgetName)
            widget.setCheckState(currentCheckState)



