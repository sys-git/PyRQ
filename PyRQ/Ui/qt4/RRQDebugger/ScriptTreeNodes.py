'''
Created on 26 Oct 2012

@author: francis
'''

from PyQt4 import QtGui
from PyRQ.Ui.qt4.RRQDebugger.ExecutionState import ExecutionState

class _TreeNode(QtGui.QTreeWidgetItem):
    def __init__(self, script, *args, **kwargs):
        super(_TreeNode, self).__init__(*args, **kwargs)
        self._script = script
        self.show()
    def getScript(self):
        return self._script
    def show(self):
        self._defaultBackgroundColour = QtGui.QColor(255, 255, 255)
        print "default colours: ", self._defaultBackgroundColour.red(), self._defaultBackgroundColour.green(), self._defaultBackgroundColour.blue()
    def defaultBackgroundColour(self):
        return self._defaultBackgroundColour
    @classmethod
    def showTreePopup(cls, scripter, node, actions, menu, pos):
        a = []
        isReadOnly = scripter._readOnly
        script = node.getScript()
        a.append(actions["tree_expandAll"])
        a.append(actions["tree_collapseAll"])
        a.append(actions["tree_scrollTop"])
        a.append(actions["tree_scrollBottom"])
        a.append("")
        #    Execute/Pause.
        if script.enabled==False:
            a.append(actions["script_enable"])
        else:
            if (script.state==ExecutionState.PAUSED) or (script.state==ExecutionState.NOT_RUN):
                a.append(actions["script_disable"])
                if (scripter._executing==None) or (scripter._executing==scripter._scripts.index(script)):
                    a.append(actions["script_run"])
            elif script.state==ExecutionState.RUNNING:
                a.append(actions["script_pause"])
        if isReadOnly==False:
            a.append("")
            #    Per-node:
            if isinstance(node, _baseTreeCommandConfig):
                a.append(actions["command_disable"])
                a.append(actions["command_enable"])
                a.append(actions["command_delayPre"])
                a.append(actions["command_delayPost"])
                a.append(actions["command_author"])
            elif isinstance(node, TreeCommandRoot):
                a.append(actions["all_command_disable"])
                a.append(actions["all_command_enable"])
                a.append(actions["all_command_delayPre"])
                a.append(actions["all_command_delayPost"])
                a.append(actions["all_command_author"])
                a.append("")
                a.append(actions["all_command_collapseAll"])
                a.append(actions["all_command_expandAll"])
            elif isinstance(node, TreeScriptDelayPre):
                a.append(actions["script_delayPre"])
                a.append(actions["script_delayPost"])
            elif isinstance(node, _TreeRoot):
                a.append(actions["script_delayPre"])
                a.append(actions["script_delayPost"])
                a.append(actions["script_author"])
            elif isinstance(node, TreeRoot):
                a.append(actions["script_delayPre"])
                a.append(actions["script_delayPost"])
                a.append(actions["script_author"])
                a.append("")
                a.append(actions["script_remove"])
                a.append("")
                a.append(actions["all_script_disable"])
                a.append(actions["all_script_enable"])
                a.append(actions["all_script_delayPre"])
                a.append(actions["all_script_delayPost"])
                a.append(actions["all_script_author"])
        for action in a:
            if isinstance(action, basestring):
                menu.addSeparator()
            else:
                menu.addAction(action)
        result = menu.exec_(pos)
        return (result, node)

class TreeRoot(_TreeNode):
    pass

class _TreeRoot(_TreeNode):
    pass

class TreeScriptAuthor(_TreeRoot):
    pass

class TreeScriptDelayPre(_TreeRoot):
    pass

class TreeScriptDelayPost(_TreeRoot):
    pass

class TreeCommandRoot(_TreeNode):
    pass

class _baseTreeCommand(_TreeNode):
    def __init__(self, script, index, *args, **kwargs):
        super(_baseTreeCommand, self).__init__(script, *args, **kwargs)
        self._index = index
    def getIndex(self):
        return self._index

class _baseTreeCommandConfig(_baseTreeCommand):
    def __init__(self, script, index, config, *args, **kwargs):
        super(_baseTreeCommandConfig, self).__init__(script, index, *args, **kwargs)
        self._config = config
    def getConfig(self):
        return self._config

class TreeCommandDelayPre(_baseTreeCommandConfig):
    pass

class TreeCommandDelayPost(_baseTreeCommandConfig):
    pass

class TreeCommandAuthor(_baseTreeCommandConfig):
    pass

class TreeCommands(_baseTreeCommandConfig):
    pass

class TreeCommandResult(_baseTreeCommandConfig):
    pass

class TreeCommand(_baseTreeCommandConfig):
    pass
