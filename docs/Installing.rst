Installing
==========

Requirements
~~~~~~~~~~~~

Core
----

 * `gdb <https://www.gnu.org/s/gdb>`_ (version 7.3+)

GUI
---

 - `Pyrasite <https://github.com/lmacken/pyrasite>`_
 - python-debuginfo (needed for live object inspection)
 - PyGObject3 Introspection bindings

   - Fedora: pygobject3
   - Ubuntu: python-gobject-dev
   - Arch: python2-gobject

 - WebKitGTK3

   - Fedora: webkitgtk3
   - Ubuntu: gir1.2-webkit-3.0
   - Arch: libwebkit3

 - `meliae <https://launchpad.net/meliae>`_
   - easy_install/pip may not work for this install. If not, use the tarball from the distribution website. You may need to install `Cython <http://cython.org>`_ in order to get meliae to build.

   - Fedora: python-meliae
   - Ubuntu: python-meliae
   - Arch: python2-meliae

 - `pycallgraph <http://pycallgraph.slowchop.com>`_

   - Fedora: python-pycallgraph
   - Ubuntu: python-pycallgraph
   - Arch: python2-pycallgraph

 - `psutil <http://code.google.com/p/psutil>`_

   - Fedora: python-psutil
   - Ubuntu: python-psutil
   - Arch: python2-psutil

Download
~~~~~~~~

Download the latest stable release from PyPi: http://pypi.python.org/pypi/pyrasite

::

    pip install pyrasite

Running from git
~~~~~~~~~~~~~~~~

::

    git clone git://github.com/lmacken/pyrasite.git
    cd pyrasite
    python -m pyrasite.main

.. note::

   If you're on Python 2.4, you can run pyrasite by doing
   ``PYTHONPATH=$(pwd) python pyrasite/main.py``

Additional installation notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fedora
------

pyrasite and pycallgraph are currently not available in Fedora. You can run
pyrasite on Fedora by doing the following:

.. code-block:: bash

   sudo yum -y install python-meliae python-devel python-psutil pygobject3 graphviz python-virtualenv git-core gcc
   sudo yum -y --enablerepo=\*-debuginfo install python-debuginfo
   git clone -b develop git://github.com/lmacken/pyrasite.git
   cd pyrasite
   virtualenv [--system-site-packages if on F16+] env
   source env/bin/activate
   python setup.py develop
   pyrasite-gui

If you're using Fedora 17 or later, you'll need to disable an SELinux boolean to allow ptrace.

.. code-block:: bash

   sudo setsebool -P deny_ptrace=off

Mac OS X
--------

If you don't want to override Apple's default gdb, install the latest version of gdb with a prefix (e.g. gnu)

::

    $ ./configure --program-prefix=gnu
    $ pyrasite <PID> payloads/reverse_python_shell.py --prefix="gnu"

Arch Linux
----------

You can install pyrasite from the `Arch User Repository <https://aur.archlinux.org/packages.php?ID=57604>`_ If you want python debugging symbols, you may have to self compile python2.

Ubuntu
------

Since version 10.10, Ubuntu ships with a `controversial patch <https://lkml.org/lkml/2010/6/16/421>`_ that restricts the scope of ptrace, which can be disabled by running:

::

    echo 0 > /proc/sys/kernel/yama/ptrace_scope


