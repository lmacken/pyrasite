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
# Copyright (C) 2011 Red Hat, Inc.

import os, sys
import argparse

from inject import CodeInjector

def main():
    parser = argparse.ArgumentParser(
        description='pyrasite - inject code into a running python process',
        epilog="For updates, visit https://github.com/lmacken/pyrasite"
        )
    parser.add_argument('pid', help="The ID of the process to inject code into")
    parser.add_argument('filename', default=None, nargs='?', help="The second argument must be a filename")
    parser.add_argument('--gdb-prefix', dest='gdb_prefix', help='GDB prefix (if specified during installation)', default="")
    parser.add_argument('--verbose', dest='verbose', help='Verbose mode', default=False, action='store_const', const=True)
    
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()

    try:
        pid = int(args.pid)
    except ValueError:
        print "Error: The first argument must be a pid"
        sys.exit(2)
        
    filename = args.filename
    if filename:
        if not os.path.exists(filename):
            print "Error: Invalid path or file doesn't exist"
            sys.exit(3)
    else:
        print "Error: The second argument must be a filename"
        sys.exit(4)

    injector = CodeInjector(pid, filename, verbose=args.verbose, gdb_prefix=args.gdb_prefix)
    injector.inject()

if __name__ == '__main__':
    main()
