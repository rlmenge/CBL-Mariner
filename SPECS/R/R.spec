# We do not want this.
%define __brp_mangle_shebangs /usr/bin/true

%global runjavareconf 1

# lapack comes from openblas, whenever possible.
# We decided to implement this change in Fedora 31+ and EPEL-8 only.
# This was to minimize the impact on end-users who might have R modules
# installed locally with the old dependency on libRlapack.so

%if 0%{?fedora} >= 31
%global syslapack 1
%else
%if 0%{?rhel} && 0%{?rhel} >= 8
%global syslapack 1
%else
%global syslapack 0
%endif
%endif

%if 0%{?rhel} >= 8
 %global openblas 1
%else
 %if 0%{?rhel} == 7
  %ifarch x86_64 %{ix86} armv7hl %{power64} aarch64
   %global openblas 1
  %else
   %global openblas 0
  %endif
 %else
  %if 0%{?fedora}
   %global openblas 1
  %else
   %global openblas 0
  %endif
 %endif
%endif

%if 0%{?fedora} >= 33
%global flexiblas 1
%else
%global flexiblas 0
%endif

%if 0%{?fedora} >= 31
%global usemacros 1
%else
%if 0%{?rhel} && 0%{?rhel} >= 8
%global usemacros 1
%else
%global usemacros 0
%endif
%endif

%if 0%{?rhel} && 0%{?rhel} <= 6
%ifarch ppc64 ppc64le
%global runjavareconf 0
%endif
%endif

%ifarch x86_64
%global java_arch amd64
%else
%global java_arch %{_arch}
%endif

# Assume not modern. Override if needed.
%global modern 0

# Track if we're hardening (all current fedora and RHEL 7+)
%global hardening 0

%global with_lto 0
%global with_java_headless 0

%global system_tre 0
# We need to use system tre on F21+/RHEL7
%if 0%{?fedora} >= 21
%global system_tre 1
%global with_java_headless 1
%endif

# We need this on old EL for C++11 support.
%if 0%{?rhel} && 0%{?rhel} <= 7
%global use_devtoolset 1
%else
%global use_devtoolset 0
%endif

%if 0%{?rhel} == 7
%global dts_version 8
%endif

%if 0%{?rhel} == 6
%global dts_version 7
%endif

# Using lto breaks debuginfo.
# %%if 0%%{?fedora} >= 19
# %%global with_lto 1
# %%endif

%if 0%{?rhel} >= 7
%global system_tre 1
# %%global with_lto 1
%global with_java_headless 1
%global hardening 1
%endif

%if 0%{?fedora}
%global modern 1
%global hardening 1
%endif

%if 0%{?rhel} >= 6
%global modern 1
%endif

# R really wants zlib 1.2.5, bzip2 1.0.6, xz 5.0.3, curl 7.28, and pcre 8.10+
# These are too new for RHEL 5/6. HACKITY HACK TIME.
%global zlibhack 0

%if 0%{?rhel} == 5
%global zlibhack 1
%endif

%if 0%{?rhel} == 6
%global zlibhack 1
%endif

# RHEL 6 ppc64 doesn't have icu. Everyone else modern does.

%if %{modern}
%global libicu 1
%else
%global libicu 0
%endif

%if 0%{?rhel} == 6
%ifarch ppc64
%global libicu 0
%endif
%endif

# default to 0.
%global texi2any 0

%if 0%{?fedora} >= 20
%global texi2any 1
%endif

%if 0%{?rhel} >= 7
%global texi2any 1
%endif

%global major_version 4
%global minor_version 0
%global patch_version 5

Name: R
Version: %{major_version}.%{minor_version}.%{patch_version}
Release: 1%{?dist}
Summary: A language for data analysis and graphics
URL: http://www.r-project.org
Source0: https://cran.r-project.org/src/base/R-4/R-%{version}.tar.gz
%if %{texi2any}
# If we have texi2any 5.1+, we can generate the docs on the fly.
# If not, we're building for a very old target (RHEL 6 or older)
%else
# In this case, we need to use pre-built manuals.
# NOTE: These need to be updated for every new version.
Source100: https://cran.r-project.org/doc/manuals/r-release/R-intro.html
Source101: https://cran.r-project.org/doc/manuals/r-release/R-data.html
Source102: https://cran.r-project.org/doc/manuals/r-release/R-admin.html
Source103: https://cran.r-project.org/doc/manuals/r-release/R-exts.html
Source104: https://cran.r-project.org/doc/manuals/r-release/R-lang.html
Source105: https://cran.r-project.org/doc/manuals/r-release/R-ints.html
Source106: https://cran.r-project.org/doc/FAQ/R-FAQ.html
%endif
%if %{zlibhack}
%global zlibv 1.2.11
%global bzipv 1.0.8
%global xzv 5.2.5
%global pcrev 8.44
%global curlv 7.72.0
Source1000: http://zlib.net/zlib-%{zlibv}.tar.gz
Source1001: https://www.sourceware.org/pub/bzip2/bzip2-%{bzipv}.tar.gz
Source1002: http://tukaani.org/xz/xz-%{xzv}.tar.bz2
Source1003: https://ftp.pcre.org/pub/pcre/pcre-%{pcrev}.tar.bz2
Source1004: https://curl.haxx.se/download/curl-%{curlv}.tar.bz2
BuildRequires: make
BuildRequires: glibc-devel
BuildRequires: groff
BuildRequires: krb5-libs
BuildRequires: krb5-devel
BuildRequires: libgssapi-devel
BuildRequires: libidn-devel
BuildRequires: libmetalink-devel
BuildRequires: libssh2-devel
BuildRequires: openldap
BuildRequires: openldap-devel
BuildRequires: openssl-devel
BuildRequires: openssh-clients
BuildRequires: openssh-server
BuildRequires: pkgconfig
BuildRequires: python
BuildRequires: stunnel
%endif
# see https://bugzilla.redhat.com/show_bug.cgi?id=1324145
Patch1: R-3.3.0-fix-java_path-in-javareconf.patch
License: GPLv2+
BuildRequires: gcc-gfortran
BuildRequires: gcc-c++, tex(latex), texinfo-tex
BuildRequires: libpng-devel, libjpeg-devel, readline-devel
BuildRequires: tcl-devel, tk-devel, ncurses-devel
BuildRequires: pcre-devel, zlib-devel
%if 0%{modern}
# Fedora (at least rawhide) pulls this into the buildroot anyways, but lets be explicit for consistency
BuildRequires: pcre2-devel
%endif
%if 0%{?rhel}
 # RHEL older than 6
 %if 0%{?rhel} < 7
 # RHEL 5 used to use curl-devel, but it is now too old.
 #BuildRequires: curl-devel
 # RHEL newer than 6
 %else
BuildRequires: libcurl-devel
 %endif
# Fedora (assuming modern)
%else
BuildRequires: libcurl-devel
%endif
# valgrind is available only on selected arches
%ifarch %{ix86} x86_64 ppc ppc64 ppc64le s390x armv7hl aarch64
BuildRequires: valgrind-devel
%endif
%if %{with_java_headless}
BuildRequires: java-headless
%else
BuildRequires: java
%endif
%if %{system_tre}
BuildRequires: tre-devel
BuildRequires: autoconf, automake, libtool
%endif
%if %{flexiblas}
BuildRequires: flexiblas-devel
%else
%if %{openblas}
BuildRequires: openblas-devel
%endif
%endif

%if %{syslapack}
%if !%{flexiblas}
%if !%{openblas}
BuildRequires: lapack-devel >= 3.5.0-7
BuildRequires: blas-devel >= 3.5.0-7
%endif
%endif
%endif

BuildRequires: libSM-devel, libX11-devel, libICE-devel, libXt-devel
BuildRequires: bzip2-devel, libXmu-devel, cairo-devel, libtiff-devel
BuildRequires: pango-devel, xz-devel
%if %{libicu}
BuildRequires: libicu-devel
%endif
BuildRequires: less
%if 0%{?fedora} >= 18
BuildRequires: tex(inconsolata.sty)
BuildRequires: tex(upquote.sty)
%endif
%if %{use_devtoolset}
BuildRequires: devtoolset-%{dts_version}-toolchain
%endif

# R-devel will pull in R-core
Requires: R-devel = %{version}-%{release}
# libRmath-devel will pull in libRmath
Requires: libRmath-devel = %{version}-%{release}
%if %{modern}
# Pull in Java bits (if you don't want this, use R-core)
Requires: R-java = %{version}-%{release}
%endif

%description
This is a metapackage that provides both core R userspace and
all R development components.

R is a language and environment for statistical computing and graphics.
R is similar to the award-winning S system, which was developed at
Bell Laboratories by John Chambers et al. It provides a wide
variety of statistical and graphical techniques (linear and
nonlinear modelling, statistical tests, time series analysis,
classification, clustering, ...).

R is designed as a true computer language with control-flow
constructions for iteration and alternation, and it allows users to
add additional functionality by defining new functions. For
computationally intensive tasks, C, C++ and Fortran code can be linked
and called at run time.

%package core
Summary: The minimal R components necessary for a functional runtime
Requires: xdg-utils
# Bugzilla 1875165
Recommends: cups
# R inherits the compiler flags it was built with, hence we need this on hardened systems
%if 0%{hardening}
Requires: redhat-rpm-config
%endif
%if %{modern}
Requires: tex(dvips), vi
%else
Requires: vim-minimal
%endif
%if 0%{?fedora}
Requires: perl-interpreter
%else
Requires: perl
%endif
Requires: sed, gawk, tex(latex), less, make, unzip
# Make sure we bring the new libRmath with us
Requires: libRmath%{?_isa} = %{version}-%{release}

%if !%{syslapack}
%if !%{flexiblas}
%if %{openblas}
Requires: openblas-Rblas
%endif
%endif
%endif

%if %{use_devtoolset}
# We need it for CXX11 and higher support.
Requires: devtoolset-%{dts_version}-toolchain
%endif

# This is our ABI provides to prevent mismatched installs.
# R packages should autogenerate a Requires: R(ABI) based on the R they were built against.
Provides: R(ABI) = %{major_version}.%{minor_version}

# These are the submodules that R-core provides. Sometimes R modules say they
# depend on one of these submodules rather than just R. These are provided for
# packager convenience.
%define add_submodule() %{lua:
  local name = rpm.expand("%1")
  local version = rpm.expand("%2")
  local rpm_version = string.gsub(version, "-", ".")
  print("Provides: R-" .. name .. " = " .. rpm_version .. "\\n")
  print("Provides: R(" .. name .. ") = " .. rpm_version)
}
%add_submodule base %{version}
%add_submodule boot 1.3-27
%add_submodule class 7.3-18
%add_submodule cluster 2.1.1
%add_submodule codetools 0.2-18
%add_submodule compiler %{version}
%add_submodule datasets %{version}
%add_submodule foreign 0.8-81
%add_submodule graphics %{version}
%add_submodule grDevices %{version}
%add_submodule grid %{version}
%add_submodule KernSmooth 2.23-18
%add_submodule lattice 0.20-41
%add_submodule MASS 7.3-53.1
%add_submodule Matrix 1.3-2
Obsoletes: R-Matrix < 0.999375-7
%add_submodule methods %{version}
%add_submodule mgcv 1.8-34
%add_submodule nlme 3.1-152
%add_submodule nnet 7.3-15
%add_submodule parallel %{version}
%add_submodule rpart 4.1-15
%add_submodule spatial 7.3-13
%add_submodule splines %{version}
%add_submodule stats %{version}
%add_submodule stats4 %{version}
%add_submodule survival 3.2-10
%add_submodule tcltk %{version}
%add_submodule tools %{version}
%add_submodule translations %{version}
%add_submodule utils %{version}

