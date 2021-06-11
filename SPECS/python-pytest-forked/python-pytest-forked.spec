%{!?python3_pkgversion: %global python3_pkgversion 3}
%{!?python3_version: %define python3_version %(python3 -c "import sys; sys.stdout.write(sys.version[:3])")}
%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?py3_build: %define py3_build CFLAGS="%{optflags}" %{__python3} setup.py build}
%{!?py3_install: %define py3_install %{__python3} setup.py install --skip-build --root %{buildroot}}

%global pypi_name pytest-forked

Name:           python-%{pypi_name}
Version:        1.3.0
Release:        2%{?dist}
Summary:        py.test plugin for running tests in isolated forked subprocesses
License:        MIT
URL:            https://github.com/pytest-dev/pytest-forked
#Source0:       https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
Source0:        https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-py
BuildRequires:  python3-pytest
BuildRequires:  python3-setuptools
BuildRequires:  python3-setuptools_scm

%global _description %{expand:
The pytest-forked plugin extends py.test by adding an option to run tests in
isolated forked subprocesses. This is useful if you have tests involving C or
C++ libraries that might crash the process. To use the plugin, simply use the
--forked argument when invoking py.test.}

%description %_description

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       python3-py
%description -n python3-%{pypi_name} %_description

%prep
%autosetup -n %{pypi_name}-%{version} -p1

%build
%py3_build

%install
%py3_install

%check
%pytest

%files -n python3-%{pypi_name}
%doc example/boxed.txt README.rst
%license LICENSE
%{python3_sitelib}/pytest_forked*

%changelog
* Tue Dec 08 2020 Steve Laughman <steve.laughman@microsoft.com> - 1.3.0-2
- Initial CBL-Mariner import from Fedora 33 (license: MIT)
* Tue Jul 28 2020 Scott Talbert <swt@techie.net> - 1.3.0-1
- Update to new upstream release 1.3.0 (#1861096)
* Thu Jun 25 2020 Scott Talbert <swt@techie.net> - 1.2.0-1
- Update to new upstream release 1.2.0 (#1851035)
* Wed Jun 24 2020 Scott Talbert <swt@techie.net> - 1.1.1-6
- Modernize Python packaging; BR setuptools
* Fri May 29 2020 Charalampos Stratakis <cstratak@redhat.com> - 1.1.1-5
- Fix pytest 5 compatibility
* Fri May 29 2020 Charalampos Stratakis <cstratak@redhat.com> - 1.1.1-4
- Drop manual requires on python3-pytest to support usage with pytest4 compat package
* Sun May 24 2020 Miro Hrončok <mhroncok@redhat.com> - 1.1.1-3
- Rebuilt for Python 3.9
* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild
* Thu Oct 10 2019 Scott Talbert <swt@techie.net> - 1.1.1-1
- Update to new upstream release 1.1.1 (#1760556)
* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 1.0.2-5
- Rebuilt for Python 3.8.0rc1 (#1748018)
* Sat Aug 17 2019 Miro Hrončok <mhroncok@redhat.com> - 1.0.2-4
- Rebuilt for Python 3.8
* Fri Aug 09 2019 Scott Talbert <swt@techie.net> - 1.0.2-3
- Remove Python 2 subpackages (#1739658)
* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild
* Wed Feb 20 2019 Scott Talbert <swt@techie.net> - 1.0.2-1
- New upstream release 1.0.2
* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild
* Sat Jan 12 2019 Scott Talbert <swt@techie.net> - 1.0.1-1
- New upstream release 1.0.1
* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild
* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 0.2-4
- Rebuilt for Python 3.7
* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild
* Thu Aug 17 2017 Scott Talbert <swt@techie.net> - 0.2-2
- Updated to use py[23]dist macros for BR and R
* Thu Aug 10 2017 Scott Talbert <swt@techie.net> - 0.2-1
- Initial package.