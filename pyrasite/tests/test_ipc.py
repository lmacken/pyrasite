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
import sys

import pyrasite
from pyrasite.tests.utils import run_program, generate_program, stop_program, unittest


class TestIPCContextManager(unittest.TestCase):

    def setUp(self):
        self.prog = generate_program()
        self.p = run_program(self.prog)

    def tearDown(self):
        stop_program(self.p)

    def test_context_manager(self):
        # Check that we're on a version of python that
        # supports context managers
        info = sys.version_info
        major, minor = info[0], info[1]
        if major <= 2 and minor <= 5:
            self.skipTest("Context Managers not supported on Python<=2.5")

        # Otherwise import a module which contains modern syntax.
        # It really contains our test case, but we have pushed it out into
        # another module so that python 2.4 never sees it.
        import pyrasite.tests.context_manager_case
        pyrasite.tests.context_manager_case.context_manager_business(self)


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
