PyRQ
====

A drop-in replacement for python 2.7's multiprocessing.queue using a centralised socket-based server encapsulating multiple queues. Includes a PyQt4 debugger for real-time queue inspection. Provides convenient work arounds to the runtime limitations of a severely stressed/hammered multiprocessing.queue fed with insecure data.