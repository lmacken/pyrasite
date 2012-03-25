pyrasite-memory-viewer - View the largest objects in your process
-----------------------------------------------------------------

Pyrasite provides a tool to view object memory usage statistics, and the
live value, of largest objects in your process. This requires `urwid
<http://pypi.python.org/pypi/urwid>`_ and `meliae
<https://launchpad.net/meliae>`_ to be installed.

::

    $ pyrasite-memory-viewer <PID>


.. image:: http://lewk.org/img/pyrasite-memory-viewer.png

.. note:: We recommend using python-meliae from your OS distribution, if available.  If it is not, you will need to first install Cython, and then meliae seperately. If pip/easy_install does not work, you may need to use the tarball from the upstream website.

This tool automatically injects the following payload:

.. literalinclude:: ../pyrasite/payloads/dump_memory.py
   :language: python
   :start-after: html

You can easily dump the object memory usage JSON data by hand, if you wish:

::

    $ pyrasite <PID> pyrasite/payloads/dump_memory.py


