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
:mod:`pyrasite.ipc` - Pyrasite Inter-Python Communication
=========================================================
"""

import os
import socket
import struct
import tempfile
import pyrasite

from os.path import dirname, abspath, join


class PyrasiteIPC(object):
    """Pyrasite Inter-Python Communication.

    This object is used in communicating to or from another Python process.

    It can perform a variety of tasks:

    - Injection of the :class:`pyrasite.ReversePythonConnection` payload via
      :meth:`PyrasiteIPC.connect()`, which causes the process to connect back
      to a port that we are listening on. The connection with the process is
      then available via `self.sock`.

    - Python code can then be executed in the process using
      :meth:`PyrasiteIPC.cmd`. Both stdout and stderr are returned.

    - Low-level communication with the process, both reliably (via a length
      header) or unreliably (raw data, ideal for use with netcat) with a
      :class:`pyrasite.ReversePythonConnection` payload, via
      :meth:`PyrasiteIPC.send(data)` and :meth:`PyrasiteIPC.recv(data)`.

    The :class:`PyrasiteIPC` is subclassed by
    :class:`pyrasite.tools.gui.Process` as well as
    :class:`pyrasite.reverse.ReverseConnection`.

    """
    # Allow subclasses to disable this and just send/receive raw data, as
    # opposed to prepending a length header, to ensure reliability. The reason
    # to enable 'unreliable' connections is so we can still use our reverse
    # shell payloads with netcat.
    reliable = True

    def __init__(self, pid):
        super(PyrasiteIPC, self).__init__()
        self.pid = pid
        self.sock = None

    def connect(self):
        """
        Setup a communication socket with the process by injecting
        a reverse subshell and having it connect back to us.
        """
        self.listen()
        self.inject()
        self.wait()

    def listen(self):
        """Listen on a random port"""
        for res in socket.getaddrinfo('localhost', None, socket.AF_UNSPEC,
                                      socket.SOCK_STREAM, 0, 0):
            af, socktype, proto, canonname, sa = res
            try:
                self.server_sock = socket.socket(af, socktype, proto)
            except socket.error:
                self.server_sock = None
                continue
            try:
                self.server_sock.bind(sa)
                self.server_sock.listen(1)
            except socket.error:
                self.server_sock.close()
                self.server_sock = None
                continue
            break

        self.hostname, self.port = self.server_sock.getsockname()[0:2]
        self.running = True

    def create_payload(self):
        """Write out a reverse python connection payload with a custom port"""
        (fd, filename) = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        path = dirname(abspath(join(pyrasite.__file__, '..')))
        payload = open(join(path, 'pyrasite', 'reverse.py'))
        tmp.write('import sys; sys.path.insert(0, "%s")\n' % path)

        for line in payload.readlines():
            if line.startswith('#'):
                continue
            line = line.replace('port = 9001', 'port = %d' % self.port)
            line = line.replace('reliable = False', 'reliable = True')
            tmp.write(line)

        tmp.write('ReversePythonConnection().start()\n')
        tmp.close()
        payload.close()

        return filename

    def inject(self):
        """Inject the payload into the process."""
        filename = self.create_payload()
        injector = pyrasite.CodeInjector(self.pid)
        injector.inject(filename)
        os.unlink(filename)

    def wait(self):
        """Wait for the injected payload to connect back to us"""
        (clientsocket, address) = self.server_sock.accept()
        self.sock = clientsocket
        self.sock.settimeout(5)
        self.address = address

    def cmd(self, cmd):
        """
        Send a python command to exec in the process and return the output
        """
        self.send(cmd + '\n')
        return self.recv()

    def send(self, data):
        """Send arbitrary data to the process via self.sock"""
        header = b''
        data = data.encode('utf-8')
        if self.reliable:
            header = struct.pack('<L', len(data))
        self.sock.sendall(header + data)

    def recv(self):
        """Receive a command from a given socket"""
        if self.reliable:
            header_data = self.recv_bytes(4)
            if len(header_data) == 4:
                msg_len = struct.unpack('<L', header_data)[0]
                data = self.recv_bytes(msg_len).decode('utf-8')
                if len(data) == msg_len:
                    return data
        else:
            return self.sock.recv(4096)

    def recv_bytes(self, n):
        """Receive n bytes from a socket"""
        data = b''
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def close(self):
        if self.sock:
            self.sock.close()

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.pid)

    def __str__(self):
        return self.title
