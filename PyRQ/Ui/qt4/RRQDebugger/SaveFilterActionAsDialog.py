'''
Created on 11 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore

class SaveFilterActionAsDialog(QtGui.QDialog):
    RESOURCE_NAME = "SaveFilterActionAsDialog.ui"
    def __init__(self, parent, action, existingNames, desc=None, *args, **kwargs):
        super(SaveFilterActionAsDialog, self).__init__(parent=parent)
        self._parent = parent
        self._action = action
        self._existingNames = existingNames
        self._name = None
        if desc==None:
            desc = "Save the filter properties for action: %(A)s"%{"A":action}
        self.desc = desc
    def setupUi(self, desc=None):
        if desc==None:
            desc = self.desc
        self.connect(self.lineEdit_Custom, Qt.SIGNAL('textChanged(QString)'), self._onTextChanged, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Existing, Qt.SIGNAL('pressed()'), Qt.SLOT("accept()"), QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Custom, Qt.SIGNAL('pressed()'), Qt.SLOT("accept()"), QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Reject, Qt.SIGNAL('pressed()'), self._onReject, QtCore.Qt.QueuedConnection)
        self.connect(self.listWidget_Existing, Qt.SIGNAL('itemClicked(QListWidgetItem*)'), self._onClicked, QtCore.Qt.QueuedConnection)
        self._render(desc)
    def _render(self, desc):
        self.label_Description.setText(desc)
        self.listWidget_Existing.setEnabled(len(self._existingNames)>0)
        for row, name in enumerate(self._existingNames):
            self.listWidget_Existing.addItem(str(name))
            self.listWidget_Existing.item(row).setCheckState(QtCore.Qt.Unchecked)
    def _onClicked(self, item):
        text = str(item.text())
        if item.checkState()==QtCore.Qt.Checked:
            #    Uncheck!
            self._uncheckAll()
            newState = QtCore.Qt.Unchecked
        else:
            #    Check:
            self._uncheckAll()
            newState = QtCore.Qt.Checked
            pass
        item.setCheckState(newState)
        if self._allUnchecked():
            self.pushButton_Existing.setEnabled(False)
            self._name = None
        else:
            self.pushButton_Existing.setEnabled(True)
            self._name = text
    def _allUnchecked(self):
        for row in xrange(self.listWidget_Existing.count()):
            if self.listWidget_Existing.item(row).checkState()!=QtCore.Qt.Unchecked:
                return False
        return True
    def _uncheckAll(self):
        for row in xrange(self.listWidget_Existing.count()):
            self.listWidget_Existing.item(row).setCheckState(QtCore.Qt.Unchecked)
    def getName(self):
        return self._name
    def _onTextChanged(self, text):
        t = str(text)
        self.pushButton_Custom.setEnabled(len(t))
        self._name = str(text)
    def _onDoubleClicked(self, item):
        table = self.listWidget_Existing
        for row in xrange(table.count()):
            table.item(row).setCheckState(QtCore.Qt.Unchecked)
        item.setCheckState(QtCore.Qt.Checked)
        self._name = str(item.text())
    def _onReject(self):
        self._name = None
        self.reject()
