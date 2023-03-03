.. image:: http://pyrasite.com/logo.png

pyrasite
========

.. image:: https://api.travis-ci.org/lmacken/pyrasite.png?branch=develop
   :target: http://travis-ci.org/lmacken/pyrasite
.. image:: https://coveralls.io/repos/lmacken/pyrasite/badge.png?branch=develop
   :target: https://coveralls.io/r/lmacken/pyrasite?branch=develop
.. image:: https://pypip.in/v/pyrasite/badge.png
   :target: https://crate.io/packages/pyrasite
.. image:: https://pypip.in/d/pyrasite/badge.png
   :target: https://crate.io/packages/pyrasite

.. split here

Tools for injecting arbitrary code into running Python processes.

:homepage: http://pyrasite.com
:documentation: http://pyrasite.rtfd.org
:download: http://pypi.python.org/pypi/pyrasite
:source: http://github.com/lmacken/pyrasite
:screenshots: http://readthedocs.org/docs/pyrasite/en/latest/GUI.html
:mailing list: https://fedorahosted.org/mailman/listinfo/pyrasite
:jenkins: http://ci.csh.rit.edu/view/Pyrasite
:irc: #pyrasite on Freenode

Requirements
~~~~~~~~~~~~

 * `gdb <https://www.gnu.org/s/gdb>`_ (version 7.3+ (or RHEL5+))
 
On OS X you will need to have a codesigned gdb - see https://sourceware.org/gdb/wiki/BuildingOnDarwin
if you get errors while running with --verbose which mention codesigning.

Compatibility
~~~~~~~~~~~~~

Pyrasite works with Python 2.4 and newer. Injection works between versions
as well, so you can run Pyrasite under Python 3 and inject into 2, and
vice versa.

pyrasite-gui
~~~~~~~~~~~~

The graphical interface can be found here: https://github.com/lmacken/pyrasite-gui

.. image:: http://lewk.org/img/pyrasite/pyrasite-info-thumb.png

Authors
~~~~~~~

Created by `Luke Macken <http://twitter.com/lmacken>`_ with the help of
`David Malcolm <http://dmalcolm.livejournal.com>`_ and many other
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
