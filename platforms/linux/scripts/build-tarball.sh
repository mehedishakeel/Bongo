#!/usr/bin/env bash
#
# Build the universal Linux tarball for Bongo (x86_64 and aarch64).
#
# The archive contains a prebuilt payload and a self-contained installer, so it
# works on distributions that do not consume .deb or .rpm packages. Run this on
# the architecture you are packaging; the release workflow does both natively.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${LINUX_ROOT}/release"
VERSION="${VERSION:-1.1.0}"

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64|amd64) TARBALL_ARCH="x86_64" ;;
    aarch64|arm64) TARBALL_ARCH="aarch64" ;;
    *)
        echo "Error: unsupported architecture for the universal tarball: ${ARCH}." >&2
        exit 1
        ;;
esac

# The release tarball must ship the fcitx5 frontend; a silent omission would
# produce an archive that looks complete but cannot type on KDE/Hyprland.
BONGO_FCITX5="${BONGO_FCITX5:-1}"

NAME="Bongo-${VERSION}-linux-${TARBALL_ARCH}"
BUILD_ROOT="${LINUX_ROOT}/build/tarball"
BUNDLE_DIR="${BUILD_ROOT}/${NAME}"
STAGE_DIR="${BUILD_ROOT}/stage"

echo "--> Building Bongo universal tarball (${NAME})..."

rm -rf "${BUILD_ROOT}"
mkdir -p "${BUNDLE_DIR}" "${DIST_DIR}"

# Stage the same system-wide tree the .deb ships.
DESTDIR="${STAGE_DIR}" PREFIX="/usr" \
    BONGO_FCITX5="${BONGO_FCITX5}" \
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
elif [[ "${BONGO_FCITX5}" == "0" ]]; then
    echo "Warning: building without the fcitx5 addon because BONGO_FCITX5=0." >&2
else
    echo "Error: fcitx5 addon missing from the staged payload." >&2
    echo "Install fcitx5 development headers or set BONGO_FCITX5=0 explicitly." >&2
    exit 1
fi

install -m 755 "${SCRIPT_DIR}/install.sh" "${BUNDLE_DIR}/install.sh"
printf '%s\n' "${TARBALL_ARCH}" > "${BUNDLE_DIR}/ARCH"

cat > "${BUNDLE_DIR}/README.txt" <<EOF
Bongo ${VERSION} — universal Linux package (${TARBALL_ARCH})

Install system-wide:
  sudo bash install.sh --prebuilt

Uninstall (from this extracted directory):
  sudo bash install.sh --uninstall

The installer detects GNOME (IBus) or KDE / Hyprland / Omarchy (fcitx5) and
enables Bongo automatically. It verifies MANIFEST.sha256 before copying files.

Requirements:
  - glibc 2.39 or newer (Ubuntu 24.04+, Debian 13+, Fedora 40+, Arch)
  - Python 3 with PyGObject and GTK 4 for bongo-settings
  - IBus or fcitx5 (the input framework your desktop already uses)

This archive contains prebuilt binaries for ${TARBALL_ARCH}; no compiler or
network access is needed. For Debian 12 / Ubuntu 22.04 or custom prefixes, use
the source installer from the repository instead.
EOF

(
    cd "${BUNDLE_DIR}"
    manifest_inputs=(payload install.sh README.txt ARCH)
    if [[ -d fcitx5 ]]; then
        manifest_inputs+=(fcitx5)
    fi
    find "${manifest_inputs[@]}" -type f -print0 |
        sort -z |
        xargs -0 sha256sum > MANIFEST.sha256
)

tar -C "${BUILD_ROOT}" \
    --owner=0 --group=0 --numeric-owner --sort=name \
    -czf "${DIST_DIR}/${NAME}.tar.gz" "${NAME}"

echo "Successfully generated: ${DIST_DIR}/${NAME}.tar.gz"
