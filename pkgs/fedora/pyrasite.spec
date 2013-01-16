Name:             pyrasite
Version:          2.0
Release:          3%{?dist}
Summary:          Code injection and monitoring of running Python processes

Group:            Development/Languages
License:          GPLv3
URL:              http://pyrasite.com
Source0:          http://pypi.python.org/packages/source/p/%{name}/%{name}-%{version}.tar.gz

BuildArch:        noarch
BuildRequires:    python-devel
BuildRequires:    python-setuptools-devel
BuildRequires:    python-nose
BuildRequires:    python-sphinx

Requires:         gdb
Requires:         python-meliae
Requires:         python-urwid
Requires:         python-setuptools

%if 0%{?rhel} <= 6
BuildRequires:    python-argparse
Requires:         python-argparse
%endif

%description
Pyrasite uses the GNU debugger to inject code into a running Python process.
It is comprised of a command-line tool, and a Python API. This package
also comes with a variety of example payloads.

%prep
%setup -q

%build
%{__python} setup.py build
make -C docs man

%check
%{__python} setup.py test

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_mandir}/man1
gzip -c docs/_build/man/pyrasite.1 > %{buildroot}/%{_mandir}/man1/pyrasite.1.gz

%files
%defattr(-,root,root,-)
%doc README.rst LICENSE
%doc %{_mandir}/man1/pyrasite.1.gz
%{_bindir}/pyrasite
%{_bindir}/pyrasite-memory-viewer
%{_bindir}/pyrasite-shell
%{python_sitelib}/*

%changelog
* Wed Jan 16 2013 Luke Macken <lmacken@redhat.com> - 2.0-3
- Require python-setuptools needed for pkg_resources

* Tue Aug 21 2012 Luke Macken <lmacken@redhat.com> - 2.0-2
- Require python-urwid for the pyrasite-memory-viewer
- Require python-meliae for the memory-viewer and dump_memory payload
  (github#40)

* Mon Mar 12 2012 Luke Macken <lmacken@redhat.com> 2.0-1
- Initial package for Fedora
