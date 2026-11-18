Changelog
=========

Unreleased
----------

- Do not print the Yama ``ptrace_scope`` warning when running as root, since
  root is not restricted by it.

2.3.0 (2026-11-18)
------------------

- Add ``--bind-host``, ``--connect-host``, and ``--port`` to
  ``pyrasite-shell``, so the target can connect back from another container or
  host. The default remains a loopback-only ephemeral port.
- Document injecting into a remote process over SSH with
  ``ssh host pyrasite <pid> - < payload.py`` and ``ssh -t host
  pyrasite-shell <pid>``.

2.2.0 (2026-11-15)
------------------

- Read payloads in the pyrasite process and embed them in the gdb command, so
  injection works when the target cannot read the payload file, such as when
  root attaches to a process owned by another user.
- Accept ``-`` as the payload to read code from standard input, and support
  FIFOs and shell process substitution.
- Report injection failures from ``pyrasite-shell`` and the memory viewer as
  short errors instead of tracebacks, and close the listening socket when a
  connection attempt fails.
- Keep ``pyrasite-shell`` connected when a command takes longer than the
  connect timeout, and exit cleanly if the target closes the connection.
- Fail clearly when the memory dump used by ``pyrasite-memory-viewer`` is not
  created instead of raising ``FileNotFoundError``.

2.1.0 (2026-11-15)
------------------

- Support CPython 3.9 through 3.15, including cross-interpreter injection.
- Replace nose and Travis CI with pytest, tox-uv, and GitHub Actions.
- Package with ``pyproject.toml`` and publish an SPDX license expression.
- Use ``PyGILState_Ensure`` for single-threaded targets and
  ``Py_AddPendingCall`` for multi-threaded ones.
- Report payload exceptions back to the client instead of leaving the target
  in a broken state.
- Make ``pyrasite.inspect`` work with stripped distribution Python builds by
  falling back to the stable C API when debug symbols are unavailable.
- Add ``--version``, ``--inject-timeout``, and
  ``--inject-method {auto,pending,direct}`` CLI options.
- Fix Python 3 bytes/string handling, imports, and the reverse shell payloads.
- Restore ``pyrasite.utils`` for payloads that run subprocesses.
- Drop the unmaintained Python 2 distro packaging and callgraph payloads.

2.0 (2013)
----------

- Previous release.
