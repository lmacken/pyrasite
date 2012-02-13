Installing
==========

Requirements
~~~~~~~~~~~~

 * gdb (https://www.gnu.org/s/gdb) (version 7.3+)

Download
~~~~~~~~

Download the latest stable release from PyPi: http://pypi.python.org/pypi/pyrasite

::

    easy_install pyrasite

Grab the latest source by running:

::

    git clone git://git.fedorahosted.org/git/pyrasite

You can also fork pyrasite on GitHub: http://github.com/lmacken/pyrasite

Additional installation notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mac OS X
--------

If you don't want to override Apple's default gdb, install the latest version of gdb with a prefix (e.g. gnu)

::

    $ ./configure --program-prefix=gnu
    $ pyrasite <PID> payloads/reverse_python_shell.py --prefix="gnu"

Ubuntu
------

Since version 10.10, Ubuntu ships with a `controversial patch <https://lkml.org/lkml/2010/6/16/421>`_ that restricts the scope of ptrace, which can be disabled by running:

::

    echo 0 > /proc/sys/kernel/yama/ptrace_scope



