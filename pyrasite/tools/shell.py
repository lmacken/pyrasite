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
# Copyright (C) 2012 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import sys
import pyrasite


def shell():
    """Open a Python shell in a running process"""

    if not len(sys.argv) == 2:
        print("Usage: pyrasite-shell <PID>")
        sys.exit(1)

    ipc = pyrasite.PyrasiteIPC(int(sys.argv[1]))
    ipc.connect()

    print("pyrasite shell %s" % pyrasite.__version__)
    print(ipc.cmd('import sys; print("Python " + sys.version + ' +
                  '" on " + sys.platform)'))
    try:
        while True:
            print(ipc.cmd(raw_input('>>> ')))
    except:
        pass

    ipc.close()
    print()
