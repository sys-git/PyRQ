'''
Created on 11 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore, uic
from PyRQ.Ui.qt4.RRQDebugger.ConfigFiltersImportDialog import \
    ConfigFiltersImportDialog
from PyRQ.Ui.qt4.RRQDebugger.FilterConfig import FiltersConfig
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
import os
from PyRQ.Ui.qt4.RRQDebugger.SaveFilterActionAsDialog import SaveFilterActionAsDialog

class ConfigureFiltersDialog(QtGui.QDialog):
    RESOURCE_NAME = "ConfigureFiltersDialog.ui"
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
    def __init__(self, debugger, config, *args, **kwargs):
        super(ConfigureFiltersDialog, self).__init__(*args, **kwargs)
        self.debugger = debugger
        self.resourcesPath = self.debugger._parent.debugger.resourcesPath
        self.config = config
        self.currentIndex = 0
        self.originalConfig = None
    def setupUi(self):
        self.connect(self.pushButton_Accept, Qt.SIGNAL('pressed()'), self._onAccept, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Reject, Qt.SIGNAL('pressed()'), self._onReject, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Reset, Qt.SIGNAL('pressed()'), self._onReset, QtCore.Qt.QueuedConnection)
        self.connect(self.comboBox_Action, Qt.SIGNAL('currentIndexChanged(int)'), self._onAction, QtCore.Qt.QueuedConnection)
        self.connect(self.fontComboBox_Font, Qt.SIGNAL('currentIndexChanged(int)'), self._onFontChanged, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_TextColour, Qt.SIGNAL('pressed()'), self._onTextColourChanged, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_BackgroundColour, Qt.SIGNAL('pressed()'), self._onBackgroundColourChanged, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Export, Qt.SIGNAL('pressed()'), self._onExport, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Import, Qt.SIGNAL('pressed()'), self._onImport, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_LoadFrom, Qt.SIGNAL('pressed()'), self._onLoadFrom, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_SaveAs, Qt.SIGNAL('pressed()'), self._onSaveAs, QtCore.Qt.QueuedConnection)
        self.connect(self.listWidget_Items, Qt.SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self._onActionChanged, QtCore.Qt.QueuedConnection)
        self.originalConfig = self.config.create(self.fontComboBox_Font.currentFont(), self.listWidget_Example.palette())
        self.config.setFont(self.fontComboBox_Font.currentFont())
        self._render()
    def _onActionChanged(self, item):
        action = str(item.text().toAscii()).lower()
        index = ConfigureFiltersDialog.indicees.index(action)
        self.currentIndex = index
        self.comboBox_Action.setCurrentIndex(index)
        self.listWidget_Example.scrollToItem(self.listWidget_Example.item(index))
        self._setExampleLabelColours()
    def _onReset(self):
        self.config = self.originalConfig.clone()
        self._render()
    def _renderRow(self, index):
        action = ConfigureFiltersDialog.indicees[index]
        item = self.listWidget_Example.item(index)
        item.setBackgroundColor(self.config.backgroundColour(action))
        item.setFont(self.config.font(action))
        c = self.config.textColour(action)
        item.setTextColor(c)
    def _render(self):
        self._setExampleLabelColours()
        for row, action in enumerate(ConfigureFiltersDialog.indicees):
            item = self.listWidget_Example.item(row)
            backgroundColour = self.config.backgroundColour(action)
            if backgroundColour!=None:
                item.setBackgroundColor(backgroundColour)
            font = self.config.font(action)
            if font!=None:
                item.setFont(font)
            textColour = self.config.textColour(action)
            if textColour!=None:
                item.setTextColor(textColour)
    def _setExampleLabelColours(self):
        action = ConfigureFiltersDialog.indicees[self.currentIndex]
        self._setExampleLabelColourItem(self.label_TextColourForeground, self.config._configs[action].textColour())
        self._setExampleLabelColourItem(self.label_TextColourBackground, self.config._configs[action].backgroundColour())
    def _setExampleLabelColourItem(self, item, colour):
        item.setText("")
        args = {"R":colour.red(), "G":colour.green(), "B":colour.blue()}
        item.setStyleSheet("QLabel { background-color : rgb(%(R)s, %(G)s, %(B)s); color : rgb(%(R)s, %(G)s, %(B)s); }"%args)
    def _onTextColourChanged(self):
        action = ConfigureFiltersDialog.indicees[self.currentIndex]
        colour = QtGui.QColorDialog().getColor(initial=self.config.textColour(action))
        if colour.isValid()==True:
            self.config._configs[action].setTextColour(colour)
            self._renderRow(self.currentIndex)
            self._setExampleLabelColours()
    def _onBackgroundColourChanged(self):
        action = ConfigureFiltersDialog.indicees[self.currentIndex]
        colour = QtGui.QColorDialog().getColor(initial=self.config.backgroundColour(action))
        if colour.isValid()==True:
            self.config._configs[action].setBackgroundColour(colour)
            self._renderRow(self.currentIndex)
            self._setExampleLabelColours()
    def _onFontChanged(self, index):
        font = self.fontComboBox_Font.currentFont()
        action = ConfigureFiltersDialog.indicees[self.currentIndex]
        self.config._configs[action].setFont(font)
        self._renderRow(self.currentIndex)
    def _onAction(self, index):
        self.currentIndex = index
        action = ConfigureFiltersDialog.indicees[self.currentIndex]
        self.fontComboBox_Font.setCurrentFont(self.config.font(action))
        self.listWidget_Example.scrollToItem(self.listWidget_Example.item(index))
        self._setExampleLabelColours()
    def _onReject(self):
        self.reject()
    def _onAccept(self):
        self.accept()
    def getConfig(self):
        return self.config
    def _getFileSaveLocation(self, caption="Export current filter settings to...", filter="ini files (*.ini);;Text files (*.txt)"):
        filename = QtGui.QFileDialog.getSaveFileName(parent=self, caption=caption, filter=filter)
        return filename
    def _getFileLoadLocation(self, caption="Import filter settings from...", filter="ini files (*.ini);;Text files (*.txt)"):
        filename = QtGui.QFileDialog.getOpenFileName(parent=self, caption=caption, filter=filter)
        return filename
    def _onExport(self):
        #    Export current config via settings to an 'ini' file:
        filename = self._getFileSaveLocation()
        if filename!=None and filename!="":
            self.config.export_(filename)
    def _onImport(self):
        #    Import config previously pickled to a file with '_onExport'.
        #    Ask the user which actions to load config for - present dialog with coloured actions like this dialog.
        filename = self._getFileLoadLocation()
        if filename!=None and filename!="":
            newConfig = FiltersConfig(None, None).import_(filename)
            cfid = ConfigFiltersImportDialog(self, self.config.clone(), newConfig)
            path = os.path.join(self.resourcesPath, ConfigFiltersImportDialog.RESOURCE_NAME)
            uic.loadUi(path, cfid)
            cfid.setupUi()
            if cfid.exec_()==QtGui.QDialog.Rejected:
                return
            config = cfid.getConfig()
            if self.config!=config:
                self.config = config
                self._render()
    def _onSaveAs(self):
        action = ConfigureFiltersDialog.indicees[self.comboBox_Action.currentIndex()]
        existingNames = self.config.getExistingUserActionFilterNames(action)
        #    Ask for the name to save as, present the existing one, offer overwrite action.
        mb = SaveFilterActionAsDialog(self, action, existingNames)
        path = os.path.join(self.resourcesPath, SaveFilterActionAsDialog.RESOURCE_NAME)
        uic.loadUi(path, mb)
        mb.setupUi()
        if mb.exec_()==QtGui.QDialog.Rejected:
            return
        name = mb.getName()
        #    Save as a custom user setting for this action
        self.config.exportAs(action, name)
    def _onLoadFrom(self):
        action = ConfigureFiltersDialog.indicees[self.comboBox_Action.currentIndex()]
        existingNames = self.config.getExistingUserActionFilterNames(action)
        #    Ask for the name to save as, present the existing one, offer overwrite action.
        desc = "Load the filter properties for action: %(A)s"%{"A":action}
        mb = SaveFilterActionAsDialog(self, action, existingNames, desc=desc)
        path = os.path.join(self.resourcesPath, SaveFilterActionAsDialog.RESOURCE_NAME)
        uic.loadUi(path, mb)
        mb.setupUi()
        if mb.exec_()==QtGui.QDialog.Rejected:
            return
        name = mb.getName()
        #    Save as a custom user setting for this action
        self.config.importFrom(action, name)
        self._render()




