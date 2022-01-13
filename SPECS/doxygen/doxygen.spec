Name:           doxygen
Version:        1.9.3
Release:        1%{?dist}
Summary:        Automated C, C++, and Java Documentation Generator
License:        GPL
Group:          Development/Tools/Doc Generators
Url:            https://www.doxygen.nl
Vendor:		Microsoft Corporation
Distribution:	Mariner
Source0:        https://doxygen.nl/files/%{name}-%{version}.src.tar.gz

%global debug_package %{nil}

BuildRequires:  bison
BuildRequires:  cmake
BuildRequires:  flex
BuildRequires:  gcc
BuildRequires:  python3
BuildRequires:  python3-xml
BuildRequires:  python3-defusedxml
Obsoletes:      doxygen-doc

%description
Doxygen is a documentation system for C, C++, Java, and IDL. It can
generate an online class browser (in HTML) and an offline reference
manual (in LaTeX) from a set of documented source files. The
documentation is extracted directly from the sources. Doxygen is
developed on a Linux platform, but it runs on most other UNIX flavors
as well.

%prep
%setup -q

%build
cmake -G "Unix Makefiles"     \
    -DCMAKE_BUILD_TYPE=Release    \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -Wno-dev .
make %{?_smp_mflags}


%install
make install DESTDIR=%{buildroot}
mkdir -p %{buildroot}%{_mandir}/man1/
install -vm 644 doc/doxygen.1 %{buildroot}%{_mandir}/man1/

%files
%doc LANGUAGE.HOWTO
%attr(644,root,root) %{_mandir}/man1/doxygen.1.gz
%attr(755,root,root) %{_bindir}/doxygen
%license LICENSE

%changelog
* Wed Jan 12 2022 Rachel Menge <rachelmenge@microsoft.com> - 1.9.3-1
- Update to version 1.9.3

* Wed Dec 16 2020 Joe Schmitt <joschmit@microsoft.com> - 1.8.17-2
- Remove buildarch

* Mon Apr 06 2020 Anirudh Gopal <angop@microsoft.com> 1.8.17-1
- Original version for CBL-Mariner.
