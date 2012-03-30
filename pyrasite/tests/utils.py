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
# Copyright (C) 2011-2012 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import os
import sys
import glob
import time
import textwrap
import tempfile
import subprocess
import unittest

if sys.version_info[0] == 2:
    if sys.version_info[1] < 7:
        import unittest2 as unittest


def generate_program(threads=1):
    (fd, filename) = tempfile.mkstemp()
    tmp = os.fdopen(fd, 'w')
    script = textwrap.dedent("""
        import os, time, threading
        running = True
        pidfile = '/tmp/pyrasite_%d' % os.getpid()
        open(pidfile, 'w').close()
        def cpu_bound():
            i = 0
            while running:
                i += 1
    """)
    # CPU-bound threads
    for t in range(threads):
        script += "threading.Thread(target=cpu_bound).start()\n"
    script += textwrap.dedent("""
        while os.path.exists(pidfile):
            time.sleep(0.1)
        running = False
    """)
    tmp.write(script)
    tmp.close()
    return filename


def run_program(program, exe='/usr/bin/python'):
    p = subprocess.Popen([exe, program],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    flag = '/tmp/pyrasite_%d' % p.pid
    i = 0
    while not os.path.exists(flag):
        time.sleep(0.1)
        i += 1
        if i > 100:
            raise Exception("Program never touched pid file!")
    return p


def stop_program(p):
    os.unlink('/tmp/pyrasite_%d' % p.pid)


def interpreters():
    for exe in glob.glob('/usr/bin/python*.*'):
        try:
            int(exe.split('.')[-1])
        except ValueError:
            continue  # skip python2.7-config, etc
        yield exe
