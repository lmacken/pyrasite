Installing
==========

Requirements
~~~~~~~~~~~~

* `gdb <https://www.gnu.org/s/gdb>`_ (version 7.3+)


Python Compatibility
~~~~~~~~~~~~~~~~~~~~

Pyrasite works with Python 2.4 and newer. Injection works between versions
as well, so you can run Pyrasite under Python 3 and inject into 2, and
vice versa.

Installing
~~~~~~~~~~

You can download the latest tarballs, RPMs, and debs from `PyPi <http://pypi.python.org/pypi/pyrasite>`_. Installing the package specific to your distribution is recommended. However, you
can also install it using ``pip`` if you wish

::

    pip install pyrasite pyrasite-gui


.. seealso:: `pyrasite-gui <http://pyrasite.readthedocs.org/en/latest/GUI.html>`_ for instructions on installing the graphical interface

Additional installation notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fedora
------

If you're using Fedora 17 or later, you'll need to disable an SELinux boolean to allow ptrace.

.. code-block:: bash

   sudo setsebool -P deny_ptrace=off

Mac OS X
--------

If you don't want to override Apple's default gdb, install the latest version of gdb with a prefix (e.g. gnu)

::

    $ ./configure --program-prefix=gnu
    $ pyrasite <PID> payloads/reverse_python_shell.py --gdb-prefix="gnu"

Arch Linux
----------

You can install pyrasite from the `Arch User Repository <https://aur.archlinux.org/packages.php?ID=57604>`_ If you want python debugging symbols, you may have to self compile python2.

Ubuntu
------

Since version 10.10, Ubuntu ships with a `controversial patch <https://lkml.org/lkml/2010/6/16/421>`_ that restricts the scope of ptrace, which can be disabled by running:

::

    echo 0 > /proc/sys/kernel/yama/ptrace_scope

You can make this change permanent by setting ``ptrace_scope`` to ``0`` in
``/etc/sysctl.d/10-ptrace.conf``.
