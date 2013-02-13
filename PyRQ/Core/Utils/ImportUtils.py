'''
Created on 20 Sep 2012

@author: francis
'''

def _importModule(where, what):
    _module = __import__(where, globals(), locals(), [what], -1)
    _type = getattr(_module, what)
    return _type

def _getClass(kls):
    parts = kls.split('.')
    module_ = ".".join(parts[:-1])
    m = __import__(module_)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

def _importModuleName(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
