'''
Created on 17 Sep 2012

@author: francis
'''

import PyRQ.Core.Errors as Errors

class Linkage(object):
    r"""
    @summary: Automagically obtains the module and name of a type.
    """
    def __init__(self, clazzpath="", clazz=""):
        self._clazzpath = clazzpath
        self._clazz = clazz
    def clazzpath(self):
        return self._clazzpath
    def clazz(self):
        return self._clazz
    def __str__(self):
        return "Linkage: %(CP)s %(C)s"%{"CP":self._clazzpath, "C":self._clazz}
    @staticmethod
    def create(what):
        try:
            mod = what.__module__
            name = what.__name__
            return Linkage(clazzpath=mod, clazz=name)
        except Exception, e:
            raise Errors.LinkageError(e)
