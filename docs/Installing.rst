Installing
==========

Requirements
~~~~~~~~~~~~

Core
----

 * `gdb <https://www.gnu.org/s/gdb>`_ (version 7.3+)

Optional (needed for the GUI)
-----------------------------

 * python-debuginfo
 * `meliae <https://launchpad.net/meliae>`_
 * `pycallgraph <http://pycallgraph.slowchop.com>`_
 * `psutil <http://code.google.com/p/psutil>`_

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


Fedora
------

pyrasite and pycallgraph are currently not available in Fedora. You can run
pyrasite on Fedora by doing the following:

.. code-block:: bash

   sudo yum -y install python-meliae python-devel python-psutil pygobject3 graphviz python-virtualenv git-core gcc
   sudo yum -y --enablerepo=\*-debuginfo install python-debuginfo
   git clone -b develop git://git.fedorahosted.org/git/pyrasite
   cd pyrasite
   virtualenv [--system-site-packages if on F16+] env
   source env/bin/activate
   python setup.py develop
   pyrasite-gui


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



