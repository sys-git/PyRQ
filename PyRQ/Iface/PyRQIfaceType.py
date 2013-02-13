'''
Created on 17 Oct 2012

@author: francis
'''

class PyRQIfaceType(object):
    MULTIPROCESSING_QUEUE = 1
    PYRQ = 2
    ENUMERATION_MP_QUEUE = "multiprocessing"
    ENUMERATION_PYRQ_QUEUE = "pyrq"
    @staticmethod
    def enumerate_(value):
        if value==PyRQIfaceType.MULTIPROCESSING_QUEUE:
            return PyRQIfaceType.ENUMERATION_MP_QUEUE
        if value==PyRQIfaceType.PYRQ:
            return PyRQIfaceType.ENUMERATION_PYRQ_QUEUE
