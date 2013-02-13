'''
Created on 24 Sep 2012

@author: francis
'''

import unittest
from PyRQ.Core.Utils.PyRQTimeUtils import PyRQTimeUtils

def getTimeOverride():
    return 123

def timeSleepOverride(howLong):
    return howLong

class Test(unittest.TestCase):
    def setUp(self):
        self.t = PyRQTimeUtils
        print "getTime original: ", self.t.getTime()
        print "delayTime original: ", self.t.delayTime(0)
    def tearDown(self):
        pass
    def test(self):
        self.t.set_getTime(getTimeOverride)
        assert self.t.getTime()==123
        self.t.set_delayTime(timeSleepOverride)
        assert self.t.delayTime(1456)==1456

if __name__ == '__main__':
    unittest.main()
