.. image:: https://raw.githubusercontent.com/lmacken/pyrasite/develop/docs/logo.png

pyrasite
========

.. image:: https://github.com/lmacken/pyrasite/actions/workflows/ci.yml/badge.svg?branch=develop
   :target: https://github.com/lmacken/pyrasite/actions/workflows/ci.yml
.. image:: https://img.shields.io/pypi/v/pyrasite?style=flat
   :target: https://pypi.org/project/pyrasite/

Tools for injecting arbitrary code into running Python processes.

:homepage: https://github.com/lmacken/pyrasite
:documentation: https://pyrasite.readthedocs.io/
:download: https://pypi.org/project/pyrasite/
:source: https://github.com/lmacken/pyrasite
:issues: https://github.com/lmacken/pyrasite/issues

Requirements
~~~~~~~~~~~~

 * `gdb <https://www.gnu.org/s/gdb>`_ (version 7.3+)
 * A Linux system whose ptrace policy allows attaching to the target
   process.  See `ptrace_scope` below.

On OS X you will need to have a codesigned gdb - see https://sourceware.org/gdb/wiki/BuildingOnDarwin
if you get errors while running with --verbose which mention codesigning.

Installation
~~~~~~~~~~~~

::

    pipx install pyrasite

or, for the optional memory viewer::

    pip install "pyrasite[memory-viewer]"

Compatibility
~~~~~~~~~~~~~

Pyrasite runs on CPython 3.9 through 3.15. Injection works between versions
as well, so you can run Pyrasite under one Python and inject into a process
running another. Both the pyrasite client and the target process must be
CPython.

ptrace_scope
~~~~~~~~~~~~

Recent Linux distributions restrict ptrace so that a process may only be
attached to by its ancestors. If ``/proc/sys/kernel/yama/ptrace_scope`` is
non-zero you will see a warning. You can either allow attaching globally::

    echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

or let the target process opt in by calling ``prctl(PR_SET_PTRACER,
PR_SET_PTRACER_ANY)``. On Fedora, SELinux may also need::

    sudo setsebool -P deny_ptrace=off

For multi-threaded programs pyrasite queues the payload with
``Py_AddPendingCall`` so that it runs on a thread that already holds the GIL.
If the target is blocked in C and never executes Python bytecode, use
``--inject-method direct`` instead.

Testing
~~~~~~~

::

    pip install -e ".[dev]"
    pytest
    ruff check .
    ruff format --check .

To run the suite against every supported interpreter with `uv
<https://docs.astral.sh/uv/>`_::

    uv python install 3.9 3.10 3.11 3.12 3.13 3.14 3.15
    tox

To test injecting from one interpreter into all of the others, set
``PYRASITE_TEST_INTERPRETERS`` to a colon-separated list of interpreter
paths before running pytest.


pyrasite-gui
~~~~~~~~~~~~

The graphical interface is maintained separately at
https://github.com/lmacken/pyrasite-gui.

Authors
~~~~~~~

Created by `Luke Macken <https://twitter.com/lmacken>`_ with the help of
`David Malcolm <https://dmalcolm.livejournal.com>`_ and many other
`contributors <https://github.com/lmacken/pyrasite/contributors>`_.
Logo by `Adam Saunders <https://fedorahosted.org/design-team/ticket/214>`_.

Licenses
~~~~~~~~

Code
^^^^

.. image:: https://www.gnu.org/graphics/gplv3-127x51.png
   :target: https://www.gnu.org/licenses/gpl.txt

Logo
^^^^

.. image:: https://creativecommons.org/images/deed/nolaw.png
   :target: https://creativecommons.org/publicdomain/zero/1.0/
