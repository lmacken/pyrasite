``pyrasite`` - Inject arbitrary code into a running Python process
==================================================================

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

.. seealso:: :doc:`Payloads`
