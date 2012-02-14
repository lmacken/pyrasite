# http://code.activestate.com/recipes/577081-humanized-representation-of-a-number-of-bytes/

from __future__ import division

def humanize_bytes(bytes, precision=1):
    """Return a humanized string representation of a number of bytes."""
    abbrevs = (
        (1<<50L, 'PB'),
        (1<<40L, 'TB'),
        (1<<30L, 'GB'),
        (1<<20L, 'MB'),
        (1<<10L, 'kB'),
        (1, 'bytes')
    )
    if bytes == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytes >= factor:
            break
    return '%.*f %s' % (precision, bytes / factor, suffix)


# Some useful functions based on code from Will Maier's 'ideal Python script'
# https://github.com/wcmaier/python-script
#
# Copyright (c) 2010 Will Maier <willmaier@ml1.net>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import logging
import subprocess

def run(*args, **kwargs):
    """Run a subprocess.

    Returns a tuple (*process*, *stdout*, *stderr*). If the *communicate*
    keyword argument is True, *stdout* and *stderr* will be strings.
    Otherwise, they will be None. *process* is a :class:`subprocess.Popen`
    instance. By default, the path to the script itself will be used as the
    executable and *args* will be passed as arguments to it.

    .. note::
    The value of *executable* will be prepended to *args*.

    :param args: arguments to be passed to :class:`subprocess.Popen`.
    :param kwargs: keyword arguments to be passed to :class:`subprocess.Popen`.
    :param communicate: if True, call :meth:`subprocess.Popen.communicate` after creating the subprocess.
    :param executable: if present, the path to a program to execute instead of this script.
    """
    _kwargs = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": True,
    }
    communicate = kwargs.pop("communicate", True)
    _kwargs.update(kwargs)
    kwargs = _kwargs
    process = subprocess.Popen(args, **kwargs)

    if communicate is True:
        stdout, stderr = process.communicate()
    else:
        stdout, stderr = None, None

    return process, stdout, stderr


def setup_logger(verbose=False):
    # NullHandler was added in Python 3.1.
    try:
        NullHandler = logging.NullHandler
    except AttributeError:
        class NullHandler(logging.Handler):
            def emit(self, record): pass

    # Add a do-nothing NullHandler to the module logger to prevent "No handlers
    # could be found" errors. The calling code can still add other, more useful
    # handlers, or otherwise configure logging.
    log = logging.getLogger('pyrasite')
    log.addHandler(NullHandler())

    level = logging.INFO
    if verbose:
        level = logging.DEBUG

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(level)
    log.addHandler(handler)
    log.setLevel(level)

    return log
