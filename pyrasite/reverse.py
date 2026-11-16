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
"""
:mod:`pyrasite.reverse` - Pyrasite Reverse Connection Payload
=============================================================
"""

import os
import socket
import sys
import threading
import traceback
from code import InteractiveConsole
from io import StringIO

import pyrasite


class ReverseConnection(pyrasite.PyrasiteIPC, threading.Thread):
    """A payload that connects to a given host:port and receives commands"""

    host = 'localhost'
    port = 9001
    reliable = True

    def __init__(self, host=None, port=None):
        default_host, default_port = self.host, self.port
        pyrasite.PyrasiteIPC.__init__(self, pid=os.getpid())
        threading.Thread.__init__(self, daemon=True)
        self.sock = None
        self.host = host or default_host
        self.port = port or default_port

    def on_connect(self):
        """Called when we successfully connect to `self.host`"""

    def on_command(self, cmd):
        """Called when the host sends us a command"""

    def _connect(self):
        last_error = None
        for res in socket.getaddrinfo(self.host, self.port,
                                      socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                sock = socket.socket(af, socktype, proto)
                try:
                    sock.connect(sa)
                except OSError as e:
                    sock.close()
                    last_error = e
                    continue
            except OSError as e:
                last_error = e
                continue
            self.sock = sock
            return

        raise OSError(
            'pyrasite cannot establish reverse connection to %s:%d (%s)' %
            (self.host, self.port, last_error))

    def run(self):
        try:
            self._connect()
            self.on_connect()
            while True:
                cmd = self.recv()
                if not cmd or cmd.strip() == 'quit':
                    break
                if not self.on_command(cmd):
                    break
        except Exception:
            traceback.print_exc()
        finally:
            self.close()


class ReversePythonConnection(ReverseConnection):
    """A reverse Python connection payload.

    Executes Python commands and returns the output.
    """

    def __init__(self, host=None, port=None):
        super(ReversePythonConnection, self).__init__(host=host, port=port)
        # Keep a persistent namespace so commands can define variables that
        # are still available to later commands.
        self.namespace = {'__name__': '__pyrasite__'}

    def on_command(self, cmd):
        buffer = StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = buffer
        try:
            try:
                exec(cmd, self.namespace)
            except SystemExit:
                pass
            output = buffer.getvalue()
        except BaseException:
            output = buffer.getvalue() + traceback.format_exc()
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
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

        if cmd is None:
            raise EOFError
        return cmd


class ReversePythonShell(pyrasite.PyrasiteIPC, threading.Thread):
    """A reverse Python shell that behaves like Python interactive interpreter.

    """

    host = 'localhost'
    port = 9001
    reliable = True

    def __init__(self, host=None, port=None):
        default_host, default_port = self.host, self.port
        pyrasite.PyrasiteIPC.__init__(self, pid=os.getpid())
        threading.Thread.__init__(self, daemon=True)
        self.host = host or default_host
        self.port = port or default_port

    def _connect(self):
        last_error = None
        for res in socket.getaddrinfo(self.host, self.port,
                                      socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                sock = socket.socket(af, socktype, proto)
                try:
                    sock.connect(sa)
                except OSError as e:
                    sock.close()
                    last_error = e
                    continue
            except OSError as e:
                last_error = e
                continue
            self.sock = sock
            return

        raise OSError(
            'pyrasite cannot establish reverse connection to %s:%d (%s)' %
            (self.host, self.port, last_error))

    def run(self):
        try:
            self._connect()
            DistantInteractiveConsole(self).interact()
        except SystemExit:
            pass
        except Exception:
            traceback.print_exc(file=sys.__stderr__)
        finally:
            sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
            self.close()
