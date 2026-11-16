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

"""Inject a Python file into a running interpreter using gdb.

There are two ways of running code in the target process.  :func:`inject`
picks one automatically based on the number of threads in the target, and
``method`` can be used to force a particular choice:

``pending``
    Ask CPython to execute the payload at its next bytecode boundary using
    :c:func:`Py_AddPendingCall`.  This is safe with multi-threaded programs:
    the code runs on a thread that already holds the GIL, so we never wait for
    a GIL owned by a thread that gdb has stopped.  The bootstrap starts the
    payload in a fresh daemon thread so that the interrupted thread can resume
    immediately.

``direct``
    Acquire the GIL with :c:func:`PyGILState_Ensure` and call
    :c:func:`PyRun_SimpleString` from gdb.  This can execute code in a process
    that is blocked in C, but deadlocks if another thread owns the GIL, which
    is why it is only used for single-threaded targets.  The payload runs
    inline, so gdb returns once it has finished.
"""

import contextlib
import os
import platform
import re
import subprocess
import tempfile
import time


class InjectionError(RuntimeError):
    """Raised when gdb could not inject the payload into the target."""


def _c_string(value):
    """Return *value* as a double-quoted C string literal.

    gdb evaluates the commands we pass it as C expressions, so the payload
    path has to be escaped using C rules.  We deliberately do not use
    :func:`repr`, because gdb treats single quotes as character literals.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return '"%s"' % escaped


def _python_string(value):
    """Return *value* as a Python string literal."""
    return repr(value)


def build_code(filename, marker=None, threaded=False, source=None):
    """Return the Python source that gdb should execute in the target.

    The payload is read here, in the calling process, and embedded in the gdb
    command.  The target therefore does not need read access to the payload
    file, which matters when injecting as root into a process running as
    another user.  The source is compiled with the original filename so that
    tracebacks still point at the real file, and encoding declarations are
    honoured.

    Both the payload's directory and the pyrasite source tree are added to
    ``sys.path`` so that payloads can import both their neighbours and
    pyrasite itself.

    When *marker* is given the wrapper writes ``ok`` to that file after the
    payload finishes, or ``error`` followed by the traceback if it raises.
    Catching the exception inside the target is important for the pending-call
    method: leaving an exception set in the interpreter can corrupt the next
    operation performed by the target.

    With *threaded* set the payload runs in a new daemon thread.  This is used
    for the pending-call method, where the bootstrap itself runs at an
    arbitrary bytecode boundary and must return as quickly as possible so that
    the target's interrupted thread can continue.  The direct method runs the
    payload inline instead, so that gdb's call returns only after the payload
    has finished.
    """
    filename = os.path.abspath(filename)
    if source is None:
        with open(filename, "rb") as payload_file:
            source = payload_file.read()
    payload_dir = os.path.dirname(filename)
    package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    lines = [
        "import sys",
        "sys.path.insert(0, %s)" % _python_string(payload_dir),
        "sys.path.insert(0, %s)" % _python_string(package_root),
        "",
        # Format the traceback by hand instead of importing the traceback
        # module.  Importing anything from the injected thread triggers the
        # import machinery, which can take seconds (or longer) in a busy
        # multi-threaded process because every import releases and reacquires
        # the GIL.  Everything below only uses builtins and sys.
        "def __pyrasite_traceback(exc):",
        '    lines = ["Traceback (most recent call last):"]',
        "    tb = exc.__traceback__",
        # Drop the frame belonging to this bootstrap; the useful part of the
        # traceback starts at the payload.
        '    if tb is not None and tb.tb_frame.f_code.co_name == "__pyrasite_inject":',
        "        tb = tb.tb_next",
        "    while tb is not None:",
        "        code = tb.tb_frame.f_code",
        "        lines.append(",
        "            '  File \"%s\", line %d, in %s' %",
        "            (code.co_filename, tb.tb_lineno, code.co_name))",
        "        tb = tb.tb_next",
        '    lines.append("%s: %s" % (type(exc).__name__, exc))',
        '    return "\\n".join(lines) + "\\n"',
    ]
    if marker is not None:
        marker_literal = _python_string(marker)
        lines.extend(
            [
                "",
                "def __pyrasite_report(status):",
                "    try:",
                '        with open(%s, "w") as marker_file:' % marker_literal,
                "            marker_file.write(status)",
                "    except BaseException:",
                "        pass",
            ]
        )
    lines.extend(
        [
            "",
            "def __pyrasite_inject():",
            "    try:",
            '        exec(compile(%s, %s, "exec"), globals())'
            % (_python_string(source), _python_string(filename)),
            "    except BaseException as exc:",
            "        try:",
            "            detail = __pyrasite_traceback(exc)",
            "        except BaseException:",
            '            detail = "Payload raised %s\\n" % type(exc).__name__',
            "        try:",
            "            sys.stderr.write(detail)",
            "            sys.stderr.flush()",
            "        except BaseException:",
            "            pass",
        ]
    )
    if marker is not None:
        lines.extend(
            [
                '        __pyrasite_report("error\\n" + detail)',
                "    else:",
                '        __pyrasite_report("ok")',
            ]
        )
    if threaded:
        lines.extend(
            [
                "",
                "import threading",
                'threading.Thread(target=__pyrasite_inject, name="pyrasite",'
                " daemon=True).start()",
            ]
        )
    else:
        lines.append("")
        lines.append("__pyrasite_inject()")
    return "\n".join(lines) + "\n"


def _gdb_base(pid, gdb_prefix=""):
    return [
        (gdb_prefix or "") + "gdb",
        "-p",
        str(pid),
        "-batch",
        "-nx",  # ignore the user's ~/.gdbinit
        "-eval-command=set pagination off",
        "-eval-command=set confirm off",
    ]


def build_gdb_argv(pid, filename, gdb_prefix="", method="pending", marker=None):
    """Build the gdb command line used to inject *filename* into *pid*."""
    if method not in ("pending", "direct"):
        raise ValueError("unknown injection method: %r" % (method,))

    argv = _gdb_base(pid, gdb_prefix=gdb_prefix)
    code = _c_string(
        build_code(filename, marker=marker, threaded=(method == "pending"))
    )

    if method == "direct":
        argv.extend(
            [
                "-eval-command=call (void*) PyGILState_Ensure()",
                "-eval-command=call (int) PyRun_SimpleString(%s)" % code,
                "-eval-command=call (void) PyGILState_Release($1)",
            ]
        )
    else:  # method == 'pending'
        # Py_AddPendingCall takes an int (*)(void *) callback.  PyRun_SimpleString
        # has a compatible calling convention (const char * -> int), so we can
        # use it directly.  strdup moves the source into the target's memory so
        # it outlives this gdb invocation.  The caller waits for the marker
        # file (or for the direct call to return) to know when the payload is
        # done.
        argv.extend(
            [
                "-eval-command=break PyRun_SimpleString",
                "-eval-command=call (int) Py_AddPendingCall("
                "(int (*)(void *)) PyRun_SimpleString, (void *) strdup(%s))" % code,
                "-eval-command=continue",
                "-eval-command=detach",
            ]
        )

    return argv


# These strings are printed by gdb when it fails to attach, find the
# interpreter, or call into it.  gdb itself often still exits with status 0 in
# these cases, so we have to inspect its output as well.
_GDB_ERROR_MARKERS = (
    "No such process",
    "ptrace: ",
    "No symbol table is loaded",
    "No symbol ",
    "Cannot access memory",
    "Could not attach",
    "Cannot call functions",
)


def _check_result(output, method):
    """Raise if gdb reported that our injection call failed."""
    if method == "pending":
        match = re.search(r"^\$1 = (-?\d+)\s*$", output, re.MULTILINE)
        if match and int(match.group(1)) != 0:
            raise InjectionError("Py_AddPendingCall failed with %s" % match.group(1))
    elif method == "direct":
        match = re.search(r"^\$2 = (-?\d+)\s*$", output, re.MULTILINE)
        if match and int(match.group(1)) != 0:
            raise InjectionError(
                "PyRun_SimpleString failed with %s; the payload may have "
                "raised an exception (see the target's stderr)" % match.group(1)
            )


def _thread_count(pid):
    """Return the number of threads in *pid* on Linux, or None."""
    try:
        with open("/proc/%d/status" % pid) as status:
            for line in status:
                if line.startswith("Threads:"):
                    return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def _pending_was_scheduled(output):
    match = re.search(r"^\$1 = (-?\d+)\s*$", output, re.MULTILINE)
    return match is not None and int(match.group(1)) == 0


def _new_marker():
    fd, path = tempfile.mkstemp(prefix="pyrasite-", suffix=".status")
    os.close(fd)
    os.unlink(path)
    return path


def _read_marker(path):
    try:
        with open(path) as marker:
            status = marker.read()
    except OSError:
        return None
    return status or None


def _wait_for_marker(path, deadline):
    while True:
        status = _read_marker(path)
        if status is not None:
            return status
        if deadline is not None and time.monotonic() >= deadline:
            return None
        time.sleep(0.05)


def _marker_error(status):
    if status.startswith("error"):
        detail = status[len("error") :].lstrip("\n")
        return "The payload raised an exception:\n%s" % detail
    return None


def _remaining(deadline):
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def _partial_output(exc):
    partial = ""
    if exc.stdout:
        partial += (
            exc.stdout
            if isinstance(exc.stdout, str)
            else exc.stdout.decode("utf-8", "replace")
        )
    if exc.stderr:
        partial += (
            exc.stderr
            if isinstance(exc.stderr, str)
            else exc.stderr.decode("utf-8", "replace")
        )
    return partial


def inject(
    pid, filename, verbose=False, gdb_prefix="", timeout=60, fallback=True, method=None
):
    """Execute a file in a running Python process.

    :param pid: process id of the target interpreter
    :param filename: path to the payload that should be executed
    :param verbose: print gdb's stdout and stderr
    :param gdb_prefix: prefix prepended to the ``gdb`` executable
    :param timeout: total number of seconds to wait for gdb and for the
        payload to finish. Pass ``None`` to wait forever.
    :param fallback: if the pending-call request could not be scheduled, try
        the direct GIL-based method as a fallback. The fallback is never used
        after a pending call has been successfully scheduled, since that would
        execute the payload twice.
    :param method: force a specific method (``'pending'`` or ``'direct'``).
        By default pyrasite uses ``direct`` for single-threaded processes and
        ``pending`` for multi-threaded ones.
    :raises InjectionError: if gdb could not inject the payload or the payload
        raised an exception
    """
    filename = os.path.abspath(filename)
    if method is None:
        if _thread_count(pid) == 1:
            methods = ("direct",)
        else:
            methods = ("pending", "direct") if fallback else ("pending",)
    elif method in ("pending", "direct"):
        methods = (method,)
    else:
        raise ValueError("unknown injection method: %r" % (method,))

    deadline = None if timeout is None else time.monotonic() + timeout
    errors = []

    for current_method in methods:
        marker = _new_marker()
        try:
            argv = build_gdb_argv(
                pid,
                filename,
                gdb_prefix=gdb_prefix,
                method=current_method,
                marker=marker,
            )
            try:
                p = subprocess.run(
                    argv,
                    capture_output=True,
                    timeout=_remaining(deadline),
                    text=True,
                )
            except FileNotFoundError:
                raise InjectionError(
                    "Could not find the gdb executable (%r). Please install "
                    "gdb." % argv[0]
                ) from None
            except subprocess.TimeoutExpired as e:
                partial = _partial_output(e)
                scheduled = current_method == "pending" and _pending_was_scheduled(
                    partial
                )
                errors.append(
                    "%s method timed out%s"
                    % (
                        current_method,
                        ("\n" + partial.strip()) if partial.strip() else "",
                    )
                )

                status = _read_marker(marker)
                if status is None and scheduled:
                    status = _wait_for_marker(marker, deadline)
                if status is not None:
                    problem = _marker_error(status)
                    if problem:
                        raise InjectionError(problem) from None
                    return 0

                if scheduled:
                    errors.append(
                        "The payload was queued with Py_AddPendingCall but "
                        "did not finish in time. It may still run later. Use "
                        "method='direct' for processes blocked in C."
                    )
                    break
                continue

            out, err = p.stdout, p.stderr
            if verbose:
                print(out)
                print(err)

            combined = out + err
            failed = p.returncode != 0
            if not failed:
                failed = any(
                    marker_text in combined for marker_text in _GDB_ERROR_MARKERS
                )
            if not failed:
                try:
                    _check_result(combined, current_method)
                except InjectionError as e:
                    failed = True
                    errors.append(str(e))

            status = _read_marker(marker)
            scheduled = current_method == "pending" and _pending_was_scheduled(combined)

            if current_method == "pending" and status is None and scheduled:
                status = _wait_for_marker(marker, deadline)

            if status is not None:
                problem = _marker_error(status)
                if problem:
                    raise InjectionError(problem) from None
                # The payload finished successfully. gdb may have failed while
                # detaching, but the work has been done.
                return p.returncode if not failed else 0

            if current_method == "pending":
                if scheduled:
                    errors.append(
                        "The payload was queued with Py_AddPendingCall but "
                        "did not report completion in time. It may still run "
                        "later. Use method='direct' for processes blocked in "
                        "C."
                    )
                    break
                # Nothing was queued, so trying the direct method is safe.
                if failed:
                    errors.append(
                        "gdb exited with %s:\n%s" % (p.returncode, combined.strip())
                    )
                continue

            # The direct method is synchronous, so a missing marker only means
            # the target could not write to /tmp. Trust gdb's result.
            if not failed:
                return p.returncode
            errors.append("gdb exited with %s:\n%s" % (p.returncode, combined.strip()))
        finally:
            with contextlib.suppress(OSError):
                os.unlink(marker)

    raise InjectionError(
        "Failed to inject %s into pid %s:\n%s" % (filename, pid, "\n".join(errors))
    )


if platform.system() == "Windows":

    def _inject_win(
        pid,
        filename,
        verbose=False,
        gdb_prefix="",
        timeout=60,
        fallback=True,
        method=None,
    ):
        if not gdb_prefix:
            gdb_prefix = os.path.join(os.path.dirname(__file__), "win") + os.sep
        filename = os.path.abspath(filename)
        # The helper takes forward-slash paths, but the payload source itself
        # must not be rewritten.
        code = build_code(filename.replace("\\", "/"))
        argv = [gdb_prefix + "inject_python_32.exe", str(pid), code]
        p = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout,
            text=True,
        )
        # The helper returns 25 when the target is a 64-bit interpreter.
        if p.returncode == 25:
            argv[0] = gdb_prefix + "inject_python_64.exe"
            p = subprocess.run(
                argv,
                capture_output=True,
                timeout=timeout,
                text=True,
            )
        if verbose:
            print(p.stdout)
            print(p.stderr)
        if p.returncode != 0:
            raise InjectionError(
                "Failed to inject %s into pid %s (exit code %s):\n%s"
                % (filename, pid, p.returncode, (p.stdout + p.stderr).strip())
            )
        return p.returncode

    inject = _inject_win
