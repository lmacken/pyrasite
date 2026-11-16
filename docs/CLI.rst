``pyrasite`` - Inject arbitrary code into a running Python process
==================================================================

::

    usage: pyrasite [-h] [-l] [--gdb-prefix GDB_PREFIX] [--verbose]
                    [--version] [--output OUTPUT_TYPE]
                    [--ipc-timeout IPC_TIMEOUT]
                    [--inject-timeout INJECT_TIMEOUT]
                    [--inject-method {auto,pending,direct}]
                    [pid] [payload]

    pyrasite - inject code into a running python process

    positional arguments:
      pid                   The ID of the process to inject code into
      payload               The Python script to be executed inside the running
                            process. Can be one of the standard payloads (see
                            --list-payloads), a filename, or - to read the
                            script from stdin.

    options:
      -h, --help            show this help message and exit
      -l, --list-payloads   List standard payloads
      --gdb-prefix GDB_PREFIX
                            GDB prefix (if specified during installation)
      --verbose             Verbose mode
      --version             show program's version number and exit
      --output OUTPUT_TYPE  Set where output is to be printed. 'procstreams'
                            prints output in stdout/stderr of running process and
                            'localterm' prints output in local terminal.
      --ipc-timeout IPC_TIMEOUT
                            The number of seconds to wait for the injected code to
                            reply over IPC before giving up.
      --inject-timeout INJECT_TIMEOUT
                            The number of seconds to wait for the injected payload
                            to run. Use 0 to wait forever.
      --inject-method {auto,pending,direct}
                            How to run code in the target. 'auto' uses the
                            direct method for single-threaded processes and
                            Py_AddPendingCall for multi-threaded ones. Use
                            'direct' for processes blocked in C.

    For updates, visit https://github.com/lmacken/pyrasite

.. seealso:: :doc:`Payloads`
