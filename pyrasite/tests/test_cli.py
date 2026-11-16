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

import os

import pytest

import pyrasite
from pyrasite.main import main
from pyrasite.tests.utils import generate_program, run_program, stop_program


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
