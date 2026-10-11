#!/usr/bin/env bash
#
# Build Debian/Ubuntu (.deb) package for Bongo
# Supports Ubuntu 22.04+, 24.04+, Debian 12+, Linux Mint, Pop!_OS
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${LINUX_ROOT}/release"

VERSION="1.0.0"
ARCH="$(dpkg --print-architecture 2>/dev/null || uname -m)"
case "${ARCH}" in
    x86_64) DEB_ARCH="amd64" ;;
    aarch64|arm64) DEB_ARCH="arm64" ;;
    *) DEB_ARCH="${ARCH}" ;;
esac

PKG_NAME="bongo_${VERSION}_${DEB_ARCH}"
BUILD_ROOT="${LINUX_ROOT}/build/deb/${PKG_NAME}"

echo "--> Building Bongo Debian Package (${PKG_NAME}.deb)..."

# Clean prior build
rm -rf "${BUILD_ROOT}"
mkdir -p "${BUILD_ROOT}/DEBIAN"
mkdir -p "${DIST_DIR}"

# Run install.sh into DESTDIR
DESTDIR="${BUILD_ROOT}" PREFIX="/usr" bash "${SCRIPT_DIR}/install.sh"

# Create DEBIAN/control
cat <<EOF > "${BUILD_ROOT}/DEBIAN/control"
Package: bongo
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${DEB_ARCH}
Maintainer: Mehedi Shakeel <contact@getbongo.app>
Depends: ibus, python3, python3-gi, gir1.2-ibus-1.0, gir1.2-gtk-4.0 | gir1.2-gtk-3.0
Homepage: https://getbongo.app
Description: Native Avro phonetic Bengali typing for Linux
 Bongo brings fast, natural Avro phonetic Bengali typing to modern Linux desktops
 (GNOME, KDE Plasma, XFCE). Powered by a pure-Rust offline transliteration engine
 with full candidate suggestions and IBus integration.
EOF

# Create DEBIAN/postinst
cat <<'EOF' > "${BUILD_ROOT}/DEBIAN/postinst"
#!/bin/sh
set -e
if [ "$1" = "configure" ]; then
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
    fi
    if command -v ibus >/dev/null 2>&1; then
        ibus write-cache || true
    fi
fi
exit 0
EOF
chmod 755 "${BUILD_ROOT}/DEBIAN/postinst"

# Create DEBIAN/postrm
cat <<'EOF' > "${BUILD_ROOT}/DEBIAN/postrm"
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
    fi
    if command -v ibus >/dev/null 2>&1; then
        ibus write-cache || true
    fi
fi
exit 0
EOF
chmod 755 "${BUILD_ROOT}/DEBIAN/postrm"

# Build .deb archive
if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb --build --root-owner-group "${BUILD_ROOT}" "${DIST_DIR}/${PKG_NAME}.deb"
    echo "Successfully generated: ${DIST_DIR}/${PKG_NAME}.deb"
else
    echo "dpkg-deb not found. Staged tree is ready at ${BUILD_ROOT}"
fi
