Example Payloads
================

These payloads can be found in the `pyrasite/payloads
<https://github.com/lmacken/pyrasite/tree/master/pyrasite/payloads>`_
directory.

Dumping thread stacks
---------------------

.. literalinclude:: ../pyrasite/payloads/dump_stacks.py
   :language: python

Viewing loaded modules
----------------------

.. literalinclude:: ../pyrasite/payloads/dump_modules.py
   :language: python

Call Graph
----------

Pyrasite comes with a payload that generates an image of your processes call
graph using `pycallgraph <http://pycallgraph.slowchop.com>`_.

.. literalinclude:: ../pyrasite/payloads/start_callgraph.py
   :language: python
   :start-after: http

.. literalinclude:: ../pyrasite/payloads/stop_callgraph.py
   :language: python
   :start-after: http


The callgraph is then generated using `graphviz <http://www.graphviz.org>`_ and
saved to `callgraph.png`. You can see an example callgraph `here <http://pycallgraph.slowchop.com/pycallgraph/wiki/RegExpExample>`_.

Forcing garbage collection
---------------------------

.. literalinclude:: ../pyrasite/payloads/force_garbage_collection.py
   :language: python

Dumping out object memory usage statistics
------------------------------------------

.. literalinclude:: ../pyrasite/payloads/dump_memory.py
   :language: python

.. seealso:: :doc:`MemoryViewer`

Reverse Subprocess Shell
------------------------

.. literalinclude:: ../pyrasite/payloads/reverse_shell.py
   :language: python
   :start-after: Copyright

::

    $ pyrasite <PID> pyrasite/payloads/reverse_shell.py

::

    $ nc -l 9001
    Linux tomservo 2.6.40.3-0.fc15.x86_64 #1 SMP Tue Aug 16 04:10:59 UTC 2011 x86_64 x86_64 x86_64 GNU/Linux
    % ls

Reverse Python Shell
--------------------

.. deprecated:: 2.0
   Use the `pyrasite-shell <http://readthedocs.org/docs/pyrasite/en/latest/Shell.html>`_ instead

This lets you easily introspect or alter any objects in your running process.

.. literalinclude:: ../pyrasite/payloads/reverse_python_shell.py
   :language: python
   :start-after: Copyright

::

    $ python
    >>> x = 'foo'

::

    $ pyrasite <PID> pyrasite/payloads/reverse_python_shell.py

::

    $ nc -l 9001
    Python 2.7.1 (r271:86832, Apr 12 2011, 16:15:16)
    [GCC 4.6.0 20110331 (Red Hat 4.6.0-2)]
    >>> print x
    foo
    >>> globals()['x'] = 'bar'

