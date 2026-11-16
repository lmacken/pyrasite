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
"""
:mod:`pyrasite.utils` - Small helpers used by payloads
======================================================
"""

import subprocess


def run(cmd):
    """Run *cmd* in a subshell and return ``(process, stdout, stderr)``.

    The returned output is decoded as UTF-8 (replacing invalid bytes) so
    payloads can concatenate it with regular strings.
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    return p, out.decode('utf-8', 'replace'), err.decode('utf-8', 'replace')
