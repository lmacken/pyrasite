pyrasite
========

.. split here

Pyrasite lets you to inject arbitrary code into an unaltered running Python
process.

Requirements
~~~~~~~~~~~~

  - gdb (https://www.gnu.org/s/gdb) (version 7.3+)

Download
~~~~~~~~

Download the latest stable release from PyPi: http://pypi.python.org/pypi/pyrasite

::

    pip install pyrasite

You can also run the latest pyrasite from source:

::

    git clone git://git.fedorahosted.org/git/pyrasite
    cd pyrasite
    python -m pyrasite.main

You can also fork pyrasite on GitHub: http://github.com/lmacken/pyrasite

pyrasite-gui
~~~~~~~~~~~~

The gui has been moved into it's own repository: https://github.com/lmacken/pyrasite-gui

.. image:: http://lewk.org/img/pyrasite/pyrasite-info.png

API
~~~

::

    from pyrasite.inject import CodeInjector

    ci = CodeInjector(p.pid)
    ci.inject('pyrasite/payloads/helloworld.py')


Payloads
~~~~~~~~

Reverse Python Shell
--------------------

This lets you easily introspect or alter any objects in your running process.


::

    $ python
    >>> x = 'foo'

::

    $ pyrasite <PID> pyrasite/payloads/reverse_python_shell.py
    $ nc -l localhost 9001
    Python 2.7.1 (r271:86832, Apr 12 2011, 16:15:16)
    [GCC 4.6.0 20110331 (Red Hat 4.6.0-2)]
    Type 'quit' to exit.
    >>> print x
    foo
    >>> globals()['x'] = 'bar'


Viewing the largest objects in your process
-------------------------------------------

This payload uses `meliae <https://launchpad.net/meliae>`_ to dump all of the objects in your process to an `objects.json` file (currently dumped in the working directory of your process).

.. note:: We recommend using python-meliae from your OS distribution, if available. If  it is not, you will need to first install Cython, and then meliae seperately. If pip/easy_install does not work, you may need to use the tarball from the upstream website.

::

    $ pyrasite <PID> pyrasite/payloads/dump_memory.py


Pyrasite also provides a tool to view the values of largest objects in your process.


::

    $ pyrasite-memory-viewer <PID> objects.json


.. image:: http://lewk.org/img/pyrasite-memory-viewer.png


Reverse Shell
-------------

::

    $ pyrasite <PID> pyrasite/payloads/reverse_shell.py
    $ nc -l localhost 9001
    Linux tomservo 2.6.40.3-0.fc15.x86_64 #1 SMP Tue Aug 16 04:10:59 UTC 2011 x86_64 x86_64 x86_64 GNU/Linux
    Type 'quit' to exit.
    % ls


Call Graph
----------

Pyrasite comes with a payload that generates an image of your processes call
graph using `pycallgraph <http://pycallgraph.slowchop.com>`_.

::

    $ pyrasite <PID> pyrasite/payloads/start_callgraph.py
    $ pyrasite <PID> pyrasite/payloads/stop_callgraph.py

The callgraph is then generated using `graphviz <http://www.graphviz.org>`_ and
saved to `callgraph.png`. You can see an example callgraph `here <http://pycallgraph.slowchop.com/pycallgraph/wiki/RegExpExample>`_.


Dumping modules, thread stacks, and forcing garbage collection
--------------------------------------------------------------

::

    pyrasite/payloads/dump_modules.py
    pyrasite/payloads/dump_stacks.py
    pyrasite/payloads/force_garbage_collection.py

Additional installation notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mac OS X
--------

If you don't want to override Apple's default gdb, install the latest version of gdb with a prefix (e.g. gnu)

::

    $ ./configure --program-prefix=gnu
    $ pyrasite <PID> pyrasite/payloads/reverse_python_shell.py --prefix="gnu"

Ubuntu
------

Since version 10.10, Ubuntu ships with a `controversial patch <https://lkml.org/lkml/2010/6/16/421>`_ that restricts the scope of ptrace, which can be disabled by running:

::

    echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope



Mailing List
~~~~~~~~~~~~

https://fedorahosted.org/mailman/listinfo/pyrasite

IRC
~~~

#pyrasite on Freenode.

Authors
~~~~~~~

Luke Macken <lmacken@redhat.com>

.. image:: http://api.coderwall.com/lmacken/endorsecount.png
   :target: http://coderwall.com/lmacken

David Malcolm <dmalcolm@redhat.com>
