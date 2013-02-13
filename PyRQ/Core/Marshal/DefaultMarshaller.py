'''
Created on 12 Sep 2012

@author: francis
'''
from PyRQ.Core.Marshal.iMarshaller import iMarshaller
import PyRQ.Core.Errors as Errors
import pickle
import sys
import traceback
from PyRQ.Core.Marshal.OversizedDataError import OversizedDataError

class DefaultMarshaller(iMarshaller):
    r"""
    @summary: Marshals data using a simple string: HEADER+SIZE+DATA package.
    """
    DATA = "raw_data"
    SIZE = "size:"
    PADDING_SIZE = 64
    def __init__(self, type_, quiet=True, maxsize=None):
        self._type = type_
        self._quiet = quiet
        self._buffer = ""
        self._maxSize = maxsize
#        sys.stderr.write("DefaultMarshaller is quiet: %(Q)s\r\n"%{"Q":quiet})
    def type_(self):
        return self._type
    def package(self, data, **kwargs):
        maxsize = kwargs.get("maxsize", self._maxSize)
        tx = DefaultMarshaller._package(data, maxsize=maxsize)
        return tx
    @staticmethod
    def _package(data, maxsize=None):
        d = pickle.dumps(data)
        if (maxsize!=None) and (len(d)>maxsize):
            raise OversizedDataError(len(d), maxsize)
        basesize =  len(d)
        basesize += len(DefaultMarshaller.SIZE)
        basesize += len(DefaultMarshaller.DATA)
        basesize += DefaultMarshaller.PADDING_SIZE
        basesize += 2   #    2 dot-seperators.
        s = "%d"%basesize
        s = s.rjust(64, " ")
        size = "".join([DefaultMarshaller.SIZE, s])
        tx = ".".join([DefaultMarshaller.DATA, size, d])
        return tx
    def receive(self, data):
        #    Keep yielding packaged data until none left.
        if not self._quiet:
            sys.stderr.write("\r\nReceived <%(S)s>\r\nbuffer: <%(D)s>.\r\n"%{"D":self._buffer, "S":data})
        self._buffer += data
        if not self._quiet:
            sys.stderr.write("\r\nReceived...new buffer: <%(D)s>.\r\n"%{"D":self._buffer})
        while len(self._buffer)>0:
            #    Search the buffer for whole packages:
            if not self._quiet: sys.stderr.write("\r\nSearching for <%(S)s> in <%(D)s>.\r\n"%{"D":self._buffer, "S":DefaultMarshaller.DATA})
            index = self._buffer.find(DefaultMarshaller.DATA)
            b1 = len(self._buffer)
            b2 = len(DefaultMarshaller.SIZE)
            b2 += len(DefaultMarshaller.DATA)
            b2 += DefaultMarshaller.PADDING_SIZE
            b2 += 2   #    2 dot-seperators.
            if (index==-1) and (b1>=b2):
                if not self._quiet: sys.stderr.write("\r\nCorrupt data received[0]\r\n")
                raise Errors.CorruptDataReceived(self._buffer[:])
            if index>0:
                if not self._quiet: sys.stderr.write("\r\nCorrupt data received[1], header found at index: %(I)s\r\n"%{"I":index})
                lostData = self._buffer[:index]
                #    Clear out the junk:
                self._buffer = self._buffer[index:]
                #    Now the user has the option to continue attempting to read or stop using the queue.
                raise Errors.LostDataReceived(lostData)
            if index!=-1:
                constraints = DefaultMarshaller._decode(self._buffer, index=index, quiet=self._quiet)
                if constraints:
                    (startIndex, endIndex) = constraints
                    payload = self._buffer[startIndex:endIndex]
                    self._buffer = self._buffer[endIndex:]
                    if not self._quiet: sys.stderr.write("\r\nremaining buffer size post unpackage: %s\r\n"%len(self._buffer))
                    try:
                        result = pickle.loads(payload)
                    except Exception, _e:
                        if not self._quiet: sys.stderr.write("\r\npickle exception: <%(S)s>\r\n"%{"S":traceback.format_exc()})
                        if not self._quiet: sys.stderr.write("\r\npickle exception data: <%(S)s>\r\n"%{"S":payload})
                    else:
                        if not self._quiet: sys.stderr.write("\r\npickle result: <%(S)s>\r\n"%{"S":result})
                        yield result
            #    Not enough data for a package yet:
            raise StopIteration()
        #    If not more packages:
        raise StopIteration()
    @staticmethod
    def _decode(buff, index=None, quiet=True):
        if index==None:
            index = buff.find(DefaultMarshaller.DATA)
        l = len(DefaultMarshaller.DATA)+len(DefaultMarshaller.SIZE)+1
        ll = len(buff)
        if ll>=(index+l+64):
            length = buff[(index+l):(index+l+64)]
            length = length.strip()
            length = int(length)
            if ll>=length:
                if not quiet: sys.stderr.write("Package contains %(N)s bytes in total\r\n"%{"N":length})
                #    Buffer contains at least one package, in theory!
                #    So return the start and end index of the actual data (should be a constant for now).
                startIndex = index
                startIndex += len(DefaultMarshaller.DATA)
                startIndex += len(DefaultMarshaller.SIZE)
                startIndex += DefaultMarshaller.PADDING_SIZE
                startIndex += 2   #    2 dot-seperators.
                endIndex =  index
                endIndex += length
                if not quiet: sys.stderr.write("Found start: %(S)s and end: %(E)s\r\n"%{"S":startIndex, "E":endIndex})
                return (startIndex, endIndex)

