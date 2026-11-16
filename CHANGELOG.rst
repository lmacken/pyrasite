Changelog
=========

2.1.0 (2026-11-15)
------------------

- Support CPython 3.9 through 3.15, including cross-interpreter injection.
- Replace nose and Travis CI with pytest, tox-uv, and GitHub Actions.
- Package with ``pyproject.toml`` and publish an SPDX license expression.
- Use ``PyGILState_Ensure`` for single-threaded targets and
  ``Py_AddPendingCall`` for multi-threaded ones.
- Report payload exceptions back to the client instead of leaving the target
  in a broken state.
- Add ``--version``, ``--inject-timeout``, and
  ``--inject-method {auto,pending,direct}`` CLI options.
- Fix Python 3 bytes/string handling, imports, and the reverse shell payloads.
- Restore ``pyrasite.utils`` for payloads that run subprocesses.
- Drop the unmaintained Python 2 distro packaging and callgraph payloads.

2.0 (2013)
----------

- Previous release.
