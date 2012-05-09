import sys
from setuptools import setup, find_packages

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

requirements = []
if sys.version_info[0] == 3:
    if sys.version_info[1] < 2:
        requirements.append('argparse')
elif sys.version_info[0] == 2:
    if sys.version_info[1] < 7:
        requirements.append('argparse')

tests_require = ['nose']
if sys.version_info[0] == 2:
    if sys.version_info[1] < 7:
        tests_require.append('unittest2')

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
      )
