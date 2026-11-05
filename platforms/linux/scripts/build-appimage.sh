#!/usr/bin/env bash
#
# Build the standalone Bongo AppImage for Linux (x86_64 and aarch64).
#
# Packages Bongo Settings & IBus/Fcitx5 components into a single executable AppImage
# tailored for standard distributions and immutable operating systems (e.g., SteamOS,
# Bazzite, Fedora Silverblue).
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${LINUX_ROOT}/release"
VERSION="${VERSION:-1.2.0}"

ARCH="$(uname -m)"
case "${ARCH}" in
    x86_64|amd64) TARBALL_ARCH="x86_64" ;;
    aarch64|arm64) TARBALL_ARCH="aarch64" ;;
    *)
        echo "Error: unsupported architecture for AppImage: ${ARCH}." >&2
        exit 1
        ;;
esac

NAME="Bongo-${VERSION}-linux-${TARBALL_ARCH}"
TARBALL="${DIST_DIR}/${NAME}.tar.gz"
BUILD_ROOT="${LINUX_ROOT}/build/appimage"
APPDIR="${BUILD_ROOT}/AppDir"
OUTPUT_APPIMAGE="${DIST_DIR}/${NAME}.AppImage"

echo "--> Building Bongo AppImage (${NAME}.AppImage)..."

# Ensure prebuilt tarball exists or build it
if [[ ! -f "${TARBALL}" ]]; then
    echo "--> Universal tarball not found; building it first..."
    VERSION="${VERSION}" bash "${SCRIPT_DIR}/build-tarball.sh"
fi

rm -rf "${BUILD_ROOT}"
mkdir -p "${APPDIR}" "${DIST_DIR}"

# Extract prebuilt bundle
TMP_EXTRACT="${BUILD_ROOT}/extracted"
mkdir -p "${TMP_EXTRACT}"
tar -xzf "${TARBALL}" -C "${TMP_EXTRACT}"
BUNDLE_DIR="${TMP_EXTRACT}/${NAME}"

# Populate AppDir
mkdir -p "${APPDIR}/usr"
cp -a "${BUNDLE_DIR}/payload/." "${APPDIR}/usr/"

# Copy desktop file and icons to top-level of AppDir
cp "${APPDIR}/usr/share/applications/app.getbongo.Bongo.desktop" "${APPDIR}/"
cp "${APPDIR}/usr/share/pixmaps/bongo.png" "${APPDIR}/"
ln -sf bongo.png "${APPDIR}/.DirIcon"

# Embed installer & payload for rootless / immutable installs
cp -a "${BUNDLE_DIR}/payload" "${APPDIR}/"
cp -a "${BUNDLE_DIR}/install.sh" "${APPDIR}/"
if [[ -d "${BUNDLE_DIR}/fcitx5" ]]; then
    cp -a "${BUNDLE_DIR}/fcitx5" "${APPDIR}/"
    mkdir -p "${APPDIR}/usr/lib/fcitx5"
    cp -a "${BUNDLE_DIR}/fcitx5/libbongo.so" "${APPDIR}/usr/lib/fcitx5/"
fi

# Write AppRun dispatcher
cat > "${APPDIR}/AppRun" << 'EOF'
#!/usr/bin/env bash
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"

case "${1:-}" in
    --install|--install-user)
        echo "--> Installing Bongo to $HOME/.local (rootless / immutable install)..."
        DESTDIR="" PREFIX="$HOME/.local" PREBUILT=true bash "$HERE/install.sh" --prebuilt --user "${@:2}"
        echo ""
        echo ":: Bongo installed successfully to $HOME/.local"
        echo "   * GNOME (IBus): Add 'Bangla (Bongo)' in Settings -> Keyboard -> Input Sources."
        echo "   * KDE / Hyprland (Fcitx5): Bongo has been added to your profile. Restart fcitx5 if needed."
        exit 0
        ;;
    --uninstall)
        echo "--> Uninstalling Bongo from $HOME/.local..."
        DESTDIR="" PREFIX="$HOME/.local" UNINSTALL=true bash "$HERE/install.sh" --uninstall --user "${@:2}"
        echo ":: Bongo uninstalled from $HOME/.local"
        exit 0
        ;;
    --status)
        echo "Bongo Installation Status:"
        if [[ -f "$HOME/.local/lib/bongo/libbongo_engine.so" ]]; then
            echo "  User install (~/.local):  INSTALLED"
        else
            echo "  User install (~/.local):  NOT INSTALLED"
        fi
        if [[ -f "/usr/lib/bongo/libbongo_engine.so" ]]; then
            echo "  System install (/usr):    INSTALLED"
        else
            echo "  System install (/usr):    NOT INSTALLED"
        fi
        exit 0
        ;;
    -h|--help)
        echo "Bongo AppImage"
        echo "Usage: $(basename "$0") [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  (no args)       Launch Bongo Settings & Layout UI"
        echo "  --install-user  Install Bongo IME & Settings into ~/.local (for SteamOS, Bazzite, Silverblue)"
        echo "  --uninstall     Uninstall Bongo from ~/.local"
        echo "  --status        Show Bongo installation status"
        echo "  -h, --help      Show this help message"
        exit 0
        ;;
