'''
Created on 18 Sep 2012

@author: francis
'''

class ACK(object):
    def __init__(self, namespace):
        self.namespace = namespace
    def __str__(self):
        return "ACK(%(NS)s)"%{"NS":self.namespace}
