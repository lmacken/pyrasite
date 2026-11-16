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
# Copyright (C) 2011-2013 Red Hat, Inc.

import os

import pytest

import pyrasite
from pyrasite.tests.utils import generate_program, run_program, stop_program


@pytest.fixture
def target(gdb_available):
    program = generate_program()
    p = run_program(program)
    try:
        yield p
    finally:
        stop_program(p)
        os.unlink(program)


@pytest.fixture
def ipc(target):
    ipc = pyrasite.PyrasiteIPC(target.pid)
    try:
        yield ipc
    finally:
        ipc.close()


def test_listen(ipc):
    ipc.listen()
    assert ipc.server_sock
    assert ipc.hostname
    assert ipc.port
    assert ipc.server_sock.getsockname()[1] == ipc.port


def test_create_payload(ipc):
    ipc.listen()
    ipc.hostname = "example.test"
    payload = ipc.create_payload()
    try:
        assert os.path.exists(payload)
        with open(payload) as code:
            source = code.read()
        compile(source, payload, "exec")
        assert "host = %r" % ipc.hostname in source
        assert "port = %d" % ipc.port in source
    finally:
        os.unlink(payload)


def test_connect(ipc):
    ipc.connect()
    assert ipc.sock
    assert ipc.address


def test_cmd(ipc):
    ipc.connect()
    assert ipc.cmd('print("mu")') == "mu\n"


def test_cmd_keeps_namespace(ipc):
    ipc.connect()
    ipc.cmd("pyrasite_test_value = 41")
    assert ipc.cmd("print(pyrasite_test_value + 1)") == "42\n"


def test_unreliable(ipc):
    ipc.reliable = False
    ipc.connect()
    out = ipc.cmd('print("mu")')
    assert out == "mu\n", out


def test_repr(ipc):
    assert repr(ipc)


def test_title(ipc):
    assert ipc.title


def test_context_manager(target):
    with pyrasite.PyrasiteIPC(target.pid) as ipc:
        assert ipc.cmd('print("mu")') == "mu\n"

    # The context manager must close the connection.
    with pytest.raises(OSError):
        ipc.cmd('print("mu")')


def test_wait_timeout(target):
    ipc = pyrasite.PyrasiteIPC(target.pid, timeout=0.1)
    ipc.listen()
    try:
        with pytest.raises(RuntimeError):
            ipc.wait()
    finally:
        ipc.close()
