Development
===========

Running from git
----------------

::

    git clone https://github.com/lmacken/pyrasite.git
    cd pyrasite
    python -m pip install -e ".[test]"
    python -m pyrasite.main --help

Run the test suite with::

    pytest

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

Style
-----

 * `PEP8 <https://peps.python.org/pep-0008/>`_
