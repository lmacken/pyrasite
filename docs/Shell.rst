``pyrasite-shell`` - Give it a pid, get a shell
===============================================

You can easily drop into a shell and execute commands in a running process
using the ``pyrasite-shell``.

.. code-block:: bash

   $ pyrasite-shell
   Usage: pyrasite-shell <PID>

.. code-block:: bash

   $ pyrasite-shell $(pgrep -f "ipython")
   Pyrasite Shell 2.1.0
   Connected to 'ipython'
   Python 3.12.3 (main, ...) [GCC ...] on linux
   >>> print(x)
   foo
   
   >>> globals()['x'] = 'bar'

Source
------

.. literalinclude:: ../pyrasite/tools/shell.py
   :language: python
   :start-after: Copyright
