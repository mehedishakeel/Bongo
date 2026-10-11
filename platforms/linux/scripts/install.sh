#!/usr/bin/env bash
#
# Bongo Linux One-Command Installer
# Builds the native Rust engine and installs IBus component, GTK settings, and desktop integration.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${LINUX_ROOT}/../.." && pwd)"

PREFIX="${PREFIX:-/usr}"
DESTDIR="${DESTDIR:-}"

echo "=================================================="
echo "           Bongo Linux Installation               "
echo "=================================================="

# Check for Cargo / Rust
if ! command -v cargo >/dev/null 2>&1; then
    echo "Error: cargo (Rust package manager) is required to build Bongo." >&2
    echo "Install Rust via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh" >&2
    exit 1
fi

# Build native Rust engine
echo "--> Building native engine (libbongo_engine.so)..."
cd "${LINUX_ROOT}/engine"
cargo build --release

LIB_TARGET="${LINUX_ROOT}/engine/target/release/libbongo_engine.so"
if [[ ! -f "${LIB_TARGET}" ]]; then
    echo "Error: ${LIB_TARGET} not found." >&2
    exit 1
fi

echo "--> Installing components to ${DESTDIR}${PREFIX}..."

# 1. Install library
install -d "${DESTDIR}${PREFIX}/lib/bongo"
install -m 755 "${LIB_TARGET}" "${DESTDIR}${PREFIX}/lib/bongo/libbongo_engine.so"

# 2. Install IBus engine daemon
install -d "${DESTDIR}${PREFIX}/libexec"
install -m 755 "${LINUX_ROOT}/ibus/bongo_ibus_engine.py" "${DESTDIR}${PREFIX}/libexec/bongo-ibus-engine"

# 3. Install IBus component XML
install -d "${DESTDIR}${PREFIX}/share/ibus/component"
install -m 644 "${LINUX_ROOT}/ibus/bongo.xml" "${DESTDIR}${PREFIX}/share/ibus/component/bongo.xml"

# 4. Install GTK Settings & Welcome app
install -d "${DESTDIR}${PREFIX}/bin"
install -m 755 "${LINUX_ROOT}/ui/bongo_settings.py" "${DESTDIR}${PREFIX}/bin/bongo-settings"

# 5. Install Desktop entry
install -d "${DESTDIR}${PREFIX}/share/applications"
install -m 644 "${LINUX_ROOT}/data/app.getbongo.Bongo.desktop" "${DESTDIR}${PREFIX}/share/applications/app.getbongo.Bongo.desktop"

# 6. Install AppStream metadata
install -d "${DESTDIR}${PREFIX}/share/metainfo"
install -m 644 "${LINUX_ROOT}/data/app.getbongo.Bongo.metainfo.xml" "${DESTDIR}${PREFIX}/share/metainfo/app.getbongo.Bongo.metainfo.xml"

# 7. Install Icons
for size in 16 32 48 64 128 256 512; do
    ICON_SRC="${LINUX_ROOT}/data/icons/hicolor/${size}x${size}/apps/bongo.png"
    if [[ -f "${ICON_SRC}" ]]; then
        install -d "${DESTDIR}${PREFIX}/share/icons/hicolor/${size}x${size}/apps"
        install -m 644 "${ICON_SRC}" "${DESTDIR}${PREFIX}/share/icons/hicolor/${size}x${size}/apps/bongo.png"
    fi
done

# Update system caches if running on live system (not packaging)
if [[ -z "${DESTDIR}" ]]; then
    echo "--> Updating desktop and icon caches..."
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "${PREFIX}/share/applications" || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "${PREFIX}/share/icons/hicolor" || true
    fi

    # Restart IBus daemon if running
    if command -v ibus >/dev/null 2>&1; then
        echo "--> Refreshing IBus component registry..."
        ibus write-cache || true
        ibus restart || true
    fi
fi

echo "=================================================="
echo "   Bongo has been successfully installed!        "
echo "=================================================="
echo ""
echo "Next Steps:"
echo "1. Open GNOME / KDE Settings -> Keyboard -> Input Sources."
echo "2. Add 'Bengali (Bongo)' to your active keyboards."
echo "3. Switch keyboards anytime with Super + Space or Control + Space."
echo "4. Launch 'bongo-settings' to customize typing modes and fonts."
echo ""
