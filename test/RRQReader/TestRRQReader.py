'''
Created on 18 Sep 2012

@author: francis
'''

from Mock.mock import TimeoutMockHandler, MockHandler
from PyRQ.Core.Errors.ClosedError import ClosedError
from PyRQ.Core.Errors.NoSuchQueue import NoSuchQueue
from PyRQ.Core.Errors.PyRQError import PyRQError
from PyRQ.Core.Linkage.Linkage import Linkage
from PyRQ.Core.Marshal.MarshallerFactory import MarshallerFactory
from PyRQ.Core.QueueServer.SubprocessQueueServer import SubprocessQueueServer
from PyRQ.Core.Utils.ImportUtils import _importModuleName
from PyRQ.Core.Utils.PyRQTimeUtils import PyRQTimeUtils
from PyRQ.Iface.PyRQIface import PyRQIface
from Queue import Empty, Full
from multiprocessing.queues import Queue
from multiprocessing.synchronize import RLock, Lock, Semaphore
from random import Random
import copy
import threading
import time
import traceback
import unittest

MultipleItems = 10
MultipleGetters = 10
MultiplePutters = 10

try:
    import logging
    testLoggingModule = logging
except:
    testLoggingModule = _importModuleName("PyRQ.logger.logging")

class _BaseReader(unittest.TestCase):
    HAMMER_TIME = 10
    def _getLogger(self):
        loggingModule = testLoggingModule
        logger = loggingModule.getLogger("TEST")
        loggingLevel = loggingModule.DEBUG
        self.loggingLevel = loggingLevel
        logger.setLevel(loggingLevel)
        try:
            #    Remove existing logger handlers:
            for handler in logger.handlers[:]:
                try:    logger.removeHandler(handler)
                except: pass
        except:
            pass
        self.loggerHandler = loggingModule.StreamHandler()
        self.loggerHandler.setLevel(loggingLevel)
        formatter = loggingModule.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.loggerHandler.setFormatter(formatter)
        logger.addHandler(self.loggerHandler)
        return logger
    def _teardownLoggers(self):
        try:    del self.logger
        except: pass
        try:    self.loggerHandler.close()
        except: pass
        try:    self.logger.removeHandler(self.loggerHandler)
        except: pass
        try:    del self.loggerHandler
        except: pass

