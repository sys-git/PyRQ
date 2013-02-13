'''
Created on 18 Sep 2012

@author: francis
'''

class PyRQError(Exception):
    r"""
    @summary: Unable to communicate with the PyRQ instance.
    Queue already closed.
    Failed to create the queue via the PyRQ in the given timeout.
    Failed to marshall and send data to the PyRQ.
    Any unhandled error whilst communicating with the PyRQ.
    """
    def __str__(self):
        return "PyRQErrors.PyRQError: %(E)s"%{"E":super(PyRQError, self).__str__()}
