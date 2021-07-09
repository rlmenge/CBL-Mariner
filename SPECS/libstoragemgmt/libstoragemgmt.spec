%{!?python3_sitelib: %define python3_sitelib %(python3 -c "from distutils.sysconfig import get_python_lib;print(get_python_lib())")}

Summary:        Storage array management library
Name:           libstoragemgmt
Version:        1.8.4
Release:        6%{?dist}
License:        LGPLv2+
URL:            https://github.com/libstorage/libstoragemgmt
Vendor:         Microsoft Corporation
Distribution:   Mariner
Source0:        https://github.com/libstorage/libstoragemgmt/releases/download/%{version}/%{name}-%{version}.tar.gz
Patch1:         0001-change-run-dir.patch

Requires:       python3-%{name}
BuildRequires:  gcc
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  libxml2-devel
#Provided by check
#BuildRequires: check-devel 
BuildRequires:  check
BuildRequires:  perl
BuildRequires:  openssl-devel
BuildRequires:  glib-devel
BuildRequires:  systemd
BuildRequires:  bash-completion
BuildRequires:  libconfig
BuildRequires:  systemd-devel
BuildRequires:  procps-ng
BuildRequires:  sqlite-devel
BuildRequires:  python3-six
BuildRequires:  python3-devel
BuildRequires:  python3-pywbem

%{?systemd_requires}
BuildRequires:  systemd 
BuildRequires:  systemd-devel

BuildRequires:  chrpath
BuildRequires:  valgrind

%description
The libStorageMgmt library will provide a vendor agnostic open source storage
application programming interface (API) that will allow management of storage
arrays.  The library includes a command line interface for interactive use and
scripting (command lsmcli).  The library also has a daemon that is used for
executing plug-ins in a separate process (lsmd).

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package        -n python3-%{name}
Summary:        Python 3 client libraries and plug-in support for %{name}
Requires:       %{name} = %{version}-%{release}
BuildArch:      noarch
Requires:       python3-%{name}-clibs
%{?python_provide:%python_provide python3-%{name}}

%description    -n python3-%{name}
This contains python 3 client libraries as well as python framework
support and open source plug-ins written in python 3.

%package        -n python3-%{name}-clibs
Summary:        Python 3 C extension module for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
%{?python_provide:%python_provide python3-%{name}-clibs}

%description    -n python3-%{name}-clibs
This package contains python 3 client C extension libraries.

%package        smis-plugin
Summary:        Files for SMI-S generic array support for %{name}
BuildRequires:  python3-pywbem
Requires:       python3-pywbem
BuildArch:      noarch
Provides:       %{name}-ibm-v7k-plugin = 2:%{version}-%{release}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}


%description    smis-plugin
The %{name}-smis-plugin package contains plug-in for generic SMI-S array
support.


%package        netapp-plugin
Summary:        Files for NetApp array support for %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
Requires:       python3-%{name} = %{version}-%{release}
BuildArch:      noarch

%description    netapp-plugin
The %{name}-netapp-plugin package contains plug-in for NetApp array
support.


%package        targetd-plugin
Summary:        Files for targetd array support for %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    targetd-plugin
The %{name}-targetd-plugin package contains plug-in for targetd array
support.


%package        nstor-plugin
Summary:        Files for NexentaStor array support for %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    nstor-plugin
The %{name}-nstor-plugin package contains plug-in for NexentaStor array
support.

%package        udev
Summary:        Udev files for %{name}

%description    udev
The %{name}-udev package contains udev rules and helper utilities for
uevents generated by the kernel.

%package        megaraid-plugin
Summary:        Files for LSI MegaRAID support for %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    megaraid-plugin
The %{name}-megaraid-plugin package contains the plugin for LSI
MegaRAID storage management via storcli.

%package        hpsa-plugin
Summary:        Files for HP SmartArray support for %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    hpsa-plugin
The %{name}-hpsa-plugin package contains the plugin for HP
SmartArray storage management via hpssacli.

