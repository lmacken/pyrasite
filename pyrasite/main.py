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
# Copyright (C) 2011, 2012 Red Hat, Inc.

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
            if out.decode('utf-8') == u'deny_ptrace --> on\n':
                print("WARNING: ptrace is disabled. Injection will not work.")
                print("You can enable it by running the following:")
                print("sudo setsebool -P deny_ptrace=off")
                print("")


def main():
    ptrace_check()

    parser = argparse.ArgumentParser(
            description='pyrasite - inject code into a running python process',
            epilog="For updates, visit https://github.com/lmacken/pyrasite")
    parser.add_argument('pid',
                        help="The ID of the process to inject code into")
    parser.add_argument('filename',
                        help="The second argument must be a filename")
    parser.add_argument('--gdb-prefix', dest='gdb_prefix',
                        help='GDB prefix (if specified during installation)',
                        default="")
    parser.add_argument('--verbose', dest='verbose', help='Verbose mode',
                        default=False, action='store_const', const=True)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    try:
        pid = int(args.pid)
    except ValueError:
        print("Error: The first argument must be a pid")
        sys.exit(2)

    filename = args.filename
    if filename:
        if not os.path.exists(filename):
            print("Error: Invalid path or file doesn't exist")
            sys.exit(3)
    else:
        print("Error: The second argument must be a filename")
        sys.exit(4)

    pyrasite.inject(pid, filename, verbose=args.verbose,
                    gdb_prefix=args.gdb_prefix)


if __name__ == '__main__':
    main()