%description core
A language and environment for statistical computing and graphics.
R is similar to the award-winning S system, which was developed at
Bell Laboratories by John Chambers et al. It provides a wide
variety of statistical and graphical techniques (linear and
nonlinear modelling, statistical tests, time series analysis,
classification, clustering, ...).

R is designed as a true computer language with control-flow
constructions for iteration and alternation, and it allows users to
add additional functionality by defining new functions. For
computationally intensive tasks, C, C++ and Fortran code can be linked
and called at run time.

%package core-devel
Summary: Core files for development of R packages (no Java)
Requires: R-core = %{version}-%{release}
# You need all the BuildRequires for the development version
Requires: gcc-c++, gcc-gfortran, tex(latex), texinfo-tex
Requires: bzip2-devel, libX11-devel, zlib-devel
Requires: tcl-devel, tk-devel, pkgconfig, xz-devel
# This may go away at some point, possibly R 3.6?
Requires: pcre-devel
%if 0%{modern}
# Configure picks this up, but despite linking to it, it does not seem to be used as of R 3.5.2.
Requires: pcre2-devel
%endif
%if %{syslapack}
%if %{flexiblas}
Requires: flexiblas-devel
%else
%if %{openblas}
Requires: openblas-devel
%endif
%endif
%endif
%if %{modern}
Requires: libicu-devel
%endif
%if %{system_tre}
Requires: tre-devel
%endif
# TeX files needed
%if 0%{?fedora} >= 18
Requires: tex(ecrm1000.tfm)
Requires: tex(inconsolata.sty)
Requires: tex(ptmr8t.tfm)
Requires: tex(ptmb8t.tfm)
Requires: tex(pcrr8t.tfm)
Requires: tex(phvr8t.tfm)
Requires: tex(ptmri8t.tfm)
Requires: tex(ptmro8t.tfm)
Requires: tex(cm-super-ts1.enc)
%endif
# "‘qpdf’ is needed for checks on size reduction of PDFs"
# qpdf is not in epel, and since 99% of R doesn't use it, we'll let it slide.
%if 0%{?fedora}
Requires: qpdf
%endif

Provides: R-Matrix-devel = 1.3.2
Obsoletes: R-Matrix-devel < 0.999375-7

%if %{modern}
%description core-devel
Install R-core-devel if you are going to develop or compile R packages.
This package does not configure the R environment for Java, install
R-java-devel if you want this.
%else
%description core-devel
Install R-core-devel if you are going to develop or compile R packages.
%endif

%package devel
Summary: Full R development environment metapackage
%if %{usemacros}
Requires: R-rpm-macros
%endif
Requires: R-core-devel = %{version}-%{release}
%if %{modern}
Requires: R-java-devel = %{version}-%{release}
%else
%endif

%description devel
This is a metapackage to install a complete (with Java) R development
environment.

%if %{modern}
%package java
Summary: R with Fedora provided Java Runtime Environment
Requires(post): R-core = %{version}-%{release}
%if %{with_java_headless}
Requires: java-headless
%else
Requires: java
%endif

%description java
A language and environment for statistical computing and graphics.
R is similar to the award-winning S system, which was developed at
Bell Laboratories by John Chambers et al. It provides a wide
variety of statistical and graphical techniques (linear and
nonlinear modelling, statistical tests, time series analysis,
classification, clustering, ...).

R is designed as a true computer language with control-flow
constructions for iteration and alternation, and it allows users to
add additional functionality by defining new functions. For
computationally intensive tasks, C, C++ and Fortran code can be linked
and called at run time.

This package also has an additional dependency on java, as provided by
Fedora's openJDK.

%package java-devel
Summary: Development package for use with Java enabled R components
Requires(post): R-core-devel = %{version}-%{release}
Requires(post): java-devel

%description java-devel
Install R-java-devel if you are going to develop or compile R packages
that assume java is present and configured on the system.
%endif

%package -n libRmath
Summary: Standalone math library from the R project

%description -n libRmath
A standalone library of mathematical and statistical functions derived
from the R project.  This package provides the shared libRmath library.

%package -n libRmath-devel
Summary: Headers from the R Standalone math library
Requires: libRmath = %{version}-%{release}, pkgconfig

%description -n libRmath-devel
A standalone library of mathematical and statistical functions derived
from the R project.  This package provides the libRmath header files.

%package -n libRmath-static
Summary: Static R Standalone math library
Requires: libRmath-devel = %{version}-%{release}

%description -n libRmath-static
A standalone library of mathematical and statistical functions derived
from the R project.  This package provides the static libRmath library.

%prep
%if %{zlibhack}
%setup -q -n %{name}-%{version} -a 1000 -a 1001 -a 1002 -a 1003 -a 1004
%else
%setup -q -n %{name}-%{version}
%endif
%patch1 -p1 -b .fixpath

# Filter false positive provides.
cat <<EOF > %{name}-prov
#!/bin/sh
%{__perl_provides} \
| grep -v 'File::Copy::Recursive' | grep -v 'Text::DelimMatch'
EOF

%global __perl_provides %{_builddir}/R-%{version}/%{name}-prov
chmod +x %{__perl_provides}

# Filter unwanted Requires:
cat << \EOF > %{name}-req
#!/bin/sh
%{__perl_requires} \
| grep -v 'perl(Text::DelimMatch)'
EOF
%global __perl_requires %{_builddir}/R-%{version}/%{name}-req
chmod +x %{__perl_requires}

%build
# If you're seeing this, I'm sorry. This is ugly.
# But short of updating RHEL 5/6 (which isn't happening), this is the best worst way to keep R working.
%if %{zlibhack}
pushd zlib-%{zlibv}
./configure --libdir=%{_libdir} --includedir=%{_includedir} --prefix=%{_prefix} --static
make %{?_smp_mflags} CFLAGS='%{optflags} -fpic -fPIC'
mkdir -p target
make DESTDIR=./target install
popd
pushd bzip2-%{bzipv}
make %{?_smp_mflags} libbz2.a CC="%{__cc}" AR="%{__ar}" RANLIB="%{__ranlib}" CFLAGS="$RPM_OPT_FLAGS -D_FILE_OFFSET_BITS=64 -fpic -fPIC" LDFLAGS="%{__global_ldflags}"
mkdir -p target%{_libdir}
mkdir -p target%{_includedir}
cp -p bzlib.h target%{_includedir}
install -m 644 libbz2.a target%{_libdir}
popd
pushd xz-%{xzv}
CFLAGS="%{optflags} -fpic -fPIC" %configure --enable-static=yes --enable-shared=no
make %{?_smp_mflags}
mkdir -p target
make DESTDIR=%{_builddir}/%{name}-%{version}/xz-%{xzv}/target install
popd
pushd pcre-%{pcrev}
CFLAGS="%{optflags} -fpic -fPIC" %configure --enable-static=yes --enable-shared=no --enable-utf --enable-unicode-properties --enable-pcre8 --enable-pcre16 --enable-pcre32
make %{?_smp_mflags}
mkdir -p target
make DESTDIR=%{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target install
popd
pushd curl-%{curlv}
CFLAGS="%{optflags} -fpic -fPIC" %configure --enable-static=yes --enable-shared=no --with-ssl --enable-ipv6 --with-ca-bundle=%{_sysconfdir}/pki/tls/certs/ca-bundle.crt --with-gssapi --with-libidn --enable-ldaps --with-libssh2 --enable-threaded-resolver --with-libmetalink
make %{?_smp_mflags} V=1
mkdir -p target
make DESTDIR=%{_builddir}/%{name}-%{version}/curl-%{curlv}/target INSTALL="install -p" install
popd
%endif

%if %{use_devtoolset}
. /opt/rh/devtoolset-%{dts_version}/enable
%endif

# Add PATHS to Renviron for R_LIBS_SITE
echo 'R_LIBS_SITE=${R_LIBS_SITE-'"'/usr/local/lib/R/site-library:/usr/local/lib/R/library:%{_libdir}/R/library:%{_datadir}/R/library'"'}' >> etc/Renviron.in
# No inconsolata on RHEL tex
%if 0%{?rhel}
export R_RD4PDF="times,hyper"
sed -i 's|inconsolata,||g' etc/Renviron.in
%endif
export R_PDFVIEWER="%{_bindir}/xdg-open"
export R_PRINTCMD="lpr"
export R_BROWSER="%{_bindir}/xdg-open"

case "%{_target_cpu}" in
      x86_64|mips64|ppc64|powerpc64|sparc64|s390x|powerpc64le|ppc64le)
          export CC="gcc -m64"
          export CXX="g++ -m64"
          export F77="gfortran -m64"
          export FC="gfortran -m64"
      ;;
      ia64|alpha|arm*|aarch64|sh*|riscv*)
          export CC="gcc"
          export CXX="g++"
          export F77="gfortran"
          export FC="gfortran"
      ;;
      s390)
          export CC="gcc -m31"
          export CXX="g++ -m31"
          export F77="gfortran -m31"
          export FC="gfortran -m31"
      ;;
      *)
          export CC="gcc -m32"
          export CXX="g++ -m32"
          export F77="gfortran -m32"
          export FC="gfortran -m32"
      ;;
esac

%if 0%{?zlibhack}
export CFLAGS="%{optflags} -fpic -fPIC -I%{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_includedir}"
# export LDFLAGS="-L%{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_libdir}/ -L%{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_libdir}/ -L%{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_libdir}/ -L%{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_libdir}/ -L%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/"
export CURL_CFLAGS='-DCURL_STATICLIB -I%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_includedir}'
export CURL_LIBS=`%{_builddir}/%{name}-%{version}/curl-%{curlv}/target/usr/bin/curl-config --libs`
export LDFLAGS="-ldl -lpthread -lc -lrt -Wl,--as-needed -Wl,--whole-archive %{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_libdir}/libz.a %{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_libdir}/libbz2.a %{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_libdir}/liblzma.a %{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_libdir}/libpcre.a %{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/libcurl.a -Wl,--no-whole-archive -L%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/ $CURL_LIBS"
%endif

%if 0%{?fedora} >= 21
%if %{with_lto}
# With gcc 4.9, if we don't pass -ffat-lto-objects along with -flto, Matrix builds without the needed object code
# ... and doesn't work at all as a result.
export CFLAGS="%{optflags} -ffat-lto-objects"
export CXXFLAGS="%{optflags} -ffat-lto-objects"
export FCFLAGS="%{optflags} -ffat-lto-objects"
%endif
%else
export FCFLAGS="%{optflags}"
%endif

