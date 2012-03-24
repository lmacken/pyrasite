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
# Copyright (C) 2011, 2012 Red Hat, Inc.

import os
import unittest

import pyrasite
from pyrasite.tests.utils import run_program, generate_program, stop_program


class TestIPC(unittest.TestCase):

    def setUp(self):
        self.prog = generate_program()
        self.p = run_program(self.prog)
        self.ipc = pyrasite.PyrasiteIPC(self.p.pid)

    def tearDown(self):
        stop_program(self.p)
        self.ipc.close()

    def test_listen(self):
        self.ipc.listen()
        assert self.ipc.server_sock
        assert self.ipc.hostname
        assert self.ipc.port
        assert self.ipc.server_sock.getsockname()[1] == self.ipc.port

    def test_create_payload(self):
        self.ipc.listen()
        payload = self.ipc.create_payload()
        assert os.path.exists(payload)
        code = open(payload)
        compile(code.read(), payload, 'exec')
        code.close()
        os.unlink(payload)

    def test_connect(self):
        self.ipc.connect()
        assert self.ipc.sock
        assert self.ipc.address

    def test_cmd(self):
        self.ipc.connect()
        assert self.ipc.cmd('print("mu")') == 'mu\n'

    def test_unreliable(self):
        self.ipc.reliable = False
        self.ipc.connect()
        out = self.ipc.cmd('print("mu")')
        assert out == 'mu\n', out

    def test_repr(self):
        assert repr(self.ipc)


if __name__ == '__main__':
    unittest.main()