class TestRRQReader(_BaseReader):
    def setUp(self):
        self.logger = self._getLogger()
        self.quiet = True
        self._queues = []
        self.random = Random()
        self.timerTerminate = 0
        self._timers = []
        self.namespaces = []
        self.iface = PyRQIface(quiet=self.quiet, ref="default", loggingModule=testLoggingModule)
        self.dummyQueue = Queue()
        self.marshaller = MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=self.quiet)
        desiredPort = "19001"
        self.r = SubprocessQueueServer(
                                       desiredPort=desiredPort,
                                       quiet=self.quiet,
                                       handlerClazz=Linkage.create(MockHandler),
#           includePydevd="/home/francis/.eclipse/org.eclipse.platform_3.7.0_155965261/plugins/org.python.pydev.debug_2.5.0.2012040618/pysrc"
           )
        PyRQIface.setGlobalPYRQ(self.r.details())
        self.r.start().waitUntilRunning()
        pass
    def tearDown(self):
        self.logger.info("------------ TEST END ------------")
        self.timerTerminate = 1
        time.sleep(2)
        try:
            self.dummyQueue.close()
            del self.dummyQueue
        except Exception, _e:
            pass
        for namespace in self.namespaces:
            self.iface.setNamespace(namespace)
        try:    self.iface.close()
        except ClosedError, _e:
            pass
        try:    self.r.close()
        except: pass
        for i in self._timers:
            try:    i.cancel()
            except: pass
        for i in self._queues:
            try:
                i.close()
                del i
            except Exception, _e:
                pass
        self._teardownLoggers()
    def _createInterface(self, maxsize=0):
        namespace = self.iface.create(maxsize=maxsize)
        self.namespaces.append(namespace)
        self.iface.setNamespace(namespace)
        return namespace
    def testCreate(self, maxsize=0):
        #    Create a new queue and get it's namespace:
        self.namespace = self.iface.create(maxsize=maxsize)
    def testParallelGets_MultiplePuttersMultipleGettersMultipleItems(self, count=10):
        self.testParallelGets_MultiplePuttersMultipleGettersOneItem(count=count)
    def testParallelGets_MultiplePuttersSingleGetterMultipleItems(self, count=10):
        self.testParallelGets_MultiplePuttersSingleGetterOneItem(count=count)
    def testParallelGets_SinglePutterMultipleGettersMultipleItems(self, count=10):
        self.testParallelGets_SinglePutterMultipleGettersOneItem(count=count)
    def testParallelGets_SinglePutterOneGetterMultipleItems(self, count=10):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count)
    def testParallelGets_MultiplePuttersMultipleGettersOneItem(self, count=1, numGetters=MultipleGetters, numPutters=MultiplePutters):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count, numGetters=numGetters, numPutters=numPutters)
    def testParallelGets_MultiplePuttersSingleGetterOneItem(self, count=1, numGetters=1, numPutters=MultiplePutters):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count, numGetters=numGetters, numPutters=numPutters)
    def testParallelGets_SinglePutterMultipleGettersOneItem(self, count=1, numGetters=MultipleGetters, numPutters=1):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count, numGetters=numGetters, numPutters=numPutters)
    def testParallelGets_SinglePutterOneGetterOneItem(self, numGetters=1, numPutters=1, count=1, getTimeout=1, putTimeout=1):
        self.testCreate()
        self.logger.info("------------ TEST START ------------")
        self._createInterface()
        eGets = []
        ePuts = []
        dataQ = Queue()
        glock = RLock()
        plock = RLock()
        putters = Semaphore(0)
        allPutData = []
        self._queues.append(eGets)
        self._queues.append(dataQ)
        initialDelay = 1
        numData = (numPutters*count)
        getterThreads = []
        def doGet(initialDelay, ref, getTimeout):
            time.sleep(initialDelay)
            self.logger.debug("GET %(R)s START"%{"R":ref})
            iface = PyRQIface(namespace=self.namespace, quiet=self.quiet, ref="get.%(R)s"%{"R":ref}, loggingModule=testLoggingModule)
            while self.timerTerminate==0:
                try:
                    data = iface.get(block=True, timeout=min(1, min(1, getTimeout)))
                except Empty, data:
                    continue
                except Exception, _e:
