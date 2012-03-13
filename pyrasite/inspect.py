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

from .utils import run


class ObjectInspector(object):
    """Inspects objects in a running Python program"""

    def __init__(self, pid):
        self.pid = pid

    def inspect(self, address):
        """Return the value of an object at a given address"""
        cmd = ' '.join([
            'gdb --quiet -p %s -batch' % self.pid,
            '-eval-command="print (PyObject *)%s"' % address,
        ])
        for line in run(cmd)[1].split('\n'):
            if line.startswith('$1 = '):
                return line[5:]
