'''
Created on 12 Sep 2012

@author: francis
'''

class ClosedError(Exception):
    r"""
    @summary: Raised when the PyRQ has closed.
    """
    def __init__(self, result=True, namespace=None):
        super(ClosedError, self).__init__(result)
        self.result = result
        self.namespace = namespace
    def __str__(self):
        return "PyRQErrors.ClosedError[%(NS)s]: %(R)s"%{"NS":self.namespace, "R":self.result}
