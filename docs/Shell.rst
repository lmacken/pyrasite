``pyrasite-shell`` - Give it a pid, get a shell
===============================================

You can easily drop into a shell and execute commands in a running process
using the ``pyrasite-shell``.

.. code-block:: bash

   $ pyrasite-shell $(pgrep -f "ipython")
   Pyrasite Shell 2.3.0
   Connected to 'ipython'
   Python 3.12.3 (main, ...) [GCC ...] on linux
   >>> print(x)
   foo
   
   >>> globals()['x'] = 'bar'

Options
-------

``--timeout SECONDS``
    How long to wait for the target to connect back. The environment variable
    ``PYRASITE_IPC_TIMEOUT`` provides the default. Once connected, commands are
    not subject to this timeout.

``--bind-host ADDRESS``
    Address to listen on. The default is ``localhost``. Binding to a
    non-loopback address exposes an unauthenticated code-execution socket.

``--connect-host ADDRESS``
    Hostname or address the target should connect back to. By default the
    target uses the bound address, which does not work when it is in another
    container or host.

``--port PORT``
    Port to listen on. By default an ephemeral port is chosen.

For example, with the target in another container::

    pyrasite-shell <pid> --bind-host 0.0.0.0 \
        --connect-host 10.0.0.5 --port 9001

Source
------

.. literalinclude:: ../pyrasite/tools/shell.py
   :language: python
   :start-after: Copyright
