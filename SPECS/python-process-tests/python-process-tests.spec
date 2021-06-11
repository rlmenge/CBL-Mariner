%{!?python3_pkgversion: %global python3_pkgversion 3}
%{!?python3_version: %define python3_version %(python3 -c "import sys; sys.stdout.write(sys.version[:3])")}
%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?py3_build: %define py3_build CFLAGS="%{optflags}" %{__python3} setup.py build}
%{!?py3_install: %define py3_install %{__python3} setup.py install --skip-build --root %{buildroot}}

%global srcname process-tests

Summary:        Tools for testing processes
Name:           python-%{srcname}
Version:        2.0.2
Release:        9%{?dist}
License:        BSD
URL:            https://github.com/ionelmc/python-process-tests
#Source0:       https://pypi.python.org/packages/source/p/%{srcname}/%{srcname}-%{version}.tar.gz
Source0:        https://pypi.python.org/packages/source/p/%{srcname}/%{name}-%{version}.tar.gz
BuildArch:      noarch

%description
Tools for testing processes.

%package -n python%{python3_pkgversion}-%{srcname}
Summary:        Tools for testing processes
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
%{?python_provide:%python_provide python%{python3_pkgversion}-%{srcname}}

%description -n python%{python3_pkgversion}-%{srcname}
Tools for testing processes for Python 3.

%prep
%setup -q -n %{srcname}-%{version}

%build
%{py3_build}

%install
%{py3_install}

%files -n python%{python3_pkgversion}-%{srcname}
%doc README.rst
%license LICENSE
%{python3_sitelib}/__pycache__/*
%{python3_sitelib}/process_tests*

%changelog
* Tue Dec 08 2020 Steve Laughman <steve.laughman@microsoft.com> - 2.0.2-9
- Initial CBL-Mariner import from Fedora 33 (license: MIT)
* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.2-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild
* Fri May 22 2020 Miro Hrončok <mhroncok@redhat.com> - 2.0.2-7
- Rebuilt for Python 3.9
* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild
* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 2.0.2-5
- Rebuilt for Python 3.8.0rc1 (#1748018)
* Thu Aug 15 2019 Miro Hrončok <mhroncok@redhat.com> - 2.0.2-4
- Rebuilt for Python 3.8
* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2.0.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild
* Mon Apr  8 2019 Orion Poplawski <orion@nwra.com> - 2.0.2-2
- Drop python2 (bug #1697617)
* Tue Feb 12 2019 Orion Poplawski <orion@nwra.com> - 2.0.2-1
- Update to 2.0.2
* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild
* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild
* Thu Jun 14 2018 Miro Hrončok <mhroncok@redhat.com> - 1.0.0-11
- Rebuilt for Python 3.7
* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild
* Wed Aug 9 2017 Orion Poplawski <orion@cora.nwra.com> - 1.0.0-9
- Ship python2-process-tests
- Build for python3 on EPEL
* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild
* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild
* Tue Dec 13 2016 Stratakis Charalampos <cstratak@redhat.com> - 1.0.0-6
- Rebuild for Python 3.6
* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.0-5
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages
* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.0.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild
* Fri Nov 06 2015 Robert Kuska <rkuska@redhat.com> - 1.0.0-3
- Rebuilt for Python3.5 rebuild
* Wed Jul 29 2015 Orion Poplawski <orion@cora.nwra.com> - 1.0.0-2
- Do not own python3 __pycache__ dir
* Wed Jul 29 2015 Orion Poplawski <orion@cora.nwra.com> - 1.0.0-1
- Initial package