%package        arcconf-plugin
Summary:        Files for Microsemi Adaptec and Smart Family support for %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    arcconf-plugin
The %{name}-arcconf-plugin package contains the plugin for Microsemi
Adaptec RAID and Smart Family Controller storage management.

%package        nfs-plugin
Summary:        Files for NFS local filesystem support for %{name}
Requires:       python3-%{name} = %{version}
Requires:       %{name}-nfs-plugin-clibs = %{version}
Requires:       nfs-utils
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    nfs-plugin
The nfs-plugin package contains plug-in for local NFS exports support.

%package        nfs-plugin-clibs
Summary:        Python C extension module for %{name} NFS plugin
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    nfs-plugin-clibs
The %{name}-nfs-plugin-clibs package contains python C
extension for %{name} NFS plugin.


%package        local-plugin
Summary:        Files for local pseudo plugin of %{name}
Requires:       python3-%{name} = %{version}
Requires(post): python3-%{name} = %{version}
Requires(postun): python3-%{name} = %{version}
BuildArch:      noarch

%description    local-plugin
The %{name}-local-plugin is a plugin that provides auto
plugin selection for locally managed storage.

%prep
%autosetup -p1

%build
./autogen.sh
%configure --with-python3 --disable-static
%make_build

%install
rm -rf %{buildroot}

%make_install

find %{buildroot} -name '*.la' -exec rm -f {} ';'

#Files for udev handling
mkdir -p %{buildroot}/%{_udevrulesdir}
install -m 644 tools/udev/90-scsi-ua.rules \
    %{buildroot}/%{_udevrulesdir}/90-scsi-ua.rules
install -m 755 tools/udev/scan-scsi-target \
    %{buildroot}/%{_udevrulesdir}/../scan-scsi-target

mkdir -p %{buildroot}/%{_datadir}/bash-completion/completions/
mv %{buildroot}/etc/bash_completion.d/lsmcli %{buildroot}/%{_datadir}/bash-completion/completions/

%check
if ! make check
then
  cat test-suite.log || true
  exit 1
fi

%pre
getent group libstoragemgmt >/dev/null || groupadd -r libstoragemgmt
getent passwd libstoragemgmt >/dev/null || \
    useradd -r -g libstoragemgmt -d /var/run/lsm -s /sbin/nologin \
    -c "daemon account for libstoragemgmt" libstoragemgmt

%post
/sbin/ldconfig
# Create tmp socket folders.
%tmpfiles_create %{_tmpfilesdir}/%{name}.conf
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
/sbin/ldconfig
%systemd_postun %{name}.service

# Need to restart lsmd if plugin is new installed or removed.
%post smis-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%postun smis-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post netapp-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%postun netapp-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post targetd-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%postun targetd-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post nstor-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%postun nstor-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post megaraid-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%postun megaraid-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post hpsa-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%postun hpsa-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post arcconf-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%postun arcconf-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post nfs-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%postun nfs-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# Need to restart lsmd if plugin is new installed or removed.
%post local-plugin
if [ $1 -eq 1 ]; then
    # New install.
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi
%postun local-plugin
if [ $1 -eq 0 ]; then
    # Remove
    /usr/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%files
