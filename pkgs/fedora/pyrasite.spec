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

Requires:         gdb >= 7.3

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

%check
%{__python} setup.py test

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc README.rst
%{_bindir}/pyrasite
%{_bindir}/pyrasite-memory-viewer
%{_bindir}/pyrasite-shell
%{python_sitelib}/*

%changelog
* Mon Mar 12 2012 Luke Macken <lmacken@redhat.com> 2.0-0.1.beta1
- Initial package for Fedora
