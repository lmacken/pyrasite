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
# Copyright (C) 2013 Red Hat, Inc., Luke Macken <lmacken@redhat.com>

import os
import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from pyrasite.main import main

class TestCLI(object):

    def test_usage(self):
        sys.argv = ['pyrasite']
        try:
            main()
        except SystemExit:
            exit_code = sys.exc_info()[1].code
            assert exit_code == 1, exit_code

    def test_list_payloads(self):
        sys.argv = ['pyrasite', '-l']
        stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            main()
        except SystemExit:
            pass
        value = sys.stdout.getvalue()
        sys.stdout = stdout
        assert 'Available payloads:' in value, repr(value)
        assert 'helloworld.py' in value, repr(value)

    def test_invalid_pid(self):
        sys.argv = ['pyrasite', 'foo', 'bar']
        stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            main()
        except SystemExit:
            exit_code = sys.exc_info()[1].code
            assert exit_code == 2, exit_code
        value = sys.stdout.getvalue()
        sys.stdout = stdout
        assert 'Error: The first argument must be a pid' in value, repr(value)

    def test_invalid_payload(self):
        sys.argv = ['pyrasite', str(os.getpid()), 'foo']
        stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            main()
        except SystemExit:
            exit_code = sys.exc_info()[1].code
            assert exit_code == 3, exit_code
        value = sys.stdout.getvalue()
        sys.stdout = stdout
        assert "Error: Invalid path or file doesn't exist" in value, repr(value)

    def test_injection(self):
        sys.argv = ['pyrasite', str(os.getpid()), 'helloworld.py']
        stdout = sys.stdout
        sys.stdout = StringIO()
        main()
        value = sys.stdout.getvalue()
        sys.stdout = stdout
        assert "Hello World!" in value, repr(value)
