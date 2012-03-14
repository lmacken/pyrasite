from .inject import CodeInjector
from .inspect import ObjectInspector
from .ipc import PyrasiteIPC
from .reverse import ReverseConnection, ReversePythonConnection

__version__ = '2.0beta5'
__all__ = ('CodeInjector', 'ObjectInspector', 'PyrasiteIPC',
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
