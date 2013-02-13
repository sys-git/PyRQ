'''
Created on 13 Sep 2012

@author: francis
'''

class iQueueServerDetails(object):
    r"""
    @summary: Details of a QueueServer or PyRQ.
    """
    def host(self):
        raise NotImplementedError("iQueueServerDetails.host")
    def port(self):
        raise NotImplementedError("iQueueServerDetails.port")
    def namespace(self):
        raise NotImplementedError("iQueueServerDetails.namespace")
