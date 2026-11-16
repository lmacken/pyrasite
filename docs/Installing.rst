Installing
==========

Requirements
~~~~~~~~~~~~

* `gdb <https://www.gnu.org/s/gdb>`_ (version 7.3+)
* Linux (or another Unix with a working gdb). Windows support is optional and
  less well tested.
* Permission to attach to the target process with ptrace. See below.


Python Compatibility
~~~~~~~~~~~~~~~~~~~~

Pyrasite runs on CPython 3.9 through 3.14. Injection works between versions
as well, so you can run Pyrasite under one Python and inject into a process
running another. Both the pyrasite client and the target process must be
CPython.

Installing
~~~~~~~~~~

You can download the latest tarballs, RPMs, and debs from `PyPI
<https://pypi.org/project/pyrasite/>`_. Installing the package specific to
your distribution is recommended. However, you can also install it with
``pipx`` or ``pip``::

    pipx install pyrasite

The optional memory viewer needs a couple of extra packages::

    pip install "pyrasite[memory-viewer]"

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

You can install pyrasite from the `Arch User Repository <https://aur.archlinux.org/packages.php?ID=57604>`_.

Ubuntu
------

Since version 10.10, Ubuntu ships with a `controversial patch <https://lkml.org/lkml/2010/6/16/421>`_ that restricts the scope of ptrace, which can be disabled by running:

::

    echo 0 > /proc/sys/kernel/yama/ptrace_scope

You can make this change permanent by setting ``ptrace_scope`` to ``0`` in
``/etc/sysctl.d/10-ptrace.conf``.

Alternatively, a target process can opt in to being traced by calling
``prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY)`` before pyrasite attaches.
