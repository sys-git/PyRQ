'''
Created on 23 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, Qt, QtCore
from PyRQ.Ui.qt4.RRQDebugger.ExecutionState import ExecutionState
from PyRQ.Ui.qt4.RRQDebugger.GlobalExecutioner import GlobalExecutioner
from PyRQ.Ui.qt4.RRQDebugger.NoResult import NoResult
from PyRQ.Ui.qt4.RRQDebugger.ScriptTreeBuilder import TreeBuilder
from PyRQ.Ui.qt4.RRQDebugger.ScriptTreeNodes import TreeCommand, \
    TreeCommandDelayPost, TreeCommandDelayPre, TreeCommandAuthor, TreeCommands, \
    TreeCommandRoot, TreeScriptDelayPre, TreeScriptDelayPost, TreeScriptAuthor, TreeRoot, \
    TreeCommandResult, _baseTreeCommandConfig
import itertools
import os
import pickle
import threading

class Scripter(QtGui.QWidget):
    RESOURCE_NAME = "Scripter.ui"
    DEFAULT_LOOP_INDEX = 2
    DEFAULT_TREE_EXPANDED_STATE = 2     #    0=collapsed, 1=expanded, 2=whatever
    uId = itertools.count(0)
    dataCount = itertools.count(0)
    def __init__(self, parent):
        super(Scripter, self).__init__(parent=parent)
        self._parent = parent
        self._scripts = []
        self._executing = None
        self._resourcePath = self._parent.resourcesPath
        self._paused = False
        self._readOnly = False
        self._enableTreeChangeEvents = False
        self._timeouts = self._getDefaultsTimeouts()
        self._treeIsExpanded = Scripter.DEFAULT_TREE_EXPANDED_STATE
        self._icons = {"exec":{"running":None, "paused":None, "finished":None},
                       "result":{"none":None, "exc":None, "ok":None},
                       "author":None,
                       "time":{"sleep":None, "delay":None},
                       "enabled":{True:None, False:None},
                       "node":None,
                       "command":{"generic":None, "create":None, "close":None, "put":None, "get":None, "qsize":None, "maxQSize":None},
                       "state":{ExecutionState.FINISHED:None, ExecutionState.NOT_RUN:None, ExecutionState.RUNNING:None, ExecutionState.PAUSED:None}}
    def show(self):
        super(Scripter, self).show()
        self.connect(self, Qt.SIGNAL("readOnly()"), self._onReadOnly)
        self.connect(self._parent, Qt.SIGNAL("injectScript(PyQt_PyObject)"), self._onInjectScript, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("executeStarted(int, PyQt_PyObject)"), self._onExecutionStarted, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("executeFinished(int, PyQt_PyObject)"), self._onExecutionFinished, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("executeStepped(int, int, PyQt_PyObject)"), self._onExecutionStepped, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("executeStepping(int, int, PyQt_PyObject)"), self._onExecutionStepping, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("executeStepResult(int, PyQt_PyObject, PyQt_PyObject)"), self._onExecutionStepResult, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("executeDelay(int, int, int, PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)"), self._onExecutionDelay, QtCore.Qt.QueuedConnection)
        self.connect(self._parent, Qt.SIGNAL("stepExecution(int, PyQt_PyObject)"), self._onStepExecution, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Run, Qt.SIGNAL("pressed()"), self._onExecute, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Pause, Qt.SIGNAL("pressed()"), self._onPause, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Clear, Qt.SIGNAL("pressed()"), self._onClear, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Save, Qt.SIGNAL("pressed()"), self._onSave, QtCore.Qt.QueuedConnection)
        self.connect(self.pushButton_Reload, Qt.SIGNAL("pressed()"), self._onReload, QtCore.Qt.QueuedConnection)
        self.connect(self.treeWidget_ScriptActions, Qt.SIGNAL("customContextMenuRequested(QPoint)"), self._onTreePopup, QtCore.Qt.QueuedConnection)
        self.connect(self.treeWidget_ScriptActions, Qt.SIGNAL("itemPressed(QTreeWidgetItem*, int)"), self._onTreeItemClicked)
        self.connect(self.treeWidget_ScriptActions, Qt.SIGNAL("itemClicked(QTreeWidgetItem*, int)"), self._onTreeClicked)
        self.connect(self.treeWidget_ScriptActions, Qt.SIGNAL("itemChanged(QTreeWidgetItem*, int)"), self._onTreeChanged)
        self._configureMenuActions()
        self._configureIcons()
        self.label_executing.setText("")
        self.label_executing.setPixmap(self._icons["exec"]["paused"])
        self.tb = TreeBuilder(self.treeWidget_ScriptActions, self._icons)
        self._enableTreeChangeEvents = True
    def _configureMenuActions(self):
        self._actions = {
                         #    Tree:
                         "tree_scrollTop":QtGui.QAction("Go to top", self.treeWidget_ScriptActions),
                         "tree_scrollBottom":QtGui.QAction("Go to bottom", self.treeWidget_ScriptActions),
                         "tree_collapseAll":QtGui.QAction("Collapse all", self.treeWidget_ScriptActions),
                         "tree_expandAll":QtGui.QAction("Expand all", self.treeWidget_ScriptActions),
                         #    Script:    DONE.
                         "script_run":QtGui.QAction("Run script", self.treeWidget_ScriptActions),
                         "script_pause":QtGui.QAction("Pause script", self.treeWidget_ScriptActions),
                         "script_enable":QtGui.QAction("Enable script", self.treeWidget_ScriptActions),
                         "script_disable":QtGui.QAction("Disable script", self.treeWidget_ScriptActions),
                         "script_delayPre":QtGui.QAction("Configure script delay pre", self.treeWidget_ScriptActions),
                         "script_delayPost":QtGui.QAction("Configure script delay post", self.treeWidget_ScriptActions),
                         "script_author":QtGui.QAction("Configure script author", self.treeWidget_ScriptActions),
                         "script_remove":QtGui.QAction("Remove script", self.treeWidget_ScriptActions),
                         #    All script:
                         "all_script_enable":QtGui.QAction("Enable all scripts", self.treeWidget_ScriptActions),
                         "all_script_disable":QtGui.QAction("Disable all scripts", self.treeWidget_ScriptActions),
                         "all_script_delayPre":QtGui.QAction("Configure all scripts' delay pre", self.treeWidget_ScriptActions),
                         "all_script_delayPost":QtGui.QAction("Configure all scripts' delay post", self.treeWidget_ScriptActions),
                         "all_script_author":QtGui.QAction("Configure all scripts' author", self.treeWidget_ScriptActions),
                         #    Commands:
                         "command_enable":QtGui.QAction("Enable this command", self.treeWidget_ScriptActions),
                         "command_disable":QtGui.QAction("Disable this command", self.treeWidget_ScriptActions),
                         "command_delayPre":QtGui.QAction("Configure command delay pre", self.treeWidget_ScriptActions),
                         "command_delayPost":QtGui.QAction("Configure command delay post", self.treeWidget_ScriptActions),
                         "command_author":QtGui.QAction("Edit command's author", self.treeWidget_ScriptActions),
                         #    All command
                         "all_command_enable":QtGui.QAction("Enable all commands", self.treeWidget_ScriptActions),
                         "all_command_disable":QtGui.QAction("Disable all commands", self.treeWidget_ScriptActions),
                         "all_command_delayPre":QtGui.QAction("Configure all commands' delay pre", self.treeWidget_ScriptActions),
                         "all_command_delayPost":QtGui.QAction("Configure all commands' delay post", self.treeWidget_ScriptActions),
                         "all_command_author":QtGui.QAction("Edit all command's author", self.treeWidget_ScriptActions),
                         "all_command_collapseAll":QtGui.QAction("Collapse all script's commands", self.treeWidget_ScriptActions),
                         "all_command_expandAll":QtGui.QAction("Expand all script's commands", self.treeWidget_ScriptActions),
                         }
    def _configureIcons(self):
        resourcesPath = self._resourcePath
        self._icons["enabled"][True] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "tree_tick.png"))
        self._icons["enabled"][False] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "tree_cross.png"))
        self._icons["state"][ExecutionState.RUNNING] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "state_running.png"))
        self._icons["state"][ExecutionState.PAUSED] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "state_paused.png"))
        self._icons["state"][ExecutionState.FINISHED] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "state_finished.png"))
        self._icons["state"][ExecutionState.NOT_RUN] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "state_notrun.png"))
        self._icons["time"]["delay"] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "time_delay.png"))
        self._icons["time"]["sleep"] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "time_sleep.png"))
        self._icons["author"] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "author.png"))
        self._icons["result"]["exc"] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "tree_cross.png"))
        self._icons["result"]["ok"] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "tree_tick.png"))
        self._icons["result"]["none"] = QtGui.QIcon(os.path.join(resourcesPath, "icons", "result_none.png"))
        self._icons["exec"]["running"] = QtGui.QPixmap(os.path.join(self._resourcePath, "icons", "icon_running.png"))
        self._icons["exec"]["paused"] = QtGui.QPixmap(os.path.join(self._resourcePath, "icons", "icon_sleep.png"))
        self._icons["exec"]["finished"] = QtGui.QPixmap(os.path.join(self._resourcePath, "icons", "icon_finished.png"))
        cmdPath = os.path.join(self._resourcePath, "icons", "actions")
        self._icons["command"]["generic"] = QtGui.QIcon(os.path.join(cmdPath, "action_command_generic.png"))
        for iconName, action in [("action_create.png", "create"),
                                 ("action_close.png", "close"),
                                 ("action_get.png", "get"),
                                 ("action_put.png", "put"),
                                 ("action_qsize.png", "qsize"),
                                 ("action_maxQSize.png", "maxQSize"),
                                 ]:
            self._loadIcon(cmdPath, iconName, action, self._icons["command"]["generic"])
        self._icons["node"] = QtGui.QIcon(os.path.join(self._resourcePath, "icons", "icon_node.png"))
    def _loadIcon(self, path, iconName, action, defaultIcon):
        p = os.path.join(path, iconName)
        if os.path.exists(p):
            icon = QtGui.QIcon(p)
        else:
            icon = defaultIcon
        self._icons["command"][action] = icon
        return icon
    def _onTreeItemClicked(self, item, index):
        if self._enableTreeChangeEvents==True:
            pass
#            print "itemPressed(QTreeWidgetItem*, int): ", item, index
    def _onTreeClicked(self, item, index):
        if self._enableTreeChangeEvents==True:
            pass
#            print "itemClicked(QTreeWidgetItem*, int): ", item, index
    def _onTreeChanged(self, item, index):
        if self._enableTreeChangeEvents==True:
            print "itemChanged(QTreeWidgetItem*, int): ", item, index
            #    Search the tree for the item and change the model's data:
            executioner = item.getScript()
            if executioner in self._scripts:
                self._changeExecutionerData(executioner, item, index)
    def _changeExecutionerData(self, executioner, item, index=1):
        newValue = item.text(index)
        if isinstance(item, TreeScriptDelayPre):
            executioner.delays["pre"] = int(newValue)
        elif isinstance(item, TreeScriptDelayPost):
            executioner.delays["post"] = int(newValue)
        elif isinstance(item, TreeScriptAuthor):
            executioner.author = str(newValue)
        elif isinstance(item, _baseTreeCommandConfig):
            config = item.getConfig()
            if isinstance(item, TreeCommandDelayPre):
                config["_delay_pre_"] = int(newValue)
            elif isinstance(item, TreeCommandDelayPost):
                config["_delay_post_"] = int(newValue)
            elif isinstance(item, TreeCommandAuthor):
                config["_author_"] = str(newValue)
        else:
            #    No idea how to edit this one!!!
            pass
#            print "No idea what I'm editing at index: %(I)s for: %(W)s"%{"I":index, "W":item}
    def _getAllRootScripts(self):
        scripts = []
        for index in xrange(self.treeWidget_ScriptActions.topLevelItemCount()):
            scripts.append(self.treeWidget_ScriptActions.topLevelItem(index).getScript())
        return scripts
    def _onTreePopup(self, pos):
        result = self._showTreePopup(pos)
        if result!=None:
            (action, item) = result
            self._handleActions(action, item)
    def _getAuthor(self, text, value):
        (value, ok) = QtGui.QInputDialog.getText(self, text, "Author:", QtGui.QLineEdit.Normal, value)
        if ok is False:
            return
        value = str(value)
        return value
    def _getDelay(self, value):
        value, ok = QtGui.QInputDialog.getInt(self, "Edit script: _delay_pre_", "Delay (seconds):", value=0, min=-1, step=1)
        if ok is False:
            return
        return value
    def _scrollToTop(self):
        try:
            self.treeWidget_ScriptActions.scrollToItem(self.treeWidget_ScriptActions.topLevelItem(0), Qt.QAbstractItemView.PositionAtTop)
        except Exception, _e:
            pass
    def _scrollToBottom(self):
        index = (self.treeWidget_ScriptActions.topLevelItemCount()-1)
        if index>=0:
            item = self.treeWidget_ScriptActions.topLevelItem(index)
            self.treeWidget_ScriptActions.scrollToItem(item, Qt.QAbstractItemView.PositionAtTop)
    def _handleActions(self, action, item):
        self._enableTreeChangeEvents = False
        try:
            script = item.getScript()
            config = None
            if isinstance(item, _baseTreeCommandConfig):
                config = item.getConfig()
            #    Script:
            if action==self._actions["tree_collapseAll"]:
                self._treeIsExpanded = 0
                self._expandTree()
            elif action==self._actions["tree_expandAll"]:
                self._treeIsExpanded = 1
                self._expandTree()
            elif action==self._actions["tree_scrollTop"]:
                self._scrollToTop()
            elif action==self._actions["tree_scrollBottom"]:
                self._scrollToBottom()
            elif action==self._actions["script_run"]:
                self._onExecute(script)
            elif action==self._actions["script_pause"]:
                self._onPause()
            elif action==self._actions["script_enable"]:
                script.enabled = True
                self._updateScriptEnabled(script)
            elif action==self._actions["script_disable"]:
                script.enabled = False
                self._updateScriptEnabled(script)
            elif action==self._actions["script_remove"]:
                self._scripts.remove(script)
                self._updateScriptRemoved(script)
            elif action==self._actions["script_author"]:
                value = self._getAuthor("Edit: Author", script.author)
                if value==None:
                    return
                script.author = value
                self._updateScriptAuthor(script)
            elif action==self._actions["script_delayPre"]:
                value = self._getDelay(script.delays["pre"])
                if value==None:
                    return
                if value==-1:
                    value = None
                script.delays["pre"] = str(value)
                self._updateScriptDelayPre(script)
            elif action==self._actions["script_delayPost"]:
                value = self._getDelay(script.delays["post"])
                if value==None:
                    return
                if value==-1:
                    value = None
                script.delays["post"] = str(value)
                self._updateScriptDelayPost(script)
            #    All script:
            elif action==self._actions["all_script_enable"]:
                for script in self._getAllRootScripts(): 
                    script.enabled = True
                    self._updateScriptEnabled(script)
            elif action==self._actions["all_script_disable"]:
                for script in self._getAllRootScripts(): 
                    script.enabled = False
                    self._updateScriptEnabled(script)
            elif action==self._actions["all_script_author"]:
                value = self._getAuthor("Edit: Author", script.author)
                if value==None:
                    return
                for script in self._getAllRootScripts(): 
                    script.author = value
                    self._updateScriptAuthor(script)
            elif action==self._actions["all_script_delayPre"]:
                value = self._getDelay(script.delays["pre"])
                if value==None:
                    return
                if value==-1:
                    value = None
                for script in self._getAllRootScripts(): 
                    script.delays["pre"] = value
                    self._updateScriptDelayPre(script)
            elif action==self._actions["all_script_delayPost"]:
                value = self._getDelay(script.delays["post"])
                if value==None:
                    return
                if value==-1:
                    value = None
                for script in self._getAllRootScripts(): 
                    script.delays["post"] = value
                    self._updateScriptDelayPost(script)
            #    Commands:
            elif action==self._actions["command_enable"]:
                config["_enabled_"] = True
                self._updateCommandEnable(script, config)
            elif action==self._actions["command_disable"]:
                config["_enabled_"] = False
                self._updateCommandEnable(script, config)
            elif action==self._actions["command_delayPre"]:
                value = self._getDelay(config["_delay_pre_"] )
                if value==None:
                    return
                if value==-1:
                    value = None
                config["_delay_pre_"] = value
                self._updateDelayPre(script, config)
            elif action==self._actions["command_delayPost"]:
                value = self._getDelay(config["_delay_post_"] )
                if value==None:
                    return
                if value==-1:
                    value = None
                config["_delay_post_"] = value
                self._updateDelayPost(script, config)
            elif action==self._actions["command_author"]:
                if "_author_" in config:
                    author = config["_author_"]
                else:
                    author = self._parent.author
                value = self._getAuthor("Edit: Author", author)
                if value==None:
                    return
                config["_author_"] = value
                self._updateCommandAuthor(script, config)
            #    All commands
            elif action==self._actions["all_command_collapseAll"]:
                #    Collapse all tree nodes for this script:
                item = self._findScript(script)
                self._collapseCommands(item)
            elif action==self._actions["all_command_expandAll"]:
                item = self._findScript(script)
                self._expandCommands(item)
            elif action==self._actions["all_command_enable"]:
                for config_ in script.configs:
                    config_["_enabled_"] = True
                    self._updateCommandEnable(script, config_)
            elif action==self._actions["all_command_disable"]:
                for config_ in script.configs:
                    config_["_enabled_"] = False
                    self._updateCommandEnable(script, config_)
            elif action==self._actions["all_command_delayPre"]:
                value = self._getDelay(0)
                if value==None:
                    return
                if value==-1:
                    value = None
                for config_ in script.configs:
                    config_["_delay_pre_"] = value
                    self._updateDelayPre(script, config_)
            elif action==self._actions["all_command_delayPost"]:
                value = self._getDelay(0)
                if value==None:
                    return
                if value==-1:
                    value = None
                for config_ in script.configs:
                    config_["_delay_post_"] = value
                    self._updateDelayPost(script, config_)
            elif action==self._actions["all_command_author"]:
                author = self._parent.author
                value = self._getAuthor("Edit: Author", author)
                if value==None:
                    return
                for config_ in script.configs:
                    config_["_author_"] = value
                    self._updateCommandAuthor(script, config_)
        finally:
            self._enableTreeChangeEvents = True
    def _expandCommands(self, item):
        #    Expand all tree command nodes for this item:
        for index in xrange(0, item.childCount()):
            child = item.child(index)
            if isinstance(child, TreeCommandRoot):
                for index in xrange(0, child.childCount()):
                    child1 = child.child(index)
                    print "expanding item: ", child1
                    self.treeWidget_ScriptActions.expandItem(child1)
                return
    def _collapseCommands(self, item):
        #    Collapse all tree command nodes for this item:
        for index in xrange(0, item.childCount()):
            child = item.child(index)
            if isinstance(child, TreeCommandRoot):
                for index in xrange(0, child.childCount()):
                    child1 = child.child(index)
                    print "collapsing item: ", child1
                    self.treeWidget_ScriptActions.collapseItem(child1)
                return
    def _updateScriptEnabled(self, script):
        #    The current script 'enabled' has changed, alter the tree to reflect this.
        root = self._findScript(script)
        self.tb.setScriptEnabled(script, root)
    def _updateScriptRemoved(self, script):
        item = self._findScript(script)
        t = self.treeWidget_ScriptActions
        t.takeTopLevelItem(t.indexOfTopLevelItem(item))
    def _updateCommandEnable(self, script, config):
        #    The current config 'enabled' has changed, alter the tree to reflect this.
        child = self._findConfig(script, config["uId"])
        commandState = config["_executing_"]
        enabledState = config["_enabled_"]
        self.tb.setConfigEnabled(child, commandState, enabledState)
        return
    def _findConfig(self, script, uId):
        for index in xrange(self.treeWidget_ScriptActions.topLevelItemCount()):
            item = self.treeWidget_ScriptActions.topLevelItem(index)
            itemScript = item.getScript()
            if itemScript==script:
                for childIndex in xrange(0, item.childCount()):
                    child = item.child(childIndex)
                    if isinstance(child, TreeCommandRoot):
                        for childIndex1 in xrange(0, child.childCount()):
                            child1 = child.child(childIndex1)
                            if isinstance(child1, TreeCommands):
                                if child1.getConfig()["uId"]==uId:
                                    return child1
    def _findConfigAuthor(self, script, uId):
        child1 = self._findConfig(script, uId)
        #    Now find the author from the child1's children,
        #    if no author, return child1.
        for index in xrange(0, child1.childCount()):
            child2 = child1.child(index)
            if isinstance(child2, TreeCommandAuthor):
                return (child1, child2)
        else:
            return (child1, None)
    def _updateDelayPre(self, script, config):
        #    The current config 'delay-pre' has changed, alter the tree to reflect this.
        delay = config["_delay_pre_"]
        item, parent = self._findConfigDelayPre(script, config["uId"])
        if delay!=None:
            if item:
                item.setText(1, str(delay))
            else:
                #    Add a new node:
                item = self.tb.addConfigDelayPre(script, script.configs.index(config), config, parent)
                parent.insertChild(0, item)
        else:
            #    Remove an existing delay:
            if item:
                parent.removeChild(item)
    def _updateDelayPost(self, script, config):
        #    The current config 'delay-post' has changed, alter the tree to reflect this.
        delay = config["_delay_post_"]
        item, parent = self._findConfigDelayPost(script, config["uId"])
        if delay!=None:
            if item:
                item.setText(1, str(delay))
            else:
                #    Add a new node:
                item = self.tb.addConfigDelayPost(script, script.configs.index(config), config, parent)
                parent.insertChild(0, item)
        else:
            #    Remove an existing delay:
            if item:
                parent.removeChild(item)
    def _findConfigDelayPost(self, script, uId):
        return self._findConfigDelay(script, uId, TreeCommandDelayPost)
    def _findConfigDelayPre(self, script, uId):
        return self._findConfigDelay(script, uId, TreeCommandDelayPre)
    def _findConfigDelay(self, script, uId, type_):
        item = self._findConfig(script, uId)
        for childIndex2 in xrange(0, item.childCount()):
            child2 = item.child(childIndex2)
            if isinstance(child2, type_):
                return child2, item
        return (None, item)
    def _updateScriptDelayPre(self, script):
        #    The current script 'delay-pre' has changed, alter the tree to reflect this.
        child = self._findScriptDelayPre(script)
        delay = script.delays["pre"]
        child.setText(1, str(delay))
    def _updateScriptDelayPost(self, script):
        #    The current script 'delay-post' has changed, alter the tree to reflect this.
        child = self._findScriptDelayPost(script)
        delay = script.delays["post"]
        child.setText(1, str(delay))
    def _findScriptDelayPost(self, script):
        #    The current script 'delay-post' has changed, alter the tree to reflect this.
        return self._findScriptDelay(script, TreeScriptDelayPost)
    def _findScriptDelayPre(self, script):
        #    The current script 'delay-pre' has changed, alter the tree to reflect this.
        return self._findScriptDelay(script, TreeScriptDelayPre)
    def _findScriptDelay(self, script, type_):
        item = self._findScript(script)
        for childIndex in xrange(0, item.childCount()):
            child = item.child(childIndex)
            if isinstance(child, type_):
                return child
    def _findScript(self, script):
        for index in xrange(self.treeWidget_ScriptActions.topLevelItemCount()):
            item = self.treeWidget_ScriptActions.topLevelItem(index)
            itemScript = item.getScript()
            if itemScript==script:
                return item
    def _updateScriptFinished(self, script):
        #    The current script has finished, alter the tree to reflect this.
        item = self._findScript(script)
        if item!=None:
            self.tb.setResultIcon(item)
            item.setText(1, "Status: Finished")
            self.tb.setStateIcon(item, ExecutionState.FINISHED)
    def _updateScriptStarted(self, script):
        #    The current script has started, alter the tree to reflect this.
        item = self._findScript(script)
        if item!=None:
            self.tb.setResultIcon(item)
            item.setText(1, "Status: Testing")
            self.tb.setStateIcon(item, ExecutionState.RUNNING)
    def _updateScriptPaused(self, script=None):
        #    The current script has paused, alter the tree to reflect this.
        if script==None:
            try:
                script = self._scripts[self._executing]
            except Exception, _e:
                return
        item = self._findScript(script)
        if item!=None:
            self.tb.setResultIcon(item)
            item.setText(1, "Status: Paused")
            self.tb.setStateIcon(item, ExecutionState.PAUSED)
    def _updateScriptAuthor(self, script):
        #    The current script 'author' has changed, alter the tree to reflect this.
        child = self._findScriptAuthor(script)
        author = str(script.author)
        child.setText(1, author)
    def _updateCommandAuthor(self, script, config):
        #    The current command 'enabled' has changed, alter the tree to reflect this.
        author = str(config["_author_"])
        (parent, child) = self._findConfigAuthor(script, config)
        if child==None:
            #    Need to add an author element.
            item = self.tb.addConfigAuthor(script, self._scripts.index(script), config, parent)
            parent.insertChild(0, item)
        else:
            #    Need to change the existing element:
            child.setText(1, str(author))
    def _updateCommandResult(self, script, config, result):
        state = config["_executing_"]
        (child, parent) = self._findCommandResult(script, config["uId"])
        if child==None:
            if isinstance(result, NoResult):
                #    Alter the parent's icon!
                self.tb.setStateIcon(parent, state)
            else:
                #    Need to add an author element.
                item = self.tb.addConfigResult(script, self._scripts.index(script), config, parent)
                parent.insertChild(0, item)
        else:
            #    Need to change the existing element:
            if result==None:
                result = ""
            child.setText(1, str(result))
            self.tb.setResultIcon(child, result)
    def _updateCommandFinished(self, script, uId):
        (child, parent) = self._findCommandResult(script, uId)
        if child!=None:
            #    Set the parent's icon too:
            self.tb.setStateIcon(parent, ExecutionState.FINISHED)
    def _findCommandResult(self, script, uId):
        node = self._findConfig(script, uId)
        for index in xrange(node.childCount()):
            child = node.child(index)
            if isinstance(child, TreeCommandResult):
                return (child, node)
        return (None, node)
    def _findScriptAuthor(self, script):
        for index in xrange(self.treeWidget_ScriptActions.topLevelItemCount()):
            item = self.treeWidget_ScriptActions.topLevelItem(index)
            itemScript = item.getScript()
            if itemScript==script:
                for childIndex in xrange(0, item.childCount()):
                    child = item.child(childIndex)
                    if isinstance(child, TreeScriptAuthor):
                        return child
    def _showTreePopup(self, pos):
        item = self.treeWidget_ScriptActions.itemAt(pos)
        if item!=None:
            pos = self.treeWidget_ScriptActions.mapToGlobal(pos)
            return item.showTreePopup(self, item, self._actions, QtGui.QMenu(self.treeWidget_ScriptActions), pos)
    def _onReload(self):
        self._onClear()
        self.doLoadUi()
    def _renderScript(self, scriptIndex):
        tb =self.tb
        script = self._scripts[scriptIndex]
        tv = self.treeWidget_ScriptActions
        #    Now create it from scratch:
        root = tb.addScriptRoot(script)
        tb.addScriptAuthor(script, root)
        delay = script.delays["pre"]
        if delay==None:
            delay = 0
        tb.addScriptDelayPre(script, str(delay), root)
        delay = script.delays["post"]
        if delay==None:
            delay = 0
        tb.addScriptDelayPost(script, str(delay), root)
        commands = tb.addConfigRoot(script, root)
        for index, config in enumerate(script.configs):
            command = tb.addConfigs(script, index, config, commands)
            if "_author_" in config and config["_author_"]!=None:
                tb.addConfigAuthor(script, index, config, command)
            if config["_delay_pre_"]!=None:
                tb.addConfigDelayPre(script, index, config, command)
            tb.addCommand(script, index, config, command)
            if config["_delay_post_"]!=None:
                tb.addConfigDelayPost(script, index, config, command)
        tv.insertTopLevelItem(0, root)
        return root
    def _render(self):
        self._enableTreeChangeEvents = False
        try:
            #    Clear the existing model:
            tv = self.treeWidget_ScriptActions
            model = tv.model()
            try:    model.removeRows(0, model.rowCount())
            except: pass
            tv.setColumnCount(2)
            for index in xrange(0, len(self._scripts)):
                self._renderScript(index)
            if len(self._scripts)>0:
                self.pushButton_Run.setEnabled(True)
                self.pushButton_Pause.setEnabled(False)
            else:
                self.pushButton_Run.setEnabled(False)
                self.pushButton_Pause.setEnabled(False)
            self._expandTree()
        finally:
            self._enableTreeChangeEvents = True
    def _getUniqueName(self, script):
        eName = script.getName()
        names = []
        for script_ in self._scripts:
            names.append(script_.getName())
        while eName in names:
            eName = script.uId.next()
        script.name = eName
    def _onInjectScript(self, script):
        self._enableTreeChangeEvents = False
        self._getUniqueName(script)
        self._scripts.append(script)
        item = self._renderScript(len(self._scripts)-1)
        #    Now scroll to show the newly inserted script:
        self.treeWidget_ScriptActions.scrollToItem(item, Qt.QAbstractItemView.EnsureVisible)
        self.pushButton_Run.setEnabled(True)
        self._enableTreeChangeEvents = True
        if (self._executing==None) and (script.enabled==True):
            self._onExecute(script=script)
    def _onPause(self):
        self._paused = True
        self.label_executing.setPixmap(self._icons["exec"]["paused"])
        if self._executing!=None:
            for script in self._scripts:
                script.pause()
            self.pushButton_Run.setEnabled(True)
            self.pushButton_Pause.setEnabled(False)
            self._updateScriptPaused()
        else:
            self.pushButton_Run.setEnabled(True)
            self.pushButton_Pause.setEnabled(False)
    def _onExecute(self, script=None, workId=None):
        #    Execute the next available script (primary) or 'script' if provided (secondary).
        self._paused = False
        if len(self._scripts)==0:
            self.pushButton_Run.setEnabled(False)
            self.pushButton_Pause.setEnabled(False)
            return
        if self._executing==None:
            #    Get the next available script:
            if script==None:
                for index, script in enumerate(self._scripts):
                    if script.enabled==True:
                        break
            else:
                index = self._scripts.index(script)
                if index==-1:
                    script = None
            if script!=None:
                #    Mark the first script as executing.
                self._executing = index
        else:
            #    Is the current script disabled, if so move onto the next script
            #    unless 'script' is disabled.
            if self._executing>=len(self._scripts):
                self._executing = 0
            startIndex = self._executing
            while self._scripts[self._executing].enabled==False:
                #    Find the next script:
                self._executing += 1
                if self._executing>=len(self._scripts):
                    self._executing = 0
                if self._executing==startIndex:
                    break
        #    Execute the current script (un-pause it)
        if self._executing!=None:
            self.label_executing.setPixmap(self._icons["exec"]["running"])
            self.pushButton_Run.setEnabled(False)
            self.pushButton_Pause.setEnabled(True)
            self._readOnly = True
            self.emit(Qt.SIGNAL("readOnly()"))
            self._scripts[self._executing].execute(workId=workId)
    def _getLoop(self):
        for what, index in [(self.radioButton_LoopOne, 0), (self.radioButton_LoopAll, 1), (self.radioButton_LoopNone, 2)]:
            if what.isChecked():
                return index
        self.radioButton_LoopOne.isChecked()
    def _setLoop(self, index):
        if index==0:
            self.radioButton_LoopOne.setChecked(True)
        elif index==1:
            self.radioButton_LoopAll.setChecked(True)
        else:
            self.radioButton_LoopNone.setChecked(True)
    def _getDefaultsTimeouts(self):
        return {"loop": 1}
    def doLoadUi(self):
        settings = self._parent.settings
        settings.beginGroup("ui")
        try:
            settings.beginGroup("scripter")
            try:
                self.loadUi(settings)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
    def loadUi(self, settings=None):
        if settings==None:
            settings = self._parent.settings
        (value, isValid) = settings.value("executing").toInt()
        if isValid:
            self._executing = int(value)
        else:
            self._executing = None
        (value, isValid) = settings.value("loop", Scripter.DEFAULT_LOOP_INDEX).toInt()
        if isValid:
            self._setLoop(int(value))
        (value, isValid) = settings.value("treeExpanded", Scripter.DEFAULT_TREE_EXPANDED_STATE).toInt()
        if isValid:
            self._treeIsExpanded = value
        self._paused = settings.value("paused").toBool()
        try:
            value = settings.value("timeouts", type=bytearray)
            value = str(value)
            self._timeouts = pickle.loads(value)
        except Exception, _e:
            pass
        settings.beginGroup("scripts")
        try:
            for group in settings.childGroups():
                settings.beginGroup(group)
                try:
                    script = GlobalExecutioner.loadUi(self, settings)
                    if script!=None:
                        self._scripts.append(script)
                finally:
                    settings.endGroup()
        finally:
            settings.endGroup()
        #    All scripts are loaded and paused.
        self._render()
    def saveUi(self, settings=None):
        if settings==None:
            settings = self._parent.settings
        settings.setValue("executing", self._executing)
        settings.setValue("loop", self._getLoop())
        settings.setValue("treeExpanded", self._treeIsExpanded)
        settings.setValue("paused", self._paused)
        settings.setValue("timeouts", bytearray(pickle.dumps(self._timeouts)))
        settings.beginGroup("scripts")
        try:
            settings.remove("")
            for script in self._scripts:
                group = script.getName()
                settings.beginGroup(group)
                try:
                    script.saveUi(settings)
                finally:
                    settings.endGroup()
        finally:
            settings.endGroup()
    def _onClear(self):
        #    Teardown the tree and rebuild it.
        for script in self._scripts:
            script.pause()
        self._scripts = []
        self._executing = None
        self._render()
    def _onSave(self):
        settings = self._parent.settings
        settings.beginGroup("ui")
        try:
            settings.beginGroup("scripter")
            try:
                self.saveUi(settings)
            finally:
                settings.endGroup()
        finally:
            settings.endGroup()
    def _onStepExecution(self, workId, script):
        if script in self._scripts:
            script.step(workId)
    def _onExecutionFinished(self, workId, script):
        #    A script has completed, mark it as completed in the tree.
        print "Script finished...workId: %(W)s, for script: %(S)s"%{"S":script, "W":workId}
        if len(self._scripts)==0:
            return
        loop = self._getLoop()
        def startTimeout(timeout, script, workId=None):
            def doExecute(script, workId=None):
                if self._paused==False:
                    self._resetScript(script, workId)
                    self._onExecute(script=script, workId=workId)
            if timeout==None:
                doExecute(script, workId)
            else:
                t = threading.Timer(timeout, doExecute, args=[script])
                t.setName("LoopOne_%(T)s"%{"T":timeout})
                t.setDaemon(True)
                t.start()
        timeout = self._timeouts["loop"]
        if loop==0:
            #    Re-run the script:
            print "Re-running script: %(S)s"%{"S":script}
            startTimeout(timeout, script, workId)
        elif loop==1:
            print "Loop onto next script: %(S)s"%{"S":script}
            #    Onto the next script:
            if (len(self._scripts)-1)==self._executing:
                #    Loop
                self._executing = 0
            else:
                self._executing += 1
            startTimeout(timeout, script)
        else:
            #    Stop script execution:
            self.label_executing.setPixmap(self._icons["exec"]["finished"])
            self.pushButton_Run.setEnabled(True)
            self.pushButton_Pause.setEnabled(False)
            self._updateScriptFinished(script)
            self._readOnly = False
            self.emit(Qt.SIGNAL("readOnly()"))
    def _resetScript(self, script, workId):
        #    Reset the script:
        script.reset(workId)
        #    TODO: reset the script in the tree.
    def _expandTree(self):
        value = self._treeIsExpanded
        if value==0:
            self.treeWidget_ScriptActions.collapseAll()
            self.treeWidget_ScriptActions.resizeColumnToContents(0)
        elif value==1:
            self.treeWidget_ScriptActions.expandAll()
            self.treeWidget_ScriptActions.resizeColumnToContents(0)
    def _onExecutionStepped(self, workId, uId, script):
        #    A script config uId is completed, mark it as completed in the tree.
        print "Command stepped...workId: %(W)s, uId: %(U)s, for script: %(S)s"%{"S":script, "W":workId, "U":uId}
        self._updateCommandFinished(script, uId)
        if self._paused==True:
            self._readOnly = False
        self.emit(Qt.SIGNAL("readOnly()"))
    def _onReadOnly(self):
        enabler = not self._readOnly
        for what in [ self.pushButton_Reload,
                      self.pushButton_Clear, 
                      self.pushButton_Reload, 
                      self.pushButton_Save,
                    ]:
            what.setEnabled(enabler)
    def _onExecutionStepping(self, workId, uId, script):
        #    A script config uId is starting to execute, mark it as started in the tree.
        print "Command stepping...workId: %(W)s, uId: %(U)s, for script: %(S)s"%{"S":script, "W":workId, "U":uId}
        for config in script.configs:
            if config["uId"]==uId:
                item = self._findConfig(script, config["uId"])
                self.tb.setStateIcon(item, ExecutionState.RUNNING)
    def _onExecutionStepResult(self, uId, kwargs, script):
        #    Script command result in...
        if script in self._scripts:
            if "result" in kwargs:
                result = kwargs["result"]
                print "Command result...uId: %(U)s, for script: %(S)s:\r\n<%(R)s>"%{"S":script, "U":uId, "R":result}
                for config in script.configs:
                    if config["uId"]==uId:
                        config["_result_"] = result
                        self._updateCommandResult(script, config, result)
                        break
    def _onExecutionStarted(self, workId, script):
        #    Script has begun execution, mark it as started in the tree.
        print "script started: %(S)s"%{"S":script}
        self._updateScriptStarted(script)
    def _onExecutionDelay(self, state, workId, delay, what, uId, script):
        #    Script/Command has begun delay action, mark it as delayed in the tree.
        print "Delay...workId: %(W)s, uId: %(U)s, delay: %(D)s, state: %(ST)s for script: %(S)s"%{"S":script, "W":workId, "U":uId, "D":delay, "ST":state}
        if "script" in what:
            if "pre" in what["script"]:
                item = self._findScriptDelayPre(script)
            else:
                item = self._findScriptDelayPost(script)
            if state==1:
                self.tb.setScriptSleepIcon(item)
            else:
                self.tb.setScriptDelayIcon(item)
        elif "config" in what:
            if "pre" in what["config"]:
                (item, _) = self._findConfigDelayPre(script, uId)
            else:
                (item, _) = self._findConfigDelayPost(script, uId)
            if item!=None:
                if state==1:
                    self.tb.setConfigSleepIcon(item)
                else:
                    self.tb.setConfigDelayIcon(item)















