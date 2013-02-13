'''
Created on 18 Sep 2012

@author: francis
'''

class GET(object):
    def __init__(self, block=True, timeout=None):
        self.block = block
        self.timeout = timeout
    def __str__(self):
        ss = ["GET("]
        block="False"
        if self.block==True:
            block="True"
        ss.append("block=%(B)s"%{"B":block})
        if self.block==True:
            ss.append(", timeout=%(T)s"%{"T":self.timeout})
        return "".join(ss)
