%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}
%{!?__python3: %global __python3 /usr/bin/python3}
%{!?python3_pkgversion: %global python3_pkgversion 3}
%{!?py3_build: %define py3_build CFLAGS="%{optflags}" %{__python3} setup.py build}
%{!?py3_install: %define py3_install %{__python3} setup.py install --skip-build --root %{buildroot}}
%{!?python3_version: %define python3_version %(python3 -c "import sys; sys.stdout.write(sys.version[:3])")}
%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}

%?python_enable_dependency_generator

%global srcname conda-package-handling
%global pkgname conda_package_handling

Name:           python-%{srcname}
Version:        1.7.2
Release:        2%{?dist}
Summary:        Create and extract conda packages of various formats

License:        BSD
URL:            https://github.com/conda/%{srcname}
Source0:        https://github.com/conda/%{srcname}/archive/%{version}/%{srcname}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  libarchive-devel

%description
Create and extract conda packages of various formats.

%package -n python%{python3_pkgversion}-%{srcname}
Summary:        %{summary}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-Cython
BuildRequires:  python%{python3_pkgversion}-six
BuildRequires:  python%{python3_pkgversion}-tqdm
BuildRequires:  python%{python3_pkgversion}-pytest
BuildRequires:  python%{python3_pkgversion}-pytest-cov
BuildRequires:  python%{python3_pkgversion}-pytest-mock
Requires:       python%{python3_pkgversion}-six
Requires:       python%{python3_pkgversion}-tqdm
%{?python_provide:%python_provide python%{python3_pkgversion}-%{srcname}}

%description -n python%{python3_pkgversion}-%{srcname}
Create and extract conda packages of various formats.

%prep
%autosetup -n %{srcname}-%{version}
sed -i -e s/archive_and_deps/archive/ setup.py

%build
%py3_build

%install
%py3_install

%check
# test_secure_refusal_to_extract_abs_paths is not ready upstream
# https://github.com/conda/conda-package-handling/issues/59
PYTHONPATH=%{buildroot}%{python3_sitearch} py.test-%{python3_version} -v tests -k 'not test_secure_refusal_to_extract_abs_paths'

%files -n python%{python3_pkgversion}-%{srcname}
%license LICENSE
%doc AUTHORS.txt CHANGELOG.md README.md
%{_bindir}/cph
%{python3_sitearch}/%{pkgname}-*.egg-info/
%{python3_sitearch}/%{pkgname}/

%changelog
* Wed Jan 27 2021 Fedora Release Engineering <releng@fedoraproject.org> - 1.7.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Sun Oct 18 2020 Orion Poplawski <orion@nwra.com> - 1.7.2-1
- Update to 1.7.2

* Wed Jul 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.7.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jun 24 2020 Orion Poplawski <orion@nwra.com> - 1.7.0-3
- Add BR on python-setuptools

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 1.7.0-2
- Rebuilt for Python 3.9

* Thu May 07 2020 Orion Poplawski <orion@nwra.com> - 1.7.0-1
- Update to 1.7.0

* Thu May 07 2020 Orion Poplawski <orion@nwra.com> - 1.6.1-1
- Update to 1.6.1

* Sun Feb 2 2020 Orion Poplawski <orion@nwra.com> - 1.6.0-3
- Exclude failing test that is not ready upstream

* Thu Jan 30 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Fri Nov  8 2019 Orion Poplawski <orion@nwra.com> - 1.6.0-1
- Update to 1.6.0

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 1.4.1-3
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1.4.1-2
- Rebuilt for Python 3.8

* Fri Aug 16 2019 Orion Poplawski <orion@nwra.com> - 1.4.1-1
- Update to 1.4.1
- Enable python dependency generator

* Mon Jul 29 2019 Orion Poplawski <orion@nwra.com> - 1.3.11-1
- Update to 1.3.11

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Tue Jun 11 2019 Orion Poplawski <orion@nwra.com> - 1.3.1-1
- Update to 1.3.1

* Sat May 18 2019 Orion Poplawski <orion@nwra.com> - 1.1.1-1
- Initial Fedora package
