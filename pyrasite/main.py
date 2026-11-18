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

import argparse
import contextlib
import os
import subprocess
import sys
import tempfile

import pyrasite
from pyrasite.injector import InjectionError


def ptrace_check():
    """Warn if the system is configured to disallow ptrace attachments."""
    if os.geteuid() == 0:
        # root has CAP_SYS_PTRACE on normal systems, so Yama's ptrace_scope
        # does not restrict it and the warning would be misleading.
        return
    ptrace_scope = "/proc/sys/kernel/yama/ptrace_scope"
    if os.path.exists(ptrace_scope):
        with open(ptrace_scope) as f:
            value = int(f.read().strip())
        if value != 0:
            print(
                "WARNING: ptrace is restricted (ptrace_scope=%d). Injection "
                "into other processes will only work if the target is a "
                "child process or has opted in via PR_SET_PTRACER." % value
            )
            print("You can enable it globally by running the following:")
            print("echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope")
            print()
    else:
        getsebool = "/usr/sbin/getsebool"
        if os.path.exists(getsebool):
            p = subprocess.run(
                [getsebool, "deny_ptrace"],
                capture_output=True,
                text=True,
                check=False,
            )
            if p.stdout.strip() == "deny_ptrace --> on":
                print("WARNING: ptrace is disabled. Injection will not work.")
                print("You can enable it by running the following:")
                print("sudo setsebool -P deny_ptrace=off")
                print()


def get_payload_dir():
    return os.path.join(os.path.dirname(pyrasite.__file__), "payloads")


def list_payloads():
    return sorted(
        fn
        for fn in os.listdir(get_payload_dir())
        if fn.endswith(".py") and not fn.startswith("_")
    )


def expand_payload(payload):
    """If a standard payload with this name exists, return its full path.

    Otherwise return the input value unchanged.
    """
    if os.path.sep not in payload and (
        os.path.altsep is None or os.path.altsep not in payload
    ):
        fn = os.path.join(get_payload_dir(), payload)
        if os.path.isfile(fn):
            return fn
    return payload


def _fail(message, code):
    print(message, file=sys.stderr)
    sys.exit(code)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="pyrasite - inject code into a running python process",
        epilog="For updates, visit https://github.com/lmacken/pyrasite",
    )

    parser.add_argument(
        "pid", nargs="?", help="The ID of the process to inject code into"
    )
    parser.add_argument(
        "payload",
        nargs="?",
        default="",
        help="The Python script to be executed inside the"
        " running process.  Can be one of the standard"
        " payloads (see --list-payloads), a filename, or -"
        " to read the script from stdin.",
    )
    parser.add_argument(
        "-l",
        "--list-payloads",
        help="List standard payloads",
        default=False,
        action="store_const",
        const=True,
    )
    parser.add_argument(
        "--gdb-prefix",
        dest="gdb_prefix",
        help="GDB prefix (if specified during installation)",
        default="",
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        help="Verbose mode",
        default=False,
        action="store_const",
        const=True,
    )
    parser.add_argument(
        "--version", action="version", version="pyrasite %s" % pyrasite.__version__
    )
    parser.add_argument(
        "--output",
        dest="output_type",
        default="procstreams",
        action="store",
        help="Set where output is to be printed. 'procstreams'"
        " prints output in stdout/stderr of running process"
        " and 'localterm' prints output in local terminal.",
    )
    parser.add_argument(
        "--ipc-timeout",
        dest="ipc_timeout",
        default=5,
        action="store",
        type=int,
        help="The number of seconds to wait for the injected"
        " code to reply over IPC before giving up.",
    )
    parser.add_argument(
        "--inject-timeout",
        dest="inject_timeout",
        default=60,
        action="store",
        type=float,
        help="The number of seconds to wait for the injected"
        " payload to run. Use 0 to wait forever.",
    )
    parser.add_argument(
        "--inject-method",
        dest="inject_method",
        default="auto",
        choices=("auto", "pending", "direct"),
        help="How to run code in the target. 'auto' uses the"
        " direct method for single-threaded processes and"
        " Py_AddPendingCall for multi-threaded ones."
        " Use 'direct' for processes blocked in C.",
    )

    if not argv:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args(argv)

    if args.list_payloads:
        print("Available payloads:")
        for payload in list_payloads():
            print("  %s" % payload)
        sys.exit()

    # Make sure the output type is valid (procstreams || localterm)
    if args.output_type not in ("procstreams", "localterm"):
        _fail("Error: --output arg must be 'procstreams' or 'localterm'", 5)

    # Check that we have a pid before doing anything else.
    if args.pid is None:
        _fail("Error: The first argument must be a pid", 2)
    try:
        pid = int(args.pid)
    except ValueError:
        _fail("Error: The first argument must be a pid", 2)

    remove_payload = False
    if args.payload == "-":
        # Read the payload from stdin.  A temporary file keeps the rest of the
        # code unchanged, and build_code() reads it back before injection.
        fd, filename = tempfile.mkstemp(prefix="pyrasite-", suffix=".py")
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(sys.stdin.buffer.read())
        remove_payload = True
    else:
        filename = expand_payload(args.payload)
        if not filename:
            _fail("Error: The second argument must be a filename or a payload name", 4)
        if not os.path.exists(filename):
            _fail("Error: Invalid path or file doesn't exist", 3)

    try:
        _run(args, filename, pid)
    finally:
        if remove_payload:
            with contextlib.suppress(OSError):
                os.unlink(filename)


def _run(args, filename, pid):
    """Inject *filename* into the process described by *args*."""
    ptrace_check()

    inject_method = None if args.inject_method == "auto" else args.inject_method
    inject_timeout = None if args.inject_timeout <= 0 else args.inject_timeout

    if args.output_type == "localterm":
        # Create new IPC connection to the process.
        try:
            ipc = pyrasite.PyrasiteIPC(
                pid,
                "ReversePythonConnection",
                timeout=args.ipc_timeout,
                inject_timeout=inject_timeout,
                inject_method=inject_method,
            )
            ipc.connect()
        except Exception as e:
            _fail("Error: %s" % e, 6)

        try:
            print("Pyrasite Shell %s" % pyrasite.__version__)
            print("Connected to '%s'" % ipc.title)

            # Read in the payload
            with open(filename) as fd:
                payload = fd.read()

            # Run the payload, print output, close ipc connection
            print(ipc.cmd(payload))
        finally:
            ipc.close()
    else:
        try:
            pyrasite.inject(
                pid,
                filename,
                verbose=args.verbose,
                gdb_prefix=args.gdb_prefix,
                timeout=inject_timeout,
                method=inject_method,
            )
        except InjectionError as e:
            _fail("Error: %s" % e, 7)


if __name__ == "__main__":
    main()
