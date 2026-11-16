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
# Copyright (C) 2011-2013 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import subprocess


def inspect(pid, address, gdb_prefix=''):
    """Return the value of an object in a given process at the specified address"""
    argv = [
        (gdb_prefix or '') + 'gdb',
        '--quiet',
        '-p', str(pid),
        '-batch',
        '-eval-command=print (PyObject *)%s' % address,
    ]
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    for line in p.stdout.splitlines():
        if line.startswith('$1 = '):
            return line[5:]
    return None
