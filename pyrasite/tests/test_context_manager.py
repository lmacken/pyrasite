import sys
import unittest

import pyrasite
from pyrasite.tests.utils import run_program, generate_program, stop_program


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

        # Check that the context manager injects ipc correctly.
        with pyrasite.PyrasiteIPC(self.p.pid) as ipc:
            assert ipc.cmd('print("mu")') == 'mu\n'

        # Check that the context manager closes the ipc correctly.
        try:
            ipc.cmd('print("mu")')
            assert False, "The connection was not closed."
        except IOError as e:
            assert "Bad file descriptor" in str(e)
