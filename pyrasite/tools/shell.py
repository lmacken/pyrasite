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
import os
import pyrasite


def shell():
    parser = argparse.ArgumentParser(description='Open a Python shell in a running process')
    parser.add_argument('pid', type=int, help='PID of the running process to attach to.')
    parser.add_argument('--timeout', type=int, default=5, help='IPC Timeout, applies for each command.')
    parser.add_argument('--server-host', default='localhost', help='The hostname to use for the listening (server) side of the IPC communication. Sometimes, (docker), localhost does not work.')
    parser.add_argument('--client-host', default='localhost', help='The hostname to use for the connecting (client) side of the IPC communication. Sometimes, (docker), localhost does not work.')
    parser.add_argument('--port', type=int, default=None, help='Optionally specify a port that will be listened on for the remote process to attach back.')
    parser.add_argument('--tmpdir', default=None, help='Use the following tmp directory for transferring the payload')

    args = parser.parse_args()

    ipc = pyrasite.PyrasiteIPC(
        args.pid,
        'ReversePythonShell',
        timeout=args.timeout,
        server_host=args.server_host,
        client_host=args.client_host,
        port=args.port,
        tmpdir=args.tmpdir,
    )

    ipc.connect()

    print("Pyrasite Shell %s" % pyrasite.__version__)
    print("Connected to '%s'" % ipc.title)

    prompt, payload = ipc.recv().split('\n', 1)
    print(payload)

    try:
        import readline
    except ImportError:
        pass

    # py3k compat
    try:
        input_ = raw_input
    except NameError:
        input_ = input

    try:
        while True:
            try:
                input_line = input_(prompt)
            except EOFError:
                input_line = 'exit()'
                print('')
            except KeyboardInterrupt:
                input_line = 'None'
                print('')

            ipc.send(input_line)
            payload = ipc.recv()
            if payload is None:
                break
            prompt, payload = payload.split('\n', 1)
            if payload != '':
                print(payload)
    except:
        print('')
        raise
    finally:
        ipc.close()


if __name__ == '__main__':
    shell()
