PyRQ
====
    What it is:
    A pure Python (>2.7) remote queue (RQ) implementation using the standard Queue api.
    
    What it is not:
    A high-performance queue replacement for a normal linux dev environment.
    
    Primary use-case:
    If you are unable to use 'os.fork' or 'multiprocessing.process.Process'
    due to environment/performance limitations then you need this!
    
    Compatability:
    This was written on and for Python2.7 on Ubuntu, if it works on anything else
    then this is a bonus!
        ** This has not been tested or written with any thought to Python3 **
    
    Installation:
    Get it here: http://pypi.python.org/pypi/PyRQ
    easy_install PyRQ
    
    Dependencies (non-standard modules):
    Interface - multiprocessing (RLock, Semaphore)
    Impl      - multiprocessing (Rlock, Semaphore, Queue)
    Debugger  - PyQt4, qt4, multiprocessing (Rlock, Semaphore, Queue), QsciScintilla
    
    Conceptually:
    A series of proxied multiprocessing-queues/lists (RQ) sit behind a socketserver
    and queue controller (PyRQ).
    These queues are accessed by interfaces which replicate (as much as possible) the 
    standard python Queue and multiprocessing.queue api and are created using a simple
    queue factory by the PyRQ.
    
    About:
    The PyRQ controls a queue proxy for each queue.
    The PyRQ resides in a separate Python Process launched by the subprocess
    module on the target system.
    The RQ proxy is accessed by the client by using the PyRQIface which holds the
    PyRQ's (host:port) and the namespace details for the desired RQ.
    Queues can be created and destroyed at will, the only limitations being the target's
    environment.
    For performance tuning, the RQ can ignore the socket data marshallers for specific
    data types (eg: large data which would kill the marshaller's performance) and use
    the target's tmp. storage for inter-process message data.
    
    Queues can be created and destroyed (freeing all resources).
    The proxy is referenced by it's (host:port) details.
    The queue is referenced by it's namespace (uuid4) returned when created.
    All methods contain a timeout value, to allow for network latency issues.
    Closing an individual queue proxy on a PyRQ results in all attached clients to
    raise exceptions which are handled in the interface PyRQIface and thus the caller
    is aware of the remote queue state.
    
    Tests:
    There is a full suite of unit and system (end-to-end) tests which each yield no
    left-over threads or processes! Currently all tests pass.
    
    Qt4 Debugger:
    There is a PyQt4 debugger for inspecting, and testing the PyRQ on the remote target
    (assuming it can be reached by the user!). The debugger can handle multiple PyRQs 
    on multiple targets simultaneously in a tabbed window arrangement.
    Inspection: The debugger shows the status of all queues including namespace, port,
    type, state (capacity, contents, every queue proxy method access, ie: get() (result,
    client, timeout, etc) - put() (client, timeout, data, etc). Users can apply
    filters to narrow the events shown.
    Testing: There is a comprehensive test-vector generator which can create unlimited
    combinations of all methods and parameters which can be fired at one, many or all
    PyRQ's attached to the debugger. These test-vectors can be saved as scripts and
    executed, replayed, looped, etc.
    Note: At the moment, the mock debugger implementation is also the real one!
    
    Warnings:
    1.
    The debugger was an after-market bolt-on the the whole system and has a few bugs
    which affect the rendering of some of the test-vector scripts during their execution
    - this does not affect the debugging abilities or usefulness of the debugger in any
    way.
    
    2.
    This was designed to be used in a resource constrained embedded environment
    with multi-vendor hardware and software stacks, very specific limitations and thus
    performance and memory requirements and 'will not suit' every use-case out there.
    This implementation solves some of the fundamental problems with the multiprocessing
    module (eg: pickling errors, data tracking, etc) in such a 'fluid' and
    stability-impaired alpha development environment which typically characterises
    bleeding-edge embedded development.
    
