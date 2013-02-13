PyRQ
====

    A pure python remote queue implementation.
    Conceptually, a series of multiprocessing-queues sit behind a socketserver 
    which acts as a proxy to them.
    The proxy resides in a separate Python Process launched by the subprocess
    module.
    Queue can be created and destroyed (freeing all resources).
    The proxy is referenced by it's host:port details.
    The queue is referenced by it's namespace (uuid4) returned when created.
    All methods contain a timeout value, to allow for network latency issues.
    At the moment, the mock debugger implementation is also the real one!
    The proxy is accessed using the PyRQIface which holds the PyRQ host:port and
    namespace details for the desired queue.


