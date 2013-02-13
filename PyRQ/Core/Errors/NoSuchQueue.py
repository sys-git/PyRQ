'''
Created on 18 Sep 2012

@author: francis
'''

class NoSuchQueue(Exception):
    r"""
    @summary: The queue's namespace does not exist and has never existed.
    """
    def __init__(self, namespace):
        super(NoSuchQueue, self).__init__(namespace)
        self.namespace = namespace
    def __str__(self):
        return "PyRQErrors.NoSuchQueue: %(NS)s"%{"NS":self.namespace}
