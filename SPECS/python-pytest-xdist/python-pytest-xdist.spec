%{!?python3_version: %define python3_version %(python3 -c "import sys; sys.stdout.write(sys.version[:3])")}
%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?py3_build: %define py3_build CFLAGS="%{optflags}" %{__python3} setup.py build}
%{!?py3_install: %define py3_install %{__python3} setup.py install --skip-build --root %{buildroot}}

%global pypi_name pytest-xdist

Summary:        py.test plugin for distributed testing and loop-on-failing modes
Name:           python-%{pypi_name}
Version:        2.1.0
Release:        2%{?dist}
License:        MIT
URL:            https://github.com/pytest-dev/pytest-xdist
#Source0:       https://files.pythonhosted.org/packages/source/p/%{srcname}/%{srcname}-%{version}.tar.gz
Source0:        https://files.pythonhosted.org/packages/source/p/%{srcname}/%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-execnet >= 1.1
BuildRequires:  python3-filelock
BuildRequires:  python3-psutil >= 3.0.0
BuildRequires:  python3-pytest >= 6.0.0
BuildRequires:  python3-pytest-forked
BuildRequires:  python3-py
BuildRequires:  python3-setuptools
BuildRequires:  python3-setuptools_scm

%global _description %{expand:
The pytest-xdist plugin extends py.test with some unique test execution modes:
* test run parallelization: if you have multiple CPUs or hosts you can use
  those for a combined test run. This allows to speed up development or to use
  special resources of remote machines.
* --boxed: run each test in a boxed subprocess to survive SEGFAULTS or
  otherwise dying processes
* --looponfail: run your tests repeatedly in a subprocess. After each run
  py.test waits until a file in your project changes and then re-runs the
  previously failing tests. This is repeated until all tests pass after which
  again a full run is performed.
* Multi-Platform coverage: you can specify different Python interpreters or
  different platforms and run tests in parallel on all of them.}

%description %_description

%package -n     python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       python3-py
%description -n python3-%{pypi_name} %_description

%prep
%autosetup -n %{pypi_name}-%{version}

%build
%py3_build

%install
%py3_install

%check
%pytest

%files -n python3-%{pypi_name}
%doc OVERVIEW.md README.rst
%license LICENSE
%{python3_sitelib}/pytest_xdist*
%{python3_sitelib}/xdist/

