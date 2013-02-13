'''
Created on 18 Sep 2012

@author: francis
'''

class CLOSED(object):
    def __init__(self, result=True, namespace=None):
        self.result = result
        self.namespace = namespace
    def __str__(self):
        return "CLOSED(ns=%(NS)s, result=%(R)s)"%{"NS":self.namespace, "R":self.result}
