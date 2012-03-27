%global betaver beta9

Name:             pyrasite
Version:          2.0
Release:          0.1.%{betaver}%{?dist}
Summary:          Code injection and monitoring of running Python processes

Group:            Development/Languages
License:          GPLv3
URL:              http://pyrasite.com
Source0:          http://pypi.python.org/packages/source/p/%{name}/%{name}-%{version}%{betaver}.tar.gz

BuildArch:        noarch
BuildRequires:    python-devel
BuildRequires:    python-setuptools-devel
BuildRequires:    python-nose
BuildRequires:    python-sphinx

Requires:         gdb

%if 0%{?rhel} <= 6
BuildRequires:    python-argparse
Requires:         python-argparse
%endif

%description
Pyrasite uses the GNU debugger to inject code into a running Python process.
It is comprised of a command-line tool, and a Python API. This package
also comes with a variety of example payloads.

%prep
%setup -q -n %{name}-%{version}%{betaver}

%build
%{__python} setup.py build
PYTHONPATH=$(pwd) make -C docs man

%check
%{__python} setup.py test

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
%{__mkdir_p} %{buildroot}%{_mandir}/man1
%{__gzip} -c docs/_build/man/pyrasite.1 > %{buildroot}/%{_mandir}/man1/pyrasite.1.gz

%files
%defattr(-,root,root,-)
%doc README.rst LICENSE docs
%doc %{_mandir}/man1/pyrasite.1.gz
%{_bindir}/pyrasite
%{_bindir}/pyrasite-memory-viewer
%{_bindir}/pyrasite-shell
%{python_sitelib}/*

%changelog
* Mon Mar 12 2012 Luke Macken <lmacken@redhat.com> 2.0-0.1.beta1
- Initial package for Fedora
