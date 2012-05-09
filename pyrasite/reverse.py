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
"""
:mod:`pyrasite.reverse` - Pyrasite Reverse Connection Payload
=============================================================
"""

import sys
import socket
import traceback
import threading
from code import InteractiveConsole

if sys.version_info[0] == 3:
    from io import StringIO
else:
    from StringIO import StringIO

import pyrasite


class ReverseConnection(threading.Thread, pyrasite.PyrasiteIPC):
    """A payload that connects to a given host:port and receives commands"""

    host = 'localhost'
    port = 9001
    reliable = True

    def __init__(self, host=None, port=None):
        super(ReverseConnection, self).__init__()
        self.sock = None
        if host:
            self.host = host
        if port:
            self.port = port

    def on_connect(self):
        """Called when we successfuly connect to `self.host`"""

    def on_command(self, cmd):
        """Called when the host sends us a command"""

    def run(self):
        running = True
        while running:
            try:
                for res in socket.getaddrinfo(self.host, self.port,
                        socket.AF_UNSPEC, socket.SOCK_STREAM):
                    af, socktype, proto, canonname, sa = res
                    try:
                        self.sock = socket.socket(af, socktype, proto)
                        try:
                            self.sock.connect(sa)
                        except socket.error:
                            self.sock.close()
                            self.sock = None
                            continue
                    except socket.error:
                        self.sock = None
                        continue
                    break

                if not self.sock:
                    raise Exception('pyrasite cannot establish reverse ' +
                            'connection to %s:%d' % (self.host, self.port))

                self.on_connect()

                while running:
                    cmd = self.recv()
                    if cmd is None or cmd == "quit\n" or len(cmd) == 0:
                        running = False
                    else:
                        running = self.on_command(cmd)

            except:
                traceback.print_exc()
                running = False
            if not running:
                self.close()


class ReversePythonConnection(ReverseConnection):
    """A reverse Python connection payload.

    Executes Python commands and returns the output.
    """
    def on_command(self, cmd):
        buffer = StringIO()
        sys.stdout = buffer
        sys.stderr = buffer
        output = ''
        try:
            exec(cmd)
            output = buffer.getvalue()
        except:
            output = traceback.format_exc()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        buffer.close()
        self.send(output)
        return True


class DistantInteractiveConsole(InteractiveConsole):
    def __init__(self, ipc):
        InteractiveConsole.__init__(self, globals())

        self.ipc = ipc
        self.set_buffer()

    def set_buffer(self):
        self.out_buffer = StringIO()
        sys.stdout = sys.stderr = self.out_buffer

    def unset_buffer(self):
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        value = self.out_buffer.getvalue()
        self.out_buffer.close()

        return value

    def raw_input(self, prompt=""):
        output = self.unset_buffer()
        # payload format: 'prompt' ? '\n' 'output'
        self.ipc.send('\n'.join((prompt, output)))

        cmd = self.ipc.recv()

        self.set_buffer()

        return cmd


class ReversePythonShell(threading.Thread, pyrasite.PyrasiteIPC):
    """A reverse Python shell that behaves like Python interactive interpreter.

    """

    host = 'localhost'
    port = 9001
    reliable = True

    def __init__(self, host=None, port=None):
        super(ReversePythonShell, self).__init__()

    def run(self):
        try:
            for res in socket.getaddrinfo(self.host, self.port,
                    socket.AF_UNSPEC, socket.SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                try:
                    self.sock = socket.socket(af, socktype, proto)
                    try:
                        self.sock.connect(sa)
                    except socket.error:
                        self.sock.close()
                        self.sock = None
                        continue
                except socket.error:
                    self.sock = None
                    continue
                break

            if not self.sock:
                raise Exception('pyrasite cannot establish reverse ' +
                        'connection to %s:%d' % (self.host, self.port))

            DistantInteractiveConsole(self).interact()

        except SystemExit:
            pass
        except:
            traceback.print_exc(file=sys.__stderr__)

        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        self.close()
