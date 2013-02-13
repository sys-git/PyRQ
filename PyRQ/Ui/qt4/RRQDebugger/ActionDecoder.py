'''
Created on 15 Oct 2012

@author: francis
'''

from PyRQ.RRQ.Debugger.iRRQDebuggerSink import iRRQDebuggerSink
from PyRQ.RRQ.RRQType import RRQType
import copy

class ActionDecoder(object):
    DEFFAULT_PARAMS__STRINGS = {
                  "namespace":"",
                  "block":"",
                  "timeout":"",
                  "response":"",
                  "result":"",
                  "uu":"",
                  "data":"",
                  "query":None,
                  "namespace_unknown":None,
                                }
    DEFFAULT_PARAMS__NONE = {
                  "namespace":None,
                  "block":None,
                  "timeout":None,
                  "response":None,
                  "result":None,
                  "uu":None,
                  "data":None,
                  "query":None,
                  "namespace_unknown":None,
                                }
    @staticmethod
    def decode(action, args, kwargs, params=None):
        if params==None:
            params = copy.deepcopy(ActionDecoder.DEFFAULT_PARAMS__STRINGS)
        params["uu"] = kwargs.get("uu", "")
        if action in iRRQDebuggerSink._getMethods():
            if action=="handle_end":
                params["response"] = args[0]
            elif action=="create_start":
                queueType = "list(synchronized)"
                if args[0]==RRQType.MULTIPROCESSING_QUEUE:
                    queueType = "multiprocessing.Queue"
                params["data"] = "QueueType: %(QT)s, maxSize: %(MS)s, pollingInterval: %(PI)s"%{"QT":queueType, "MS":args[1], "PI":args[2]}
                params["namespace_unknown"] = "?"
            elif action=="create_end":
                params["namespace"] = args[0]
            elif action=="addClient_start":
                params["namespace"] = args[0]
            elif action=="put_start":
                params["namespace"] = args[0]
                params["block"] = args[1]
                params["timeout"] = args[2]
                params["data"] = args[3]
            elif action=="put_end":
                params["namespace"] = args[0]
                params["result"] = args[1]
            elif action=="get_start":
                params["namespace"] = args[0]
                params["block"] = args[1]
                params["timeout"] = args[2]
            elif action=="get_end":
                params["namespace"] = args[0]
                params["result"] = args[1]
            elif action=="close_start":
                params["namespace"] = args[0]
            elif action=="close_end":
                params["namespace"] = args[0]
            elif action=="closeClients_start":
                params["namespace"] = args[0]
            elif action=="qsize_start":
                params["namespace"] = args[0]
            elif action=="qsize_end":
                params["namespace"] = args[0]
                params["result"] = args[1]
            elif action=="maxqsize_start":
                params["namespace"] = args[0]
            elif action=="maxqsize_end":
                params["namespace"] = args[0]
                params["result"] = args[1]
            elif action=="delay_start":
                params["where"] = args[0]
                params["duration"] = args[1]
            elif action=="query":
                namespaces = args[0]
                staleNamespaces = args[1]
                params["query"] = (namespaces, staleNamespaces)
        return params
