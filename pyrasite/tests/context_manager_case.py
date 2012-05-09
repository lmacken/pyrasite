""" This is kept in a separate file so that python2.4 never picks it up. """

import pyrasite


def context_manager_business(case):
    # Check that the context manager injects ipc correctly.
    with pyrasite.PyrasiteIPC(case.p.pid) as ipc:
        assert ipc.cmd('print("mu")') == 'mu\n'

    # Check that the context manager closes the ipc correctly.
    try:
        ipc.cmd('print("mu")')
        assert False, "The connection was not closed."
    except IOError as e:
        assert "Bad file descriptor" in str(e)
