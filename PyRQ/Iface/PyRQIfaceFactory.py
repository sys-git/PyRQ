'''
Created on 17 Oct 2012

@author: francis
'''

from PyRQ.Iface.PyRQIface import PyRQIface
from PyRQ.Iface.PyRQIfaceType import PyRQIfaceType
from PyRQ.Iface.QIface import QIface
from PyRQ.Iface.UnknownInterfaceError import UnknownInterfaceError

class PyRQIfaceFactory(object):
    @staticmethod
    def get(type_, *args, **kwargs):
        if type_==PyRQIfaceType.PYRQ:
            return PyRQIface(*args, **kwargs)
        elif type_==PyRQIfaceType.MULTIPROCESSING_QUEUE:
            return QIface(*args, **kwargs)
        raise UnknownInterfaceError(type_)