%license COPYING.LIB
%doc README NEWS
%{_mandir}/man1/lsmcli.1*
%{_mandir}/man1/lsmd.1*
%{_mandir}/man5/lsmd.conf.5*
%{_libdir}/*.so.*
%{_bindir}/lsmcli
%{_datadir}/bash-completion/completions/lsmcli
%{_bindir}/lsmd
%{_bindir}/simc_lsmplugin
%dir %{_sysconfdir}/lsm
%dir %{_sysconfdir}/lsm/pluginconf.d
%config(noreplace) %{_sysconfdir}/lsm/lsmd.conf
%{_mandir}/man1/simc_lsmplugin.1*

%{_unitdir}/%{name}.service

%ghost %dir %attr(0775, root, libstoragemgmt) /run/lsm/
%ghost %dir %attr(0775, root, libstoragemgmt) /run/lsm/ipc

%attr(0644, root, root) %{_tmpfilesdir}/%{name}.conf

%files devel
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig/%{name}.pc
%{_mandir}/man3/lsm_*
%{_mandir}/man3/libstoragemgmt*

%files -n python3-%{name}
%dir %{python3_sitelib}/lsm
%{python3_sitelib}/lsm/__init__.*
%dir %{python3_sitelib}/lsm/external
%{python3_sitelib}/lsm/external/*
%{python3_sitelib}/lsm/_client.*
%{python3_sitelib}/lsm/_common.*
%{python3_sitelib}/lsm/_local_disk.*
%{python3_sitelib}/lsm/_data.*
%{python3_sitelib}/lsm/_iplugin.*
%{python3_sitelib}/lsm/_pluginrunner.*
%{python3_sitelib}/lsm/_transport.*
%{python3_sitelib}/lsm/__pycache__/
%{python3_sitelib}/lsm/version.*
%dir %{python3_sitelib}/lsm/plugin
%{python3_sitelib}/lsm/plugin/__init__.*
%{python3_sitelib}/lsm/plugin/__pycache__/
%dir %{python3_sitelib}/lsm/plugin/sim
%{python3_sitelib}/lsm/plugin/sim/__pycache__/
%{python3_sitelib}/lsm/plugin/sim/__init__.*
%{python3_sitelib}/lsm/plugin/sim/simulator.*
%{python3_sitelib}/lsm/plugin/sim/simarray.*
%dir %{python3_sitelib}/lsm/lsmcli
%{python3_sitelib}/lsm/lsmcli/__init__.*
%{python3_sitelib}/lsm/lsmcli/__pycache__/
%{python3_sitelib}/lsm/lsmcli/data_display.*
%{python3_sitelib}/lsm/lsmcli/cmdline.*
%{_bindir}/sim_lsmplugin
%dir %{_libexecdir}/lsm.d
%{_libexecdir}/lsm.d/find_unused_lun.py*
%{_libexecdir}/lsm.d/local_sanity_check.py*
%config(noreplace) %{_sysconfdir}/lsm/pluginconf.d/sim.conf
%{_mandir}/man1/sim_lsmplugin.1*

%files -n python3-%{name}-clibs
%{python3_sitelib}/lsm/_clib.*

%files smis-plugin
%dir %{python3_sitelib}/lsm/plugin/smispy
%dir %{python3_sitelib}/lsm/plugin/smispy/__pycache__
%{python3_sitelib}/lsm/plugin/smispy/__pycache__/*
%{python3_sitelib}/lsm/plugin/smispy/__init__.*
%{python3_sitelib}/lsm/plugin/smispy/smis.*
%{python3_sitelib}/lsm/plugin/smispy/dmtf.*
%{python3_sitelib}/lsm/plugin/smispy/utils.*
%{python3_sitelib}/lsm/plugin/smispy/smis_common.*
%{python3_sitelib}/lsm/plugin/smispy/smis_cap.*
%{python3_sitelib}/lsm/plugin/smispy/smis_sys.*
%{python3_sitelib}/lsm/plugin/smispy/smis_pool.*
%{python3_sitelib}/lsm/plugin/smispy/smis_disk.*
%{python3_sitelib}/lsm/plugin/smispy/smis_vol.*
%{python3_sitelib}/lsm/plugin/smispy/smis_ag.*
%{_bindir}/smispy_lsmplugin
%{_mandir}/man1/smispy_lsmplugin.1*

%files netapp-plugin
%dir %{python3_sitelib}/lsm/plugin/ontap
%dir %{python3_sitelib}/lsm/plugin/ontap/__pycache__
%{python3_sitelib}/lsm/plugin/ontap/__pycache__/*
%{python3_sitelib}/lsm/plugin/ontap/__init__.*
%{python3_sitelib}/lsm/plugin/ontap/na.*
%{python3_sitelib}/lsm/plugin/ontap/ontap.*
%{_bindir}/ontap_lsmplugin
%{_mandir}/man1/ontap_lsmplugin.1*

%files targetd-plugin
%dir %{python3_sitelib}/lsm/plugin/targetd
%dir %{python3_sitelib}/lsm/plugin/targetd/__pycache__
%{python3_sitelib}/lsm/plugin/targetd/__pycache__/*
%{python3_sitelib}/lsm/plugin/targetd/__init__.*
%{python3_sitelib}/lsm/plugin/targetd/targetd.*
%{_bindir}/targetd_lsmplugin
%{_mandir}/man1/targetd_lsmplugin.1*

%files nstor-plugin
%dir %{python3_sitelib}/lsm/plugin/nstor
%dir %{python3_sitelib}/lsm/plugin/nstor/__pycache__
%{python3_sitelib}/lsm/plugin/nstor/__pycache__/*
%{python3_sitelib}/lsm/plugin/nstor/__init__.*
%{python3_sitelib}/lsm/plugin/nstor/nstor.*
%{_bindir}/nstor_lsmplugin
%{_mandir}/man1/nstor_lsmplugin.1*

%files udev
%{_udevrulesdir}/../scan-scsi-target
%{_udevrulesdir}/90-scsi-ua.rules

%files megaraid-plugin
%dir %{python3_sitelib}/lsm/plugin/megaraid
%dir %{python3_sitelib}/lsm/plugin/megaraid/__pycache__
%{python3_sitelib}/lsm/plugin/megaraid/__pycache__/*
%{python3_sitelib}/lsm/plugin/megaraid/__init__.*
%{python3_sitelib}/lsm/plugin/megaraid/megaraid.*
%{python3_sitelib}/lsm/plugin/megaraid/utils.*
%{_bindir}/megaraid_lsmplugin
%config(noreplace) %{_sysconfdir}/lsm/pluginconf.d/megaraid.conf
%{_mandir}/man1/megaraid_lsmplugin.1*

%files hpsa-plugin
%dir %{python3_sitelib}/lsm/plugin/hpsa
%dir %{python3_sitelib}/lsm/plugin/hpsa/__pycache__
%{python3_sitelib}/lsm/plugin/hpsa/__pycache__/*
%{python3_sitelib}/lsm/plugin/hpsa/__init__.*
%{python3_sitelib}/lsm/plugin/hpsa/hpsa.*
%{python3_sitelib}/lsm/plugin/hpsa/utils.*
%{_bindir}/hpsa_lsmplugin
%config(noreplace) %{_sysconfdir}/lsm/pluginconf.d/hpsa.conf
%{_mandir}/man1/hpsa_lsmplugin.1*

%files nfs-plugin
%dir %{python3_sitelib}/lsm/plugin/nfs
%dir %{python3_sitelib}/lsm/plugin/nfs/__pycache__
%{python3_sitelib}/lsm/plugin/nfs/__pycache__/*
%{python3_sitelib}/lsm/plugin/nfs/__init__.*
%{python3_sitelib}/lsm/plugin/nfs/nfs.*
%config(noreplace) %{_sysconfdir}/lsm/pluginconf.d/nfs.conf
%{_bindir}/nfs_lsmplugin
%{_mandir}/man1/nfs_lsmplugin.1*

%files nfs-plugin-clibs
%{python3_sitelib}/lsm/plugin/nfs/nfs_clib.*

%files arcconf-plugin
%dir %{python3_sitelib}/lsm/plugin/arcconf
%dir %{python3_sitelib}/lsm/plugin/arcconf/__pycache__
%{python3_sitelib}/lsm/plugin/arcconf/__pycache__/*
%{python3_sitelib}/lsm/plugin/arcconf/__init__.*
%{python3_sitelib}/lsm/plugin/arcconf/arcconf.*
%{python3_sitelib}/lsm/plugin/arcconf/utils.*
%{_bindir}/arcconf_lsmplugin
%config(noreplace) %{_sysconfdir}/lsm/pluginconf.d/arcconf.conf
%{_mandir}/man1/arcconf_lsmplugin.1*

%files local-plugin
%dir %{python3_sitelib}/lsm/plugin/local
%dir %{python3_sitelib}/lsm/plugin/local/__pycache__
%{python3_sitelib}/lsm/plugin/local/__pycache__/*
%{python3_sitelib}/lsm/plugin/local/__init__.*
%{python3_sitelib}/lsm/plugin/local/local.*
%config(noreplace) %{_sysconfdir}/lsm/pluginconf.d/local.conf
%{_bindir}/local_lsmplugin
%{_mandir}/man1/local_lsmplugin.1*

%changelog
* Fri Aug 21 2020 Thomas Crain <thcrain@microsoft.com> 1.8.4-6
- Initial CBL-Mariner version imported from Fedora 33 (license: MIT)
- License verified

* Sat Aug 01 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.4-5
- Second attempt - Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Tue Jul 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.4-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Mon Jul 13 2020 Tom Stellard <tstellar@redhat.com> - 1.8.4-3
- Use make macros
- https://fedoraproject.org/wiki/Changes/UseMakeBuildInstallMacro

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 1.8.4-2
- Rebuilt for Python 3.9

* Thu May 21 2020 Tony Asleson <tasleson@redhat.com> - 1.8.4-1
- Upgrade to 1.8.4

* Wed Feb 12 2020 Tony Asleson <tasleson@redhat.com> - 1.8.3-1
- Upgrade to 1.8.3

* Mon Feb 10 2020 Tony Asleson <tasleson@redhat.com> - 1.8.2-3
- Correct python clib packages to include ISA for correct dependencies

* Wed Jan 29 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Tue Dec 10 2019 Tony Asleson <tasleson@redhat.com> - 1.8.2-1
- Upgrade to 1.8.2

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 1.8.0-4
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1.8.0-3
- Rebuilt for Python 3.8

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Apr 17 2019 Tony Asleson <tasleson@redhat.com> - 1.8.0-1
- Upgrade to 1.8.0

* Mon Feb 18 2019 Tony Asleson <tasleson@redhat.com> - 1.7.3-1
- Upgrade to 1.7.3

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.7.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Dec 19 2018 Tony Asleson <tasleson@redhat.com> - 1.7.2-1
- Upgrade to 1.7.2

* Tue Nov 6 2018 Tony Asleson <tasleson@redhat.com> - 1.7.1-1
- Upgrade to 1.7.1

* Wed Oct 31 2018 Tony Asleson <tasleson@redhat.com> - 1.7.0-1
- Upgrade to 1.7.0

* Tue Sep 18 2018 Gris Ge <fge@redhat.com> - 1.6.2-10
- Add explicit package version requirement to libstoragemgmt-nfs-plugin-clibs.

* Mon Sep 17 2018 Gris Ge <fge@redhat.com> - 1.6.2-9
- Fix the `rpm -V` failures. (RHBZ #1629735, the same issue also in Fedora)

* Tue Jul 24 2018 Adam Williamson <awilliam@redhat.com> - 1.6.2-8
- Rebuild for new libconfig

* Tue Jul 24 2018 Gris Ge <fge@redhat.com> - 1.6.2-7
- Add missing gcc gcc-c++ build requirements.

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.6.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 26 2018 Gris Ge <fge@redhat.com> - 1.6.2-5
- Fix lscmli on python 3.7.

* Tue Jun 26 2018 Gris Ge <fge@redhat.com> - 1.6.2-4
- Rebuild again with --target=f29-python.

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 1.6.2-3
- Rebuilt for Python 3.7

* Mon Jun 18 2018 Gris Ge <fge@redhat.com> - 1.6.2-2
- Removed the requirement of initscripts. (RHBZ 1592363)

* Fri May 18 2018 Gris Ge <fge@redhat.com> - 1.6.2-1
- Upgrade to 1.6.2.

* Fri Mar 23 2018 Gris Ge <fge@redhat.com> - 1.6.1-7
- Fix incorect memset size.

* Fri Mar 23 2018 Gris Ge <fge@redhat.com> - 1.6.1-6
- Add ./autogen.sh back to fix the version diff on autotools.

* Fri Mar 23 2018 Gris Ge <fge@redhat.com> - 1.6.1-5
- Add missing rpm script for arcconf, nfs, local plugins.

* Thu Mar 22 2018 Gris Ge <fge@redhat.com> - 1.6.1-4
- Fix build on GCC 8

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.6.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jan 03 2018 Lumír Balhar <lbalhar@redhat.com> - 1.6.1-2
- Fix directory ownership in python subpackages

* Tue Oct 31 2017 Gris Ge <fge@redhat.com> - 1.6.1-1
- Upgrade to 1.6.1

* Thu Oct 19 2017 Gris Ge <fge@redhat.com> - 1.6.0-1
- Upgrade to 1.6.0

* Sun Oct 15 2017 Gris Ge <fge@redhat.com> - 1.5.0-3
- Specify Python version in SPEC Requires.

* Wed Oct 11 2017 Gris Ge <fge@redhat.com> - 1.5.0-2
- Fix multilib confliction of nfs-plugin by move binrary file to
  another subpackage libstoragemgmt-nfs-plugin-clibs

* Tue Oct 10 2017 Gris Ge <fge@redhat.com> - 1.5.0-0
- New upstream release 1.5.0:
    * New sub-package libstoragemgmt-nfs-plugin, libstoragemgmt-arcconf-plugin,
      and libstoragemgmt-local-plugin.
    * C API manpages for libstoragemgmt-devel package.

* Tue Oct 3 2017 Tony Asleson <tasleson@redhat.com> - 1.4.0-5
- Remove m2crypto requirement

* Sat Aug 19 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 1.4.0-4
- Python 2 binary packages renamed to python2-libstoragemgmt and python2-libstoragemgmt-clibs
  See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3
- %%python_provide added for all four python subpackages

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue Feb 21 2017 Gris Ge <fge@redhat.com> 1.4.0-1
- Add Python3 support.
- New sub rpm package python3-libstoragemgmt.
- Add support of lmiwbem(this rpm use pywbem instead).
- Allow plugin test to be run concurrently.
- Bug fixes:
    * Fix megaraid plugin for dell PERC.
    * Fix local disk rotation speed query on NVMe disk.
    * Fix lsmcli incorrect try-expect on local disk query.
    * Fix all the gcc compile warnings.
    * Fix the obsolete usage of AC_OUTPUT in configure.ac.
- Library adds:
    * Query serial of local disk:
        lsm_local_disk_serial_num_get()/lsm.LocalDisk.serial_num_get()
    * Query LED status of local disk:
        lsm_local_disk_led_status_get()/lsm.LocalDisk.led_status_get()
    * Query link speed of local disk:
        lsm_local_disk_link_speed_get()/lsm.LocalDisk.link_speed_get()

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Sep 27 2016 Gris Ge <fge@redhat.com> 1.3.5-1
- New upstream release 1.3.5

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.2-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Wed May 18 2016 Tony Asleson <tasleson@redhat.com> 1.3.2-1
- New upstream release 1.3.2

* Fri May 13 2016 Tony Asleson <tasleson@redhat.com> 1.3.1-2
- Disable make check as we are hitting a valgrind memleak in ld.so
  on arm arch.

* Fri May 13 2016 Tony Asleson <tasleson@redhat.com> 1.3.1-1
- New upstream release 1.3.1

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jun 24 2015 Gris Ge <fge@redhat.com> 1.2.3-1
- New upstream release 1.2.3:
    * Bug fixes:
        * lsmcli bash completion: Fix syntax error.
        * lsmcli bash completion: Fix volume-delete.
        * lsmcli bash completion: Add missing completions.
        * Fix: selinux dac_override
        * Manpage: Update hpsa and megaraid plugin manpages.
        * HP Smart Array Plugin: Fix pool querying on P410i.
        * MegaRAID Plugin: Fix bug when no volume configured.

* Fri Jun 19 2015 Gris Ge <fge@redhat.com> - 1.2.1-1
- New upstream release 1.2.1.
- Changed upstream URL and source URL to github.
- New sub-pacakges:
    * libstoragemgmt-megaraid-plugin
        New plugin in 1.2.0 release.
    * libstoragemgmt-hpsa-plugin
        New plugin in 1.2.0 release.
- Add bash-completion script for lsmcli.
- New rpmbuild switch: 
    * '--without test'
        Use to skip 'make check' test to save debug time.
    * '--without megaraid'
        Don't compile megaraid plugin.
    * '--without hpsa'
        Don't compile hpsa plugin.
- Remove PyYAML BuildRequires.
- Add NEWS(changelog) to document folder.
- Replace the hardcoded udev path with <percent>{_udevrulesdir}.
- Fix rpmlint error 'dir-or-file-in-var-run'.
- Mark /run/lsm and /run/lsm/ipc as <percent>ghost folder.
- Fix rpmlint warnning 'W: non-standard-uid /run/lsm libstoragemgmt'.
- Add 'Requires(post)' and 'Requires(postun)' to plugins in order
  to make sure plugin is installed after libstoragemgmt and removed before
  libstoragemgmt.
- Fix the incorrect use of <percent>bcond_with and <percent>bcond_without.
- Removed autogen.sh which is not required for release version any more.

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.1.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1.1.0-3
- Rebuilt for GCC 5 C++11 ABI change

* Fri Jan 16 2015 Tony Asleson <tasleson@redhat.com> 1.1.0-2
- Make updates work correctly for removed sub package
  libstoragemgmt-ibm-v7k-plugin

* Thu Dec 4 2014 Tony Asleson <tasleson@redhat.com> 1.1.0-1
- New upstream release
- Fix udev files directory
- Move command line files to python package

* Wed Oct 8 2014 Tony Asleson <tasleson@redhat.com> - 1.0.0-3
- Specify udev files to /usr/lib dir instead of /lib
- Move command line python files to python package

* Wed Oct 1 2014 Tony Asleson <tasleson@redhat.com> - 1.0.0-2
- BZ 850185, Use new systemd rpm macros
- BZ 1122117, Use correct tmpfiles.d dir

* Sun Sep 7 2014 Tony Asleson <tasleson@redhat.com> - 1.0.0-1
- New upstream release

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jul 3 2014 Tony Asleson <tasleson@redhat.com> - 0.1.0-1
- New upstream release

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.24-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Jan 30 2014 Tony Asleson <tasleson@redhat.com> 0.0.24-1
- New upstream release

* Wed Nov 27 2013 Tony Asleson <tasleson@redhat.com> 0.0.23-1
- New upstream release

* Mon Aug 12 2013 Tony Asleson <tasleson@redhat.com> 0.0.22-1
- New upstream release

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.21-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Jul 16 2013 Tony Asleson <tasleson@redhat.com> 0.0.21-1
- New upstream release
- Put plug-ins in separate sub packages
- Don't include IBM plug-in on RHEL > 6, missing paramiko

* Tue May 28 2013 Tony Asleson <tasleson@redhat.com> - 0.0.20-1
- New upstream release
- Separate package for python libraries
- Make timestamps match on version.py in library
- Add python-paramiko requirement for IBM plug-in

* Mon Apr 22 2013 Tony Asleson <tasleson@redhat.com> - 0.0.19-1
- New upstream release

* Fri Mar 8 2013 Tony Asleson <tasleson@redhat.com> - 0.0.18-1
- New upstream release

* Thu Jan 31 2013 Tony Asleson <tasleson@redhat.com> - 0.0.17-1
- New upstream release

* Wed Jan 2 2013 Tony Asleson <tasleson@redhat.com> - 0.0.16-1
- New upstream release

* Tue Nov 27 2012 Tony Asleson <tasleson@redhat.com> - 0.0.15-1
- New upstream release

* Wed Oct 3 2012 Tony Asleson <tasleson@redhat.com> - 0.0.13-1
- New upstream release

* Tue Sep 18 2012 Tony Asleson <tasleson@redhat.com> - 0.0.12-1
- New upstream release

* Mon Aug 13 2012 Tony Asleson <tasleson@redhat.com> 0.0.11-1
- New upstream release

* Fri Jul 27 2012 Dan Horák <dan[at]danny.cz> - 0.0.9-3
- detect also non-x86 arches in Pegasus check

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 12 2012 Tony Asleson <tasleson@redhat.com> 0.0.9-1
- Initial checkin of lio plug-in
- System filtering via URI (smispy)
- Error code mapping (ontap)
- Fixed build so same build tarball is used for all binaries

* Mon Jun 4 2012 Tony Asleson <tasleson@redhat.com> 0.0.8-1
- Make building of SMI-S CPP plugin optional
- Add pkg-config file
- SMIS: Fix exception while retrieving Volumes
- SMIS: Fix exception while retrieving Volumes
- lsm: Add package imports
- Make Smis class available in lsm python package
- Add option to disable building C unit test
- Make simulator classes available in lsm python package
- Make ontap class available in lsm python package
- Changes to support building on Fedora 17 (v2)
- Spec. file updates from feedback from T. Callaway (spot)
- F17 linker symbol visibility correction
- Remove unneeded build dependencies and cleaned up some warnings
- C Updates, client C library feature parity with python

* Fri May 11 2012 Tony Asleson <tasleson@redhat.com> 0.0.7-1
- Bug fix for smi-s constants
- Display formatting improvements
- Added header option for lsmcli
- Improved version handling for builds
- Made terminology consistent
- Ability to list visibility for access groups and volumes
- Simulator plug-in fully supports all block operations
- Added support for multiple systems with a single plug-in instance

* Fri Apr 20 2012 Tony Asleson <tasleson@redhat.com> 0.0.6-1
- Documentation improvements (man & source code)
- Support for access groups
- Unified spec files Fedora/RHEL
- Package version auto generate
- Rpm target added to make
- Bug fix for missing optional property on volume retrieval (smispy plug-in)

* Fri Apr 6 2012 Tony Asleson <tasleson@redhat.com> 0.0.5-1
- Spec file clean-up improvements
- Async. operation added to lsmcli and ability to check on job status
- Sub volume replication support
- Ability to check for child dependencies on VOLUMES, FS and files
- SMI-S Bug fixes and improvements

* Mon Mar 26 2012 Tony Asleson <tasleson@redhat.com> 0.0.4-1
- Restore from snapshot
- Job identifiers string instead of integer
- Updated license address

* Wed Mar 14 2012 Tony Asleson <tasleson@redhat.com> 0.0.3-1
- Changes to installer, daemon uid, gid, /var/run/lsm/*
- NFS improvements and bug fixes
- Python library clean up (rpmlint errors)

* Sun Mar 11 2012 Tony Asleson <tasleson@redhat.com> 0.0.2-1
- Added NetApp native plugin

* Mon Feb 6 2012 Tony Asleson <tasleson@redhat.com>  0.0.1alpha-1
- Initial version of package

