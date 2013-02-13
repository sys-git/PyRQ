'''
Created on 18 Sep 2012

@author: francis
'''

class GOT(object):
    def __init__(self, data):
        self.data = data
    def __str__(self):
        ss = ["GOT("]
        if self.data==None:
            ss.append(")")
        else:
            try:
                l = len(self.data)
            except Exception, _e:
                ss.append("data; type: %(T)s = %(D)s"%{"T":type(self.data), "D":self.data})
            else:
                ss.append("data; length: %(L)s), type: %(T)s = %(D)s"%{"L":l, "T":type(self.data), "D":self.data})
        return "".join(ss)
