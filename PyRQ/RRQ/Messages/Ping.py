'''
Created on 17 Sep 2012

@author: francis
'''

class Ping(object):
    def __init__(self, data=None, replyTo=None, quiet=False):
        self._replyTo = replyTo
        self._data = data
        self._quiet = quiet
    def data(self):
        return self._data
    def replyTo(self):
        return self._replyTo
    def quiet(self):
        return self._quiet
    def __eq__(self, other):
        if isinstance(other, Ping):
            if other.data()==self.data():
                return True
        return False
    def __neq__(self, other):
        return not self.__eq__(other)
