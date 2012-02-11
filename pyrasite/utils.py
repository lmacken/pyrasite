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

import os
import socket
import struct
import pyrasite
import tempfile
import warnings
import traceback
import subprocess

def run(cmd):
    p = subprocess.Popen(cmd, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        warnings.warn(err)
    return out.strip()


REVERSE_SHELL = """\
import sys, struct
sys.path.insert(0, "%s/../payloads/")

from StringIO import StringIO
from _reverseconnection import ReverseConnection

class ReversePythonShell(ReverseConnection):
    host = 'localhost'
    port = %d

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
        header = struct.pack('<L', len(output))
        s.sendall(header + output)
        return True

ReversePythonShell().start()
"""


class PyrasiteIPC(object):
    """
    An object that listens for connections from the reverse python shell payload,
    and then allows you to run commands in the other process.
    """
    def __init__(self, pid):
        super(PyrasiteIPC, self).__init__()
        self.pid = pid
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.bind(('localhost', 0))
        self.sock.listen(20)
        self.port = self.sock.getsockname()[1]
        self.client = None
        self.running = True

    def inject(self):
        # Write out a reverse subprocess payload with a custom port
        (fd, filename) = tempfile.mkstemp()
        self.filename = filename
        tmp = os.fdopen(fd, 'w')
        tmp.write(REVERSE_SHELL % (
            os.path.abspath(os.path.dirname(pyrasite.__file__)),
            self.port))
        tmp.close()

        injector = pyrasite.CodeInjector(self.pid)
        injector.inject(filename)

    def listen(self):
        (clientsocket, address) = self.sock.accept()
        self.client = clientsocket
        self.client.settimeout(3)

    def cmd(self, cmd):
        self.client.sendall(cmd + '\n')
        try:
            header_data = self._recv_bytes(4)
            if len(header_data) == 4:
                msg_len = struct.unpack('<L', header_data)[0]
                data = self._recv_bytes(msg_len)
                if len(data) == msg_len:
                    return data
                else:
                    print("Response doesn't match header len (%s) : %r" % (
                          msg_len, data))
        except:
            traceback.print_exc()
            self.close()

    def _recv_bytes(self, n):
        data = ''
        while len(data) < n:
            chunk = self.client.recv(n - len(data))
            if chunk == '':
                break
            data += chunk
        return data

    def close(self):
        os.unlink(self.filename)
        if self.client:
            self.client.sendall('exit\n')
            self.client.close()

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.pid)
