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
import time
import glob
import signal
import atexit
import unittest
import textwrap
import tempfile
import subprocess

import pyrasite

pids = []
default_program = stop_program = None


def cleanup():
    os.unlink(default_program)
    os.unlink(stop_program)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass

atexit.register(cleanup)


class TestCodeInjection(unittest.TestCase):

    def __init__(self, *args, **kw):
        super(TestCodeInjection, self).__init__(*args, **kw)
        global default_program, stop_program
        self.stop_program = stop_program = self.generate_program_stopper()
        self.default_program = default_program = self.generate_program()

    def generate_program(self, cpu_threads=1, io_threads=1):
        (fd, filename) = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        script = textwrap.dedent("""
            import time, threading, random
            running = True
            def cpu_bound():
                i = 2
                y = 0
                def fib(n):
                    return fib(n - 1) + fib(n - 2)
                while running:
                    y += fib(i)
                    i += 1
            def io_bound():
                rand = SystemRandom()
                while running:
                    rand.random()
        """)
        # CPU-bound threads
        for t in range(cpu_threads):
            script += "threading.Thread(target=cpu_bound).start()\n"
        # I/O bound (/dev/urandom)
        for t in range(io_threads):
            script += "threading.Thread(target=io_bound).start()\n"
        tmp.write(script)
        tmp.close()
        return filename

    def generate_program_stopper(self):
        (fd, filename) = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        tmp.write('globals()["running"] = False')
        tmp.close()
        return filename

    def generate_single_character_printer(self):
        (fd, filename) = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        tmp.write("print('!')")
        tmp.close()
        return filename

    def run_python(self, program, exe='python'):
        p = subprocess.Popen('%s %s' % (exe, program),
                shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        pids.append(p.pid)
        # FIXME: Hack to ensure that python (3, specifically) fully loads
        # before we inject code into it. To optimize this, we should
        # have the program print something out once it's loaded, then
        # we should ensure this happens before injecting.
        time.sleep(0.5)
        return p

    def assert_output_contains(self, stdout, stderr, text):
        assert text in str(stdout), \
                "Code injection failed: %s\n%s" % (stdout, stderr)

    def interpreters(self):
        for exe in glob.glob('/usr/bin/python*.*'):
            try:
                int(exe.split('.')[-1])
            except ValueError:
                continue  # skip python2.7-config, etc
            yield exe

    def test_injection_into_all_interpreters_with_no_threads(self):
        for exe in self.interpreters():
            print("sys.executable = %s" % sys.executable)
            print("injecting into %s" % exe)
            p = self.run_python('-c "import time; time.sleep(2.0)"', exe=exe)
            pyrasite.inject(p.pid,
                    'pyrasite/payloads/helloworld.py', verbose=True)
            stdout, stderr = p.communicate()
            self.assert_output_contains(stdout, stderr, 'Hello World!')

    def test_injecting_into_all_interpreters_with_gil_contention(self):
        program = self.generate_program(cpu_threads=3, io_threads=3)
        try:
            for exe in self.interpreters():
                print("sys.executable = %s" % sys.executable)
                print("injecting into %s" % exe)
                p = self.run_python(program, exe=exe)
                pyrasite.inject(p.pid,
                        'pyrasite/payloads/helloworld.py', verbose=True)
                pyrasite.inject(p.pid, self.stop_program, verbose=True)
                stdout, stderr = p.communicate()
                self.assert_output_contains(stdout, stderr, 'Hello World!')
        finally:
            os.unlink(program)

    def test_many_payloads_into_program_with_many_threads(self):
        program = self.generate_program(cpu_threads=3, io_threads=3)
        for exe in self.interpreters():
            p = self.run_python(program, exe=exe)

            total = 100
            for i in range(total):
                pyrasite.inject(p.pid,
                        'pyrasite/payloads/helloworld.py', verbose=True)

            pyrasite.inject(p.pid, self.stop_program, verbose=True)
            stdout, stderr = p.communicate()

            count = 0
            for line in stdout.decode('utf-8').split('\n'):
                if line.strip() == 'Hello World!':
                    count += 1

        os.unlink(program)

        assert count == total, "Read %d hello worlds" % count


if __name__ == '__main__':
    unittest.main()
