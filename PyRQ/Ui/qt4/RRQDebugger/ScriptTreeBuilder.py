'''
Created on 26 Oct 2012

@author: francis
'''

from PyQt4 import QtGui, QtCore
from PyRQ.Ui.qt4.RRQDebugger.ExecutionState import ExecutionState
from PyRQ.Ui.qt4.RRQDebugger.NoResult import NoResult
from PyRQ.Ui.qt4.RRQDebugger.ScriptTreeNodes import TreeCommand, \
    TreeCommandDelayPost, TreeCommandDelayPre, TreeCommandAuthor, TreeCommands, \
    TreeCommandRoot, TreeScriptDelayPre, TreeScriptDelayPost, TreeScriptAuthor, TreeRoot, \
    TreeCommandResult

class TreeBuilder(object):
    def __init__(self, parent, icons):
        self._parent = parent
        self._icons = icons
    def setEnabledIcon(self, item, isEnabled, col=0):
        item.setIcon(col, self._getEnabledIcon(isEnabled))
    def setStateIcon(self, item, state, col=0):
        item.setIcon(col, self._getStateIcon(state))
    def setResultIcon(self, item, result=None, col=0):
        item.setIcon(col, self._getResultIcon(result))
    def setScriptDelayIcon(self, item):
        item.setIcon(0, self._icons["time"]["delay"])
    def setScriptSleepIcon(self, item):
        item.setIcon(0, self._icons["time"]["sleep"])
    def setConfigDelayIcon(self, item):
        item.setIcon(0, self._icons["time"]["delay"])
    def setConfigSleepIcon(self, item):
        item.setIcon(0, self._icons["time"]["sleep"])
    def setConfigIcon(self, item):
        config = item.getConfig()
        action = config["action"]
        try:
            icon = self._icons["command"][action]
        except Exception, _e:
            icon = self._icons["command"]["generic"]
        item.setIcon(0, icon)
    def setNodeIcon(self, item):
        item.setIcon(0, self._icons["node"])
    def _getStateIcon(self, state):
        return self._icons["state"][state]
    def _getEnabledIcon(self, isEnabled):
        return self._icons["enabled"][isEnabled]
    def _getResultIcon(self, result):
        if isinstance(result, Exception):
            return self._icons["result"]["exc"]
        elif isinstance(result, NoResult):
            return self._icons["result"]["none"]
        return self._icons["result"]["ok"]
    def addCommand(self, script, index, config, parent):
        item = TreeCommand(script, index, config, parent)
        item.setText(0, "Command")
        try:
            desc = config["_desc_"]
        except Exception, _e:
            desc = str(config)
        item.setText(1, desc)
        #    Add the icon
        self.setConfigIcon(item)
        return item
    def addConfigDelayPost(self, script, index, config, parent):
        item = TreeCommandDelayPost(script, index, config, parent)
        item.setText(0, "_delay_post_")
        item.setText(1, str(config["_delay_post_"]))
        item.setIcon(0, self._icons["time"]["delay"])
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def _makeEditable(self, item):
        flags = item.flags()
        flags |= QtCore.Qt.ItemIsEditable
        item.setFlags(flags)
    def addConfigDelayPre(self, script, index, config, parent):
        item = TreeCommandDelayPre(script, index, config, parent)
        item.setText(0, "_delay_pre_")
        item.setText(1, str(config["_delay_pre_"]))
        item.setIcon(0, self._icons["time"]["delay"])
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addConfigSleepPost(self, script, index, config, parent):
        item = TreeCommandDelayPost(script, index, config, parent)
        item.setText(0, "_delay_post_")
        item.setText(1, str(config["_delay_post_"]))
        item.setIcon(0, self._icons["time"]["sleep"])
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addConfigSleepPre(self, script, index, config, parent):
        item = TreeCommandDelayPre(script, index, config, parent)
        item.setText(0, "_delay_pre_")
        item.setText(1, str(config["_delay_pre_"]))
        item.setIcon(0, self._icons["time"]["sleep"])
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addConfigAuthor(self, script, index, config, parent):
        item = TreeCommandAuthor(script, index, config, parent)
        item.setText(0, "Author")
        item.setText(1, str(config["_author_"]))
        item.setIcon(0, self._icons["author"])
        #    Allow the author to be editable:
        self._makeEditable(item)
        return item
    def addConfigs(self, script, index, config, parent):
        item = TreeCommands(script, index, config, parent)
        item.setText(0, "%(I)s"%{"I":index})
        commandState = config["_executing_"]
        enabledState = config["_enabled_"]
        self.setConfigEnabled(item, commandState, enabledState)
        return item
    def addConfigRoot(self, script, parent):
        item = TreeCommandRoot(script, parent)
        item.setText(0, "commands")
        self.setNodeIcon(item)
        return item
    def addScriptDelayPre(self, script, value, parent):
        item = TreeScriptDelayPre(script, parent)
        item.setText(0, "_delay_pre_")
        item.setText(1, value)
        self.setScriptDelayIcon(item)
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addScriptDelayPost(self, script, value, parent):
        item = TreeScriptDelayPost(script, parent)
        item.setText(0, "_delay_post_")
        item.setText(1, value)
        self.setScriptDelayIcon(item)
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addScriptSleepPre(self, script, value, parent):
        item = TreeScriptDelayPre(script, parent)
        item.setText(0, "_delay_pre_")
        item.setText(1, value)
        self.setScriptSleepIcon(item)
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addScriptSleepPost(self, script, value, parent):
        item = TreeScriptDelayPost(script, parent)
        item.setText(0, "_delay_post_")
        item.setText(1, value)
        self.setScriptSleepIcon(item)
        #    Allow the delay to be editable:
        self._makeEditable(item)
        return item
    def addScriptAuthor(self, script, parent):
        item = TreeScriptAuthor(script, parent)
        item.setText(0, "Author")
        item.setText(1, str(script.author))
        item.setIcon(0, self._icons["author"])
        #    Allow the author to be editable:
        self._makeEditable(item)
        return item
    def addScriptRoot(self, script, parent=None):
        if parent==None:
            parent = self._parent
        name = script.getName()
        item = TreeRoot(script, parent)
        item.setText(0, name)
        self.setScriptEnabled(script, item)
        return item
    def setScriptEnabled(self, script, item):
        isEnabled = script.enabled
        isFinished = script.isFinished()
        state = script.state
        if isEnabled==False:
            self.setEnabledIcon(item, isEnabled)
            #    Set the background colour for the script to grey.
            colour = QtGui.QColor(200, 200, 200)
            item.setBackgroundColor(0, colour)
            item.setBackgroundColor(1, colour)
        else:
            if isFinished==True:
                self.setStateIcon(item, ExecutionState.FINISHED)
            else:
                self.setStateIcon(item, state)
            #    Set the background colour for the script to default.
            colour = item.defaultBackgroundColour()
            item.setBackgroundColor(0, colour)
            item.setBackgroundColor(1, colour)
    def setConfigEnabled(self, item, commandState, enabledState):
        if enabledState==True:
            self.setStateIcon(item, commandState)
            #    Set the background colour for the script to default.
            colour = item.defaultBackgroundColour()
            item.setBackgroundColor(0, colour)
            item.setBackgroundColor(1, colour)
        else:
            self.setEnabledIcon(item, enabledState)
            #    Set the background colour for the script to grey.
            colour = QtGui.QColor(200, 200, 200)
            item.setBackgroundColor(0, colour)
            item.setBackgroundColor(1, colour)
    def addConfigResult(self, script, index, config, parent):
        item = TreeCommandResult(script, index, config, parent)
        item.setText(0, "Result")
        try:
            result = config["_result_"]
        except Exception, result:
            print "ERROR - No result found!!!"
        item.setText(1, str(result))
        self.setResultIcon(item, result)
        return item