%if 0%{?fedora} >= 30
# gcc9 needs us to pass --no-optimize-sibling-calls to gfortran
export FCFLAGS="%{optflags} --no-optimize-sibling-calls"
export FFLAGS="%{optflags} --no-optimize-sibling-calls"
%endif

# RHEL 5 & 6 & 7 have a broken BLAS, so we need to use the bundled bits in R until
# they are fixed... and it doesn't look like it will ever be fixed in RHEL 5.
# https://bugzilla.redhat.com/show_bug.cgi?id=1117491
# https://bugzilla.redhat.com/show_bug.cgi?id=1117496
# https://bugzilla.redhat.com/show_bug.cgi?id=1117497
#
# On old RHEL, we use --enable-BLAS-shlib here. It generates a shared library
# of the R bundled blas, that can be replaced by an optimized version.
# It also results in R using the bundled lapack copy.

%if %{flexiblas}
# avoid this check
sed -i '/"checking whether the BLAS is complete/i r_cv_complete_blas=yes' configure
%endif

( %configure \
%if 0%{?rhel} && 0%{?rhel} <= 5
    --with-readline=no \
%endif
%if %{system_tre}
    --with-system-tre \
%endif
    --with-system-valgrind-headers \
%if %{syslapack}
    --with-lapack \
%if %{flexiblas}
    --with-blas="flexiblas" \
%else
    --with-blas \
%endif
%else
    --enable-BLAS-shlib \
%endif
    --with-tcl-config=%{_libdir}/tclConfig.sh \
    --with-tk-config=%{_libdir}/tkConfig.sh \
    --enable-R-shlib \
    --enable-prebuilt-html \
    --enable-R-profiling \
    --enable-memory-profiling \
%if %{with_lto}
%ifnarch %{arm}
    --enable-lto \
%endif
%endif
%if %{texi2any}
    MAKEINFO=texi2any \
%else
    MAKEINFO=makeinfo \
%endif
    rdocdir=%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}} \
    rincludedir=%{_includedir}/R \
    rsharedir=%{_datadir}/R) | tee CONFIGURE.log
cat CONFIGURE.log | grep -A30 'R is now' - > CAPABILITIES
%if 0%{?zlibhack}
make V=1 CURL_CPPFLAGS='-DCURL_STATICLIB -I%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_includedir}' CURL_LIBS=`%{_builddir}/%{name}-%{version}/curl-%{curlv}/target/usr/bin/curl-config --libs`
%else
make V=1
%endif
(cd src/nmath/standalone; make)
#make check-all
make pdf
%if 0%{?fedora} >= 19
# What a hack.
# Current texinfo doesn't like @eqn. Use @math instead where stuff breaks.
cp doc/manual/R-exts.texi doc/manual/R-exts.texi.spot
cp doc/manual/R-intro.texi doc/manual/R-intro.texi.spot
sed -i 's|@eqn|@math|g' doc/manual/R-exts.texi
sed -i 's|@eqn|@math|g' doc/manual/R-intro.texi
%endif
%if %{texi2any}
    make MAKEINFO=texi2any info
%else
# Well, this used to work, but now rhel 6 is too old and buggy.
# make MAKEINFO=makeinfo info
%endif

%if %{texi2any}
# Convert to UTF-8
for i in doc/manual/R-intro.info doc/manual/R-FAQ.info doc/FAQ doc/manual/R-admin.info doc/manual/R-exts.info-1; do
  iconv -f iso-8859-1 -t utf-8 -o $i{.utf8,}
  mv $i{.utf8,}
done
%endif

%install
%if %{texi2any}
make DESTDIR=${RPM_BUILD_ROOT} install install-info
%else
make DESTDIR=${RPM_BUILD_ROOT} install
%endif
# And now, undo the hack. :P
%if 0%{?fedora} >= 19
mv doc/manual/R-exts.texi.spot doc/manual/R-exts.texi
mv doc/manual/R-intro.texi.spot doc/manual/R-intro.texi
%endif
%if 0%{?zlibhack}
# Ugh. Old ancient broken. Barf barf barf.
%else
make DESTDIR=${RPM_BUILD_ROOT} install-pdf
%endif

rm -f ${RPM_BUILD_ROOT}%{_infodir}/dir
rm -f ${RPM_BUILD_ROOT}%{_infodir}/dir.old
mkdir -p ${RPM_BUILD_ROOT}%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}
install -p CAPABILITIES ${RPM_BUILD_ROOT}%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}

#Install libRmath files
(cd src/nmath/standalone; make install DESTDIR=${RPM_BUILD_ROOT})

mkdir -p $RPM_BUILD_ROOT/etc/ld.so.conf.d
echo "%{_libdir}/R/lib" > $RPM_BUILD_ROOT/etc/ld.so.conf.d/%{name}-%{_arch}.conf

mkdir -p $RPM_BUILD_ROOT%{_datadir}/R/library

# Fix multilib
touch -r README ${RPM_BUILD_ROOT}%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}/CAPABILITIES
touch -r README doc/manual/*.pdf
touch -r README $RPM_BUILD_ROOT%{_bindir}/R

# Fix html/packages.html
# We can safely use RHOME here, because all of these are system packages.
sed -i 's|\..\/\..|%{_libdir}/R|g' $RPM_BUILD_ROOT%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}/html/packages.html

for i in $RPM_BUILD_ROOT%{_libdir}/R/library/*/html/*.html; do
  sed -i 's|\..\/\..\/..\/doc|%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}|g' $i
done

# Fix exec bits
chmod +x $RPM_BUILD_ROOT%{_datadir}/R/sh/echo.sh
chmod +x $RPM_BUILD_ROOT%{_libdir}/R/bin/*
chmod -x $RPM_BUILD_ROOT%{_libdir}/R/library/mgcv/CITATION ${RPM_BUILD_ROOT}%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}/CAPABILITIES


# Symbolic link for convenience
if [ ! -d "$RPM_BUILD_ROOT%{_libdir}/R/include" ]; then
	pushd $RPM_BUILD_ROOT%{_libdir}/R
	ln -s ../../include/R include
	popd
fi

# Symbolic link for LaTeX
if [ ! -d "$RPM_BUILD_ROOT%{_datadir}/texmf/tex/latex/R" ]; then
	mkdir -p $RPM_BUILD_ROOT%{_datadir}/texmf/tex/latex
	pushd $RPM_BUILD_ROOT%{_datadir}/texmf/tex/latex
	ln -s %{_datadir}/R/texmf/tex/latex R
	popd
fi

%if %{texi2any}
# Do not need to copy files...
%else
# COPY THAT FLOPPY
cp -a %{SOURCE100} %{SOURCE101} %{SOURCE102} %{SOURCE103} %{SOURCE104} %{SOURCE105} %{SOURCE106} %{buildroot}%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}/manual/
%endif

%if 0%{?zlibhack}
# Clean our shameful shame out of the files.
sed -i 's|-Wl,--whole-archive %{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_libdir}/libz.a %{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_libdir}/libbz2.a %{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_libdir}/liblzma.a %{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_libdir}/libpcre.a %{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/libcurl.a -Wl,--no-whole-archive -L%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/||g' %{buildroot}%{_libdir}/R/etc/Makeconf
sed -i 's|-Wl,--whole-archive %{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_libdir}/libz.a %{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_libdir}/libbz2.a %{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_libdir}/liblzma.a %{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_libdir}/libpcre.a %{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/libcurl.a -Wl,--no-whole-archive -L%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_libdir}/||g' %{buildroot}%{_libdir}/pkgconfig/libR.pc
sed -i 's|-ldl -lpthread .* -lldap -lz -lrt||g' %{buildroot}%{_libdir}/R/etc/Makeconf
sed -i 's|-ldl -lpthread .* -lldap -lz -lrt||g' %{buildroot}%{_libdir}/pkgconfig/libR.pc
sed -i 's|-I%{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_includedir}||g' %{buildroot}%{_libdir}/R/etc/Makeconf
sed -i 's|-I%{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_includedir}||g' %{buildroot}%{_libdir}/R/bin/libtool
sed -i 's|-I%{_builddir}/%{name}-%{version}/zlib-%{zlibv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/bzip2-%{bzipv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/xz-%{xzv}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/pcre-%{pcrev}/target%{_includedir} -I%{_builddir}/%{name}-%{version}/curl-%{curlv}/target%{_includedir}||g' ${RPM_BUILD_ROOT}%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}/CAPABILITIES
#el6 FLIBS
sed -i 's|-ldl -lpthread .* -lldap -lz||g' %{buildroot}%{_libdir}/R/etc/Makeconf
#el5 FLIBS
sed -i 's|-ldl -lpthread .* -lldap||g' %{buildroot}%{_libdir}/R/etc/Makeconf
# ldpaths
sed -i 's|:/builddir/build/BUILD/R-%{version}/curl-%{curlv}/target%{_libdir}/:/builddir/build/BUILD/R-%{version}/curl-%{curlv}/target%{_libdir}||g' %{buildroot}%{_libdir}/R/etc/ldpaths
sed -i 's|/builddir/build/BUILD/R-%{version}/curl-%{curlv}/target%{_libdir}/:/builddir/build/BUILD/R-%{version}/curl-%{curlv}/target%{_libdir}||g' %{buildroot}%{_libdir}/R/etc/ldpaths
%endif

%if !%{syslapack}
%if !%{flexiblas}
%if %{openblas}
# Rename the R blas so.
mv %{buildroot}%{_libdir}/R/lib/libRblas.so %{buildroot}%{_libdir}/R/lib/libRrefblas.so
%endif
%endif
%endif

# okay, look. its very clear that upstream does not run the test suite on any non-intel architectures.
%check
%if 0%{?zlibhack}
# Most of these tests pass. Some don't. All pieces belong to you.
%else
%ifnarch ppc64 ppc64le armv7hl s390x aarch64
# Needed by tests/ok-error.R, which will smash the stack on PPC64. This is the purpose of the test.
ulimit -s 16384
TZ="Europe/Paris" make check
%endif
%endif

%post core
/sbin/ldconfig
%if %{runjavareconf}
R CMD javareconf \
    JAVA_HOME=%{_jvmdir}/jre \
    JAVA_CPPFLAGS='-I%{_jvmdir}/java/include\ -I%{_jvmdir}/java/include/linux' \
    JAVA_LIBS='-L%{_jvmdir}/jre/lib/%{java_arch}/server \
    -L%{_jvmdir}/jre/lib/%{java_arch}\ -L%{_jvmdir}/java/lib/%{java_arch}\ -L%{_jvmdir}/jre/lib/server \
    -L/usr/java/packages/lib/%{java_arch}\ -L/lib\ -L/usr/lib\ -ljvm' \
    JAVA_LD_LIBRARY_PATH=%{_jvmdir}/jre/lib/%{java_arch}/server:%{_jvmdir}/jre/lib/%{java_arch}:%{_jvmdir}/java/lib/%{java_arch}:%{_jvmdir}/jre/lib/server:/usr/java/packages/lib/%{java_arch}:/lib:/usr/lib \
    > /dev/null 2>&1 || exit 0
%endif

# With 2.10.0, we no longer need to do any of this.

# Update package indices
# %__cat %{_libdir}/R/library/*/CONTENTS > %{_docdir}/R-%{version}/html/search/index.txt 2>/dev/null
# Don't use .. based paths, substitute RHOME
# sed -i "s!../../..!%{_libdir}/R!g" %{_docdir}/R-%{version}/html/search/index.txt

