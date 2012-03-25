Payloads
========

Viewing the largest objects in your process
-------------------------------------------

Pyrasite provides a tool to view object memory usage statistics, and the
live value, of largest objects in your process. This requires `urwid
<http://pypi.python.org/pypi/urwid>`_ and `meliae
<https://launchpad.net/meliae>`_ to be installed.

::

    $ pyrasite-memory-viewer <PID>


.. image:: http://lewk.org/img/pyrasite-memory-viewer.png

.. note:: We recommend using python-meliae from your OS distribution, if available.  If it is not, you will need to first install Cython, and then meliae seperately. If pip/easy_install does not work, you may need to use the tarball from the upstream website.

This tool automatically injects the following payload:

.. literalinclude:: ../pyrasite/payloads/dump_memory.py
   :language: python
   :start-after: html

You can easily dump the object memory usage JSON data by hand, if you wish:

::

    $ pyrasite <PID> pyrasite/payloads/dump_memory.py


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

