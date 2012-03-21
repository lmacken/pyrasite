pyrasite - A command-line interface for injecting code into running Python processes
====================================================================================

::

    usage: pyrasite [-h] [--gdb-prefix GDB_PREFIX] [--verbose] pid [filename]

    pyrasite - inject code into a running python process

    positional arguments:
      pid                   The ID of the process to inject code into
      filename              The second argument must be a filename

    optional arguments:
      -h, --help            show this help message and exit
      --gdb-prefix GDB_PREFIX
                            GDB prefix (if specified during installation)
      --verbose             Verbose mode

    For updates, visit https://github.com/lmacken/pyrasite


pyrasite-shell
--------------

You can easily open up a shell and execute commands in a running process using
the `pyrasite-shell`.

.. code-block:: bash

   $ pyrasite-shell
   Usage: pyrasite-shell <PID>

.. code-block:: bash

   $ pyrasite-shell $(pgrep -f "python -v")
   Pyrasite Shell 2.0beta7
   Python 2.7.2 (default, Oct 27 2011, 01:40:22) 
   [GCC 4.6.1 20111003 (Red Hat 4.6.1-10)] on linux2
   
   >>> print(x)
   foo
   
   >>> globals()['x'] = 'bar'

.. seealso:: :doc:`Payloads`
