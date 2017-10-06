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

import os
import sys
import argparse
import subprocess

import pyrasite


def ptrace_check():
    ptrace_scope = '/proc/sys/kernel/yama/ptrace_scope'
    if os.path.exists(ptrace_scope):
        f = open(ptrace_scope)
        value = int(f.read().strip())
        f.close()
        if value == 1:
            print("WARNING: ptrace is disabled. Injection will not work.")
            print("You can enable it by running the following:")
            print("echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope")
            print("")
    else:
        getsebool = '/usr/sbin/getsebool'
        if os.path.exists(getsebool):
            p = subprocess.Popen([getsebool, 'deny_ptrace'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if str(out) == 'deny_ptrace --> on\n':
                print("WARNING: ptrace is disabled. Injection will not work.")
                print("You can enable it by running the following:")
                print("sudo setsebool -P deny_ptrace=off")
                print("")


def get_payload_dir():
    return os.path.join(os.path.dirname(pyrasite.__file__), 'payloads')


def list_payloads():
    return sorted(fn for fn in os.listdir(get_payload_dir())
                  if fn.endswith('.py') and not fn.startswith('_'))

def expand_payload(payload):
    """If a standard payload with this name exists, return its full path.

    Otherwise return the input value unchanged.
    """
    if os.path.sep not in payload:
        fn = os.path.join(get_payload_dir(), payload)
        if os.path.isfile(fn):
            return fn
    return payload


def main():
    ptrace_check()

    parser = argparse.ArgumentParser(
            description='pyrasite - inject code into a running python process',
            epilog="For updates, visit https://github.com/lmacken/pyrasite")

    parser.add_argument('pid', nargs='?',
                        help="The ID of the process to inject code into")
    parser.add_argument('payload', nargs='?', default='',
                        help="The Python script to be executed inside the"
                             " running process.  Can be one of the standard"
                             " payloads (see --list-payloads) or a filname.")
    parser.add_argument('-l', '--list-payloads', help='List standard payloads',
                        default=False, action='store_const', const=True)
    parser.add_argument('--gdb-prefix', dest='gdb_prefix',
                        help='GDB prefix (if specified during installation)',
                        default="")
    parser.add_argument('--verbose', dest='verbose', help='Verbose mode',
                        default=False, action='store_const', const=True)
    parser.add_argument('--output', dest='output_type', default='procstreams',
                        action='store',
                        help="Set where output is to be printed. 'procstreams'" 
                             " prints output in stdout/stderr of running process"
                             " and 'localterm' prints output in local terminal.")
    parser.add_argument('--ipc-timeout', dest='ipc_timeout', default=5,
                        action='store', type=int,
                        help="The number of seconds to wait for the injected"
                             " code to reply over IPC before giving up.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.list_payloads:
        print("Available payloads:")
        for payload in list_payloads():
            print("  %s" % payload)
        sys.exit()

    # Make sure the output type is valid (procstreams || localterm)
    if args.output_type != 'procstreams' and args.output_type != 'localterm':
        print("Error: --output arg must be 'procstreams' or 'localterm'")
        sys.exit(5)

    try:
        pid = int(args.pid)
    except ValueError:
        print("Error: The first argument must be a pid")
        sys.exit(2)

    filename = expand_payload(args.payload)
    if filename:
        if not os.path.exists(filename):
            print("Error: Invalid path or file doesn't exist")
            sys.exit(3)
    else:
        print("Error: The second argument must be a filename or a payload name")
        sys.exit(4)


    if args.output_type == 'localterm':
        # Create new IPC connection to the process.
        ipc = pyrasite.PyrasiteIPC(pid, 'ReversePythonConnection',
                                   timeout=args.ipc_timeout)
        ipc.connect()
        print("Pyrasite Shell %s" % pyrasite.__version__)
        print("Connected to '%s'" % ipc.title)

        # Read in the payload
        fd = open(filename)
        payload = fd.read()
        fd.close

        # Run the payload, print output, close ipc connection
        print(ipc.cmd(payload))
        ipc.close()
    else:
        pyrasite.inject(pid, filename, verbose=args.verbose,
                        gdb_prefix=args.gdb_prefix)


if __name__ == '__main__':
    main()
