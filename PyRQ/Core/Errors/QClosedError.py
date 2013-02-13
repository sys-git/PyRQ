'''
Created on 12 Sep 2012

@author: francis
'''

class QClosedError(Exception):
    r"""
    @summary: Raised when a PyRQ has closed a queue.
    """
    def __init__(self, result=True, namespace=None):
        super(QClosedError, self).__init__(result)
        self.result = result
        self.namespace = namespace
    def __str__(self):
        return "PyRQErrors.QClosedError[%(NS)s]: %(R)s"%{"NS":self.namespace, "R":self.result}