#                    self.logger.error("GET %(R)s EXCEPTION: %(E)s"%{"R":ref, "E":_e})
                    continue
                else:
                    with glock:
                        eGets.append(data)
                        allPutData.remove(data)
                        self.logger.info("GET %(R)s now."%{"R":len(eGets)})
                        if len(eGets)==numData:
                            self.logger.info("GET ALL DONE")
                            break
                    self.logger.debug("GET %(R)s got: %(E)s from: %(W)s"%{"R":ref, "E":data, "W":iface.getLastSockDetails()})
                time.sleep(1)
            self.logger.debug("GET %(R)s COMPLETE from: %(W)s"%{"R":ref, "W":iface.getLastSockDetails()})
        for i in xrange(numGetters):
            t = threading.Thread(target=doGet, args=[initialDelay, i, getTimeout])
            t.setDaemon(True)
            t.setName("Parallel_GET_%(C)s"%{"C":i})
            self._timers.append(t)
            getterThreads.append(t)
            t.start()
        #    Now pump the data into the queues over time:
        initialDelay = 1
        def doPut(initialDelay, ref, putTimeout, dataQ):
            time.sleep(initialDelay)
            self.logger.debug("PUT %(R)s START"%{"R":ref})
            iface = PyRQIface(namespace=self.namespace, quiet=self.quiet, ref="put.%(R)s"%{"R":ref}, loggingModule=testLoggingModule)
            while self.timerTerminate==0:
                try:
                    (delay, eData) = dataQ.get(block=True, timeout=1)
                except Empty, _e:
                    self.logger.error("PUT %(R)s no data, finished!"%{"R":ref})
                    break
                except Exception, _e:
                    self.logger.error("PUT %(R)s ERROR Incorrect test vector: %(T)s!"%{"R":ref, "T":traceback.format_exc()})
                    break
                else:
                    if delay>0:
                        time.sleep(delay)
                    self.logger.debug("PUT %(R)s putting: %(D)s"%{"R":ref, "D":eData})
                    try:
                        iface.put(data=eData, timeout=putTimeout)
                    except Exception, e:
                        self.logger.error("PUT %(R)s ERROR Failed: %(E)s from: %(W)s."%{"R":ref, "E":e, "W":iface.getLastSockDetails()})
                    else: 
                        self.logger.debug("PUT %(R)s OK from: %(W)s. "%{"R":ref, "W":iface.getLastSockDetails()})
                    with plock:
                        ePuts.append(eData)
                        self.logger.info("PUT %(R)s now: %(RR)s."%{"R":ref, "RR":len(ePuts)})
            self.logger.error("PUT %(R)s COMPLETE."%{"R":ref})
            putters.release()
        #    Now create the data:
        for k in xrange(0, numData):
            J = k+1
            delay = self.random.random()
            eData = "hello.world...%(C)s"%{"C":J}
            allPutData.append(eData)
            dataQ.put((delay, eData))
        self.logger.debug("DATA contains %(D)s items...\r\n"%{"D":numData})
        while dataQ.qsize()!=numData:
            PyRQTimeUtils.delayTime(1)
        putterThreads = []
        for i in xrange(0, numPutters):
            k = i+1
            t = threading.Thread(target=doPut, args=[initialDelay, k, putTimeout, dataQ])
            t.setDaemon(True)
            t.setName("Parallel_PUT_%(C)s"%{"C":k})
            self._timers.append(t)
            t.start()
            putterThreads.append(t)
        for k in xrange(0, numPutters):
            putters.acquire()
        #    Now wait for all the data to be received:
        maxPutDelay = (1+(count*numGetters*1))*2
        self.logger.info("Now waiting for all data to be put and got for MAX: %(T)s seconds..."%{"T":maxPutDelay})
        gotData = []
        putData = []
        complete = False
        for x in putterThreads:
            x.join()
        self.logger.info("~~~~~~~ All putters finished")
        while True:
            self.logger.info("~~~~~~~ len(eGets):  %(T)s"%{"T":len(eGets)})
            with glock:
                self.logger.info("~~~~~~~ waiting for:  %(T)s"%{"T":allPutData})
                if len(eGets)==numData:
                    #    Finished getting data.
                    self.timerTerminate=1
                    complete = True
                    putData = copy.deepcopy(ePuts)
                    gotData = copy.deepcopy(eGets)
                    break
            time.sleep(1)
        assert complete
        self.timerTerminate=1
        for x in getterThreads:
            x.join()
        #    Now check all the put data (we still have the lock):
        self.logger.info("numData:  %(T)s"%{"T":numData})
        self.logger.info("len(PUT): %(T)s"%{"T":len(putData)})
        self.logger.info("len(GOT): %(T)s"%{"T":len(gotData)})
        self.timerTerminate = 1
        assert len(gotData)==numData
        #    Now check the data:
        for data in putData:
            assert data in gotData
        #    Was all the get data PUT?
        for data in gotData:
            assert data in putData
        self.logger.info("Now waiting for all threads to finish")
    def testNonBlockingGet(self):
        self.namespace = self._createInterface()
        iface = PyRQIface(ref="testNonBlockingGet", namespace=self.namespace, quiet=self.quiet, loggingModule=testLoggingModule)
        try:
            _data = iface.get(block=False, timeout=None)
        except Empty, _e:
            assert True
        else:
            self.logger.error("Received data in error: %(D)s\r\n"%{"D":_data})
            assert False
    def testCreateHammer(self, iterations=None):
        if iterations==None:
            iterations = _BaseReader.HAMMER_TIME
        #    Create a new queue and get it's namespace:
        for _ in xrange(1, iterations):
            namespace = self.iface.create()
            assert namespace not in self.namespaces
            self.namespaces.append(namespace)
            assert isinstance(namespace, basestring)
    def testCloseNoConnections(self):
        self.testCreate()
        self.iface.close()
    def testPostCloseSameIface(self, eData="hello.world!", block=True, timeout=None):
        self.testCreate()
        self.iface.close()
        #    Now attempt a PUT:
        try:
            self.iface.put(eData, block=block, timeout=timeout)
        except ClosedError, _e:
            assert True
        else:
            assert False
        #    Now attempt a GET:
        try:
            self.iface.get(block=block, timeout=timeout)
        except ClosedError, _e:
            assert True
        else:
            assert False
    def testPostCloseDifferentIface(self, eData="hello.world!", block=True, timeout=None):
        self.testCreate()
        self.iface.close(timeout=100000)
        #    Now attempt a PUT:
        iface = PyRQIface(ref="testPostCloseDifferentIface.0", namespace=self.namespace, quiet=self.quiet, loggingModule=testLoggingModule)
        try:
            iface.put(eData, block=block, timeout=timeout)
        except ClosedError, _e:
            assert True
        else:
            assert False
        finally:
            try:    iface.close()
            except: pass
        #    Now attempt a GET:
        iface = PyRQIface(ref="testPostCloseDifferentIface.1", namespace=self.namespace, quiet=self.quiet, loggingModule=testLoggingModule)
        try:
            iface.get(block=block, timeout=timeout)
        except ClosedError, _e:
            assert True
        else:
            assert False
        finally:
            try:    iface.close()
            except: pass
    def testCloseDuringGet(self):
        self.testCreate()
        def close(namespace):
            iface = PyRQIface(ref="testCloseDuringGet", namespace=namespace, quiet=self.quiet, loggingModule=testLoggingModule)
            iface.close()
        threading.Timer(0, close, args=[self.namespace]).start()
        try:
            self.iface.get(block=True, timeout=None)
        except ClosedError, _e:
            assert True
        except Exception, _e:
            pass
        else:
            assert False
    def testPutInvalidNamespace(self):
        #    Put some data into an invalid queue.
        self.testCreate()
        namespace = self.iface.create()
        self.namespaces.append(namespace)
        eQUId = namespace+"123"
        self.iface.setNamespace(eQUId)
        eData="hello world!"
        block=True
        timeout=None
        try:
            self.iface.put(eData, block, timeout)
        except NoSuchQueue, e:
            #    namespace does not exist, this should fail.
            assert e.namespace==eQUId
        else:
            assert False
    def testPut(self, eData="hello world!", noCheck=False, block=True, timeout=None):
        #    Put some data into the given queue.
        self.testCreate()
        self._createInterface()
        (eData, _block, _timeout) = self._checkPut(eData=eData, block=block, timeout=timeout)
        return (eData, _block, _timeout)
    def _checkPut(self, eData="hello world!", block=True, timeout=None):
        self.iface.put(eData, block=block, timeout=timeout)
        assert True
        return (eData, block, timeout)
    def testPutHammer(self, iterations=None, block=True, timeout=None):
        if iterations==None:
            iterations = _BaseReader.HAMMER_TIME
        self.testCreate()
        self._createInterface()
        exData = []
        for iteration in xrange(0, iterations):
            data = "iteration_%(I)s"%{"I":iteration}
            (eData, _block, _timeout) = self._checkPut(eData=data, block=block, timeout=timeout)
            exData.append(eData)
    def testGet(self, block=True, timeout=None):
        #    Put some data onto the given queue and retrieve it.
        (eData, _block, _timeout) = self.testPut(noCheck=True)
        data = self._doGet(block=block, timeout=timeout)
        assert data==eData
    def _doGet(self, block=True, timeout=None):
        data = self.iface.get(block=block, timeout=timeout)
        return data
    def testMaxQSizeDefault(self, maxsize=0, timeout=None):
        self.testCreate(maxsize=maxsize)
        #    Retrieve the size of the queue.
        qSize = self.iface.maxQSize(timeout=timeout)
        assert qSize==0
    def testMaxQSizeNonDefault(self, maxsize=10, timeout=None):
        self.testCreate(maxsize=maxsize)
        #    Retrieve the size of the queue.
        qSize = self.iface.maxQSize(timeout=timeout)
        assert qSize==maxsize
    def testQSizeDefault(self, maxsize=0, timeout=None):
        r"""
        @attention: All we can test is that the call completes without error,
        the exact return value of the call is untestable.
        @see: multiprocessing.Queue.qsize().
        """
        self.testCreate(maxsize=maxsize)
        #    Retrieve the size of the queue.
        _qSize = self.iface.qsize(timeout=timeout)
        assert True

