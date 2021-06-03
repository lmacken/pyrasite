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

import os
import subprocess
import platform

def inject(pid, filename, verbose=False, gdb_prefix=''):
    """Executes a file in a running Python process."""
    filename = os.path.abspath(filename)
    gdb_cmds = [
        'PyGILState_Ensure()',
        'PyRun_SimpleString("'
            'import sys; sys.path.insert(0, \\"%s\\"); '
            'sys.path.insert(0, \\"%s\\"); '
            'exec(open(\\"%s\\").read())")' %
                (os.path.dirname(filename),
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
                filename),
        'PyGILState_Release($1)',
        ]
    p = subprocess.Popen('%sgdb -p %d -batch %s' % (gdb_prefix, pid,
        ' '.join(["-eval-command='call %s'" % cmd for cmd in gdb_cmds])),
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if verbose:
        print(out)
        print(err)

_platform = platform.system()
if _platform == 'Darwin':
    def inject_mac(pid, filename, verbose=False, gdb_prefix=''):
        filename = os.path.abspath(filename)
        gdb_cmds = [
            '(int) PyGILState_Ensure()',
            '(int) PyRun_SimpleString("'
                'import sys; sys.path.insert(0, \\"%s\\"); '
                'sys.path.insert(0, \\"%s\\"); '
                'exec(open(\\"%s\\").read())")' %
                    (os.path.dirname(filename),
                    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
                    filename),
            '(int) PyGILState_Release($1)',
            ]
        p = subprocess.Popen('%slldb -p %d -b %s -k quit' % (gdb_prefix, pid,
            ' '.join(["-k 'call %s'" % cmd for cmd in gdb_cmds])),
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if verbose:
            print(out)
            print(err)
    inject = inject_mac

elif _platform == 'Windows':
    def inject_win(pid, filename, verbose=False, gdb_prefix=''):
        if gdb_prefix == '':
            gdb_prefix = os.path.join(os.path.dirname(__file__), 'win') + os.sep
        filename = os.path.abspath(filename)
        code = 'import sys; sys.path.insert(0, \\"%s\\"); sys.path.insert(0, \\"%s\\"); exec(open(\\"%s\\").read())' % (os.path.dirname(filename).replace('\\', '/'), os.path.abspath(os.path.join(os.path.dirname(__file__), '..')).replace('\\', '/'), filename.replace('\\', '/'))
        p = subprocess.Popen('%sinject_python_32.exe %d \"%s\"' % (gdb_prefix, pid, code), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        out, err = p.communicate()
        if p.wait() == 25:
            p = subprocess.Popen('%sinject_python_64.exe %d \"%s\"' % (gdb_prefix, pid, code), shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            out, err = p.communicate()
        if verbose:
            print(out)
            print(err)
    inject = inject_win
