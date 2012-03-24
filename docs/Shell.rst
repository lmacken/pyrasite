pyrasite-shell - Give it a pid, get a shell
===========================================

You can easily drop into a shell and execute commands in a running process
using the ``pyrasite-shell``.

.. code-block:: bash

   $ pyrasite-shell
   Usage: pyrasite-shell <PID>

.. code-block:: bash

   $ pyrasite-shell $(pgrep -f "python -v")
   pyrasite shell 2.0beta7
   Python 2.7.2 (default, Oct 27 2011, 01:40:22) 
   [GCC 4.6.1 20111003 (Red Hat 4.6.1-10)] on linux2
   
   >>> print(x)
   foo
   
   >>> globals()['x'] = 'bar'

Source
------

.. literalinclude:: ../pyrasite/tools/shell.py
   :language: python
   :start-after: Copyright
