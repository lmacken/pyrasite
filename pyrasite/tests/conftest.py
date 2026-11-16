import pytest

from pyrasite.tests.utils import allow_ptrace_any, has_gdb


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "injection: tests that attach to another process with gdb"
    )


@pytest.fixture(scope="session", autouse=True)
def _opt_in_to_ptrace():
    """Allow gdb to attach to the test process under Yama's ptrace_scope=1."""
    allow_ptrace_any()
    yield


@pytest.fixture(scope="session")
def gdb_available():
    if not has_gdb():
        pytest.skip("gdb is not installed")
    return True
