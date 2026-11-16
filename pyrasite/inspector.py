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

import subprocess

_INSPECT_MARKER = "__PYRASITE_INSPECT__"

# Distribution Python builds are stripped, so gdb cannot resolve the PyObject
# type.  The stable C API is available through the dynamic symbol table, so
# this script calls it from gdb's Python interpreter.  gdb keeps the other
# threads running while an inferior call executes, which lets PyGILState_Ensure
# take the GIL even if another thread held it when gdb attached.
_GDB_SCRIPT = """
import gdb

inferior = gdb.selected_inferior()


def readable(address):
    for size in (16, 1):
        try:
            inferior.read_memory(address, size)
            return True
        except Exception:
            continue
    return False


def evaluate(expression):
    return int(gdb.parse_and_eval(expression))


def inspect(address):
    if not readable(address):
        return "<address is not readable>"
    gil = evaluate("(int) PyGILState_Ensure()")
    try:
        obj = evaluate("(void*) PyObject_Repr((void*) %d)" % address)
        if obj == 0:
            gdb.execute("call (void) PyErr_Clear()")
            return "<repr raised an exception>"
        value = evaluate("(char*) PyUnicode_AsUTF8((void*) %d)" % obj)
        if value == 0:
            return "<value is not printable>"
        try:
            return gdb.parse_and_eval("(char*) %d" % value).string()
        except Exception:
            return "<value contains invalid characters>"
    finally:
        gdb.execute("call (void) PyGILState_Release(%d)" % gil)


gdb.write("__MARKER__%s\\n" % inspect(__ADDRESS__))
"""


def _run_gdb(gdb, pid, commands, timeout):
    argv = [gdb, "--quiet", "-p", str(pid), "-batch", "-nx", *commands]
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _inspect_with_c_api(gdb, pid, address, timeout):
    """Return the repr of the object using only exported C symbols."""
    try:
        numeric = int(address, 0) if isinstance(address, str) else int(address)
    except (TypeError, ValueError):
        return None

    script = _GDB_SCRIPT.replace("__ADDRESS__", str(numeric)).replace(
        "__MARKER__", _INSPECT_MARKER
    )
    p = _run_gdb(gdb, pid, ["-eval-command=python exec(%r)" % script], timeout)
    if p is None or _INSPECT_MARKER not in p.stdout:
        return None
    return p.stdout.split(_INSPECT_MARKER, 1)[1].splitlines()[0]


def _inspect_with_gdb_types(gdb, pid, address, timeout):
    """Use gdb's type information when the target has Python debug symbols."""
    p = _run_gdb(
        gdb,
        pid,
        ["-eval-command=print (PyObject *)%s" % address],
        timeout,
    )
    if p is None:
        return None
    for line in p.stdout.splitlines():
        if line.startswith("$1 = "):
            return line[5:]
    return None


def inspect(pid, address, gdb_prefix="", timeout=10):
    """Return the value of an object in a given process at the specified address.

    The primary implementation uses the stable C API and therefore works with
    stripped distribution Python builds.  If that fails, ``gdb``'s knowledge of
    the ``PyObject`` type is used, which requires the Python debug symbols.
    """
    gdb = (gdb_prefix or "") + "gdb"
    value = _inspect_with_c_api(gdb, pid, address, timeout)
    if value is not None:
        return value
    return _inspect_with_gdb_types(gdb, pid, address, timeout)
