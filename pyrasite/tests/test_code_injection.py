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

import os
import subprocess
import sys
import tempfile

import pytest

import pyrasite
from pyrasite.tests.utils import (generate_program, interpreters, run_program,
                                  stop_program)

PAYLOAD_DIR = os.path.join(os.path.dirname(pyrasite.__file__), 'payloads')
HELLOWORLD = os.path.join(PAYLOAD_DIR, 'helloworld.py')


def _interpreters_or_skip():
    found = interpreters()
    if not found:
        return [pytest.param(sys.executable,
                             marks=pytest.mark.skip(
                                 reason="no usable CPython interpreters found"))]
    return found


@pytest.mark.parametrize('exe', _interpreters_or_skip())
def test_injecting_into_interpreter(exe, gdb_available):
    program = generate_program()
    try:
        p = run_program(program, exe=exe)
        try:
            pyrasite.inject(p.pid, HELLOWORLD)
        finally:
            stdout, stderr = stop_program(p)
        assert 'Hello World!' in stdout, \
            "Code injection into %s failed:\n%s\n%s" % (exe, stdout, stderr)
    finally:
        os.unlink(program)


@pytest.mark.parametrize('exe', _interpreters_or_skip())
def test_many_payloads_into_program_with_many_threads(exe, gdb_available):
    program = generate_program(threads=25)
    num_payloads = 5
    try:
        p = run_program(program, exe=exe)
        try:
            for _ in range(num_payloads):
                pyrasite.inject(p.pid, HELLOWORLD)
        finally:
            stdout, stderr = stop_program(p)
        count = sum(1 for line in stdout.splitlines()
                    if line.strip() == 'Hello World!')
        assert count == num_payloads, \
            "Read %d hello worlds from %s:\n%s\n%s" % (
                count, exe, stdout, stderr)
    finally:
        os.unlink(program)


@pytest.mark.parametrize('exe', _interpreters_or_skip())
def test_pyrasite_script(exe, gdb_available):
    program = generate_program()
    try:
        p = run_program(program, exe=exe)
        try:
            subprocess.run(
                [sys.executable, '-m', 'pyrasite.main', str(p.pid),
                 HELLOWORLD],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        finally:
            stdout, stderr = stop_program(p)
        assert 'Hello World!' in stdout, \
            "pyrasite CLI injection into %s failed:\n%s\n%s" % (
                exe, stdout, stderr)
    finally:
        os.unlink(program)


def test_injection_into_path_with_spaces(gdb_available):
    program = generate_program()

    # Put the payload in a directory whose name contains spaces and quotes.
    import tempfile
    directory = tempfile.mkdtemp(prefix='pyrasite payload "quoted" ')
    payload = os.path.join(directory, 'hello world.py')
    with open(payload, 'w') as f:
        f.write('print("Hello from a quoted path!", flush=True)\n')
    try:
        p = run_program(program)
        try:
            pyrasite.inject(p.pid, payload)
        finally:
            stdout, stderr = stop_program(p)
        assert 'Hello from a quoted path!' in stdout, \
            "%s\n%s" % (stdout, stderr)
    finally:
        os.unlink(program)
        os.unlink(payload)
        os.rmdir(directory)


def _write_payload(source):
    fd, path = tempfile.mkstemp(prefix='pyrasite-payload-', suffix='.py')
    with os.fdopen(fd, 'w') as f:
        f.write(source)
    return path


@pytest.mark.parametrize('threads', [1, 4])
def test_payload_exception_is_reported(threads, gdb_available):
    """A failing payload must raise in the client and leave the target alive.

    Reporting the error must not import anything inside the target: in a
    process with busy threads the import machinery can be extremely slow.
    """
    program = generate_program(threads=threads)
    payload = _write_payload('raise RuntimeError("boom from payload")\n')
    try:
        p = run_program(program)
        try:
            with pytest.raises(pyrasite.injector.InjectionError) as excinfo:
                pyrasite.inject(p.pid, payload)
            assert 'RuntimeError' in str(excinfo.value)
            assert 'boom from payload' in str(excinfo.value)
            # The wrapper catches the exception, so the target keeps running.
            assert p.poll() is None
        finally:
            stdout, stderr = stop_program(p)
        assert 'boom from payload' in stderr, \
            "Expected the traceback on the target's stderr:\n%s\n%s" % (
                stdout, stderr)
    finally:
        os.unlink(program)
        os.unlink(payload)
