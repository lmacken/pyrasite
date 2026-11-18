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

import argparse
import contextlib
import os
import sys

import pyrasite


def shell():
    """Open a Python shell in a running process"""

    parser = argparse.ArgumentParser(
        description="Open a Python shell in a running process"
    )
    parser.add_argument("pid", type=int, help="PID of the process to attach to")
    parser.add_argument(
        "--timeout",
        type=float,
        default=os.getenv("PYRASITE_IPC_TIMEOUT") or 5,
        help="Seconds to wait for the target to connect back",
    )
    parser.add_argument(
        "--bind-host",
        default="localhost",
        help="Address to listen on. Binding to a non-loopback address exposes "
        "an unauthenticated code-execution socket; use it only on a trusted "
        "network",
    )
    parser.add_argument(
        "--connect-host",
        default=None,
        help="Hostname or address the target should connect back to. Defaults "
        "to the bound address; override this when the target is in another "
        "container or host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on. Defaults to an ephemeral port",
    )
    args = parser.parse_args()
    pid = args.pid

    ipc = pyrasite.PyrasiteIPC(
        args.pid,
        "ReversePythonShell",
        timeout=args.timeout,
        bind_host=args.bind_host,
        connect_host=args.connect_host,
        port=args.port,
    )
    try:
        ipc.connect()
    except KeyboardInterrupt:
        print("")
        sys.exit(130)
    except Exception as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(1)

    print("Pyrasite Shell %s" % pyrasite.__version__)
    print("Connected to '%s'" % ipc.title)

    # PYRASITE_IPC_TIMEOUT only bounds the connect-back wait. Once connected,
    # a command can legitimately take longer than that to finish, so let the
    # command socket block until the target sends its response.
    ipc.sock.settimeout(None)

    greeting = ipc.recv()
    if greeting is None:
        print(
            "Error: connection to pid %s closed during startup" % pid,
            file=sys.stderr,
        )
        ipc.close()
        sys.exit(1)
    prompt, payload = greeting.split("\n", 1)
    print(payload)

    with contextlib.suppress(ImportError):
        import readline  # noqa: F401 - imported for its side effects

    try:
        while True:
            try:
                input_line = input(prompt)
            except EOFError:
                input_line = "exit()"
                print("")
            except KeyboardInterrupt:
                input_line = "None"
                print("")

            try:
                ipc.send(input_line)
                payload = ipc.recv()
            except KeyboardInterrupt:
                print("")
                sys.exit(130)
            except OSError as exc:
                print(
                    "\nError: lost connection to pid %s: %s" % (pid, exc),
                    file=sys.stderr,
                )
                sys.exit(1)

            if payload is None:
                print("\nConnection to pid %s closed." % pid, file=sys.stderr)
                break
            prompt, payload = payload.split("\n", 1)
            if payload != "":
                print(payload)
    finally:
        ipc.close()


if __name__ == "__main__":
    shell()
