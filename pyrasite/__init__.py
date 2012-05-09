__version__ = '2.0'
__all__ = ('inject', 'inspect', 'PyrasiteIPC',
           'ReverseConnection', 'ReversePythonConnection')
__license__ = """\
pyrasite is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyrasite is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyrasite.  If not, see <http://www.gnu.org/licenses/>.\
"""
__copyright__ = "Copyright (C) 2011, 2012 Red Hat, Inc."

from pyrasite.injector import inject
from pyrasite.inspector import inspect
from pyrasite.ipc import PyrasiteIPC
from pyrasite.reverse import ReverseConnection, ReversePythonConnection