# This could fail if there are no noarch R libraries on the system.
# %__cat %{_datadir}/R/library/*/CONTENTS >> %{_docdir}/R-%{version}/html/search/index.txt 2>/dev/null || exit 0
# Don't use .. based paths, substitute /usr/share/R
# sed -i "s!../../..!/usr/share/R!g" %{_docdir}/R-%{version}/html/search/index.txt

%postun core
/sbin/ldconfig
if [ $1 -eq 0 ] ; then
    /usr/bin/mktexlsr %{_datadir}/texmf &>/dev/null || :
fi

%posttrans core
/usr/bin/mktexlsr %{_datadir}/texmf &>/dev/null || :

%if %{modern}
%post java
%if %{runjavareconf}
R CMD javareconf \
    JAVA_HOME=%{_jvmdir}/jre \
    JAVA_CPPFLAGS='-I%{_jvmdir}/java/include\ -I%{_jvmdir}/java/include/linux' \
    JAVA_LIBS='-L%{_jvmdir}/jre/lib/%{java_arch}/server \
    -L%{_jvmdir}/jre/lib/%{java_arch}\ -L%{_jvmdir}/java/lib/%{java_arch}\ -L%{_jvmdir}/jre/lib/server \
    -L/usr/java/packages/lib/%{java_arch}\ -L/lib\ -L/usr/lib\ -ljvm' \
    JAVA_LD_LIBRARY_PATH=%{_jvmdir}/jre/lib/%{java_arch}/server:%{_jvmdir}/jre/lib/%{java_arch}:%{_jvmdir}/java/lib/%{java_arch}:%{_jvmdir}/jre/lib/server:/usr/java/packages/lib/%{java_arch}:/lib:/usr/lib \
    > /dev/null 2>&1 || exit 0
%endif

%post java-devel
%if %{runjavareconf}
R CMD javareconf \
    JAVA_HOME=%{_jvmdir}/jre \
    JAVA_CPPFLAGS='-I%{_jvmdir}/java/include\ -I%{_jvmdir}/java/include/linux' \
    JAVA_LIBS='-L%{_jvmdir}/jre/lib/%{java_arch}/server \
    -L%{_jvmdir}/jre/lib/%{java_arch}\ -L%{_jvmdir}/java/lib/%{java_arch}\ -L%{_jvmdir}/jre/lib/server \
    -L/usr/java/packages/lib/%{java_arch}\ -L/lib\ -L/usr/lib\ -ljvm' \
    JAVA_LD_LIBRARY_PATH=%{_jvmdir}/jre/lib/%{java_arch}/server:%{_jvmdir}/jre/lib/%{java_arch}:%{_jvmdir}/java/lib/%{java_arch}:%{_jvmdir}/jre/lib/server:/usr/java/packages/lib/%{java_arch}:/lib:/usr/lib \
    > /dev/null 2>&1 || exit 0
%endif
%endif

%ldconfig_scriptlets -n libRmath

%files
# Metapackage

