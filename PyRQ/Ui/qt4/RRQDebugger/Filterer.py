'''
Created on 10 Oct 2012

@author: francis
'''
from PyQt4 import QtGui
from PyRQ.Ui.qt4.RRQDebugger.ActionDecoder import ActionDecoder
from PyRQ.Ui.qt4.RRQDebugger.FilterConfig import FiltersConfig
from PyRQ.Ui.qt4.RRQDebugger.FiltererEnablers import Enablers
from Queue import Empty, Full
import copy
import time

class Filterer(object):
    def __init__(self, parent, ref, font=None):
        self.parent = parent
        self.ref = ref
        self.settings = self.parent.debugger.settings
        self.tableName = self.parent.theFilterer.listView_FilteredItems
        self._follow = False
        self.enablers = {}
        self._successfullGetOnly = False
        self.config = FiltersConfig(self.settings, self.ref, font=font)
        for i in dir(Enablers):
            if i.isupper():
                self.enablers[getattr(Enablers, i)] = False
        self.load()
    def follow(self, state):
        self._follow = state
        self._checkFollow()
    def enableAll(self, state):
        for i in self.enablers.keys():
            self.enablers[i] = state
    def enable(self, what, state):
        previousState = self.enablers[what]
        self.enablers[what] = state
        if previousState != self.enablers[what]:
            if state==True:
                self.tableName.clear()
            self._render()
    def successfullGetOnly(self, enabler):
        if enabler!=self._successfullGetOnly:
            self._successfullGetOnly = enabler
            self.tableName.clear()
            self._render()
    def isSuccessfullGetOnly(self):
        return self._successfullGetOnly
    def _getData(self):
        return self.parent.getData()
    def _render(self):
        #   Update the filter window from scratch!
        data = self._getData()
        for i in iter(data):
            (action, args, kwargs) = i
            peer = args[0]
            theTime = args[1]
            timeNow = time.time()
            timeOffset = timeNow - self.parent.startTime
            args = args[2:]
            params = self.parent._extractDecode(action, args, kwargs, decoderParams=copy.deepcopy(ActionDecoder.DEFFAULT_PARAMS__NONE))
            if params["query"]!=None:
                continue
            actionCode = self._getActionCode(action)
            self._doRender(peer, theTime, actionCode, timeOffset, params)
        self._checkFollow()
    def _getActionCode(self, action):
        actions = {
                   "put_start":Enablers.PUT_START,
                   "put_end":Enablers.PUT_END,
                   "get_start":Enablers.GET_START,
                   "get_end":Enablers.GET_END,
                   "create_start":Enablers.CREATE_START,
                   "create_end":Enablers.CREATE_END,
                   "close_start":Enablers.CLOSE_START,
                   "close_end":Enablers.CLOSE_END,
                   "qsize_start":Enablers.QSIZE_START,
                   "qsize_end":Enablers.QSIZE_END,
                   "maxqsize_start":Enablers.MAXQSIZE_START,
                   "maxqsize_end":Enablers.MAXQSIZE_END,
                   }
        return actions.get(action, None)
    def data(self, peer, theTime, action, timeOffset, params):
        self._doRender(peer, theTime, action, timeOffset, params)
        self._checkFollow()
    def _checkFollow(self):
        if self._follow==True:
            self.tableName.scrollToBottom()
    def _doRender(self, peer, theTime, action, timeOffset, params):
        what = self._getActionCode(action)
        if what!=None:
            if self.enablers[what]:
                if what==Enablers.GET_END:
                    if self._successfullGetOnly==True:
                        if isinstance(params["result"], Exception):
                            return
                self._data(peer, theTime, what, timeOffset, params)
    @staticmethod
    def _checkFullEmpty(what):
        if isinstance(what, Empty):
            return "Empty"
        elif isinstance(what, Full):
            return "Full"
        return what
    def _data(self, peer, theTime, action, timeOffset, params):
        #    Render the already-decoded data:
        desc = Filterer.getDesc(peer, theTime, action, timeOffset, params)
        item = QtGui.QListWidgetItem(desc)
        self._colourItem(action, item)
        self.tableName.addItem(item)
    @staticmethod
    def getDesc(peer, theTime, action, timeOffset, params):
        nsId_ = params["nsId"]
        block_ = params["block"]
        timeout_ = params["timeout"]
        result_ = params["result"]
        response_ = params["response"]
        data_ = params["data"]
        uu_ = params["uu"]
        ss = []
        blockTimeout = None
        if block_!=None:
            if block_==True:
                if timeout_!=None:
                    blockTimeout = "(block=True, timeout=%(T)s)"%{"T":timeout_}
                else:
                    blockTimeout = "(block=True)"
            else:
                blockTimeout = "(block=False)"
        if action==Enablers.CREATE_START:
            nsId_ = "?"
        response_ = Filterer._checkFullEmpty(response_)
        result_ = Filterer._checkFullEmpty(result_)
        args = {"PEER":peer, "ACTION":action, "B_T":blockTimeout, "NSID":nsId_, "D":data_, "R":result_, "RS":response_, "TT":theTime, "TO":timeOffset, "UU":uu_}
        ss.append("[%(PEER)s]"%args)
        if nsId_!=None:
            ss.append("[%(NSID)s]"%args)
        if action!=None:
            args["ACTION"] = args["ACTION"].upper()
            ss.append("%(ACTION)s"%args)
#        print "ACTION: %(A)s"%{"A":args["ACTION"]}
        sss = []
        if blockTimeout!=None:
            sss.append("%(B_T)s"%args)
        if (data_!=None) and (data_!=""):
            sss.append("Data: <%(D)s>"%args)
        if (result_!=None) and (result_!=""):
            sss.append("Result: <%(R)s>"%args)
        if (response_!=None) and len(response_)>0 and (response_!=""):
            sss.append("Response: <%(RS)s>"%args)
        if len(sss)>0:
            ss.append("[")
        ss.extend(sss)
        if len(sss)>0:
            ss.append("]")
        ss.append("[ Time: %(TT)s (%(TO)s), UU: %(UU)s ]"%args)
        desc = " - ".join(ss)
#        print "DESC: %(A)s"%{"A":desc}
        return desc
    def _colourItem(self, action, item):
        if self.config!=None:
            #    Background colour:
            c = self.config.backgroundColour(action)
            if c!=None:
                item.setBackgroundColor(c)
            #    Text colour:
            c = self.config.textColour(action)
            if c!=None:
                item.setTextColor(c)
            #    Font:
            c = self.config.font(action)
            if c!=None:
                item.setFont(c)
    def setConfig(self, config):
        self.config = config
        self._render()
    def cloneConfig(self):
        return self.config.clone()
    def dump(self):
        self.config.dump()
    def load(self):
        self.config.load()
    def getConfig(self):
        return self.config.getConfig()





