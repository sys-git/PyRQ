'''
Created on 22 Oct 2012

@author: francis
'''

from PyQt4 import Qt
from PyRQ.Iface.PyRQIfaceType import PyRQIfaceType
from PyRQ.Ui.qt4.RRQDebugger.ExecutionState import ExecutionState
from PyRQ.Ui.qt4.RRQDebugger.NoResult import NoResult
from PyRQ.Ui.qt4.RRQDebugger.RRQTab import RRQTab
import copy
import inspect
import itertools
import pickle
import random
import threading
import traceback

class RandomChoice(object):
    def __init__(self, what):
        self._what = what

class AllValues(object): pass

class RandomValue(object):
    def __init__(self, count=None):
        self._count = count

class RandomRange(object):
    def __init__(self, minimum, maximum, step):
        self._minimum = minimum
        self._maximum = maximum
        self._step = step

class RandomSample(object):
    def __init__(self, what, minimum, maximum):
        self._what = what
        self._minimum = minimum
        self._maximum = maximum

class NoChoice(object): pass

class GlobalExecutioner(object):
    #    FIXME: Make generic - allow easier save/load/step - allow step item action execution following.
    gUId = itertools.count(0)
    def __init__(self, parent, params=None):
        self._parent = parent
        self._params = params
        self._configs = self._build()
        self._uId = GlobalExecutioner.gUId.next()
        self._workId = self.uId
        self._name = "%(C)s"%{"C":self.uId}
        self._state = ExecutionState.NOT_RUN
        self._enabled = True
        self._stepActions = None
        self._author = "root"
        self._dirty = False
        self._currentIndex = -1
        self._delays = {"pre":None, "post":None}
    def setUid(self, uId):
        self._uId = uId
        self.dirty = True
    def getUid(self):
        return self._uId
    def setAuthor(self, author):
        self._author = author
        self.dirty = True
    def getAuthor(self):
        return self._author
    def setState(self, state):
        self._state = state
        self.dirty = True
    def getState(self):
        return self._state
    def setEnabled(self, enabled):
        self._enabled = enabled
        self.dirty = True
    def getEnabled(self):
        return self._enabled
    def getConfigs(self):
        return self._configs
    def setConfigs(self, configs):
        self._configs = configs
        self.dirty = True
    def setName(self, name):
        self._name = name
        self.dirty = True
    def setDirty(self, dirty):
        self._dirty = dirty
    def getDirty(self):
        return self._dirty
    def getName(self):
        return self._name
    def getDelays(self):
        return self._delays
    author = property(getAuthor, setAuthor)
    state = property(getState, setState)
    uId = property(getUid, setUid)
    enabled = property(getEnabled, setEnabled)
    name = property(getName, setName)
    delays = property(getDelays)
    dirty = property(getDirty, setDirty)
    configs = property(getConfigs, setConfigs)
    def isReady(self):
        return (len(self.configs)>0)
    def _onDone(self, workId):
        self.state = ExecutionState.FINISHED
        self._parent._parent.emit(Qt.SIGNAL("executeFinished(int, PyQt_PyObject)"), workId, self)
    def _build(self):
        p = self._params
        if p==None:
            return
        #    Execute against params asynchronously.
        whichQueues = p["whichQueues"]
        maxSize = p["maxsize"]
        action = p["action"]
        uId = itertools.count(0)
        #    Create a list of actions to execute with time's between them (of zero).
        #    Each with a uId.
        #    Display the list.
        #    Execute each item in the list at the appropriate time.
        configs = []
        for tab in self._parent._parent.tabs:
            qNamespaces = dict.fromkeys(tab.qIds.keys()+tab.allQueues["active"]).keys()
            originalQNamespaces = copy.deepcopy(qNamespaces)
            details = tab.getDetails()
            if (len(qNamespaces)==0) and (action!="create"):
                continue
            #    WhichQueues:
            if isinstance(whichQueues, RandomValue):
                l = whichQueues._count
                if l==None:
                    #    Chose a random number:
                    l = random.randint(0, len(qNamespaces))
                else:
                    if l>len(qNamespaces):
                        l = len(qNamespaces)
                qNamespaces = random.sample(qNamespaces, l)
            #    Data:
            def createNewData(p):
                data = p["data"]
                if isinstance(data, RandomSample):
                    data = random.sample(data._what, random.randint(data._minimum, data._maximum))
                return data
            #    QueueType:
            def createNewQueueType(p):
                queueType = p["queueType"]
                if isinstance(queueType, RandomChoice):
                    queueType = random.choice(queueType._what)
                return queueType
            #    Timeout:
            def createNewTimeout(p):
                timeout = p["timeout"]
                if isinstance(timeout, RandomRange):
                    timeout = random.randrange(timeout._minimum, timeout._maximum, timeout._step)
                return timeout
            #    Blocking:
            def createNewBlocking(p):
                blocking = p["blocking"]
                if isinstance(blocking, RandomChoice):
                    blocking = random.choice(blocking._what)
                return blocking
            #    Now create the tab's parallel config:
            if action=="create":
                l = p["queueCount"]
                if l==-1:
                    l = 0
                for _ in xrange(l):
                    timeout = createNewTimeout(p)
                    qType = createNewQueueType(p)
                    config = {
                              "uId":uId.next(),
                              "action":action,
                              "blocking":createNewBlocking(p),
                              "maxsize":maxSize,
                              }
                    descTimeout = ""
                    if not isinstance(timeout, NoChoice):
                        config["timeout"] = timeout
                        descTimeout = "timeout=%(T)s"%{"T":timeout}
                    descQueueType = ""
                    if not isinstance(qType, NoChoice):
                        config["queueType"] = qType
                        descQueueType = "queueType=%(QT)s"%{"QT":PyRQIfaceType.enumerate_(qType)}
                    what = ", ".join(["maxSize=%(MS)s"%{"MS":maxSize}, "%(T)s"%{"T":descTimeout}, "%(QT)s"%{"QT":descQueueType}])
                    config["_desc_"] = "Create (%(W)s)"%{"W":what}
                    configs.append(config)
            elif action=="close":
                #    Chose p["queueCount"] from qNamespaces:
                requiredCount = p["queueCount"]
                actualCount = len(qNamespaces)
                l = p["queueCount"]
                allQueues = False
                if l==-1:
                    allQueues=True
                if requiredCount>actualCount:
                    requiredCount = actualCount
                if allQueues==True:
                    qNamespaces = originalQNamespaces
                    requiredCount = len(qNamespaces)
                for index in xrange(requiredCount):
                    timeout = createNewTimeout(p)
                    ns = qNamespaces[index]
                    config = {
                              "uId":uId.next(),
                              "action":action,
                              "namespace":ns,
                              }
                    descTimeout = ""
                    if not isinstance(timeout, NoChoice):
                        config["timeout"] = timeout
                        descTimeout = "timeout=%(T)s, "%{"T":timeout}
                    config["_desc_"] = "Close (%(T)snamespace=%(NS)s)"%{"T":descTimeout, "NS":ns}
                    configs.append(config)
            elif action=="put":
                for ns in qNamespaces:
                    config = {
                              "uId":uId.next(),
                              "action":action,
                              "namespace":ns,
                              "data":p["data"],
                              }
                    timeout = createNewTimeout(p)
                    descTimeout = ""
                    descBlockingTimeout = ""
                    if not isinstance(timeout, NoChoice):
                        config["timeout"] = timeout
                        descTimeout = "timeout=%(T)s, "%{"T":timeout}
                        descBlockingTimeout = descTimeout
                    blocking = createNewBlocking(p)
                    if not isinstance(blocking, NoChoice):
                        config["blocking"] = blocking
                        descBlocking = "blocking=%(B)s, "%{"B":blocking}
                        descBlockingTimeout = descBlocking
                    config["_desc_"] = "Put (%(BT)sns=%(NS)s)"%{"BT":descBlockingTimeout, "T":timeout, "NS":ns}
                    configs.append(config)
            elif action=="get":
                for ns in qNamespaces:
                    config = {
                              "uId":uId.next(),
                              "action":action,
                              "namespace":ns,
                              }
                    timeout = createNewTimeout(p)
                    descTimeout = ""
                    descBlockingTimeout = ""
                    if not isinstance(timeout, NoChoice):
                        config["timeout"] = timeout
                        descTimeout = "timeout=%(T)s, "%{"T":timeout}
                        descBlockingTimeout = descTimeout
                    blocking = createNewBlocking(p)
                    descBlocking = ""
                    if not isinstance(blocking, NoChoice):
                        config["blocking"] = blocking
                        descBlocking = "blocking=%(B)s, "%{"B":blocking}
                        descBlockingTimeout = descBlocking
                    if len(descBlocking)==0 and len(descBlocking)==0:
                        descBlockingTimeout = ", ".join([descTimeout, descBlocking])
                        descBlockingTimeout += ", "
                    config["_desc_"] = "Get (%(BT)sns=%(NS)s)"%{"BT":descBlockingTimeout, "T":timeout, "NS":ns}
                    configs.append(config)
            elif action=="qsize":
                for ns in qNamespaces:
                    config = {
                              "uId":uId.next(),
                              "action":action,
                              "namespace":ns,
                              }
                    timeout = createNewTimeout(p)
                    if not isinstance(timeout, NoChoice):
                        config["timeout"] = timeout
                    config["_desc_"] = "QSize (timeout=%(T)s, ns=%(NS)s)"%{"T":timeout, "NS":ns}
                    configs.append(config)
            elif action=="maxQSize":
                for ns in qNamespaces:
                    config = {
                              "uId":uId.next(),
                              "action":action,
                              "namespace":ns,
                              }
                    timeout = createNewTimeout(p)
                    if not isinstance(timeout, NoChoice):
                        config["timeout"] = timeout
                    config["_desc_"] = "maxQSize (timeout=%(T)s, ns=%(NS)s)"%{"T":timeout, "NS":ns}
                    configs.append(config)
        print "Created %(N)s configs!"%{"N":len(configs)}
        for config in configs:
            config["_author_"] = self._parent._parent.author
            config["_enabled_"] = True
            config["_delay_pre_"] = None
            config["_delay_post_"] = None
            config["_executing_"] = ExecutionState.NOT_RUN
            config["_details_"] = details
            config["_result_"] = None
            try:
                desc = config["_desc_"]
            except Exception, _e:
                desc = str(config)
            config["_desc_"] = desc
        return configs
    def _actionStep(self, workId):
        self._parent._parent.emit(Qt.SIGNAL("stepExecution(int, PyQt_PyObject)"), workId, self)
    def execute(self, workId=None):
        #    Run or resume execution, distinction is irrelevant.
        if self._enabled==False:
            return
        if (workId!=None) and (self._workId!=workId):
            return
        if self.state==ExecutionState.FINISHED:
            self.reset()
        self.state = ExecutionState.RUNNING
        self._paused = False
        if self._stepActions==None:
            self._stepActions = self._createStepActions()
        self._workId += 1
        self._actionStep(self._workId)
    def _createStepActions(self):
        #    Create a StepAction object for each step in the script.
        #    [predelay, commands, postdelay]
        #    commands: [predelay, command, postdelay]n
        actions = []
        delay = self._delays["pre"]
        if delay!=None:
            actions.append((self._doActionDelay, tuple([int(delay)]), {"what":{"script":"pre"}}, ))
        actions.extend(self._createStepConfigActions(self.configs))
        delay = self._delays["post"]
        if delay!=None:
            actions.append((self._doActionDelay, tuple([int(delay)]), {"what":{"script":"post"}}))
        return actions
    def _doActionDelayStarted(self, *args, **kwargs):
        self._doActionDelayState(True, *args, **kwargs)
    def _doActionDelayFinished(self, *args, **kwargs):
        self._doActionDelayState(False, *args, **kwargs)
    def _doActionDelayState(self, state, workId, delay, what, uId):
        self._parent._parent.emit(Qt.SIGNAL("executeDelay(int, int, int, PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)"), state, workId, delay, what, uId, self)
    def _doActionDelay(self, delay, uId=None, what={}):
        self._doActionDelayStarted(self._workId, delay, what, uId)
        #    FYI - workId is dynamic so must not be referenced:
        def delayFinished(workId, delay, what, uId):
            self._doActionDelayFinished(workId, delay, what, uId)
            self._actionStep(workId)
        threading.Timer(int(delay), delayFinished, args=[self._workId,delay, what, uId]).start()
    def _doActionStepped(self, uId):
        #    FYI - workId is dynamic so must not be referenced:
        self._parent._parent.emit(Qt.SIGNAL("executeStepped(int, int, PyQt_PyObject)"), self._workId, uId, self)
        self._actionStep(self._workId)
    def _doActionStepping(self, uId):
        #    FYI - workId is dynamic so must not be referenced:
        self._parent._parent.emit(Qt.SIGNAL("executeStepping(int, int, PyQt_PyObject)"), self._workId, uId, self)
        self._actionStep(self._workId)
    def _doActionScriptStarted(self):
        self._parent._parent.emit(Qt.SIGNAL("executeStarted(int, PyQt_PyObject)"), self._workId, self)
    def _doActionCommandResult(self, workId, uId, postDelay, **kwargs):
        for config in self.configs:
            if config["uId"]==uId:
                config["_executing_"] = ExecutionState.FINISHED
        self._parent._parent.emit(Qt.SIGNAL("executeStepResult(int, PyQt_PyObject, PyQt_PyObject)"), uId, kwargs, self)
        if (self._paused==False) and (postDelay==None):
            self._actionStep(self._workId)
    def _getMethodDetails(self, method):
        (args, _varargs, _varkw, defaults) = inspect.getargspec(method)
        index = len(defaults)
        newArgs = args[:-index]
        if len(newArgs)>0 and newArgs[0]=="self":
            newArgs = newArgs[1:]
        newKwargs = args[-index:]
        return (newArgs, newKwargs)
    def _doActionCallIface(self, postDelay, **kwargs):
        #    Inspect the method signature for 'action' from the Iface and
        #    extract the given args from 'config' and populate the callable
        kwargs["_executing_"] = ExecutionState.RUNNING
        details = kwargs["_details_"]
        namespace = kwargs.get("namespace", None)
        iface = RRQTab.staticGetIface(details, namespace=namespace)
        action = kwargs["action"]
        method = getattr(iface, action)
        (methodArgs, methodKwargs) = self._getMethodDetails(method)
        newArgs = [self._workId, kwargs["uId"], method, postDelay]
        newKwargs = {}
        #    Create the method args dependent on the method signature:
        #    args:
        for argName in methodArgs:
            try:
                newArgs.append(kwargs[argName])
            except Exception, _e:
                print "Unable to locate arg: <%(A)s> in: <%(K)s>."%{"A":argName, "K":kwargs}
        #    kwargs:
        for argName in methodKwargs:
            try:
                newKwargs[argName] = (kwargs[argName])
            except Exception, _e:
                print "FYI - Unable to locate action: '%(AC)s' kwarg: <%(A)s> in: <%(K)s>."%{"A":argName, "K":kwargs, "AC":action}
        #    Finally, call the method asynchronously!
        def callMethod(workId, uId, method, postDelay, *args, **kwargs):
            #    Call the Iface method:
            try:
                result = method(*args, **kwargs)
            except Exception, result:
                print "Error calling iface:\r\n%(T)s"%{"T":traceback.format_exc()}
            #    Now retire the result and request a execution-step-kick:
            self._doActionCommandResult(workId, uId, postDelay, result=result)
        threading.Timer(0, callMethod, args=newArgs, kwargs=newKwargs).start()
    def _createStepConfigActionItem(self, config, postDelay=None):
        actions = []
        #    Now create the action:
        actions.append((self._doActionCallIface, tuple([postDelay]), config))
        return actions
    def _createStepConfigAction(self, config):
        actions = []
        if config["_enabled_"] == True:
            uId = config["uId"]
            actions.append((self._doActionStepping, tuple([uId]), {}))
            delay = config["_delay_pre_"]
            if delay!=None:
                actions.append((self._doActionDelay, tuple([int(delay)]), {"uId":config["uId"], "what":{"config":"pre"}}))
            postDelay = config["_delay_post_"]
            if postDelay==None:
                pass
            actions.extend(self._createStepConfigActionItem(config, postDelay))
            if delay!=None:
                actions.append((self._doActionDelay, tuple([int(postDelay)]), {"uId":config["uId"], "what":{"config":"post"}}))
            uId = config["uId"]
            actions.append((self._doActionStepped, tuple([uId]), {}))
        return actions
    def _createStepConfigActions(self, configs):
        actions = []
        for config in configs:
            actions.extend(self._createStepConfigAction(config))
        return actions
    def isFinished(self):
        return (self.state==ExecutionState.FINISHED)
    def step(self, workId):
        if workId!=self._workId:
            return
        self._currentIndex += 1
        if self._currentIndex==0:
            self._doActionScriptStarted()
        #    Get the action to perform:
        try:
            stepAction = self._stepActions[self._currentIndex]
        except IndexError, _e:
            #    Reached the end-of-script
            self._onDone(workId)
        else:
            (method, args, kwargs) = stepAction
            #    Execute the script action:
            method(*args, **kwargs)
    def pause(self):
        self.state = ExecutionState.PAUSED
        self._paused = True
    def reset(self, workId=None):
        if (workId!=None) and (self._workId!=workId):
            return
        self._dirty = False
        self._currentIndex = -1
        self.state = ExecutionState.NOT_RUN
        for config in self.configs:
            config["_executing_"] = ExecutionState.NOT_RUN
            config["_result_"] = None
            self._parent._parent.emit(Qt.SIGNAL("executeStepResult(int, PyQt_PyObject, PyQt_PyObject)"), config["uId"], {"result":NoResult()}, self)
    @staticmethod
    def loadUi(parent, settings):
        ge = GlobalExecutioner(parent)
        #    Delays:
        try:
            value = settings.value("delays", type=bytearray)
            value = str(value)
            delays = pickle.loads(value)
        except Exception, _e:
            delays = {"pre":None, "post":None}
        ge._delays = delays
        #    Configs:
        try:
            value = settings.value("script", type=bytearray)
            value = str(value)
            configs = pickle.loads(value)
        except Exception, _e:
            configs = []
        ge.configs = configs
        ge._enabled = settings.value("enabled", True).toBool()
        name = settings.value("name").toString()
        if name!=None and len(name)!=1:
            ge.name = name
        ge.author = settings.value("author", "root").toString()
        (value, isValid) = settings.value("index", -1).toInt()
        if isValid:
            ge._currentIndex = value
        #    state:
        (value, isValid) = settings.value("state", ExecutionState.NOT_RUN).toInt()
        if isValid:
            if value==ExecutionState.RUNNING:
                value = ExecutionState.PAUSED
        ge._state = value
        return ge
    def saveUi(self, settings):
        settings.setValue("delays", bytearray(pickle.dumps(self._delays)))
        settings.setValue("name", self.name)
        settings.setValue("script", bytearray(pickle.dumps(self.configs)))
        settings.setValue("enabled", self._enabled)
        settings.setValue("author", self.author)
        settings.setValue("index", self._currentIndex)
        settings.setValue("state", self.state)


