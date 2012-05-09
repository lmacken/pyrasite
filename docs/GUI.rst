``pyrasite-gui`` - A graphical interface for Pyrasite
=====================================================

The pyrasite-gui is a graphical interface for Pyrasite that lets you
easily monitor, analyze, introspect, and alter running Python programs.

:source: https://github.com/lmacken/pyrasite-gui
:download: http://pypi.python.org/pypi/pyrasite-gui

Requirements
------------

- Python debuginfo (needed for live object inspection)
- PyGObject3 Introspection bindings
- WebKitGTK3
- `meliae <https://launchpad.net/meliae>`_ (easy_install/pip may not work for this install. If not, use the tarball from the distribution website. You may need to install `Cython <http://cython.org>`_ in order to get meliae to build)
- `pycallgraph <http://pycallgraph.slowchop.com>`_
- `psutil <http://code.google.com/p/psutil>`_

Distribution-specific instructions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Fedora
   yum --enablerepo=updates-testing install python-psutil python-debuginfo python-pycallgraph pygobject3 webkitgtk3 python-meliae

   # Ubuntu:
   apt-get install python-dbg python-pycallgraph python-gobject-dev gir1.2-webkit-3.0 python-meliae python-psutil

   # Arch
   pacman -S python2-psutil python2-gobject python2-pycallgraph libwebkit3 python2-meliae

Screenshots
-----------

.. image:: http://lewk.org/img/pyrasite/pyrasite-info.png

.. image:: http://lewk.org/img/pyrasite/pyrasite-stacks.png

.. image:: http://lewk.org/img/pyrasite/pyrasite-objects.png

.. image:: http://lewk.org/img/pyrasite/pyrasite-shell.png

.. image:: http://lewk.org/img/pyrasite/pyrasite-callgraph.png
