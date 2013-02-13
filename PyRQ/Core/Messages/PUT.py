'''
Created on 18 Sep 2012

@author: francis
'''

class PUT(object):
    def __init__(self, data, block, timeout):
        self.data = data
        self.block = block
        self.timeout = timeout
    def __str__(self):
        ss = ["PUT("]
        block="False"
        if self.block==True:
            block="True"
        ss.append("block=%(B)s"%{"B":block})
        if self.block==True:
            ss.append(", timeout=%(T)s"%{"T":self.timeout})
        if self.data==None:
            ss.append(", data=NO_DATA")
        else:
            ss.append(", data type: %(T)s"%{"T":type(self.data)})
        return "".join(ss)
