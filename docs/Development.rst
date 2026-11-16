Development
===========

Running from git
----------------

::

    git clone https://github.com/lmacken/pyrasite.git
    cd pyrasite
    python -m pip install -e ".[dev]"
    python -m pyrasite.main --help

Run the test suite and linters with::

    pytest
    ruff check .
    ruff format --check .

To run it against every supported Python version (3.9 through 3.15), use
`tox <https://tox.wiki/>`_. The ``tox-uv`` plugin automatically downloads
missing interpreters with `uv <https://docs.astral.sh/uv/>`_::

    uv python install 3.9 3.10 3.11 3.12 3.13 3.14 3.15
    tox

To exercise injection from the current interpreter into every installed
interpreter, set ``PYRASITE_TEST_INTERPRETERS`` to a colon-separated list of
interpreter paths::

    PYRASITE_TEST_INTERPRETERS=$(for v in 3.9 3.10 3.11 3.12 3.13 3.14 3.15; do
        uv python find "$v"
    done | paste -sd: -) pytest pyrasite/tests/test_code_injection.py

Injection tests need ``gdb`` and permission to attach to the target process.
The test targets opt in to being traced using ``prctl(PR_SET_PTRACER, ...)``,
so they also work when ``kernel.yama.ptrace_scope`` is ``1``.

Documentation is built with Sphinx::

    tox -e docs

Style
-----

Code is formatted and linted with `ruff <https://docs.astral.sh/ruff/>`_.
Run ``ruff format .`` before committing, or use ``tox -e lint``.

Releasing
---------

1. Update the version in ``pyrasite/__init__.py`` and ``CHANGELOG.rst``.
2. Build and validate the distributions::

       python -m build
       twine check dist/*

3. Configure trusted publishing once, if it is not already set up:

   * On PyPI, add a trusted publisher for the project with owner
     ``lmacken``, repository ``pyrasite``, workflow ``publish.yml``, and
     environment ``pypi``.
   * On TestPyPI, add the same publisher with environment ``testpypi``.
     TestPyPI is optional and uses a separate account database.
   * In the GitHub repository settings, create environments named ``pypi``
     and ``testpypi``.

   To validate the PyPI publisher without publishing a new release, run the
   **Publish** workflow manually with ``target: pypi`` and ``skip_existing``
   enabled. The job still performs the OIDC exchange, then skips the files that
   are already on PyPI.

4. Commit, tag, and push the release. Pushing a tag that starts with a digit
   runs ``.github/workflows/publish.yml`` and publishes to PyPI::

       git tag -a 2.2.0 -m "pyrasite 2.2.0"
       git push origin develop 2.2.0

   To rehearse first, run the **Publish** workflow manually with
   ``target: testpypi``.

5. If trusted publishing is not configured yet, upload the distributions from
   the build in step 2 instead::

       twine upload dist/*
