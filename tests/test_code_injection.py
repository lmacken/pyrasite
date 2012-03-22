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
import time
import unittest
import textwrap
import tempfile
import subprocess

import pyrasite

subprocesses = []
default_payload = stop_payload = None


def teardown():
    os.unlink(default_payload)
    os.unlink(stop_payload)
    for p in subprocesses:
        try:
            p.kill()
        except:
            pass


class TestCodeInjection(unittest.TestCase):

    def __init__(self, *args, **kw):
        super(TestCodeInjection, self).__init__(*args, **kw)
        global default_payload, stop_payload
        self.stop_payload = default_payload = self.generate_payload_stopper()
        self.default_payload = stop_payload = self.generate_payload()

    def generate_payload(self, threads=1):
        (fd, filename) = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        script = textwrap.dedent("""
            import time, threading, random
            global running
            running = True
            def snooze():
                global running
                while running:
                    time.sleep(random.random())

            """)
        for t in range(threads):
            script += "threading.Thread(target=snooze).start()\n"
        tmp.write(script)
        tmp.close()
        return filename

    def generate_payload_stopper(self):
        (fd, filename) = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        tmp.write('globals()["running"] = False')
        tmp.close()
        return filename

    def run_python(self, payload, exe='python'):
        p = subprocess.Popen('%s %s' % (exe, payload),
                shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        subprocesses.append(p)
        return p

    def assert_output_contains(self, stdout, stderr, text):
        assert text in str(stdout), \
                "Code injection failed: %s\n%s" % (stdout, stderr)

    def test_threadless_injection(self):
        cmd = 'python -c "import time; time.sleep(0.5)"'
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        pyrasite.inject(p.pid, 'pyrasite/payloads/helloworld.py', verbose=True)
        pyrasite.inject(p.pid, self.stop_payload, verbose=True)
        stdout, stderr = p.communicate()
        self.assert_output_contains(stdout, stderr, 'Hello World!')

    def test_multithreaded_injection(self):
        p = self.run_python(self.default_payload)
        time.sleep(0.5)
        pyrasite.inject(p.pid, 'pyrasite/payloads/helloworld.py', verbose=True)
        pyrasite.inject(p.pid, self.stop_payload, verbose=True)
        stdout, stderr = p.communicate()
        self.assert_output_contains(stdout, stderr, 'Hello World!')

    def test_many_threads_and_many_payloads(self):
        payload = self.generate_payload(threads=100)
        p = self.run_python(payload)
        time.sleep(0.5)

        total = 100
        for i in range(total):
            pyrasite.inject(p.pid,
                    'pyrasite/payloads/helloworld.py', verbose=True)

        pyrasite.inject(p.pid, self.stop_payload, verbose=True)
        stdout, stderr = p.communicate()

        count = 0
        for line in stdout.decode('utf-8').split('\n'):
            if line.strip() == 'Hello World!':
                count += 1

        os.unlink(payload)

        assert count == total, "Read %d hello worlds" % count

    def test_injecting_into_the_same_interpreter(self):
        print("sys.executable = %s" % sys.executable)
        cmd = '%s -c "import time; time.sleep(2.0)"' % sys.executable
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        time.sleep(0.5)
        pyrasite.inject(p.pid, 'pyrasite/payloads/helloworld.py', verbose=True)
        stdout, stderr = p.communicate()
        self.assert_output_contains(stdout, stderr, 'Hello World!')

    def test_injecting_threads_into_the_same_interpreter(self):
        if sys.version_info[0] == 3: exe = 'python3'
        else: exe = 'python2'
        print("sys.executable = %s" % sys.executable)
        payload = self.generate_payload(threads=10)
        p = self.run_python(payload, exe=exe)
        time.sleep(0.5)
        pyrasite.inject(p.pid, 'pyrasite/payloads/helloworld.py', verbose=True)
        pyrasite.inject(p.pid, self.stop_payload, verbose=True)
        stdout, stderr = p.communicate()
        os.unlink(payload)
        assert 'Hello World!' in str(stdout), \
               "Code injection failed: %s\n%s" % (stdout, stderr)

    def test_injecting_into_different_interpreter_version(self):
        if sys.version_info[0] == 3: exe = 'python2'
        else: exe = 'python3'
        print("sys.executable = %s" % sys.executable)
        print("injecting into %s" % exe)
        cmd = '%s -c "import time; time.sleep(2.0)"' % exe
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
        time.sleep(0.5)
        pyrasite.inject(p.pid, 'pyrasite/payloads/helloworld.py', verbose=True)
        stdout, stderr = p.communicate()
        self.assert_output_contains(stdout, stderr, 'Hello World!')

    def test_injecting_threads_into_different_interpreter(self):
        if sys.version_info[0] == 3: exe = 'python2'
        else: exe = 'python3'
        print("sys.executable = %s" % sys.executable)
        payload = self.generate_payload(threads=10)
        p = self.run_python(payload, exe=exe)
        time.sleep(0.5)
        pyrasite.inject(p.pid, 'pyrasite/payloads/helloworld.py', verbose=True)
        pyrasite.inject(p.pid, self.stop_payload, verbose=True)
        stdout, stderr = p.communicate()
        os.unlink(payload)
        self.assert_output_contains(stdout, stderr, 'Hello World!')


if __name__ == '__main__':
    unittest.main()
