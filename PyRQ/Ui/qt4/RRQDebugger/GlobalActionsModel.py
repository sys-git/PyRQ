'''
Created on 17 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.Core.Messages.CLOSE import CLOSE
from PyRQ.Core.Messages.DEBUG import DEBUG_QUERY
from PyRQ.RRQ.RRQType import RRQType
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
from PyRQ.Ui.qt4.RRQDebugger.GlobalExecutioner import GlobalExecutioner, \
    RandomChoice, NoChoice, RandomRange, RandomSample, RandomValue, AllValues
import random
import string

class GlobalActionsModel(QtGui.QFrame):
    RESOURCE_NAME = "GlobalActionsModel.ui"
    ALL_SETTIGNS = {
                    "combos":[
                                "comboBox_Actions",
                                "comboBox_Blocking",
                                "comboBox_Timeout",
                                "comboBox_QueueType",
                                "comboBox_WhichQueues",
                                "comboBox_Data",
                                ],
                    "spinners":[
                                "spinBox_CreateCount",
                                "spinBox_CreateMaxsize",
                                "spinBox_Timeout",
                                "spinBox_TimeoutMax",
                                ],
                    "lineEdit":["lineEdit_Data"],
                    }
    INDICES_ACTIONS = [ #    what, enable, disable
                      (Enablers.CREATE_START,("comboBox_QueueType", "comboBox_Timeout", "groupBox_Queue", "groupBox_Timeout"),
                                             ("comboBox_WhichQueues", "comboBox_Data", "comboBox_Blocking", "lineEdit_Data")),
                      (Enablers.CLOSE_START, ("comboBox_Timeout", "groupBox_Timeout", "groupBox_Queue"),
                                             ("comboBox_QueueType", "comboBox_Data", "comboBox_Blocking", "lineEdit_Data", "comboBox_WhichQueues")),
                      (Enablers.PUT_START, ("comboBox_Timeout", "groupBox_Timeout", "comboBox_Data", "comboBox_Blocking", "lineEdit_Data", "comboBox_WhichQueues"),
                                           ("comboBox_QueueType", "groupBox_Queue")),
                      (Enablers.GET_START, ("comboBox_Timeout", "groupBox_Timeout", "groupBox_Queue", "comboBox_Blocking", "comboBox_WhichQueues"),
                                           ("comboBox_QueueType", "comboBox_Data", "lineEdit_Data")),
                      (Enablers.QSIZE_START, ("comboBox_Timeout", "groupBox_Timeout", "comboBox_WhichQueues"),
                                             ("comboBox_QueueType", "groupBox_Queue", "comboBox_Data", "comboBox_Blocking", "lineEdit_Data")),
                      (Enablers.MAXQSIZE_START, ("comboBox_Timeout", "groupBox_Timeout", "comboBox_WhichQueues"),
                                                ("comboBox_QueueType", "groupBox_Queue", "comboBox_Data", "comboBox_Blocking", "lineEdit_Data")),
                      ]
    INDICES_BLOCKING = [
                        True,
                        False,
                        "random",
                        "unique",
                        ]
    INDICES_TIMEOUT = [
                        None,
                        "custom",
                        "random",
                        "unique",
                        ]
    INDICES_QUEUETYPE = [
                        "list",
                        "mp.queue",
                        None,
                        "random",
                        "unique",
                        ]
    INDICES_WHICHQUEUES = [
                            "all",
                            "random",
                            "n-random",
                            ]
    INDICES_DATA = [
                    "random",
                    "unique",
                    "custom",
                    None,
                    ]
    ACTIONS_NAMES = {
                     0:"create",
                     1:"close",
                     2:"put",
                     3:"get",
                     4:"qsize",
                     5:"maxQSize",
                    }
    def __init__(self, parent, *args, **kwargs):
        super(GlobalActionsModel, self).__init__(parent)
        self._parent = parent
        self._initialOptions = {
                                "actions":("comboBox_Actions", 0),
                                "blocking":("comboBox_Blocking", 0),
                                "timeout":("comboBox_Timeout", 0),
                                "queueType":("comboBox_QueueType", 0),
                                "whichQueues":("comboBox_WhichQueues", 0),
                                "data":("comboBox_Data", 0),
                                "options":{
                                           "queue":{
                                                    "count":("spinBox_CreateCount", 1),
                                                    "maxsize":("spinBox_CreateMaxsize", 0),
                                                    },
                                           "timeout":{
                                                      "custom":("spinBox_Timeout", 0),
                                                      "max":("spinBox_TimeoutMax", 10),
                                                      },
                                           "data":("lineEdit_Data", ""),
                                           },
                                }
    def show(self):
        self._onLoad()
        self.connect(self.comboBox_Actions, Qt.SIGNAL('currentIndexChanged(int)'), self._onActions, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Randomise, Qt.SIGNAL('pressed()'), self._onRandomise, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Reset, Qt.SIGNAL('pressed()'), self._onReset, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Save, Qt.SIGNAL('pressed()'), self._onSave, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Execute, Qt.SIGNAL('pressed()'), self._onExecute, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL('executeFinished()'), self._onExecuteFinished, QtCore.Qt.QueuedConnection)
    def _onSave(self):
        settings = self._parent.settings
        settings.beginGroup("ui")
        try:
            settings.beginGroup("actions")
            try:
                self.saveUi(settings)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
        self.emit(Qt.SIGNAL('executeFinished()'))
    def saveUi(self, settings=None):
        if settings==None:
            settings = self._parent.settings
        settings.beginGroup("combos")
        try:
            for what in ["actions", "blocking", "timeout", "queueType", "whichQueues", "data"]:
                self._saveComboBox(settings, what, self._initialOptions[what])
        finally:
            settings.endGroup()
        settings.beginGroup("options")
        try:
            settings.beginGroup("data")
            try:
                opt = self._initialOptions["options"]["data"]
                settings.setValue("value", getattr(self, opt[0]).text())
            finally:
                settings.endGroup()
            settings.beginGroup("queue")
            try:
                opt = self._initialOptions["options"]["queue"]
                for what in opt.keys():
                    self._saveSpinBoxes(settings, what, opt[what])
            finally:
                settings.endGroup()
            settings.beginGroup("timeout")
            try:
                opt = self._initialOptions["options"]["timeout"]
                for what in opt.keys():
                    self._saveSpinBoxes(settings, what, opt[what])
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
    def _onLoad(self):
        settings = self._parent.settings
        settings.beginGroup("ui")
        try:
            settings.beginGroup("actions")
            try:
                self.loadUi(settings)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
    def loadUi(self, settings=None):
        if settings==None:
            settings = self._parent.settings
        settings.beginGroup("combos")
        try:
            for what in ["actions", "blocking", "timeout", "queueType", "whichQueues", "data"]:
                self._loadComboBox(settings, what, self._initialOptions[what])
        finally:
            settings.endGroup()
        settings.beginGroup("options")
        try:
            settings.beginGroup("data")
            try:
                opt = self._initialOptions["options"]["data"]
                value = settings.value("value", "")
                if value.isValid():
                    getattr(self, opt[0]).setText(value.toString())
            finally:
                settings.endGroup()
            settings.beginGroup("queue")
            try:
                opt = self._initialOptions["options"]["queue"]
                for what in opt.keys():
                    self._loadSpinBoxes(settings, what, opt[what])
            finally:
                settings.endGroup()
            settings.beginGroup("timeout")
            try:
                opt = self._initialOptions["options"]["timeout"]
                for what in opt.keys():
                    self._loadSpinBoxes(settings, what, opt[what])
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
        self._checkActions()
    def _loadSpinBoxes(self, settings, key, opt):
        (index, isValid) = settings.value(key).toInt()
        if isValid:
            getattr(self, opt[0]).setValue(index)
    def _saveSpinBoxes(self, settings, key, opt):
        value =getattr(self, opt[0]).value()
        settings.setValue(key, value)
    def _loadComboBox(self, settings, key, opt):
        (index, isValid) = settings.value(key, opt[1]).toInt()
        if isValid:
            getattr(self, opt[0]).setCurrentIndex(index)
    def _saveComboBox(self, settings, key, opt):
        value = getattr(self, opt[0]).currentIndex()
        settings.setValue(key, value)
    def _onActions(self, index):
        self._checkActions()
    def _checkActions(self):
        actionSettings = GlobalActionsModel.INDICES_ACTIONS[(int(self.comboBox_Actions.currentIndex()))]
        (_action, enablers, disablers) = actionSettings
        for what in enablers:
            getattr(self, what).setEnabled(True)
        for what in disablers:
            getattr(self, what).setEnabled(False)
    def _onRandomise(self):
        for what, values in GlobalActionsModel.ALL_SETTIGNS.items():
            if what=="combos":
                self._randomiseCombo(values)
            elif what=="spinners":
                self._randomiseSpinners(values)
            elif what=="lineEdit":
                self._randomiseLineEdits(values)
        self._checkActions()
    def _randomiseCombo(self, values):
        for i in values:
            widget = getattr(self, i)
            widget.setCurrentIndex(random.randrange(0, widget.count(), 1))
    def _randomiseSpinners(self, values):
        for i in values:
            widget = getattr(self, i)
            min_ = widget.minimum()
            max_ = widget.maximum()
            widget.setValue(random.randrange(min_, max_, 1))
    def _randomiseLineEdits(self, values):
        for i in values:
            widget = getattr(self, i)
            widget.setText("".join(random.sample(string.ascii_letters, random.randint(1, 50))))
    def _onReset(self):
        self.loadUi(self._parent.settings)
    def _onExecute(self):
        params = self._getParams()
        executioner = GlobalExecutioner(self, params)
        if not executioner.isReady():
            return
        self._parent.emit(Qt.SIGNAL("injectScript(PyQt_PyObject)"), executioner)
    def _onExecuteFinished(self):
        for what in [self.pushButton_Reset, self.pushButton_Randomise, self.frame_Options, self.pushButton_Execute]:
            what.setEnabled(True)
        self._executioner = None
    def _getParams(self):
        params = {}
        #    Action:
        params["action"] = GlobalActionsModel.ACTIONS_NAMES[self.comboBox_Actions.currentIndex()]
        #    Blocking:
        index = self.comboBox_Blocking.currentIndex()
        if index==0:
            blocking = True
        elif index==1:
            blocking = False
        elif index==2:
            blocking = random.choice([True, False])
        elif index==2:
            blocking = RandomChoice([True, False])
        params["blocking"] = blocking
        #    Timeout:
        index = self.comboBox_Timeout.currentIndex()
        if index==0:
            timeout = NoChoice()
        elif index==1:
            timeout = int(self.spinBox_Timeout.value())
        elif index==2:
            timeout = random.randrange(0, int(self.spinBox_TimeoutMax.value()), 1)
        else:
            timeout = RandomRange(0, int(self.spinBox_TimeoutMax.value()), 1)
        params["timeout"] = timeout
        #    QueueType:
        index = self.comboBox_QueueType.currentIndex()
        qType = None
        if index==0:
            qType = RRQType.LOCKED_LIST
        elif index==1:
            qType = RRQType.MULTIPROCESSING_QUEUE
        elif index==2:
            qType = NoChoice()
        elif index==3:
            qType = random.choice([RRQType.LOCKED_LIST, RRQType.MULTIPROCESSING_QUEUE])
        else:
            qType = RandomChoice([RRQType.LOCKED_LIST, RRQType.MULTIPROCESSING_QUEUE])
        params["queueType"] = qType
        params["queueCount"] = int(self.spinBox_CreateCount.value())
        params["maxsize"] = int(self.spinBox_CreateMaxsize.value())
        #    WhichQueue:
        index = self.comboBox_WhichQueues.currentIndex()
        if index==0:
            whichQueues = AllValues()
        elif index==1:
            whichQueues = RandomValue(count=1)
        elif index==2:
            whichQueues = RandomValue()
        params["whichQueues"] = whichQueues
        #    Data:
        index = self.comboBox_Data.currentIndex()
        if index==0:
            try:
                data = random.sample(string.ascii_letters, random.randint(0, random.randint(0, 100)))
            except:
                data = ""
        elif index==1:
            data = RandomSample(string.ascii_letters, 0, 100)
        elif index==2:
            data = str(self.lineEdit_Data.text())
        else:
            data = None
        params["data"] = data
        return params

