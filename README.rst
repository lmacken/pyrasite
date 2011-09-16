pyrasite
========

Injects code into a running Python process.

Requirements
~~~~~~~~~~~~

  - gdb (https://www.gnu.org/s/gdb)

Example Payloads
~~~~~~~~~~~~~~~~

Hello World
-----------

::

    pyrasite <PID> payloads/helloworld.py

This payload is used by the test suite, which can be run by doing:

::

    python setup.py test


Viewing the largest objects in your process
-------------------------------------------

::

    $ pyrasite <PID> payloads/dump_memory.py
    $ python tools/memory-viewer <PID> objects.json

Note that the `objects.json` file will be in the current working directory of
the running process.

.. image:: http://lewk.org/img/pyrasite-memory-viewer.png

Reverse Python Shell
--------------------

::

    $ python
    >>> x = 'foo'

::

    $ pyrasite <PID> payloads/reverse_python_shell.py
    $ nc -l localhost 9001
    Python 2.7.1 (r271:86832, Apr 12 2011, 16:15:16)
    [GCC 4.6.0 20110331 (Red Hat 4.6.0-2)]
    Type 'quit' to exit.
    >>> print x
    foo
    
    >>> globals()['x'] = 'bar'


Reverse Shell
--------------

::

    $ pyrasite <PID> payloads/reverse_shell.py
    $ nc -l localhost 9001
    Linux tomservo 2.6.40.3-0.fc15.x86_64 #1 SMP Tue Aug 16 04:10:59 UTC 2011 x86_64 x86_64 x86_64 GNU/Linux
    Type 'quit' to exit.
    % ls


Dumping modules, thread stacks, and forcing garbage collection
--------------------------------------------------------------

::

    payloads/dump_modules.py
    payloads/dump_stacks.py
    payloads/force_garbage_collection.py


Authors
~~~~~~~

Luke Macken <lmacken@redhat.com>
David Malcolm <dmalcolm@redhat.com>
