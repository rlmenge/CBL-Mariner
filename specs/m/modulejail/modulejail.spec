## START: Set by rpmautospec
## (rpmautospec version 0.8.3)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 2;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

# This spec file has been modified by azldev to include build configuration overlays.
# Do not edit manually; changes may be overwritten.

# Based on Jeremy Cline's November 3, 2026 Fedora review proposal:
# https://jcline.fedorapeople.org/new-packages/modulejail.spec
Name:           modulejail
Version:        1.6.3
Release:        %autorelease
Summary:        Shrink Linux kernel-module attack surface

License:        GPL-3.0-only
URL:            https://modulejail.com
Source0:        https://github.com/jnuyens/modulejail/archive/refs/tags/v%{version}.tar.gz
Source1:        https://github.com/jnuyens/modulejail/releases/download/v%{version}/v%{version}.tar.gz.sig
Source2:        https://github.com/jnuyens.gpg

BuildArch:      noarch
BuildRequires:  coreutils
BuildRequires:  findutils
BuildRequires:  gawk
BuildRequires:  gnupg2
BuildRequires:  grep
BuildRequires:  sed
Requires:       coreutils
Requires:       dracut
Requires:       findutils
Requires:       gawk
Requires:       grep
Requires:       kmod
Requires:       sed
Requires:       util-linux

%description
ModuleJail snapshots the currently loaded kernel modules and generates
modprobe.d install rules for modules outside that snapshot, a selected
baseline profile, and an optional administrator-managed whitelist.

Installing this package does not generate or activate a policy. Review a
dry run and audit the intended workload before enabling enforcement.
The packaged dracut hook excludes modulejail-blacklist.conf from future
initramfs builds; existing initramfs images are not rebuilt automatically.

%prep
# Use an isolated keyring and pin the release signer, not every key GitHub
# might return from the mutable Source2 URL.
install -d -m 700 "%{_builddir}/%{name}-gnupg"
gpg2 --batch --no-options --homedir "%{_builddir}/%{name}-gnupg" \
    --import "%{SOURCE2}"
gpg2 --batch --no-options --homedir "%{_builddir}/%{name}-gnupg" \
    --status-fd 1 --verify "%{SOURCE1}" "%{SOURCE0}" \
    > "%{_builddir}/%{name}-signature.status"
awk '$2 == "VALIDSIG" && ($3 == "095F5C8B39AF010E7B615CD4487BC00D69C2A955" || $12 == "095F5C8B39AF010E7B615CD4487BC00D69C2A955") { valid=1 }
     END { if (!valid) { print "ModuleJail release signer fingerprint mismatch" > "/dev/stderr"; exit 1 } }' \
    "%{_builddir}/%{name}-signature.status"
%autosetup -n %{name}-%{version}

%build
sed -i 's/__VERSION__/%{version}/g' man/modulejail.8.in
sed -i "s/__DATE__/$(date -u -d @${SOURCE_DATE_EPOCH:?SOURCE_DATE_EPOCH must be set} +%%Y-%%m-%%d)/g" man/modulejail.8.in
# Package updates are managed through dnf, not an automatic GitHub lookup.
grep -qx 'UPDATE_CHECK_DEFAULT=1' modulejail
sed -i 's/^UPDATE_CHECK_DEFAULT=1$/UPDATE_CHECK_DEFAULT=0/' modulejail

%install
install -Dm755 modulejail "%{buildroot}%{_bindir}/modulejail"
install -Dm644 man/modulejail.8.in "%{buildroot}%{_mandir}/man8/modulejail.8"
./modulejail --install-initramfs-hook --initramfs-builder dracut \
    --destdir "%{buildroot}"

%check
sh -n "%{buildroot}%{_bindir}/modulejail"
"%{buildroot}%{_bindir}/modulejail" --version | grep -Fx 'modulejail %{version}'
"%{buildroot}%{_bindir}/modulejail" --help > /dev/null
test ! -e "%{buildroot}%{_sysconfdir}/modprobe.d/modulejail-blacklist.conf"
test ! -e "%{buildroot}%{_sysconfdir}/modulejail/whitelist.conf"

# Exercise the packaged default without networking or the build host's modules.
checkdir="$PWD/packaging-check"
mkdir -p "$checkdir/bin" "$checkdir/tmp" "$checkdir/modules/test/kernel"
export TMPDIR="$checkdir/tmp"
export MODULEJAIL_TEST_NETWORK_LOG="$checkdir/network-attempted"
cat > "$checkdir/bin/curl" <<'EOF'
#!/bin/sh
echo "Unexpected update check" > "$MODULEJAIL_TEST_NETWORK_LOG"
exit 1
EOF
chmod 755 "$checkdir/bin/curl"
touch "$checkdir/modules/test/kernel/loaded_core.ko" \
    "$checkdir/modules/test/kernel/blocked_module.ko"
printf 'loaded_core 16384 1 - Live 0x0\n' > "$checkdir/proc-modules"
env -u MODULEJAIL_NO_UPDATE_CHECK \
    PATH="$checkdir/bin:$PATH" \
    MODULEJAIL_ON_NIXOS=0 \
    MODULEJAIL_KVER=test \
    MODULEJAIL_MODULES_ROOT="$checkdir/modules" \
    MODULEJAIL_PROC_MODULES="$checkdir/proc-modules" \
    "%{buildroot}%{_bindir}/modulejail" \
    -p none --no-whitelist-file --no-syslog-logging --fail-on-module-load \
    -o "$checkdir/policy.conf"
grep -Fx 'install blocked_module /bin/false' "$checkdir/policy.conf"
test ! -e "$MODULEJAIL_TEST_NETWORK_LOG"

hook="%{buildroot}%{_prefix}/lib/dracut/modules.d/99modulejail-strip/module-setup.sh"
test -x "$hook"
sh -n "$hook"
mkdir -p "$checkdir/initrd/etc/modprobe.d"
cp "$checkdir/policy.conf" "$checkdir/initrd/etc/modprobe.d/modulejail-blacklist.conf"
echo 'blacklist unrelated_module' > "$checkdir/initrd/etc/modprobe.d/other.conf"
sh -c '. "$1"; initdir=$2; install; install' -- "$hook" "$checkdir/initrd"
test ! -e "$checkdir/initrd/etc/modprobe.d/modulejail-blacklist.conf"
grep -Fx 'blacklist unrelated_module' "$checkdir/initrd/etc/modprobe.d/other.conf"

%files
%license LICENSE
%doc README.md docs/DEFENSE-IN-DEPTH.md
%{_bindir}/modulejail
%{_mandir}/man8/modulejail.8*
%dir %{_prefix}/lib/dracut/modules.d/99modulejail-strip
%{_prefix}/lib/dracut/modules.d/99modulejail-strip/module-setup.sh

%changelog
## START: Generated by rpmautospec
* Tue Nov 10 2026 Rachel Menge <10325590+rlmenge@users.noreply.github.com> - 1.6.3-2
- Lock the ModuleJail component inputs

* Thu Jan 01 1970 azldev <> - 1.6.3-1
- Initial sources
## END: Generated by rpmautospec
