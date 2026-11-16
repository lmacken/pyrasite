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

import contextlib
import os
import sys

import pyrasite


def shell():
    """Open a Python shell in a running process"""

    usage = "Usage: pyrasite-shell <PID>"
    if len(sys.argv) != 2:
        print(usage)
        sys.exit(1)
    try:
        pid = int(sys.argv[1])
    except ValueError:
        print(usage)
        sys.exit(1)

    ipc = pyrasite.PyrasiteIPC(
        pid, "ReversePythonShell", timeout=os.getenv("PYRASITE_IPC_TIMEOUT") or 5
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
