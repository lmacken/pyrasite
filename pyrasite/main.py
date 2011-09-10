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

from inject import CodeInjector

def main():
    if len(sys.argv) < 3:
        print("Usage: %s <pid> <filename>" % sys.argv[0])
        print("\n         pid:\tThe ID of the process to inject code into")
        print("    filename:\tThe .py file to inject into the process\n")
        sys.exit(1)

    try:
        pid = int(sys.argv[1])
    except ValueError:
        print "Error: The first argument must be a pid"
        sys.exit(2)

    filename = sys.argv[2]
    if not os.path.exists(filename):
        print "Error: The second argument must be a filename"
        sys.exit(3)

    injector = CodeInjector(pid, filename, verbose='-v' in sys.argv)
    injector.inject()

if __name__ == '__main__':
    main()