class TestWithTimeouts(_BaseReader):
    def setUp(self):
        self.logger = self._getLogger()
        self.quiet=True
        self.random = Random()
        self.timerTerminate = 0
        self._timers = []
        self.namespaces = []
        self.dummyQueue = Queue()
        self.iface = PyRQIface(ref="test", quiet=self.quiet, loggingModule=testLoggingModule)
        self.marshaller = MarshallerFactory.get(MarshallerFactory.DEFAULT, quiet=self.quiet)
        desiredPort = "19001"
        self.r = SubprocessQueueServer(
                                       desiredPort=desiredPort,
                                       handlerClazz=Linkage.create(TimeoutMockHandler),
                                       quiet=self.quiet,
           )
        PyRQIface.setGlobalPYRQ(self.r.details())
    def _createInterface(self):
        namespace = self.iface.create()
        self.iface = PyRQIface(namespace=namespace, ref="test", quiet=self.quiet, loggingModule=testLoggingModule)
        self.namespaces.append(namespace)
        return namespace
    def tearDown(self):
        self.timerTerminate = 1
        time.sleep(2)
        try:
            self.dummyQueue.close()
            del self.dummyQueue
        except Exception, _e:
            pass
        for namespace in self.namespaces:
            self.iface.setNamespace(namespace)
        try:    self.iface.close()
        except ClosedError, _e:
            pass
        try:    self.r.close()
        except: pass
        for i in self._timers:
            try:    i.cancel()
            except: pass
        self._teardownLoggers()
    def testCreate(self):
        #    Create a new queue and get it's namespace:
        namespace = self.iface.create()
        assert namespace
    def _checkPut(self, eData="hello world!", block=True, timeout=None):
        self.iface.put(eData, block=block, timeout=timeout)
        return (eData, block, timeout)
    def _doGet(self, block=True, timeout=None):
        data = self.iface.get(block=block, timeout=timeout)
        return data
    def testPutTimesout(self, eData="hello world!", noCheck=False, block=True):
        namespace = self._createInterface()
        try:
            iface = PyRQIface(namespace=namespace, ref="testPutTimesout-put", quiet=self.quiet, loggingModule=testLoggingModule)
            iface.put(eData, block=block, timeout=0.1)
        except Full, _e:
            assert True
        else:
            assert False
    def testCreateTimesout(self, timeout=1):
        r"""
        @deprecated: Timeout's don't work!
        """
        #    Create a new queue and get it's namespace:
        iface = PyRQIface(ref="testCreateTimesout", quiet=self.quiet, loggingModule=testLoggingModule)
        latency = iface._minimumSocketLatency
        iface._minimumSocketLatency = 0
        try:
            try:
                iface.create(timeout=timeout)
            except PyRQError, _e:
                assert True
            else:
                assert False
        finally:
            iface._minimumSocketLatency = latency
    def testParallelGets_MultiplePuttersMultipleGettersTenItems(self, count=MultipleItems):
        self.testParallelGets_MultiplePuttersMultipleGettersOneItem(count=count)
    def testParallelGets_MultiplePuttersSingleGetterTenItems(self, count=MultipleItems):
        self.testParallelGets_MultiplePuttersSingleGetterOneItem(count=count)
    def testParallelGets_SinglePutterMultipleGettersTenItems(self, count=MultipleItems):
        self.testParallelGets_SinglePutterMultipleGettersOneItem(count=count)
    def testParallelGets_SinglePutterOneGetterTenItems(self, count=MultipleItems):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count)
    def testParallelGets_MultiplePuttersMultipleGettersOneItem(self, count=1, numGetters=MultipleGetters, numPutters=MultiplePutters):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count, numGetters=numGetters, numPutters=numPutters)
    def testParallelGets_MultiplePuttersSingleGetterOneItem(self, count=1, numGetters=1, numPutters=MultiplePutters):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count, numGetters=numGetters, numPutters=numPutters)
    def testParallelGets_SinglePutterMultipleGettersOneItem(self, count=1, numGetters=MultipleGetters, numPutters=1):
        self.testParallelGets_SinglePutterOneGetterOneItem(count=count, numGetters=numGetters, numPutters=numPutters)
    def testParallelGets_SinglePutterOneGetterOneItem(self, numGetters=1, numPutters=1, count=1, getTimeout=1, putTimeout=1):
        self.testCreate()
        namespace = self._createInterface()
        l = Lock()
        eGets = []
        initialDelay = 4
        def doGet(initialDelay, ref, getTimeout):
            time.sleep(initialDelay)
            iface = PyRQIface(ref="get.%(R)s"%{"R":ref}, namespace=namespace, quiet=self.quiet, loggingModule=testLoggingModule)
            while self.timerTerminate==0:
                rtn = False
                try:
                    data = iface.get(timeout=getTimeout)
                except Empty, data:
                    rtn = True
                with l:
                    eGets.append(data)
                if rtn:
                    return
        for i in xrange(numGetters):
            t = threading.Timer(0, doGet, args=[initialDelay, i, getTimeout])
            t.setDaemon(True)
            t.setName("Parallel_GET_%(C)s"%{"C":i})
            self._timers.append(t)
            t.start()
        #    Now pump the data into the queues over time:
        time.sleep(2)
        ePuts = []
        initialDelay = 1
        def doPut(initialDelay, ref, putTimeout, data):
            time.sleep(initialDelay)
            iface = PyRQIface(ref="put.%(R)s"%{"R":ref}, namespace=namespace, quiet=self.quiet, loggingModule=testLoggingModule)
            while self.timerTerminate==0 and len(data)>0:
                (delay, eData) = data.pop(0)
                time.sleep(delay)
                try:
                    iface.put(data=eData, timeout=putTimeout)
                except Full, eData:
                    pass
                with l:
                    ePuts.append(eData)
        for i in xrange(numPutters):
            data = []
            for k in xrange(count):
                delay = self.random.random()
                data.append((delay, "hello.world...%(C)s"%{"C":k}))
            t = threading.Timer(0, doPut, args=[initialDelay, i, putTimeout, data])
            t.setDaemon(True)
            t.setName("Parallel_PUT_%(C)s"%{"C":i})
            self._timers.append(t)
            t.start()
        time.sleep(3)
        #    Now wait for all the data to be received:
        maxPutDelay = (count*putTimeout)
        if maxPutDelay!=None:
            time.sleep(maxPutDelay)
        else:
            time.sleep(count)
        time.sleep(5)
        with l:
            for data in ePuts:
                assert isinstance(data, Full)
            for data in eGets:
                assert isinstance(data, Empty)

if __name__ == '__main__':
    unittest.main()
