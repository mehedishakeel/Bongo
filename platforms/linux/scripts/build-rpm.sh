#!/usr/bin/env bash
#
# Build Fedora/RPM (.rpm) package for Bongo
# Supports Fedora 38+, 39+, 40+, CentOS Stream, RHEL 9+, openSUSE
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${LINUX_ROOT}/release"

VERSION="${VERSION:-1.0.1}"
ARCH="$(uname -m)"
BUILD_ROOT="${LINUX_ROOT}/build/rpm"

echo "--> Building Bongo RPM Package for ${ARCH}..."

mkdir -p "${BUILD_ROOT}/BUILD" "${BUILD_ROOT}/RPMS" "${BUILD_ROOT}/SOURCES" "${BUILD_ROOT}/SPECS" "${BUILD_ROOT}/SRPMS"
mkdir -p "${DIST_DIR}"

SPEC_FILE="${BUILD_ROOT}/SPECS/bongo.spec"

cat <<EOF > "${SPEC_FILE}"
Name:           bongo
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        Native Avro phonetic Bengali typing for Linux
License:        MPL-2.0
URL:            https://getbongo.app

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Recommends:    ibus
Recommends:    fcitx5
Suggests:       fcitx5-configtool
BuildRequires:  cmake
BuildRequires:  fcitx5-devel

%description
Bongo brings fast, natural Avro phonetic Bengali typing to modern Linux desktops
(GNOME, KDE Plasma, XFCE). Powered by a pure-Rust offline transliteration engine
with full candidate suggestions and both IBus and fcitx5 frontends.

%install
DESTDIR=%{buildroot} PREFIX=/usr BONGO_FCITX5=1 bash ${SCRIPT_DIR}/install.sh

%files
/usr/lib/bongo/libbongo_engine.so
%{_libexecdir}/bongo-ibus-engine
%{_datadir}/ibus/component/bongo.xml
%{_bindir}/bongo-settings
%{_bindir}/bongo-fcitx5-setup
%{_datadir}/applications/app.getbongo.Bongo.desktop
%{_datadir}/applications/bongo.desktop
%{_datadir}/metainfo/app.getbongo.Bongo.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/bongo.png
%{_datadir}/pixmaps/bongo.png
%{_libdir}/fcitx5/libbongo.so
%{_datadir}/fcitx5/addon/bongo.conf
%{_datadir}/fcitx5/inputmethod/bongo.conf

%post
if [ \$1 -eq 1 ]; then
    /usr/bin/update-desktop-database &> /dev/null || :
    /usr/bin/gtk-update-icon-cache -f -t /usr/share/icons/hicolor &> /dev/null || :
    /usr/bin/ibus write-cache &> /dev/null || :
fi

%postun
if [ \$1 -eq 0 ]; then
    /usr/bin/update-desktop-database &> /dev/null || :
    /usr/bin/gtk-update-icon-cache -f -t /usr/share/icons/hicolor &> /dev/null || :
    /usr/bin/ibus write-cache &> /dev/null || :
fi
EOF

if command -v rpmbuild >/dev/null 2>&1; then
    rpmbuild --define "_topdir ${BUILD_ROOT}" -bb "${SPEC_FILE}"
    find "${BUILD_ROOT}/RPMS" -name "*.rpm" -exec cp {} "${DIST_DIR}/" \;
    echo "RPM successfully created in ${DIST_DIR}"
else
    echo "rpmbuild not found. Spec file created at ${SPEC_FILE}"
fi
