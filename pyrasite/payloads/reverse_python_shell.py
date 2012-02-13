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

import sys

from StringIO import StringIO

from _reverseconnection import ReverseConnection

class ReversePythonShell(ReverseConnection):

    host = '127.0.0.1'
    port = 9001

    def on_connect(self, s):
        s.send("Python %s\nType 'quit' to exit\n>>> " % sys.version)

    def on_command(self, s, cmd):
        buffer = StringIO()
        sys.stdout = buffer
        sys.stderr = buffer
        output = ''
        try:
            exec(cmd)
            output = buffer.getvalue()
        except Exception, e:
            output = str(e)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            buffer.close()
        s.send(output + '\n>>> ')
        return True

ReversePythonShell().start()
