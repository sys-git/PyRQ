'''
Created on 17 Sep 2012

@author: francis
'''

class Classicname(object):
    def __init__(self, qs):
        self._qs = qs
    def qs(self):
        return self._qs
