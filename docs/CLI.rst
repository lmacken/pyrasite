``pyrasite`` - Inject arbitrary code into a running Python process
==================================================================

::

    usage: pyrasite [-h] [--gdb-prefix GDB_PREFIX] [--verbose] pid [filepath|payloadname]
           pyrasite --list-payloads

    pyrasite - inject code into a running python process

    positional arguments:
      pid                   The ID of the process to inject code into
      filepath|payloadname  The second argument must be a path to a
                            file that will be sent as a payload to the
                            target process or it must be the name of
                            an existing payload (see --list-payloads).

    optional arguments:
      -h, --help            show this help message and exit
      --gdb-prefix GDB_PREFIX
                            GDB prefix (if specified during installation)
      --verbose             Verbose mode
      --list-payloads       List payloads that are delivered by pyrasite

    For updates, visit https://github.com/lmacken/pyrasite

.. seealso:: :doc:`Payloads`
