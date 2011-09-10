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

import subprocess

from _reverseconnection import ReverseConnection

class ReverseShell(ReverseConnection):

    host = '127.0.0.1'    # The remote host
    port = 9001           # The same port as used by the server

    def on_connect(self, s):
        uname = self._run('uname -a')[0]
        s.send("%sType 'quit' to exit\n%% " % uname)

    def on_command(self, s, cmd):
        out, err = self._run(cmd)
        if err:
            out += err
        s.send(out + '\n% ')
        return True

    def _run(self, cmd):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out, err

ReverseShell().start()