%files core
%{_bindir}/R
%{_bindir}/Rscript
%{_datadir}/R/
%{_datadir}/texmf/tex/latex/R
# Have to break this out for the translations
%dir %{_libdir}/R/
%{_libdir}/R/bin/
%dir %{_libdir}/R/etc
%config %{_libdir}/R/etc/Makeconf
%config(noreplace) %{_libdir}/R/etc/Renviron
%config(noreplace) %{_libdir}/R/etc/javaconf
%config(noreplace) %{_libdir}/R/etc/ldpaths
%config(noreplace) %{_libdir}/R/etc/repositories
%{_libdir}/R/lib/
%dir %{_libdir}/R/library/
%dir %{_libdir}/R/library/translations/
%{_libdir}/R/library/translations/DESCRIPTION
%lang(da) %{_libdir}/R/library/translations/da/
%lang(de) %{_libdir}/R/library/translations/de/
%lang(en) %{_libdir}/R/library/translations/en*/
%lang(es) %{_libdir}/R/library/translations/es/
%lang(fa) %{_libdir}/R/library/translations/fa/
%lang(fr) %{_libdir}/R/library/translations/fr/
%lang(it) %{_libdir}/R/library/translations/it/
%lang(ja) %{_libdir}/R/library/translations/ja/
%lang(ko) %{_libdir}/R/library/translations/ko/
%lang(nn) %{_libdir}/R/library/translations/nn/
%lang(pl) %{_libdir}/R/library/translations/pl/
%lang(pt) %{_libdir}/R/library/translations/pt*/
%lang(ru) %{_libdir}/R/library/translations/ru/
%lang(tr) %{_libdir}/R/library/translations/tr/
%lang(zh) %{_libdir}/R/library/translations/zh*/
# base
%{_libdir}/R/library/base/
# boot
%dir %{_libdir}/R/library/boot/
%{_libdir}/R/library/boot/bd.q
%{_libdir}/R/library/boot/CITATION
%{_libdir}/R/library/boot/data/
%{_libdir}/R/library/boot/DESCRIPTION
%{_libdir}/R/library/boot/help/
%{_libdir}/R/library/boot/html/
%{_libdir}/R/library/boot/INDEX
%{_libdir}/R/library/boot/Meta/
%{_libdir}/R/library/boot/NAMESPACE
%dir %{_libdir}/R/library/boot/po/
%lang(de) %{_libdir}/R/library/boot/po/de/
%lang(en) %{_libdir}/R/library/boot/po/en*/
%lang(fr) %{_libdir}/R/library/boot/po/fr/
%lang(it) %{_libdir}/R/library/boot/po/it/
%lang(ko) %{_libdir}/R/library/boot/po/ko/
%lang(pl) %{_libdir}/R/library/boot/po/pl/
%lang(ru) %{_libdir}/R/library/boot/po/ru/
%{_libdir}/R/library/boot/R/
# class
%dir %{_libdir}/R/library/class/
%{_libdir}/R/library/class/CITATION
%{_libdir}/R/library/class/DESCRIPTION
%{_libdir}/R/library/class/help/
%{_libdir}/R/library/class/html/
%{_libdir}/R/library/class/INDEX
%{_libdir}/R/library/class/libs/
%{_libdir}/R/library/class/Meta/
%{_libdir}/R/library/class/NAMESPACE
%{_libdir}/R/library/class/NEWS
%dir %{_libdir}/R/library/class/po/
%lang(de) %{_libdir}/R/library/class/po/de/
%lang(en) %{_libdir}/R/library/class/po/en*/
%lang(fr) %{_libdir}/R/library/class/po/fr/
%lang(it) %{_libdir}/R/library/class/po/it/
%lang(ko) %{_libdir}/R/library/class/po/ko/
%lang(pl) %{_libdir}/R/library/class/po/pl/
%{_libdir}/R/library/class/R/
# cluster
%dir %{_libdir}/R/library/cluster/
%{_libdir}/R/library/cluster/CITATION
%{_libdir}/R/library/cluster/data/
%{_libdir}/R/library/cluster/DESCRIPTION
%{_libdir}/R/library/cluster/help/
%{_libdir}/R/library/cluster/html/
%{_libdir}/R/library/cluster/INDEX
%{_libdir}/R/library/cluster/libs/
%{_libdir}/R/library/cluster/Meta/
%{_libdir}/R/library/cluster/NAMESPACE
%{_libdir}/R/library/cluster/NEWS.Rd
%{_libdir}/R/library/cluster/R/
%{_libdir}/R/library/cluster/test-tools.R
%dir %{_libdir}/R/library/cluster/po/
%lang(de) %{_libdir}/R/library/cluster/po/de/
%lang(en) %{_libdir}/R/library/cluster/po/en*/
%lang(fr) %{_libdir}/R/library/cluster/po/fr/
%lang(it) %{_libdir}/R/library/cluster/po/it/
%lang(ko) %{_libdir}/R/library/cluster/po/ko/
%lang(pl) %{_libdir}/R/library/cluster/po/pl/
# codetools
%dir %{_libdir}/R/library/codetools/
%{_libdir}/R/library/codetools/DESCRIPTION
%{_libdir}/R/library/codetools/help/
%{_libdir}/R/library/codetools/html/
%{_libdir}/R/library/codetools/INDEX
%{_libdir}/R/library/codetools/Meta/
%{_libdir}/R/library/codetools/NAMESPACE
%{_libdir}/R/library/codetools/R/
# compiler
%{_libdir}/R/library/compiler/
# datasets
%{_libdir}/R/library/datasets/
# foreign
%dir %{_libdir}/R/library/foreign/
%{_libdir}/R/library/foreign/COPYRIGHTS
%{_libdir}/R/library/foreign/DESCRIPTION
%{_libdir}/R/library/foreign/files/
%{_libdir}/R/library/foreign/help/
%{_libdir}/R/library/foreign/html/
%{_libdir}/R/library/foreign/INDEX
%{_libdir}/R/library/foreign/libs/
%{_libdir}/R/library/foreign/Meta/
%{_libdir}/R/library/foreign/NAMESPACE
%dir %{_libdir}/R/library/foreign/po/
%lang(de) %{_libdir}/R/library/foreign/po/de/
%lang(en) %{_libdir}/R/library/foreign/po/en*/
%lang(fr) %{_libdir}/R/library/foreign/po/fr/
%lang(it) %{_libdir}/R/library/foreign/po/it/
%lang(pl) %{_libdir}/R/library/foreign/po/pl/
%{_libdir}/R/library/foreign/R/
# graphics
%{_libdir}/R/library/graphics/
# grDevices
%{_libdir}/R/library/grDevices
# grid
%{_libdir}/R/library/grid/
# KernSmooth
%dir %{_libdir}/R/library/KernSmooth/
%{_libdir}/R/library/KernSmooth/DESCRIPTION
%{_libdir}/R/library/KernSmooth/help/
%{_libdir}/R/library/KernSmooth/html/
%{_libdir}/R/library/KernSmooth/INDEX
%{_libdir}/R/library/KernSmooth/libs/
%{_libdir}/R/library/KernSmooth/Meta/
%{_libdir}/R/library/KernSmooth/NAMESPACE
%dir %{_libdir}/R/library/KernSmooth/po/
%lang(de) %{_libdir}/R/library/KernSmooth/po/de/
%lang(en) %{_libdir}/R/library/KernSmooth/po/en*/
%lang(fr) %{_libdir}/R/library/KernSmooth/po/fr/
%lang(it) %{_libdir}/R/library/KernSmooth/po/it/
%lang(ko) %{_libdir}/R/library/KernSmooth/po/ko/
%lang(pl) %{_libdir}/R/library/KernSmooth/po/pl/
%{_libdir}/R/library/KernSmooth/R/
# lattice
%dir %{_libdir}/R/library/lattice/
%{_libdir}/R/library/lattice/CITATION
%{_libdir}/R/library/lattice/data/
%{_libdir}/R/library/lattice/demo/
%{_libdir}/R/library/lattice/DESCRIPTION
%{_libdir}/R/library/lattice/help/
%{_libdir}/R/library/lattice/html/
%{_libdir}/R/library/lattice/INDEX
%{_libdir}/R/library/lattice/libs/
%{_libdir}/R/library/lattice/Meta/
%{_libdir}/R/library/lattice/NAMESPACE
%{_libdir}/R/library/lattice/NEWS
%dir %{_libdir}/R/library/lattice/po/
%lang(de) %{_libdir}/R/library/lattice/po/de/
%lang(en) %{_libdir}/R/library/lattice/po/en*/
%lang(fr) %{_libdir}/R/library/lattice/po/fr/
%lang(ko) %{_libdir}/R/library/lattice/po/ko/
%lang(pl) %{_libdir}/R/library/lattice/po/pl*/
%{_libdir}/R/library/lattice/R/
# MASS
%dir %{_libdir}/R/library/MASS/
%{_libdir}/R/library/MASS/CITATION
%{_libdir}/R/library/MASS/data/
%{_libdir}/R/library/MASS/DESCRIPTION
%{_libdir}/R/library/MASS/help/
%{_libdir}/R/library/MASS/html/
%{_libdir}/R/library/MASS/INDEX
%{_libdir}/R/library/MASS/libs/
%{_libdir}/R/library/MASS/Meta/
%{_libdir}/R/library/MASS/NAMESPACE
%{_libdir}/R/library/MASS/NEWS
%dir %{_libdir}/R/library/MASS/po
%lang(de) %{_libdir}/R/library/MASS/po/de/
%lang(en) %{_libdir}/R/library/MASS/po/en*/
%lang(fr) %{_libdir}/R/library/MASS/po/fr/
%lang(it) %{_libdir}/R/library/MASS/po/it/
%lang(ko) %{_libdir}/R/library/MASS/po/ko/
%lang(pl) %{_libdir}/R/library/MASS/po/pl/
%{_libdir}/R/library/MASS/R/
%{_libdir}/R/library/MASS/scripts/
# Matrix
%dir %{_libdir}/R/library/Matrix/
%{_libdir}/R/library/Matrix/Copyrights
%{_libdir}/R/library/Matrix/data/
%{_libdir}/R/library/Matrix/doc/
%{_libdir}/R/library/Matrix/DESCRIPTION
%{_libdir}/R/library/Matrix/Doxyfile
%{_libdir}/R/library/Matrix/external/
%{_libdir}/R/library/Matrix/help/
%{_libdir}/R/library/Matrix/html/
%{_libdir}/R/library/Matrix/include/
%{_libdir}/R/library/Matrix/INDEX
%{_libdir}/R/library/Matrix/libs/
%{_libdir}/R/library/Matrix/LICENCE
%{_libdir}/R/library/Matrix/Meta/
%{_libdir}/R/library/Matrix/NAMESPACE
%{_libdir}/R/library/Matrix/NEWS.Rd
%dir %{_libdir}/R/library/Matrix/po/
%lang(de) %{_libdir}/R/library/Matrix/po/de/
%lang(en) %{_libdir}/R/library/Matrix/po/en*/
%lang(fr) %{_libdir}/R/library/Matrix/po/fr/
%lang(ko) %{_libdir}/R/library/Matrix/po/ko/
%lang(pl) %{_libdir}/R/library/Matrix/po/pl/
%{_libdir}/R/library/Matrix/R/
%{_libdir}/R/library/Matrix/test-tools.R
%{_libdir}/R/library/Matrix/test-tools-1.R
%{_libdir}/R/library/Matrix/test-tools-Matrix.R
# methods
%{_libdir}/R/library/methods/
# mgcv
%{_libdir}/R/library/mgcv/
# nlme
%dir %{_libdir}/R/library/nlme/
%{_libdir}/R/library/nlme/CITATION
%{_libdir}/R/library/nlme/data/
%{_libdir}/R/library/nlme/DESCRIPTION
%{_libdir}/R/library/nlme/help/
%{_libdir}/R/library/nlme/html/
%{_libdir}/R/library/nlme/INDEX
%{_libdir}/R/library/nlme/libs/
%{_libdir}/R/library/nlme/LICENCE
%{_libdir}/R/library/nlme/Meta/
%{_libdir}/R/library/nlme/mlbook/
%{_libdir}/R/library/nlme/NAMESPACE
%dir %{_libdir}/R/library/nlme/po/
%lang(de) %{_libdir}/R/library/nlme/po/de/
%lang(en) %{_libdir}/R/library/nlme/po/en*/
%lang(fr) %{_libdir}/R/library/nlme/po/fr/
%lang(ko) %{_libdir}/R/library/nlme/po/ko/
%lang(pl) %{_libdir}/R/library/nlme/po/pl/
%{_libdir}/R/library/nlme/R/
%{_libdir}/R/library/nlme/scripts/
# nnet
%dir %{_libdir}/R/library/nnet/
%{_libdir}/R/library/nnet/CITATION
%{_libdir}/R/library/nnet/DESCRIPTION
%{_libdir}/R/library/nnet/help/
%{_libdir}/R/library/nnet/html/
%{_libdir}/R/library/nnet/INDEX
%{_libdir}/R/library/nnet/libs/
%{_libdir}/R/library/nnet/Meta/
%{_libdir}/R/library/nnet/NAMESPACE
%{_libdir}/R/library/nnet/NEWS
%dir %{_libdir}/R/library/nnet/po
%lang(de) %{_libdir}/R/library/nnet/po/de/
%lang(en) %{_libdir}/R/library/nnet/po/en*/
%lang(fr) %{_libdir}/R/library/nnet/po/fr/
%lang(it) %{_libdir}/R/library/nnet/po/it/
%lang(ko) %{_libdir}/R/library/nnet/po/ko/
%lang(pl) %{_libdir}/R/library/nnet/po/pl/
%{_libdir}/R/library/nnet/R/
# parallel
%{_libdir}/R/library/parallel/
# rpart
%dir %{_libdir}/R/library/rpart/
%{_libdir}/R/library/rpart/data/
%{_libdir}/R/library/rpart/DESCRIPTION
%{_libdir}/R/library/rpart/doc/
%{_libdir}/R/library/rpart/help/
%{_libdir}/R/library/rpart/html/
%{_libdir}/R/library/rpart/INDEX
%{_libdir}/R/library/rpart/libs/
%{_libdir}/R/library/rpart/Meta/
%{_libdir}/R/library/rpart/NAMESPACE
%{_libdir}/R/library/rpart/NEWS.Rd
%dir %{_libdir}/R/library/rpart/po
%lang(de) %{_libdir}/R/library/rpart/po/de/
%lang(en) %{_libdir}/R/library/rpart/po/en*/
%lang(fr) %{_libdir}/R/library/rpart/po/fr/
%lang(ko) %{_libdir}/R/library/rpart/po/ko/
%lang(pl) %{_libdir}/R/library/rpart/po/pl/
%lang(ru) %{_libdir}/R/library/rpart/po/ru/
%{_libdir}/R/library/rpart/R/
# spatial
%dir %{_libdir}/R/library/spatial/
%{_libdir}/R/library/spatial/CITATION
%{_libdir}/R/library/spatial/DESCRIPTION
%{_libdir}/R/library/spatial/help/
%{_libdir}/R/library/spatial/html/
%{_libdir}/R/library/spatial/INDEX
%{_libdir}/R/library/spatial/libs/
%{_libdir}/R/library/spatial/Meta/
%{_libdir}/R/library/spatial/NAMESPACE
%{_libdir}/R/library/spatial/NEWS
%dir %{_libdir}/R/library/spatial/po
%lang(de) %{_libdir}/R/library/spatial/po/de/
%lang(en) %{_libdir}/R/library/spatial/po/en*/
%lang(fr) %{_libdir}/R/library/spatial/po/fr/
%lang(it) %{_libdir}/R/library/spatial/po/it/
%lang(ko) %{_libdir}/R/library/spatial/po/ko/
%lang(pl) %{_libdir}/R/library/spatial/po/pl/
%{_libdir}/R/library/spatial/ppdata/
%{_libdir}/R/library/spatial/PP.files
%{_libdir}/R/library/spatial/R/
# splines
%{_libdir}/R/library/splines/
# stats
%{_libdir}/R/library/stats/
# stats4
%{_libdir}/R/library/stats4/
# survival
%{_libdir}/R/library/survival/
# tcltk
%{_libdir}/R/library/tcltk/
# tools
%{_libdir}/R/library/tools/
# utils
%{_libdir}/R/library/utils/
%{_libdir}/R/modules
%{_libdir}/R/COPYING
# %%{_libdir}/R/NEWS*
%{_libdir}/R/SVN-REVISION
%if %{texi2any}
%{_infodir}/R-*.info*
%endif
%{_mandir}/man1/*
%{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}
%docdir %{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}
/etc/ld.so.conf.d/*

%files core-devel
%{_libdir}/pkgconfig/libR.pc
%{_includedir}/R
# Symlink to %%{_includedir}/R/
%{_libdir}/R/include

%files devel
# Nothing, all files provided by R-core-devel

%if %{modern}
%files java
# Nothing, all files provided by R-core

%files java-devel
# Nothing, all files provided by R-core-devel
%endif

%files -n libRmath
%doc doc/COPYING
%{_libdir}/libRmath.so

%files -n libRmath-devel
%{_includedir}/Rmath.h
%{_libdir}/pkgconfig/libRmath.pc

%files -n libRmath-static
%{_libdir}/libRmath.a

%changelog
* Mon May  3 2021 Tom Callaway <spot@fedoraproject.org> - 4.0.5-1
- update to 4.0.5

* Mon Feb 15 2021 Tom Callaway <spot@fedoraproject.org> - 4.0.4-1
- update to 4.0.4

* Wed Feb 03 2021 Elliott Sales de Andrade <quantum.analyst@gmail.com> - 4.0.3-3
- Always provide normalized versions of R submodules
- Fixes rhbz#1924565

* Mon Jan 25 2021 Fedora Release Engineering <releng@fedoraproject.org> - 4.0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Oct 12 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.3-1
- update to 4.0.3

* Tue Sep  8 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.2-5
- make cups a "Recommends" instead of a "Requires" (bz1875165)
- even though f31 uses a forked spec file, reflect the systemlapack change there here

* Fri Aug 07 2020 Iñaki Úcar <iucar@fedoraproject.org> - 4.0.2-4
- https://fedoraproject.org/wiki/Changes/FlexiBLAS_as_BLAS/LAPACK_manager

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 4.0.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul 15 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.2-2
- add additional paths to find libjvm.so (OpenJDK 11+)

* Mon Jun 22 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.2-1
- update to 4.0.2

* Tue Jun 16 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.1-1
- update to 4.0.1

* Mon Jun 15 2020 Pete Walter <pwalter@fedoraproject.org> - 4.0.0-3
- Rebuild for ICU 67

* Tue Jun 2 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.0-2
- apply upstream fix for ppc64 infinite loop

* Fri May 8 2020 Tom Callaway <spot@fedoraproject.org> - 4.0.0-1
- update to 4.0.0
  NOTE: This major release update requires all installed R modules to be rebuilt in order to work.
  To help with this, we've added an R(ABI) Provides/Requires setup.

* Mon Mar  2 2020 Tom Callaway <spot@fedoraproject.org> - 3.6.3-1
- update to 3.6.3
- conditionalize lapack changes from previous commits to Fedora 32+ and EPEL-8

* Tue Feb 18 2020 Tom Callaway <spot@fedoraproject.org> - 3.6.2-5
- fix openblas conditionals, openblas has wider arch support everywhere except el7

* Tue Feb 18 2020 Tom Callaway <spot@fedoraproject.org> - 3.6.2-4
- fix conditionals so that Fedora builds against system openblas for lapack/blas
  and we only generate the R lapack/blas libs on RHEL 5-6-7 (where system lapack/openblas
  is not reliable). Thanks to Dirk Eddelbuettel for pointing out the error.

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 3.6.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Wed Dec 18 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.2-2
- adjust ppc64 patch to reflect upstream fix

* Thu Dec 12 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.2-1
- update to 3.6.2
- disable tests on all non-intel arches
- fix powerpc64

* Fri Nov 01 2019 Pete Walter <pwalter@fedoraproject.org> - 3.6.1-3
- Rebuild for ICU 65

* Fri Aug 30 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.1-2
- conditionalize macro usage so that it only happens on Fedora 31+ and EPEL-8

* Fri Aug 16 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.1-1
- update to 3.6.1

* Sun Aug 11 2019 Elliott Sales de Andrade <quantum.analyst@gmail.com> - 3.6.0-5
- Remove unused and nonfunctional macros and helper script

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.6.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sun Jul 21 2019 Elliott Sales de Andrade <quantum.analyst@gmail.com> - 3.6.0-3
- Add automated dependency generator to R-devel
- Add standard Provides for bundled libraries

* Thu Jun 13 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.0-2
- use devtoolset toolchain to compile on el6/el7 for C++11 support

* Wed May 29 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.0-1
- update to 3.6.0
- use --no-optimize-sibling-calls for gfortran to work around issues

* Mon Mar 11 2019 Tom Callaway <spot@fedoraproject.org> - 3.5.3-1
- update to 3.5.3

* Sun Feb 17 2019 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 3.5.2-5
- Rebuild for readline 8.0

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Jan 23 2019 Pete Walter <pwalter@fedoraproject.org> - 3.5.2-3
- Rebuild for ICU 63

* Tue Jan  8 2019 Tom Callaway <spot@fedoraproject.org> - 3.5.2-2
- handle pcre2 use/detection

* Mon Jan  7 2019 Tom Callaway <spot@fedoraproject.org> - 3.5.2-1
- update to 3.5.2

* Fri Dec  7 2018 Tom Callaway <spot@fedoraproject.org> - 3.5.1-2
- use absolute path in symlink for latex dir (bz1594102)

* Mon Sep 10 2018 Tom Callaway <spot@fedoraproject.org> - 3.5.1-1
- update to 3.5.1
- update bundled curl to 7.61.1

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.5.0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jul 10 2018 Pete Walter <pwalter@fedoraproject.org> - 3.5.0-5
- Rebuild for ICU 62

* Tue Jun  5 2018 Tom Callaway <spot@fedoraproject.org> - 3.5.0-4
- only own /usr/share/texmf/tex/latex/R ... not /usr/share/texmf

* Fri May 18 2018 Tom Callaway <spot@fedoraproject.org> - 3.5.0-3
- do not run javareconf on el6/ppc64 EVEN in the java subpackages

* Fri May 18 2018 Tom Callaway <spot@fedoraproject.org> - 3.5.0-2
- do not run javareconf on el6/ppc64

* Mon May 14 2018 Tom Callaway <spot@fedoraproject.org> - 3.5.0-1
- update to 3.5.0
- update xz bundle (rhel6 only)
- disable tests on armv7hl
- disable info builds on rhel 6

* Sun May 13 2018 Stefan O'Rear <sorear2@gmail.com> - 3.4.4-3
- Add riscv* to target CPU specs

* Mon Apr 30 2018 Pete Walter <pwalter@fedoraproject.org> - 3.4.4-2
- Rebuild for ICU 61.1

* Wed Mar 28 2018 Tom Callaway <spot@fedoraproject.org> - 3.4.4-1
- update to 3.4.4
- update pcre and curl bundles (rhel6 only)

* Mon Feb 12 2018 Tom Callaway <spot@fedoraproject.org> - 3.4.3-6
- undefine %%__brp_mangle_shebangs (we need +x on files in %%{_libdir}/R/bin/)

* Wed Feb  7 2018 Tom Callaway <spot@fedoraproject.org> - 3.4.3-5
- fix exec permissions on files in %%{_libdir}/R/bin/

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Feb  2 2018 Tom Callaway <spot@fedoraproject.org> - 3.4.3-3
- rebuild for new gfortran

* Fri Dec 01 2017 Pete Walter <pwalter@fedoraproject.org> - 3.4.3-2
- Rebuild once more for ICU 60.1

* Thu Nov 30 2017 Tom Callaway <spot@fedoraproject.org> - 3.4.3-1
- update to 3.4.3

* Thu Nov 30 2017 Pete Walter <pwalter@fedoraproject.org> - 3.4.2-3
- Rebuild for ICU 60.1

* Mon Oct 30 2017 Tom Callaway <spot@fedoraproject.org> - 3.4.2-2
- conditionalize Requires on perl-interpreter for fedora only

* Fri Oct 27 2017 Tom Callaway <spot@fedoraproject.org>- 3.4.2-1
- update to 3.4.2

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.4.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jul 13 2017 Petr Pisar <ppisar@redhat.com> - 3.4.1-2
- perl dependency renamed to perl-interpreter
  <https://fedoraproject.org/wiki/Changes/perl_Package_to_Install_Core_Modules>

* Fri Jun 30 2017 Tom Callaway <spot@fedoraproject.org> - 3.4.1-1
- update to 3.4.1

* Fri May 12 2017 José Matos <jamatos@fedoraproject.org> - 3.4.0-2
- add TZ="Europe/Paris" to please make check

* Sat Apr 22 2017 Tom Callaway <spot@fedoraproject.org> - 3.4.0-1
- update to 3.4.0

* Wed Mar  8 2017 Tom Callaway <spot@fedoraproject.org> - 3.3.3-1
- update to 3.3.3

* Tue Feb 14 2017 Tom Callaway <spot@fedoraproject.org> - 3.3.2-8
- disable tests on ppc64/ppc64le (no real way to debug them)

* Tue Feb 14 2017 Björn Esser <besser82@fedoraproject.org> - 3.3.2-7
- Add Patch2 to fix detection of zlib

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.3.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Sat Jan 28 2017 Björn Esser <besser82@fedoraproject.org> - 3.3.2-5
- Rebuilt for GCC-7

* Thu Jan 12 2017 Igor Gnatenko <ignatenko@redhat.com> - 3.3.2-4
- Rebuild for readline 7.x

* Wed Dec 14 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.2-3
- openblas-Rblas provides libRblas.so now

* Mon Oct 31 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.2-2
- fix provides for openblas hack
- fix version for recommended components that are included

* Mon Oct 31 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.2-1.1
- disable readline support for el5

* Mon Oct 31 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.2-1
- update to 3.3.2

* Fri Oct 28 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.1-5
- add false Provides in openblas case

* Fri Oct 28 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.1-4
- use -Wl,--as-needed on zlibhack targets (bz 1389715)
- use openblas on architectures where it exists, keep R reference blas as "libRrefblas.so"

* Mon Aug 29 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.1-3
- fix use of _isa to be conditionalized on its existence (looking at you el5)

* Mon Aug  8 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.1-2
- add Requires: libmath to R-core

* Tue Jul  5 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.1-1
- update to 3.3.1

* Sat Jun 11 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-10
- fix CAPABILITIES pathing

* Sat Jun 11 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-9
- fix ldpaths for zlibhack
- clean libtool
- clean CAPABILITIES

* Thu Jun  9 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-8
- fix FLIBS cleanup for el5

* Thu Jun  9 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-7
- clean up zlibhack from FLIBS

* Tue Jun  7 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-6
- fix sed invocations to cover both el5 and el6 (thanks again to Mattias Ellert)

* Mon Jun  6 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-5
- fix sed invocations to fully cleanup zlibhack (thanks to Mattias Ellert)

* Wed Jun  1 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-4
- fixup libR.pc for zlibhack (el5/el6)

* Fri May 13 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-3
- we no longer need Requires: blas-devel, lapack-devel for R-core-devel

* Wed May 11 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-2.1
- implement "zlibhack" to build R against bundled bits too old in RHEL 5 & 6

* Tue May 10 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-2
- RHEL 6 ppc64 doesn't have libicu-devel. :P

* Tue May 10 2016 Tom Callaway <spot@fedoraproject.org> - 3.3.0-1
- update to 3.3.0
- fix R-java Requires (bz1324145)
- fix JAVA_PATH definition in javareconf (bz1324145)
- use bundled BLAS and LAPACK, create shared library for Rblas

* Fri Apr 15 2016 David Tardon <dtardon@redhat.com> - 3.2.4-2
- rebuild for ICU 57.1

* Fri Mar 18 2016 Tom Callaway <spot@fedoraproject.org> - 3.2.4-1
- move to 3.2.4-revised

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Jan 26 2016 Tom Callaway <spot@fedoraproject.org> - 3.2.3-4
- if texi2any is set to 0, then copy in prebuilt html manuals (RHEL 5 & 6 only)

* Tue Jan 26 2016 Tom Callaway <spot@fedoraproject.org> - 3.2.3-3
- use global instead of define

* Fri Jan 15 2016 Tom Callaway <spot@fedoraproject.org> - 3.2.3-2
- Requires: redhat-rpm-config on hardened systems (all Fedora and RHEL 7+)

* Fri Dec 11 2015 Tom Callaway <spot@fedoraproject.org> - 3.2.3-1
- update to 3.2.3

* Wed Oct 28 2015 David Tardon <dtardon@redhat.com> - 3.2.2-3
- rebuild for ICU 56.1

* Tue Oct 13 2015 Tom Callaway <spot@fedoraproject.org> - 3.2.2-2
- apply patches from upstream bug 16497 to fix X11 hangs

* Fri Aug 14 2015 Tom Callaway <spot@fedoraproject.org> - 3.2.2-1
- update to 3.2.2

* Fri Jul 10 2015 Tom Callaway <spot@fedoraproject.org> - 3.2.1-2
- BR: libcurl-devel

* Thu Jun 18 2015 Tom Callaway <spot@fedoraproject.org> - 3.2.1-1
- update to 3.2.1

* Tue Jun 16 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon May 04 2015 Jakub Čajka <jcajka@redhat.com> - 3.2.0-2
- valgrind is available only on selected arches, fixes build on s390

* Thu Apr 30 2015 Tom Callaway <spot@fedoraproject.org>
- conditionalize MAKEINFO for ancient things (rhel 6 or older)

* Sun Apr 26 2015 Tom Callaway <spot@fedoraproject.org> - 3.2.0-1
- update to 3.2.0

* Mon Mar  9 2015 Tom Callaway <spot@fedoraproject.org> - 3.1.3-1
- update to 3.1.3

* Mon Jan 26 2015 David Tardon <dtardon@redhat.com> - 3.1.2-2
- rebuild for ICU 54.1

* Fri Oct 31 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.2-1
- update to 3.1.2

* Wed Oct 29 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.1-8
- rebuild for new tcl/tk
- mark Makeconf as config (not config(noreplace) so that we get proper updated tcl/tk libs)

* Mon Sep 29 2014 Orion Poplawski <orion@cora.nwra.com> - 3.1.1-7
- Just BR/R java instead of java-1.5.0-gcj (bug #1110684)

* Tue Sep 16 2014 David Sommerseth <davids@redhat.com> - 3.1.1-6
- Setting ulimit when running make check, to avoid segfault due to too small stack (needed on PPC64)

* Tue Aug 26 2014 David Tardon <dtardon@redhat.com> - 3.1.1-5
- rebuild for ICU 53.1

* Fri Aug 15 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Fri Aug  8 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.1-3
- add "unzip" to Requirements list for R-core

* Fri Aug  8 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.1-2
- add "make" to Requirements list for R-core (thanks R config)

* Thu Jul 10 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.1-1
- update to 3.1.1

* Mon Jul  7 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-10
- disable lto everywhere (breaks debuginfo) (bz 1113404)
- apply fix for ppc64 (bz 1114240 and upstream bug 15856)
- add make check (bz 1059461)
- use bundled blas/lapack for RHEL due to bugs in their BLAS
- enable Rblas shared lib (whether using bundled BLAS or not)
- add explicit requires for new lapack

* Tue Jun 24 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-9
- mark files in %%{_libdir}/R/etc as config(noreplace), resolves 1098663

* Fri Jun 06 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.1.0-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed May 21 2014 Jaroslav Škarvada <jskarvad@redhat.com> - 3.1.0-7
- Rebuilt for https://fedoraproject.org/wiki/Changes/f21tcl86

* Thu May 15 2014 Peter Robinson <pbrobinson@fedoraproject.org> 3.1.0-6
- Add aarch64 to target CPU specs

* Wed May  7 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-5
- add blas-devel and lapack-devel as Requires for R-devel/R-core-devel
  to ease rebuild pain

* Tue Apr 29 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-4
- unified spec file for all targets

* Tue Apr 29 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-3
- epel fixes

* Fri Apr 25 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-2
- fix core-devel Requires

* Mon Apr 21 2014 Tom Callaway <spot@fedoraproject.org> - 3.1.0-1
- update to 3.1.0

* Mon Mar 24 2014 Brent Baude <baude@us.ibm.com> - 3.0.3-2
- add ppc64le support
- rhbz #1077819

* Thu Mar 20 2014 Tom Callaway <spot@fedoraproject.org> - 3.0.3-1
- update to 3.0.3
- switch to java-headless

* Fri Feb 14 2014 David Tardon <dtardon@redhat.com> - 3.0.2-7
- rebuild for new ICU

* Sat Feb  8 2014 Ville Skyttä <ville.skytta@iki.fi> - 3.0.2-6
- Install macros to %%{_rpmconfigdir}/macros.d where available.
- Fix rpmlint spaces vs tabs warnings.

* Fri Feb  7 2014 Tom Callaway <spot@fedoraproject.org> - 3.0.2-5
- add support for system tre (f21+, rhel 7+)

* Fri Feb  7 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.2-4
- Use BR java

* Fri Jan 24 2014 Tom Callaway <spot@fedoraproject.org> - 3.0.2-3
- disable lto on non-modern targets (not just ppc)

* Fri Dec 20 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.2-2
- add --with-blas, --enable-lto to configure

* Tue Oct 15 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.2-1
- update to 3.0.2

* Mon Aug 12 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.1-4
- add support for unversioned docdir in F20+
- fix compile on arm (thanks Debian, wish you'd upstreamed that patch)

* Fri Aug 02 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat May 18 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.1-2
- conditionalize the ugly hack for fedora 19+

* Fri May 17 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.1-1
- update to 3.0.1

* Sat Apr 13 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.0-2
- add Requires: tex(inconsolata.sty) to -core-devel to fix module PDF building

* Fri Apr  5 2013 Tom Callaway <spot@fedoraproject.org> - 3.0.0-1
- update to 3.0.0

* Wed Feb 27 2013 Tom Callaway <spot@fedoraproject.org> - 2.15.2-7
- add BuildRequires: xz-devel (for system xz/lzma support)
- create R-core-devel

* Sat Jan 26 2013 Kevin Fenzi <kevin@scrye.com> - 2.15.2-6
- Rebuild for new icu

* Sun Jan 20 2013 Tom Callaway <spot@fedoraproject.org> - 2.15.2-5
- apply upstream fix for cairo issues (bz 891983)

* Fri Jan 18 2013 Adam Tkac <atkac redhat com> - 2.15.2-4
- rebuild due to "jpeg8-ABI" feature drop

* Tue Nov 27 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.2-3
- add Requires: tex(cm-super-ts1.enc) for R-devel

* Tue Nov 27 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.2-2
- add additional TeX font requirements to R-devel for Fedora 18+ (due to new texlive)

* Mon Oct 29 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.2-1
- update to 2.15.2
- R now Requires: R-java (for a more complete base install)

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.15.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul  2 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.1-1
- update to 2.15.1

* Mon Jul  2 2012 Jindrich Novy <jnovy@redhat.com> - 2.15.0-4
- fix LaTeX and dvips dependencies (#836817)

* Mon May  7 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.0-3
- rebuild for new libtiff

* Tue Apr 24 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.0-2
- rebuild for new icu

* Fri Mar 30 2012 Tom Callaway <spot@fedoraproject.org> - 2.15.0-1
- Update to 2.15.0

* Fri Feb 10 2012 Petr Pisar <ppisar@redhat.com> - 2.14.1-3
- Rebuild against PCRE 8.30

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.14.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Jan  4 2012 Tom Callaway <spot@fedoraproject.org> - 2.14.1-1
- update to 2.14.1

* Tue Nov  8 2011 Tom Callaway <spot@fedoraproject.org> - 2.14.0-3
- No inconsolata for EL

* Mon Nov  7 2011 Tom Callaway <spot@fedoraproject.org> - 2.14.0-2
- add texinfo-tex to Requires for -devel package

* Wed Nov  2 2011 Tom Callaway <spot@fedoraproject.org> - 2.14.0-1
- update to 2.14.0

* Fri Oct  7 2011 Tom Callaway <spot@fedoraproject.org> - 2.13.2-1
- update to 2.13.2

* Mon Sep 12 2011 Michel Salim <salimma@fedoraproject.org> - 2.13.1-5
- rebuild for libicu 4.8.x

* Tue Aug  9 2011 Tom Callaway <spot@fedoraproject.org> - 2.13.1-4
- fix salimma's scriptlets to be on -core instead of the metapackage

* Tue Aug  9 2011 Michel Salim <salimma@fedoraproject.org> - 2.13.1-3
- Symlink LaTeX files, and rehash on package change when possible (# 630835)

* Mon Aug  8 2011 Tom Callaway <spot@fedoraproject.org> - 2.13.1-2
- add BuildRequires: less

* Mon Jul 11 2011 Tom Callaway <spot@fedoraproject.org> - 2.13.1-1
- update to 2.13.1

* Tue Apr 12 2011 Tom Callaway <spot@fedoraproject.org> - 2.13.0-1
- update to 2.13.0
- add convenience symlink for include directory (bz 688295)

* Mon Mar 07 2011 Caolán McNamara <caolanm@redhat.com> - 2.12.2-2
- rebuild for icu 4.6

* Sun Feb 27 2011 Tom Callaway <spot@fedoraproject.org> - 2.12.2-1
- update to 2.12.2

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.12.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Dec 17 2010 Tom Callaway <spot@fedoraproject.org> - 2.12.1-1
- update to 2.12.1

* Wed Oct 20 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 2.12.0-1
- update to 2.12.0

* Wed Jul  7 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 2.11.1-4
- include COPYING in libRmath package

* Wed Jun 30 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 2.11.1-3
- move libRmath static lib into libRmath-static subpackage

* Thu Jun  3 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 2.11.1-2
- overload R_LIBS_SITE instead of R_LIBS

* Tue Jun  1 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 2.11.1-1
- update to 2.11.1

* Thu Apr 22 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 2.11.0-1
- update to 2.11.0

* Fri Apr 02 2010 Caolán McNamara <caolanm@redhat.com> - 2.10.1-2
- rebuild for icu 4.4

* Mon Dec 21 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.10.1-1
- update to 2.10.1
- enable static html pages

* Mon Nov  9 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.10.0-2
- get rid of index.txt scriptlet on R-core (bz 533572)
- leave macro in place, but don't call /usr/lib/rpm/R-make-search-index.sh equivalent anymore
- add version check to see if we need to run R-make-search-index.sh guts

* Wed Nov  4 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.10.0-1
- update to 2.10.0
- use correct compiler for ARM

* Thu Oct 15 2009 Karsten Hopp <karsten@redhat.com> 2.9.2-2
- s390 (not s390x) needs the -m31 compiler flag

* Mon Aug 24 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.9.2-1
- Update to 2.9.2

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Jul 10 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.9.1-2
- don't try to make the PDFs in rawhide/i586

* Thu Jul  9 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.9.1-1
- update to 2.9.1
- fix versioned provides

* Mon Apr 20 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.9.0-2
- properly Provide/Obsolete R-Matrix

* Fri Apr 17 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.9.0-1
- update to 2.9.0, change vim dep to vi

* Tue Apr  7 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.8.1-9
- drop profile.d scripts, they broke more than they fixed
- minimize hard-coded Requires based on Martyn Plummer's analysis

* Sat Mar 28 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.8.1-8
- fix profile scripts for situation where R_HOME is already defined
  (bugzilla 492706)

* Tue Mar 24 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.8.1-7
- bump for new tag

* Tue Mar 24 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.8.1-6
- add profile.d scripts to set R_HOME
- rpmlint cleanups

* Mon Mar 23 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.8.1-5
- add R-java and R-java-devel "dummy" packages, so that we can get java dependent R-modules
  to build/install

* Wed Mar  4 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 2.8.1-4
- update post scriptlet (bz 477076)

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Jan  5 2009 Tom "spot" Callaway <tcallawa@redhat.com> 2.8.1-2
- add pango-devel to BuildRequires (thanks to Martyn Plummer and Peter Dalgaard)
- fix libRmath requires to need V-R (thanks to Martyn Plummer)

* Mon Dec 22 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.8.1-1
- update javareconf call in %%post (bz 477076)
- 2.8.1

* Sun Oct 26 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.8.0-2
- enable libtiff interface

* Sun Oct 26 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.8.0-1
- Update to 2.8.0
- New subpackage layout: R-core is functional userspace, R is metapackage
  requiring everything
- Fix system bzip2 detection

* Thu Oct 16 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.2-2
- fix sh compile (bz 464055)

* Fri Aug 29 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.2-1
- update to 2.7.2
- fix spec for alpha compile (bz 458931)
- fix security issue in javareconf script (bz 460658)

* Mon Jul  7 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.1-1
- update to 2.7.1

* Wed May 28 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.0-5
- add cairo-devel to BR/R, so that cairo backend gets built

* Wed May 21 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.0-4
- fixup sed invocation added in -3
- make -devel package depend on base R = version-release
- fix bad paths in package html files

* Wed May 21 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.0-3
- fix poorly constructed file paths in html/packages.html (bz 442727)

* Tue May 13 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.0-2
- add patch from Martyn Plummer to avoid possible bad path hardcoding in
  /usr/bin/Rscript
- properly handle ia64 case (bz 446181)

* Mon Apr 28 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.0-1
- update to 2.70
- rcompgen is no longer a standalone package
- redirect javareconf to /dev/null (bz 442366)

* Fri Feb  8 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.2-1
- properly version the items in the VR bundle
- 2.6.2
- don't use setarch for java setup
- fix R post script file

* Thu Jan 31 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.1-4
- multilib handling (thanks Martyn Plummer)
- Update indices in the right place.

* Mon Jan  7 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.1-3
- move INSTALL back into R main package, as it is useful without the
  other -devel bits (e.g. installing noarch package from CRAN)

* Tue Dec 11 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.1-2
- based on changes from Martyn Plummer <martyn.plummer@r-project.org>
- use configure options rdocdir, rincludedir, rsharedir
- use DESTDIR at installation
- remove obsolete generation of packages.html
- move header files and INSTALL R-devel package

* Mon Nov 26 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.1-1
- bump to 2.6.1

* Tue Oct 30 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.0-3.1
- fix missing perl requires

* Mon Oct 29 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.0-3
- fix multilib conflicts (bz 343061)

* Mon Oct 29 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.0-2
- add R CMD javareconf to post (bz 354541)
- don't pickup bogus perl provides (bz 356071)
- use xdg-open, drop requires for firefox/evince (bz 351841)

* Thu Oct  4 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.6.0-1
- bump to 2.6.0

* Sun Aug 26 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.5.1-3
- fix license tag
- rebuild for ppc32

* Thu Jul  5 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.5.1-2
- add rpm helper macros, script

* Mon Jul  2 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.5.1-1
- drop patch, upstream fixed
- bump to 2.5.1

* Mon Apr 30 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.5.0-2
- patch from Martyn Plummer fixes .pc files
- add new BR: gcc-objc

* Wed Apr  25 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.5.0-1
- bump to 2.5.0

* Tue Mar  13 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.4.1-4
- get rid of termcap related requires, replace with ncurses
- use java-1.5.0-gcj instead of old java-1.4.2
- add /usr/share/R/library as a valid R_LIBS directory for noarch bits

* Sun Feb  25 2007 Jef Spaleta <jspaleta@gmail.com> 2.4.1-3
- rebuild for reverted tcl/tk

* Fri Feb  2 2007 Tom "spot" Callaway <tcallawa@redhat.com> 2.4.1-2
- rebuild for new tcl/tk

* Tue Dec 19 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.4.1-1
- bump to 2.4.1
- fix install-info invocations in post/preun (bz 219407)

* Fri Nov  3 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.4.0-2
- sync with patched 2006-11-03 level to fix PR#9339

* Sun Oct 15 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.4.0-1
- bump for 2.4.0

* Tue Sep 12 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.3.1-2
- bump for FC-6

* Fri Jun  2 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.3.1-1
- bump to 2.3.1

* Tue Apr 25 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.3.0-2
- fix ppc build for FC-4 (artificial bump for everyone else)

* Mon Apr 24 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.3.0-1
- bump to 2.3.0 (also, bump module revisions)

* Tue Feb 28 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.1-5
- now BR is texinfo-tex, not texinfo in rawhide

* Tue Feb 28 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.1-4
- bump for FC-5

* Mon Jan  9 2006 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.1-3
- fix BR: XFree86-devel for FC-5

* Sat Dec 31 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.1-2
- missing BR: libXt-devel for FC-5

* Tue Dec 20 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.1-1
- bump to 2.2.1

* Thu Oct  6 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.0-2
- use fixed system lapack for FC-4 and devel

* Thu Oct  6 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.2.0-1
- bump to 2.2.0

* Mon Jul  4 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.1.1-2
- fix version numbers on supplemental package provides

* Mon Jun 20 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.1.1-1
- bugfix update

* Mon Apr 18 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.1.0-51
- proper library handling

* Mon Apr 18 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.1.0-50
- 2.1.0, fc4 version.
- The GNOME GUI is unbundled, now provided as a package on CRAN

* Thu Apr 14 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-50
- big bump. This is the fc4 package, the fc3 package is 2.0.1-11
- enable gnome gui, add requires as needed

* Thu Apr 14 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-10
- bump for cvs errors

* Mon Apr 11 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-9
- fix URL for Source0

* Mon Apr 11 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-8
- spec file cleanup

* Fri Apr  1 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-7
- use evince instead of ggv
- make custom provides for R subfunctions

* Wed Mar 30 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-6
- configure now calls --enable-R-shlib

* Thu Mar 24 2005 Tom "spot" Callaway <tcallawa@redhat.com> 2.0.1-5
- cleaned up package for Fedora Extras

* Mon Feb 28 2005 Martyn Plummer <plummer@iarc.fr> 0:2.0.1-0.fdr.4
- Fixed file ownership in R-devel and libRmath packages

* Wed Feb 16 2005 Martyn Plummer <plummer@iarc.fr> 0:2.0.1-0.fdr.3
- R-devel package is now a stub package with no files, except a documentation
  file (RPM won't accept sub-packages with no files). R now conflicts
  with earlier (i.e 0:2.0.1-0.fdr.2) versions of R-devel.
- Created libRmath subpackage with shared library.

* Mon Jan 31 2005 Martyn Plummer <plummer@iarc.fr> 0:2.0.1-0.fdr.2
- Created R-devel and libRmath-devel subpackages

* Mon Nov 15 2004 Martyn Plummer <plummer@iarc.fr> 0:2.0.1-0.fdr.1
- Built R 2.0.1

* Wed Nov 10 2004 Martyn Plummer <plummer@iarc.fr> 0:2.0.0-0.fdr.3
- Set R_PRINTCMD at configure times so that by default getOption(printcmd)
  gives "lpr".
- Define macro fcx for all Fedora distributions. This replaces Rinfo

* Tue Oct 12 2004 Martyn Plummer <plummer@iarc.fr> 0:2.0.0-0.fdr.2
- Info support is now conditional on the macro Rinfo, which is only
  defined for Fedora 1 and 2.

* Thu Oct 7 2004 Martyn Plummer <plummer@iarc.fr> 0:2.0.0-0.fdr.1
- Built R 2.0.0
- There is no longer a BUGS file, so this is not installed as a
  documentation file.

* Mon Aug  9 2004 Martyn Plummer <plummer@iarc.fr> 0:1.9.1-0.fdr.4
- Added gcc-g++ to the list of BuildRequires for all platforms.
  Although a C++ compiler is not necessary to build R, it must
  be present at configure time or R will not be correctly configured
  to build packages containing C++ code.

* Thu Jul  1 2004 Martyn Plummer <plummer@iarc.fr> 0:1.9.1-0.fdr.3
- Modified BuildRequires so we can support older Red Hat versions without
  defining any macros.

* Wed Jun 23 2004 Martyn Plummer <plummner@iarc.fr> 0:1.9.1-0.fdr.2
- Added libtermcap-devel as BuildRequires for RH 8.0 and 9. Without
  this we get no readline support.

* Mon Jun 21 2004 Martyn Plummer <plummner@iarc.fr> 0:1.9.1-0.fdr.1
- Build R 1.9.1
- Removed Xorg patch since fix is now in R sources

* Mon Jun 14 2004 Martyn Plummer <plummer@iarc.fr> 0:1.9.0-0.fdr.4
- Added XFree86-devel as conditional BuildRequires for rh9, rh80

* Tue Jun 08 2004 Martyn Plummer <plummer@iarc.fr> 0:1.9.0-0.fdr.3
- Corrected names for fc1/fc2/el3 when using conditional BuildRequires
- Configure searches for C++ preprocessor and fails if we don't have
  gcc-c++ installed. Added to BuildRequires for FC2.

* Tue Jun 08 2004 Martyn Plummer <plummer@iarc.fr> 0:1.9.0-0.fdr.2
- Added patch to overcome problems with X.org headers (backported
  from R 1.9.1; patch supplied by Graeme Ambler)
- Changed permissions of source files to 644 to please rpmlint

* Mon May 03 2004 Martyn Plummer <plummer@iarc.fr> 0:1.9.0-0.fdr.1
- R.spec file now has mode 644. Previously it was unreadable by other
  users and this was causing a crash building under mach.
- Changed version number to conform to Fedora conventions.
- Removed Provides: and Obsoletes: R-base, R-recommended, which are
  now several years old. Nobody should have a copy of R-base on a
  supported platform.
- Changed buildroot to Fedora standard
- Added Requires(post,preun): info
- Redirect output from postinstall/uninstall scripts to /dev/null
- Added BuildRequires tags necessary to install R with full
  capabilities on a clean mach buildroot. Conditional buildrequires
  for tcl-devel and tk-devel which were not present on RH9 or earlier.

* Thu Apr 01 2004 Martyn Plummer <plummer@iarc.fr>
- Added patch to set environment variable LANG to C in shell wrapper,
  avoiding warnings about UTF-8 locale not being supported

* Mon Mar 15 2004 Martyn Plummer <plummer@iarc.fr>
- No need to export optimization flags. This is done by %%configure
- Folded info installation into %%makeinstall
- Check that RPM_BASE_ROOT is not set to "/" before cleaning up

* Tue Feb 03 2004 Martyn Plummer <plummer@iarc.fr>
- Removed tcl-devel from BuildRequires

* Tue Feb 03 2004 Martyn Plummer <plummer@iarc.fr>
- Changes from James Henstridge <james@daa.com.au> to allow building on IA64:
- Added BuildRequires for tcl-devel tk-devel tetex-latex
- Use the %%configure macro to call the configure script
- Pass --with-tcl-config and --with-tk-config arguments to configure
- Set rhome to point to the build root during "make install"

* Wed Jan 07 2004 Martyn Plummer <plummer@iarc.fr>
- Changed obsolete "copyright" field to "license"

* Fri Nov 21 2003 Martyn Plummer <plummer@iarc.fr>
- Built 1.8.1
