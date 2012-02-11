# This file is part of pyrasite.
#
# pyrasite is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyrasite is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyrasite.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2011 Red Hat, Inc.
"""
pyrasite
========

Inject code into a running python process.

    http://pyrasite.fedorahosted.org

Authors:

    Luke Macken <lmacken@redhat.com>
    David Malcolm <dmalcolm@redhat.com>
"""

import os, subprocess, warnings

class CodeInjector(object):

    def __init__(self, pid, filename=None, verbose=False, gdb_prefix=""):
        self.pid = pid
        self.verbose = verbose
        self.gdb_prefix = gdb_prefix
        if filename:
            warnings.warn('Passing the payload in via the constructor is '
                          'deprecated. Please pass it to the "inject" method '
                          'instead.')
            self.filename = os.path.abspath(filename)

    def inject(self, filename=None):
        if filename:
            self.filename = os.path.abspath(filename)
        gdb_cmds = [
            'PyGILState_Ensure()',
            # Allow payloads to import modules alongside them
            'PyRun_SimpleString("import sys; sys.path.insert(0, \\"%s\\");")' %
                os.path.dirname(self.filename),
            'PyRun_SimpleString("execfile(\\"%s\\")")' % self.filename,
            'PyGILState_Release($1)',
            ]
        self._run('%sgdb -p %d -batch %s' % (self.gdb_prefix, self.pid,
            ' '.join(["-eval-command='call %s'" % cmd for cmd in gdb_cmds])))

    def _run(self, cmd):
        if self.verbose:
            print(cmd)
        p = subprocess.Popen(cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        out, err = p.communicate()
        if self.verbose:
            print(out)
        if err:
            print(err)
