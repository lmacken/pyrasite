import sys
from setuptools import setup, find_packages
from distutils.command.build_py import build_py as _build_py
import platform

try:
    # These imports are not used, but make
    # tests pass smoothly on python2.7
    import multiprocessing
    import logging
except Exception:
    pass

version = '2.0'

f = open('README.rst')
long_description = f.read().split('split here')[1]
f.close()

requirements = ['urwid']
if sys.version_info[0] == 3:
    if sys.version_info[1] < 2:
        requirements.append('argparse')
elif sys.version_info[0] == 2:
    if sys.version_info[1] < 7:
        requirements.append('argparse')

tests_require = ['nose']

class build_py(_build_py):
  def run(self):
    _build_py.run(self)
    if platform.system() == 'Windows':
      import os
      try:
        import winbuild
      except:
        self.announce("Could not find an microsoft compiler for supporting windows process injection", 2)
        return
      #can fail ?
      dirs = [x for x in self.get_data_files() if x[0] == 'pyrasite'][0]
      srcfile = os.path.join(dirs[1], 'win', 'inject_python.cpp')
      out32exe = os.path.join(dirs[2], 'win', 'inject_python_32.exe')
      out64exe = os.path.join(dirs[2], 'win', 'inject_python_64.exe')
      try:
        os.makedirs(os.path.dirname(out32exe))
      except:
        pass
      try:
        winbuild.compile(srcfile, out32exe, 'x86')
      except:
        self.announce("Could not find an x86 microsoft compiler for supporting injection to 32 bit python instances", 2)
      try:
        winbuild.compile(srcfile, out64exe, 'x64')
      except:
        self.announce("Could not find an x64 microsoft compiler for supporting injection to 64 bit python instances", 2)


setup(name='pyrasite',
      version=version,
      description="Inject code into a running Python process",
      long_description=long_description,
      keywords='debugging injection runtime',
      author='Luke Macken',
      author_email='lmacken@redhat.com',
      url='http://pyrasite.com',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requirements,
      tests_require=tests_require,
      test_suite='nose.collector',
      entry_points="""
          [console_scripts]
          pyrasite = pyrasite.main:main
          pyrasite-memory-viewer = pyrasite.tools.memory_viewer:main
          pyrasite-shell = pyrasite.tools.shell:shell
      """,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Topic :: System :: Monitoring',
          'Topic :: Software Development :: Debuggers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
      ],
      cmdclass={'build_py': build_py}
      )