%changelog
* Mon Dec 07 2020 Steve Laughman <steve.laughman@microsoft.com> - 2.1.0-2
- Initial CBL-Mariner import from Fedora 33 (license: MIT)
* Wed Aug 26 2020 Scott Talbert <swt@techie.net> - 2.1.0-1
- Update to new upstream release 2.1.0 (#1872506)
* Fri Aug 14 2020 Scott Talbert <swt@techie.net> - 2.0.0-1
- Update to new upstream release 2.0.0 (#1868954)
* Tue Jul 28 2020 Scott Talbert <swt@techie.net> - 1.34.0-1
- Update to new upstream release 1.34.0 (#1861207)
* Sat Jul 11 2020 Scott Talbert <swt@techie.net> - 1.33.0-1
- Update to new upstream release 1.33.0 (#1855516)
* Thu Jun 25 2020 Scott Talbert <swt@techie.net> - 1.32.0-4
- Modernize Python packaging; BR setuptools
* Fri May 29 2020 Charalampos Stratakis <cstratak@redhat.com> - 1.32.0-3
- Drop manual requires on python3-pytest to support usage with pytest4 compat package
* Sun May 24 2020 Miro Hrončok <mhroncok@redhat.com> - 1.32.0-2
- Rebuilt for Python 3.9
* Mon May 04 2020 Scott Talbert <swt@techie.net> - 1.32.0-1
- Update to new upstream release 1.32.0 (#1830627)
* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.31.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild
* Thu Jan 02 2020 Scott Talbert <swt@techie.net> - 1.31.0-1
- Update to new upstream release 1.31.0 (#1785526)
* Wed Oct 02 2019 Scott Talbert <swt@techie.net> - 1.30.0-1
- Update to new upstream release 1.30.0 (#1757495)
* Sat Aug 17 2019 Miro Hrončok <mhroncok@redhat.com> - 1.29.0-4
- Rebuilt for Python 3.8
* Thu Aug 08 2019 Scott Talbert <swt@techie.net> - 1.29.0-3
- Remove Python 2 subpackages (#1737399)
* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.29.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild
* Tue Jun 18 2019 Scott Talbert <swt@techie.net> - 1.29.0-1
- Update to new upstream release 1.29.0 (#1720870)
* Thu Apr 18 2019 Scott Talbert <swt@techie.net> - 1.28.0-1
- New upstream release 1.28.0
* Fri Mar 22 2019 Scott Talbert <swt@techie.net> - 1.27.0-1
- New upstream release 1.27.0
* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.26.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild
* Mon Jan 28 2019 Scott Talbert <swt@techie.net> - 1.26.1-1
- New upstream release 1.26.1
* Tue Jan 22 2019 Scott Talbert <swt@techie.net> - 1.26.0-1
- New upstream release 1.26.0
* Sat Dec 15 2018 Scott Talbert <swt@techie.net> - 1.25.0-1
- New upstream release 1.25.0
* Sun Nov 11 2018 Scott Talbert <swt@techie.net> - 1.24.1-1
- New upstream release 1.24.1
* Wed Oct 31 2018 Scott Talbert <swt@techie.net> - 1.24.0-1
- New upstream release 1.24.0
* Fri Oct 19 2018 Scott Talbert <swt@techie.net> - 1.23.2-1
- New upstream release 1.23.2
* Sat Jul 28 2018 Scott Talbert <swt@techie.net> - 1.22.5-1
- New upstream release 1.22.5
* Tue Jul 24 2018 Scott Talbert <swt@techie.net> - 1.22.3-1
- New upstream release 1.22.3
* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.22.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild
* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 1.22.2-2
- Rebuilt for Python 3.7
* Wed Feb 28 2018 Scott Talbert <swt@techie.net> - 1.22.2-1
- New upstream release 1.22.2
* Wed Feb 21 2018 Scott Talbert <swt@techie.net> - 1.22.1-1
- New upstream release 1.22.1
* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.22.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild
* Fri Jan 12 2018 Scott Talbert <swt@techie.net> - 1.22.0-1
- New upstream release 1.22.0
* Fri Dec 29 2017 Scott Talbert <swt@techie.net> - 1.21.0-1
- New upstream release 1.21.0
* Mon Nov 20 2017 Scott Talbert <swt@techie.net> - 1.20.1-2
- Avoid packaging -PYTEST.pyc files which are problematic (#1507299)
* Tue Oct 24 2017 Scott Talbert <swt@techie.net> - 1.20.1-1
- New upstream release 1.20.1
* Thu Aug 24 2017 Scott Talbert <swt@techie.net> - 1.20.0-1
- New upstream release 1.20.0
* Sat Jul 29 2017 Scott Talbert <swt@techie.net> - 1.18.2-1
- New upstream release 1.18.2
* Fri Jul 28 2017 Scott Talbert <swt@techie.net> - 1.18.1-1
- New upstream release 1.18.1
* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.18.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild
* Wed Jun 28 2017 Scott Talbert <swt@techie.net> - 1.18.0-1
- New upstream release 1.18.0
* Wed Jun 14 2017 Scott Talbert <swt@techie.net> - 1.17.1-1
- New upstream release 1.17.1
* Sat Jun 10 2017 Scott Talbert - 1.17.0-1
- New upstream release 1.17.0
* Tue May 09 2017 Scott Talbert <swt@techie.net> - 1.16.0-1
- New upstream release 1.16.0
- Enable tests
* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.15.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild
* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 1.15.0-2
- Rebuild for Python 3.6
* Mon Oct 03 2016 Scott Talbert <swt@techie.net> - 1.15.0-1
- New upstream release 1.15.0
* Thu Aug 11 2016 Scott Talbert <swt@techie.net> - 1.14-1
- Initial package.