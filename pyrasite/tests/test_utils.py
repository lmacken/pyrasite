import sys

from pyrasite.utils import run


def test_run_captures_output():
    p, out, err = run('%s -c "import sys; print(\'hi\'); '
                      'print(\'oops\', file=sys.stderr)"' % sys.executable)
    assert p.returncode == 0
    assert out.strip() == 'hi'
    assert err.strip() == 'oops'


def test_run_returns_nonzero_status():
    p, out, err = run('%s -c "raise SystemExit(3)"' % sys.executable)
    assert p.returncode == 3
