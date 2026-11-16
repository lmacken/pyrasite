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

"""Helpers shared by the pyrasite test suite."""

import contextlib
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time

# PR_SET_PTRACER and PR_SET_PTRACER_ANY from linux/prctl.h.  Recent Linux
# kernels default to Yama's restricted ptrace mode, which only allows a
# process to be traced by its ancestors.  gdb is a sibling of our test target,
# so the target opts in to being traced by anybody.
PR_SET_PTRACER = 0x59616D61
PR_SET_PTRACER_ANY = -1


def allow_ptrace_any():
    """Let any process attach to the current process (Linux only)."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        import ctypes

        libc = ctypes.CDLL(None, use_errno=True)
        return libc.prctl(PR_SET_PTRACER, PR_SET_PTRACER_ANY, 0, 0, 0) == 0
    except Exception:
        return False


def has_gdb():
    return shutil.which("gdb") is not None


def generate_program(threads=1):
    """Write a small long-running program and return its filename."""
    fd, filename = tempfile.mkstemp(prefix="pyrasite-target-", suffix=".py")
    with os.fdopen(fd, "w") as tmp:
        script = textwrap.dedent("""
            import ctypes, os, sys, tempfile, time, threading

            # Opt in to being traced even when Yama's ptrace_scope is 1.
            if sys.platform.startswith('linux'):
                try:
                    ctypes.CDLL(None).prctl(0x59616d61, ctypes.c_ulong(-1),
                                            0, 0, 0)
                except Exception:
                    pass

            running = True
            pidfile = os.path.join(tempfile.gettempdir(),
                                   'pyrasite_%d' % os.getpid())

            def cpu_bound():
                i = 0
                while running:
                    i += 1

            def wait_for_exit():
                while os.path.exists(pidfile):
                    time.sleep(0.1)
                global running
                running = False
        """)
    # CPU-bound threads
    for _ in range(threads):
        script += "threading.Thread(target=cpu_bound).start()\n"
    # Signal that the target is fully started only after all threads exist.
    script += "open(pidfile, 'w').close()\n"
    script += "wait_for_exit()\n"
    with open(filename, "a") as tmp:
        tmp.write(script)
    return filename


def run_program(program, exe=None):
    """Start *program* with *exe* and wait until it is ready."""
    if exe is None:
        exe = sys.executable
    p = subprocess.Popen(
        [exe, program],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    flag = os.path.join(tempfile.gettempdir(), "pyrasite_%d" % p.pid)
    # Interpreter startup can be slow on a loaded CI machine.
    for _ in range(600):
        if os.path.exists(flag):
            return p
        if p.poll() is not None:
            out, err = p.communicate()
            raise RuntimeError(
                "Target interpreter %s exited immediately:\n%s\n%s" % (exe, out, err)
            )
        time.sleep(0.05)
    p.kill()
    raise RuntimeError("Program never touched pid file!")


def stop_program(p):
    """Stop a program started by :func:`run_program` and return its output."""
    cached = getattr(p, "_pyrasite_output", None)
    if cached is not None:
        return cached
    flag = os.path.join(tempfile.gettempdir(), "pyrasite_%d" % p.pid)
    with contextlib.suppress(OSError):
        os.unlink(flag)
    try:
        out, err = p.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
    result = (out, err)
    p._pyrasite_output = result
    return result


def _is_usable(exe):
    """Return True if *exe* is a CPython >= 3.9 interpreter."""
    if os.path.basename(exe).startswith("pypy"):
        return False
    try:
        out = subprocess.check_output(
            [
                exe,
                "-c",
                "import sys; print(sys.version_info[0], "
                "sys.version_info[1], sys.implementation.name)",
            ],
            stderr=subprocess.DEVNULL,
            timeout=20,
            text=True,
        )
    except Exception:
        return False
    try:
        major, minor, impl = out.split()
    except ValueError:
        return False
    return impl == "cpython" and (int(major), int(minor)) >= (3, 9)


def _candidate_interpreters():
    candidates = [sys.executable]

    # Explicitly requested interpreters win, and are the easiest way to test
    # cross-version injection with interpreters not named python3.x in PATH.
    explicit = os.environ.get("PYRASITE_TEST_INTERPRETERS")
    if explicit:
        candidates.extend(x for x in explicit.split(os.pathsep) if x)
        return candidates

    pattern = re.compile(r"^python3\.\d+$")
    seen_dirs = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        directory = directory or "."
        if directory in seen_dirs:
            continue
        seen_dirs.add(directory)
        try:
            entries = os.listdir(directory)
        except OSError:
            continue
        for name in entries:
            if pattern.match(name):
                candidates.append(os.path.join(directory, name))

    for pattern in ("/usr/bin/python3.*", "/usr/local/bin/python3.*"):
        candidates.extend(glob.glob(pattern))

    return candidates


def interpreters():
    """Yield usable CPython interpreters available on this machine."""
    seen = set()
    result = []
    for exe in _candidate_interpreters():
        if not exe or not os.path.exists(exe):
            continue
        real = os.path.realpath(exe)
        if real in seen:
            continue
        seen.add(real)
        if _is_usable(exe):
            result.append(exe)
    return result
