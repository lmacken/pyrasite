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
# Copyright (C) 2013 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import io
import os
import sys
import threading
from types import SimpleNamespace

import pytest

import pyrasite
from pyrasite.main import main
from pyrasite.tests.utils import generate_program, run_program, stop_program
from pyrasite.tools.shell import shell


def test_version_matches_package_metadata():
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python 3.7 only
        return
    try:
        installed = version("pyrasite")
    except PackageNotFoundError:
        pytest.skip("pyrasite is not installed in this environment")
    assert pyrasite.__version__ == installed


def test_usage(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 1
    assert "usage:" in capsys.readouterr().out


def test_list_payloads(capsys):
    with pytest.raises(SystemExit):
        main(["-l"])
    value = capsys.readouterr().out
    assert "Available payloads:" in value, repr(value)
    assert "helloworld.py" in value, repr(value)


def test_invalid_pid(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["foo", "bar"])
    assert excinfo.value.code == 2
    assert "Error: The first argument must be a pid" in capsys.readouterr().err


def test_missing_pid(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--verbose"])
    assert excinfo.value.code == 2
    assert "Error: The first argument must be a pid" in capsys.readouterr().err


def test_invalid_payload(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([str(os.getpid()), "foo"])
    assert excinfo.value.code == 3
    assert "Error: Invalid path or file doesn't exist" in capsys.readouterr().err


def test_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert pyrasite.__version__ in capsys.readouterr().out


@pytest.fixture
def target(gdb_available):
    program = generate_program()
    p = run_program(program)
    try:
        yield p
    finally:
        stop_program(p)
        os.unlink(program)


def test_injection(target):
    main([str(target.pid), "helloworld.py"])
    stdout, _ = stop_program(target)
    assert "Hello World!" in stdout


def test_injection_localterm(target, capsys):
    main([str(target.pid), "helloworld.py", "--output", "localterm"])
    assert "Hello World!" in capsys.readouterr().out


def test_verbose_output_is_text(target, capsys):
    main([str(target.pid), "helloworld.py", "--verbose"])
    out = capsys.readouterr().out
    assert "b'" not in out
    assert 'b"' not in out


def test_injection_from_stdin(target, monkeypatch):
    source = b'print("payload from stdin")\n'
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(source)))
    main([str(target.pid), "-"])
    stdout, stderr = stop_program(target)
    assert "payload from stdin" in stdout, "%s\n%s" % (stdout, stderr)


def test_shell_command_can_outlast_the_connect_timeout(target, monkeypatch, capsys):
    """A slow command must not hit the connect-back timeout (#51).

    PYRASITE_IPC_TIMEOUT bounds how long we wait for the reverse connection.
    Applying it to the command socket made any remotely executed command that
    took longer than a few seconds fail with socket.timeout.
    """
    monkeypatch.setenv("PYRASITE_IPC_TIMEOUT", "1")
    monkeypatch.setattr(sys, "argv", ["pyrasite-shell", str(target.pid)])
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO("import time; time.sleep(1.5)\nprint('slow command finished')\n"),
    )

    shell()

    out = capsys.readouterr().out
    assert "slow command finished" in out


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires mkfifo")
def test_injection_from_fifo(target, tmp_path):
    fifo = tmp_path / "payload.fifo"
    os.mkfifo(fifo)
    source = 'print("payload from a fifo")\n'

    def writer():
        with open(fifo, "w") as payload:
            payload.write(source)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    try:
        main([str(target.pid), str(fifo)])
    finally:
        thread.join(timeout=5)
    stdout, stderr = stop_program(target)
    assert "payload from a fifo" in stdout, "%s\n%s" % (stdout, stderr)
