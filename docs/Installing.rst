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

Pyrasite runs on CPython 3.9 through 3.15. Injection works between versions
as well, so you can run Pyrasite under one Python and inject into a process
running another. Both the pyrasite client and the target process must be
CPython.

Installing
~~~~~~~~~~

Install the latest release from `PyPI <https://pypi.org/project/pyrasite/>`_
with ``pipx`` or ``pip``::

    pipx install pyrasite

The optional memory viewer needs a couple of extra packages::

    pip install "pyrasite[memory-viewer]"

.. seealso:: The `pyrasite-gui <https://github.com/lmacken/pyrasite-gui>`_
   project provides a graphical interface, but is maintained separately and
   is not part of this release.

Additional installation notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ptrace
------

Recent Linux distributions restrict ptrace so that a process may only be
attached to by its ancestors. If ``/proc/sys/kernel/yama/ptrace_scope`` is
non-zero, enable attaching globally::

    echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

To make the change permanent, set ``ptrace_scope`` to ``0`` in
``/etc/sysctl.d/10-ptrace.conf``.

Alternatively, a target process can opt in to being traced by calling
``prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY)`` before pyrasite attaches.

On Fedora, SELinux may also need::

    sudo setsebool -P deny_ptrace=off

macOS
-----

If you don't want to override Apple's default gdb, install the latest version
of gdb with a prefix (e.g. ``gnu``)::

    ./configure --program-prefix=gnu
    pyrasite <PID> payloads/reverse_python_shell.py --gdb-prefix="gnu"
