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

import os
import sys
import subprocess

import pyrasite

from pyrasite.tests.utils import generate_program, run_program, stop_program, \
                                 interpreters, unittest


class TestCodeInjection(unittest.TestCase):

    def assert_output_contains(self, stdout, stderr, text):
        assert text in str(stdout), \
                "Code injection failed: %s\n%s" % (stdout, stderr)

    def test_injecting_into_all_interpreters(self):
        program = generate_program()
        try:
            for exe in interpreters():
                print("sys.executable = %s" % sys.executable)
                print("injecting into %s" % exe)
                p = run_program(program, exe=exe)
                pyrasite.inject(p.pid,
                        'pyrasite/payloads/helloworld.py', verbose=True)
                stop_program(p)
                stdout, stderr = p.communicate()
                self.assert_output_contains(stdout, stderr, 'Hello World!')
        finally:
            os.unlink(program)

    def test_many_payloads_into_program_with_many_threads(self):
        program = generate_program(threads=25)
        num_payloads = 25
        try:
            for exe in interpreters():
                p = run_program(program, exe=exe)
                for i in range(num_payloads):
                    pyrasite.inject(p.pid,
                            'pyrasite/payloads/helloworld.py', verbose=True)
                stop_program(p)
                stdout, stderr = p.communicate()
                count = 0
                for line in stdout.decode('utf-8').split('\n'):
                    if line.strip() == 'Hello World!':
                        count += 1
                assert count == num_payloads, "Read %d hello worlds" % count
        finally:
            os.unlink(program)

    def test_pyrasite_script(self):
        program = generate_program()
        try:
            for exe in interpreters():
                print("sys.executable = %s" % sys.executable)
                print("injecting into %s" % exe)
                p = run_program(program, exe=exe)
                subprocess.call([sys.executable, 'pyrasite/main.py',
                    str(p.pid), 'pyrasite/payloads/helloworld.py'],
                    env={'PYTHONPATH': os.getcwd()})
                stop_program(p)
                stdout, stderr = p.communicate()
                self.assert_output_contains(stdout, stderr, 'Hello World!')
        finally:
            os.unlink(program)

if __name__ == '__main__':
    unittest.main()
