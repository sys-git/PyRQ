'''
Created on 13 Sep 2012

@author: francis
'''

from PyRQ.Core.Errors.AlreadyStartedError import AlreadyStartedError
from PyRQ.Core.Errors.ConfigurationError import ConfigurationError
from PyRQ.Core.Errors.CorruptDataReceived import CorruptDataReceived
from PyRQ.Core.Errors.Finished import Finished
from PyRQ.Core.Errors.LinkageError import LinkageError
from PyRQ.Core.Errors.LostDataReceived import LostDataReceived
from PyRQ.Core.Errors.NoSuchQueue import NoSuchQueue
from PyRQ.Core.Errors.PyRQError import PyRQError
from PyRQ.Core.Errors.TooManyClientsError import TooManyClientsError
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
import sys
import unittest

class Test(unittest.TestCase):
    def setUp(self, quiet=True, eResult="hello.world", corruption="blah!"):
        self.eResult = eResult
        self.corruption = corruption
        self.quiet = quiet
        self.dm = MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=self.quiet)
        self.data = self.dm._package(self.eResult)
        if not self.quiet: sys.stderr.write("data: %(D)s"%{"D":self.data})
    def tearDown(self):
        pass
    def testDecode(self):
        t = self.dm._decode(self.data)
        if not self.quiet: sys.stderr.write("start: %(S)s, end: %(E)s"%{"S":t[0], "E": t[1]})
        if not self.quiet: sys.stderr.write("testDecode Finished\r\n")
    def testPackageReceiveRoundTripAllInOne(self):
        c = 0
        for t in self.dm.receive(self.data):
            if not self.quiet: sys.stderr.write("decoded: <%(T)s>"%{"T":t})
            assert t==self.eResult
            c += 1
        assert c==1
        assert len(self.dm._buffer)==0
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripAllInOne Finished\r\n")
    def testPackageReceiveRoundTripInMultipleChunksWithCorruptHeader(self):
        max_ = len(self.dm.SIZE) + len(self.dm.DATA) + self.dm.PADDING_SIZE + 2
        data = "".join([self.data[:5], self.corruption, self.data[5+len(self.corruption):max_]])
        c = 0
        for d in data:
            try:
                c += 1
                for t in self.dm.receive(d):
                    if not self.quiet: sys.stderr.write("decoded: <%(T)s>"%{"T":t})
                    assert t==self.eResult
            except CorruptDataReceived, _e:
                if not self.quiet: sys.stderr.write("found corrupt header!")
                assert c==max_
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripInMultipleChunksWithCorruptHeader Finished\r\n")
    def testPackageReceiveRoundTripInSingleBytes(self):
        c = 0
        for d in self.data:
            for t in self.dm.receive(d):
                if not self.quiet: sys.stderr.write("decoded: <%(T)s>"%{"T":t})
                assert t==self.eResult
                c += 1
        assert c==1
        assert len(self.dm._buffer)==0
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripInSingleBytes Finished\r\n")
    def testPackageReceiveRoundTripCorruptHeaderReceived(self):
        max_ = len(self.dm.SIZE) + len(self.dm.DATA) + self.dm.PADDING_SIZE + 2
        data = "".join([self.data[:5], self.corruption, self.data[5+len(self.corruption):(max_-1)]])
        try:
            self.dm.receive(data).next()
        except StopIteration:
            assert True
        else:
            assert False
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripCorruptHeaderReceived Finished\r\n")
    def testPackageReceiveRoundTripHeaderOnlyReceived(self):
        max_ = len(self.dm.SIZE) + len(self.dm.DATA) + self.dm.PADDING_SIZE + 2
        data = "".join([self.data[:5], self.corruption, self.data[5+len(self.corruption):max_]])
        try:
            self.dm.receive(data).next()
        except CorruptDataReceived, e:
            f = e.data()
            assert f==data
        else:
            assert False
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripHeaderOnlyReceived Finished\r\n")
    def testPackageReceiveRoundTripCorruptUnexpectedOffsetHeaderReceived(self):
        data = "".join([self.corruption, self.data])
        try:
            self.dm.receive(data).next()
        except LostDataReceived, e:
            assert e.data()==self.corruption
        else:
            assert False
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripCorruptUnexpectedOffsetHeaderReceived Finished\r\n")
    def testPackageReceiveRoundTripUnexpectedOffsetHeaderReceivedThenValidData(self):
        data = "".join([self.corruption, self.data])
        try:
            self.dm.receive(data).next()
        except LostDataReceived, e:
            assert e.data()==self.corruption
        else:
            assert False
        assert len(self.dm._buffer)==len(self.data)
        #    Get the next data:
        count = 0
        for t in self.dm.receive(""):
            assert t==self.eResult
            count += 1
        assert count==1
        assert len(self.dm._buffer)==0
        if not self.quiet: sys.stderr.write("testPackageReceiveRoundTripUnexpectedOffsetHeaderReceivedThenValidData Finished\r\n")

if __name__ == '__main__':
    unittest.main()
