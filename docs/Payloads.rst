Payloads
========

Reverse Python Shell
--------------------

This lets you easily introspect or alter any objects in your running process.

.. literalinclude:: ../pyrasite/payloads/reverse_python_shell.py
   :language: python
   :start-after: Copyright

::

    $ python
    >>> x = 'foo'

::

    $ pyrasite <PID> pyrasite/payloads/reverse_python_shell.py
    $ nc -l 9001
    Python 2.7.1 (r271:86832, Apr 12 2011, 16:15:16)
    [GCC 4.6.0 20110331 (Red Hat 4.6.0-2)]
    Type 'quit' to exit.
    >>> print x
    foo
    >>> globals()['x'] = 'bar'

Viewing the largest objects in your process
-------------------------------------------

This payload uses `meliae <https://launchpad.net/meliae>`_ to dump all of the objects in your process to an `objects.json` file (currently dumped in the working directory of your process).

.. literalinclude:: ../pyrasite/payloads/dump_memory.py
   :language: python
   :start-after: html

::

    $ pyrasite <PID> pyrasite/payloads/dump_memory.py


Pyrasite also provides a command-line tool to view the values of largest
objects in your process.


::

    $ pyrasite-memory-viewer <PID> objects.json


.. image:: http://lewk.org/img/pyrasite-memory-viewer.png


Reverse Shell
-------------

.. literalinclude:: ../pyrasite/payloads/reverse_shell.py
   :language: python
   :start-after: Copyright

::

    $ pyrasite <PID> pyrasite/payloads/reverse_shell.py
    $ nc -l 9001
    Linux tomservo 2.6.40.3-0.fc15.x86_64 #1 SMP Tue Aug 16 04:10:59 UTC 2011 x86_64 x86_64 x86_64 GNU/Linux
    Type 'quit' to exit.
    % ls


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

::

    $ pyrasite <PID> pyrasite/payloads/start_callgraph.py
    $ pyrasite <PID> pyrasite/payloads/stop_callgraph.py

The callgraph is then generated using `graphviz <http://www.graphviz.org>`_ and
saved to `callgraph.png`. You can see an example callgraph `here <http://pycallgraph.slowchop.com/pycallgraph/wiki/RegExpExample>`_.


Viewing loaded modules
----------------------

.. literalinclude:: ../pyrasite/payloads/dump_modules.py
   :language: python

::

    $ pyrasite <PID> pyrasite/payloads/dump_modules.py

Dumping thread stacks
---------------------

.. literalinclude:: ../pyrasite/payloads/dump_stacks.py
   :language: python

::

    $ pyrasite <PID> pyrasite/payloads/dump_stacks.py

Forcing garbage collection
---------------------------

.. literalinclude:: ../pyrasite/payloads/force_garbage_collection.py
   :language: python

::

    $ pyrasite <PID> pyrasite/payloads/force_garbage_collection.py
