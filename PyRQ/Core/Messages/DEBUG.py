'''
Created on 18 Sep 2012

@author: francis
'''

class DEBUG(object):    pass

class DEBUG_START(DEBUG):
    def __init__(self, filename=None, server=None):
        self.filename = filename
        self.server = server

class DEBUG_STOP(DEBUG):    pass

class DEBUG_SOMETHING(DEBUG):    pass

class DEBUG_QUERY(DEBUG): pass

class UnknownDebuggerCommand(Exception):    pass
