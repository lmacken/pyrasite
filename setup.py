"""Setuptools build hooks.

All package metadata lives in ``pyproject.toml``.  This file only exists to
wire up the optional Windows injector build step.
"""

import contextlib
import platform

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        _build_py.run(self)
        if platform.system() != "Windows":
            return

        import os

        try:
            import winbuild
        except Exception:
            self.announce(
                "Could not find a Microsoft compiler for supporting Windows "
                "process injection",
                2,
            )
            return

        srcfile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "pyrasite",
            "win",
            "inject_python.cpp",
        )
        out32exe = os.path.join(
            self.build_lib, "pyrasite", "win", "inject_python_32.exe"
        )
        out64exe = os.path.join(
            self.build_lib, "pyrasite", "win", "inject_python_64.exe"
        )
        with contextlib.suppress(OSError):
            os.makedirs(os.path.dirname(out32exe))
        for outexe, arch, message in (
            (out32exe, "x86", "32-bit"),
            (out64exe, "x64", "64-bit"),
        ):
            try:
                winbuild.compile(srcfile, outexe, arch)
            except Exception:
                self.announce(
                    "Could not find an %s Microsoft compiler for supporting "
                    "injection into %s python instances" % (arch, message),
                    2,
                )


setup(cmdclass={"build_py": build_py})
