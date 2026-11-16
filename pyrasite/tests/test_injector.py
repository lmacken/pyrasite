"""Unit tests for the gdb command construction (no gdb required)."""

import os

import pytest

import pyrasite
from pyrasite.injector import InjectionError, build_code, build_gdb_argv
from pyrasite.tests.utils import generate_program, run_program, stop_program

HELLOWORLD = os.path.join(
    os.path.dirname(pyrasite.__file__), "payloads", "helloworld.py"
)


def test_build_code_uses_compile_and_absolute_path():
    filename = os.path.abspath("some payload with spaces.py")
    code = build_code(filename)
    assert "exec(compile(open(" in code
    assert repr(filename) in code
    assert repr(os.path.dirname(filename)) in code


def test_build_code_threading_depends_on_method():
    threaded = build_code("payload.py", threaded=True)
    assert "threading.Thread" in threaded
    inline = build_code("payload.py", threaded=False)
    assert "threading.Thread" not in inline
    assert "__pyrasite_inject()" in inline


def test_build_code_error_reporting_does_not_import_traceback():
    code = build_code("payload.py", marker="/tmp/marker")
    assert "import traceback" not in code
    assert "__pyrasite_traceback" in code


def test_build_gdb_argv_pending_is_shell_safe():
    filename = os.path.abspath('a "quoted" payload.py')
    argv = build_gdb_argv(1234, filename)
    assert argv[0] == "gdb"
    assert "-p" in argv and "1234" in argv
    assert any("Py_AddPendingCall" in arg for arg in argv)
    assert any("PyRun_SimpleString" in arg for arg in argv)
    assert any("break PyRun_SimpleString" in arg for arg in argv)


def test_build_gdb_argv_direct():
    filename = os.path.abspath("payload.py")
    argv = build_gdb_argv(1234, filename, method="direct")
    assert any("PyGILState_Ensure" in arg for arg in argv)
    assert any("PyRun_SimpleString" in arg for arg in argv)
    assert any("PyGILState_Release" in arg for arg in argv)


def test_build_gdb_argv_rejects_unknown_method():
    with pytest.raises(ValueError):
        build_gdb_argv(1234, "payload.py", method="nope")


def test_build_gdb_argv_prefix():
    argv = build_gdb_argv(1, "payload.py", gdb_prefix="/usr/local/bin/")
    assert argv[0] == "/usr/local/bin/gdb"


def test_injection_into_missing_process(gdb_available):
    with pytest.raises(InjectionError):
        pyrasite.inject(999999999, "pyrasite/payloads/helloworld.py")


def test_direct_injection(gdb_available):
    # A process whose main thread is sleeping has released the GIL, so the
    # direct method can run code without a pending call.
    program = generate_program(threads=0)
    try:
        p = run_program(program)
        try:
            pyrasite.inject(p.pid, HELLOWORLD, method="direct")
        finally:
            stdout, stderr = stop_program(p)
        assert "Hello World!" in stdout, "%s\n%s" % (stdout, stderr)
    finally:
        os.unlink(program)


def test_invalid_injection_method():
    with pytest.raises(ValueError):
        pyrasite.inject(1, "payload.py", method="nope")