esac

# Default execution: Launch Bongo Settings
export PATH="$HERE/usr/bin:$PATH"
export XDG_DATA_DIRS="$HERE/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/bongo:${LD_LIBRARY_PATH:-}"

if [[ ! -f "$HOME/.local/lib/bongo/libbongo_engine.so" && ! -f "/usr/lib/bongo/libbongo_engine.so" ]]; then
    echo "Notice: Bongo input method engine is not yet installed." >&2
    echo "        To install into ~/.local on SteamOS, Bazzite, or Fedora Silverblue," >&2
    echo "        run: $(basename "$0") --install-user" >&2
fi

exec "$HERE/usr/bin/bongo-settings" "$@"
EOF

chmod +x "${APPDIR}/AppRun"

echo "--> AppDir assembled at ${APPDIR}"

# Locate or download appimagetool if running on Linux
if [[ "$(uname -s)" == "Linux" ]]; then
    APPIMAGETOOL=""
    if command -v appimagetool >/dev/null 2>&1; then
        APPIMAGETOOL="appimagetool"
    elif [[ -x "${BUILD_ROOT}/appimagetool" ]]; then
        APPIMAGETOOL="${BUILD_ROOT}/appimagetool"
    elif [[ -x "${LINUX_ROOT}/build/appimagetool" ]]; then
        APPIMAGETOOL="${LINUX_ROOT}/build/appimagetool"
    fi

    if [[ -z "${APPIMAGETOOL}" ]]; then
        TOOL_ARCH="${TARBALL_ARCH}"
        TOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/13/appimagetool-${TOOL_ARCH}.AppImage"
        echo "--> Downloading appimagetool from ${TOOL_URL}..."
        mkdir -p "${BUILD_ROOT}/tool"
        if curl -fsSL -o "${BUILD_ROOT}/tool/appimagetool" "${TOOL_URL}" 2>/dev/null; then
            chmod +x "${BUILD_ROOT}/tool/appimagetool"
            # Extract appimagetool to bypass requirement for libfuse2 on Ubuntu 24.04+
            (
                cd "${BUILD_ROOT}/tool"
                ./appimagetool --appimage-extract >/dev/null 2>&1
            )
            APPIMAGETOOL="${BUILD_ROOT}/tool/squashfs-root/AppRun"
        fi
    fi

    if [[ -n "${APPIMAGETOOL}" && -x "${APPIMAGETOOL}" ]]; then
        echo "--> Generating AppImage with appimagetool..."
        ARCH="${TARBALL_ARCH}" "${APPIMAGETOOL}" "${APPDIR}" "${OUTPUT_APPIMAGE}"
        if [[ -f "${OUTPUT_APPIMAGE}" ]]; then
            chmod +x "${OUTPUT_APPIMAGE}"
            echo "--> Successfully generated: ${OUTPUT_APPIMAGE}"
            (
                cd "${DIST_DIR}"
                sha256sum "$(basename "${OUTPUT_APPIMAGE}")" > "$(basename "${OUTPUT_APPIMAGE}").sha256"
            )
        else
            echo "Error: appimagetool failed to create ${OUTPUT_APPIMAGE}." >&2
            exit 1
        fi
    else
        echo "Warning: appimagetool not available; AppDir preserved at ${APPDIR}." >&2
    fi
else
    echo "Note: AppImage generation skipped on non-Linux host ($(uname -s)). AppDir is ready at ${APPDIR}."
fi
