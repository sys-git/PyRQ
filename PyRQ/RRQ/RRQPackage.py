'''
Created on 18 Sep 2012

@author: francis
'''

class RRQPackage(object):
    r"""
    Encapsulates data sent from the PyRQIface to the PyRQ.
    """
    def __init__(self, namespace, data):
        self.namespace = namespace
        self.data = data
