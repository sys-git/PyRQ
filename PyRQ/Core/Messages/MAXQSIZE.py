'''
Created on 18 Sep 2012

@author: francis
'''

class MAXQSIZE(object):
    def __init__(self, size=None):
        self.size = size
    def __str__(self):
        ss = ["MAXQSIZE("]
        if self.size==None:
            ss.append(")")
        else:
            ss.append("size: %(S)s)"%{"S":self.size})
        return "".join(ss)
