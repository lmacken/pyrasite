``pyrasite-memory-viewer`` - View the largest objects in your process
=====================================================================

Pyrasite provides a tool to view object memory usage statistics, and the
live value, of largest objects in your process. This requires `urwid
<https://pypi.org/project/urwid/>`_ and `meliae
<https://launchpad.net/meliae>`_ to be installed::

    pip install "pyrasite[memory-viewer]"

::

    $ pyrasite-memory-viewer <PID>

This tool automatically injects the following payload:

.. literalinclude:: ../pyrasite/payloads/dump_memory.py
   :language: python

You can easily dump the object memory usage JSON data by hand, if you wish:

::

    $ pyrasite <PID> pyrasite/payloads/dump_memory.py


