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
:mod:`pyrasite.ipc` - Pyrasite Inter-Python Communication
=========================================================
"""

import contextlib
import os
import platform
import re
import socket
import stat
import struct
import subprocess
import tempfile
from os.path import abspath, dirname, join

import pyrasite


class PyrasiteIPC:
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

    def __init__(
        self,
        pid,
        reverse="ReversePythonConnection",
        timeout=5,
        inject_timeout=60,
        inject_method=None,
        bind_host="localhost",
        connect_host=None,
        port=None,
    ):
        super().__init__()
        self.pid = pid
        self.sock = None
        self.server_sock = None
        self.hostname = None
        self.port = port
        self.reverse = reverse
        self.timeout = float(timeout)
        self.inject_timeout = inject_timeout
        self.inject_method = inject_method
        self.bind_host = bind_host
        self.connect_host = connect_host

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    @property
    def title(self):
        if not getattr(self, "_title", None):
            if platform.system() == "Windows":
                p = subprocess.Popen(
                    'tasklist /v /fi "pid eq %d" /nh /fo csv' % self.pid,
                    stdout=subprocess.PIPE,
                    shell=True,
                )
                tmp = p.communicate()[0].decode("utf-8", "replace").strip().split(",")
                if tmp[-1] == '"N/A"':
                    self._title = tmp[0][1:-1]
                else:
                    self._title = tmp[-1][1:-1]
            else:
                p = subprocess.Popen(
                    ["ps", "-o", "command=", "-p", str(self.pid)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                out, _ = p.communicate()
                self._title = out.decode("utf-8", "replace")
        return self._title.strip()

    def connect(self):
        """
        Setup a communication socket with the process by injecting
        a reverse subshell and having it connect back to us.
        """
        self.listen()
        try:
            self.inject()
            self.wait()
        except BaseException:
            self.close()
            raise

    def listen(self):
        """Listen on a random port"""
        self.server_sock = None
        for res in socket.getaddrinfo(
            self.bind_host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, 0
        ):
            af, socktype, proto, _canonname, sa = res
            try:
                server_sock = socket.socket(af, socktype, proto)
                try:
                    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    server_sock.bind(sa)
                    server_sock.listen(1)
                except OSError:
                    server_sock.close()
                    server_sock = None
                    continue
            except OSError:
                server_sock = None
                continue
            self.server_sock = server_sock
            break

        if not self.server_sock:
            raise RuntimeError("pyrasite was unable to setup a local server socket")

        self.hostname, self.port = self.server_sock.getsockname()[0:2]

    def create_payload(self):
        """Write out a reverse python connection payload with a custom port"""
        fd, filename = tempfile.mkstemp(prefix="pyrasite-", suffix=".py")
        path = dirname(abspath(pyrasite.__file__))
        connect_host = self.connect_host or self.hostname
        with os.fdopen(fd, "w") as tmp:
            with open(join(path, "reverse.py")) as payload:
                for line in payload:
                    if line.startswith("#"):
                        continue
                    line = re.sub(
                        r"host = [\"']localhost[\"']",
                        "host = %r" % connect_host,
                        line,
                    )
                    line = line.replace("port = 9001", "port = %d" % self.port)
                    if not self.reliable:
                        line = line.replace("reliable = True", "reliable = False")
                    tmp.write(line)

            tmp.write("%s().start()\n" % self.reverse)

        if platform.system() != "Windows":
            os.chmod(filename, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

        return filename

    def inject(self):
        """Inject the payload into the process."""
        filename = self.create_payload()
        try:
            pyrasite.inject(
                self.pid,
                filename,
                timeout=self.inject_timeout,
                method=self.inject_method,
            )
        finally:
            os.unlink(filename)

    def wait(self):
        """Wait for the injected payload to connect back to us"""
        self.server_sock.settimeout(self.timeout)
        try:
            (clientsocket, address) = self.server_sock.accept()
        except socket.timeout:
            raise RuntimeError(
                "Timed out after %s seconds waiting for pid %s to connect "
                "back. Is ptrace enabled?" % (self.timeout, self.pid)
            ) from None
        self.sock = clientsocket
        self.sock.settimeout(self.timeout)
        self.address = address
        # We only accept one connection, so free the listening port.
        self.server_sock.close()
        self.server_sock = None

    def cmd(self, cmd):
        """
        Send a python command to exec in the process and return the output
        """
        if not isinstance(cmd, str):
            cmd = cmd.decode("utf-8")
        self.send(cmd + "\n")
        return self.recv()

    def send(self, data):
        """Send arbitrary data to the process via self.sock"""
        if self.sock is None:
            raise OSError("pyrasite connection is closed")
        if isinstance(data, str):
            data = data.encode("utf-8")
        header = b""
        if self.reliable:
            header = struct.pack("<L", len(data))
        self.sock.sendall(header + data)

    def recv(self):
        """Receive a command from a given socket"""
        if self.sock is None:
            raise OSError("pyrasite connection is closed")
        if self.reliable:
            header_data = self.recv_bytes(4)
            if len(header_data) == 4:
                msg_len = struct.unpack("<L", header_data)[0]
                data = self.recv_bytes(msg_len)
                if len(data) == msg_len:
                    return data.decode("utf-8")
        else:
            data = self.sock.recv(4096)
            if data:
                return data.decode("utf-8")
        return None

    def recv_bytes(self, n):
        """Receive n bytes from a socket"""
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def close(self):
        for sock in (self.sock, getattr(self, "server_sock", None)):
            if sock is not None:
                with contextlib.suppress(OSError):
                    sock.close()
        self.sock = None
        self.server_sock = None

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.pid)
