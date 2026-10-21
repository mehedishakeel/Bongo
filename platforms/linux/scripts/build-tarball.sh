#!/usr/bin/env bash
#
# Build the universal Linux tarball for Bongo (x86_64).
#
# The archive contains a prebuilt payload and a self-contained installer, so it
# works on distributions that do not consume .deb or .rpm packages.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${LINUX_ROOT}/release"
VERSION="${VERSION:-1.0.1}"

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64|amd64) TARBALL_ARCH="x86_64" ;;
    *)
        echo "Error: the universal tarball is built for x86_64 only (got ${ARCH})." >&2
        exit 1
        ;;
esac

NAME="Bongo-${VERSION}-linux-${TARBALL_ARCH}"
BUILD_ROOT="${LINUX_ROOT}/build/tarball"
BUNDLE_DIR="${BUILD_ROOT}/${NAME}"
STAGE_DIR="${BUILD_ROOT}/stage"

echo "--> Building Bongo universal tarball (${NAME})..."

rm -rf "${BUILD_ROOT}"
mkdir -p "${BUNDLE_DIR}" "${DIST_DIR}"

# Stage the same system-wide tree the .deb ships.
DESTDIR="${STAGE_DIR}" PREFIX="/usr" \
    BONGO_FCITX5="${BONGO_FCITX5:-auto}" \
    bash "${SCRIPT_DIR}/install.sh" --no-configure-fcitx5

if [[ ! -d "${STAGE_DIR}/usr" ]]; then
    echo "Error: installer did not produce a staged tree." >&2
    exit 1
fi

cp -a "${STAGE_DIR}/usr" "${BUNDLE_DIR}/payload"

# fcitx5 discovers addons in a distribution-specific libdir (multiarch on
# Debian/Ubuntu, lib64 on Fedora, /usr/lib on Arch). Keep the addon separate
# and let the prebuilt installer place it in the target's own addon directory.
ADDON_SO="$(find "${BUNDLE_DIR}/payload" -type f \
    -path '*/fcitx5/libbongo.so' -print -quit)"
if [[ -n "${ADDON_SO}" ]]; then
    install -Dm755 "${ADDON_SO}" "${BUNDLE_DIR}/fcitx5/libbongo.so"
    rm -f "${ADDON_SO}"
    rmdir "$(dirname "${ADDON_SO}")" 2>/dev/null || true
fi

install -m 755 "${SCRIPT_DIR}/install.sh" "${BUNDLE_DIR}/install.sh"

cat > "${BUNDLE_DIR}/README.txt" <<EOF
Bongo ${VERSION} — universal Linux package (${TARBALL_ARCH})

Install system-wide:
  sudo bash install.sh --prebuilt

The installer detects GNOME (IBus) or KDE / Hyprland / Omarchy (fcitx5) and
enables Bongo automatically.

Requirements:
  - glibc 2.39 or newer (Ubuntu 24.04+, Debian 13+, Fedora 40+, Arch)
  - Python 3 with PyGObject and GTK 4 for bongo-settings
  - IBus or fcitx5 (the input framework your desktop already uses)

This archive contains prebuilt binaries; no compiler or network access is
needed. For Debian 12 / Ubuntu 22.04 or custom prefixes, use the source
installer from the repository instead.
EOF

(
    cd "${BUNDLE_DIR}"
    manifest_inputs=(payload install.sh README.txt)
    if [[ -d fcitx5 ]]; then
        manifest_inputs+=(fcitx5)
    fi
    find "${manifest_inputs[@]}" -type f -print0 |
        sort -z |
        xargs -0 sha256sum > MANIFEST.sha256
)

tar -C "${BUILD_ROOT}" -czf "${DIST_DIR}/${NAME}.tar.gz" "${NAME}"

echo "Successfully generated: ${DIST_DIR}/${NAME}.tar.gz"
