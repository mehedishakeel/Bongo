#!/usr/bin/env bash
#
# Bongo Linux One-Command Installer
# Supports one-line pipe installation via curl (installs prebuilt deb package or builds from source),
# as well as local in-tree compilation and installation.
#

set -euo pipefail

SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]:-}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd || true)"
fi

# Detect whether running locally inside cloned repository
IS_LOCAL=false
if [[ -n "${SCRIPT_DIR}" && -f "${SCRIPT_DIR}/../ibus/bongo.xml" ]]; then
    IS_LOCAL=true
fi

# Describes the desktop user the installer configures input methods for.
SUDO_HOME=""
if [[ -n "${SUDO_USER:-}" ]]; then
    SUDO_HOME="$(getent passwd "${SUDO_USER}" 2>/dev/null | cut -d: -f6 || true)"
fi

TARGET_USER_NAME="$(id -un)"
TARGET_USER_ID="$(id -u)"
TARGET_HOME="${HOME}"
if [[ $EUID -eq 0 && -n "${SUDO_USER:-}" ]]; then
    TARGET_USER_NAME="${SUDO_USER}"
    TARGET_USER_ID="$(id -u "${SUDO_USER}")"
    if [[ -n "${SUDO_HOME}" ]]; then
        TARGET_HOME="${SUDO_HOME}"
    fi
fi
TARGET_USER_GID="$(id -g "${TARGET_USER_NAME}" 2>/dev/null || id -g)"

# Run a command inside the desktop user's session (DBus, XDG runtime dir) so
# gsettings, ibus and systemctl --user talk to that session instead of root's.
bongo_as_user() {
    if [[ $EUID -eq 0 && -n "${SUDO_USER:-}" ]] && command -v runuser >/dev/null 2>&1; then
        runuser -u "${SUDO_USER}" -- env \
            "HOME=${TARGET_HOME}" \
            "XDG_RUNTIME_DIR=/run/user/${TARGET_USER_ID}" \
            "DBUS_SESSION_BUS_ADDRESS=/run/user/${TARGET_USER_ID}/bus" \
            "$@"
    else
        "$@"
    fi
}

# Returns 1 when pgrep is unavailable, so detection degrades safely.
bongo_pgrep_user() {
    command -v pgrep >/dev/null 2>&1 || return 1
    pgrep -u "${TARGET_USER_ID}" -x "$1" >/dev/null 2>&1
}

# Detect the desktop that is actually running so Bongo is enabled in the
# input-method framework that desktop uses: GNOME uses IBus, everything else
# (KDE, Hyprland, other Wayland compositors) uses native fcitx5. Process
# detection is more reliable than XDG_CURRENT_DESKTOP, which sudo/pkexec
# usually drop and which uwsm sessions may leave empty.
DESKTOP_KIND="unknown"
if bongo_pgrep_user gnome-shell; then
    DESKTOP_KIND="gnome"
elif bongo_pgrep_user plasmashell; then
    DESKTOP_KIND="kde"
elif bongo_pgrep_user Hyprland || bongo_pgrep_user sway || \
     bongo_pgrep_user river || bongo_pgrep_user wayfire || \
     bongo_pgrep_user labwc; then
    DESKTOP_KIND="wlwm"
elif [[ "${XDG_CURRENT_DESKTOP:-}" == *GNOME* ]]; then
    DESKTOP_KIND="gnome"
elif [[ "${XDG_CURRENT_DESKTOP:-}" == *KDE* ]]; then
    DESKTOP_KIND="kde"
fi

# Print a GNOME input-sources value with Bongo appended. Kept pure so the
# distribution tests can exercise the merge without a GNOME session.
bongo_ibus_add_source() {
    local current="$1"
    local updated="${current%]}"
    if [[ "${updated}" == *"("* ]]; then
        updated="${updated}, "
    fi
    printf '%s' "${updated}('ibus', 'bongo')]"
}

# Add Bongo to the desktop user's GNOME input sources when GNOME is in use.
# Existing sources are preserved and the previous value is printed.
bongo_enable_gnome_source() {
    command -v gsettings >/dev/null 2>&1 || return 0
    local current updated
    current="$(bongo_as_user gsettings get \
        org.gnome.desktop.input-sources sources 2>/dev/null || true)"
    [[ -n "${current}" ]] || return 0
    if [[ "${current}" == *"'bongo'"* ]]; then
        IBUS_SOURCE_ENABLED=true
        echo "--> Bongo is already in the GNOME input sources."
        return 0
    fi
    updated="$(bongo_ibus_add_source "${current}")"
    if bongo_as_user gsettings set \
        org.gnome.desktop.input-sources sources "${updated}"; then
        IBUS_SOURCE_ENABLED=true
        echo "--> Added Bongo to the GNOME input sources."
        echo "    (previous sources: ${current})"
    fi
}

IBUS_SOURCE_ENABLED=false

# ========================================================
# Remote Mode (e.g. curl -sSL ... | bash)
# ========================================================
if [[ "${IS_LOCAL}" != "true" ]]; then
    echo "=================================================="
    echo "           Bongo Linux Installation               "
    echo "=================================================="

    ARCH="$(uname -m)"
    case "${ARCH}" in
        x86_64|amd64)
            DEB_ARCH="amd64"
            ;;
        aarch64|arm64)
            DEB_ARCH="arm64"
            ;;
        *)
            echo "Error: Unsupported CPU architecture: ${ARCH}" >&2
            exit 1
            ;;
    esac

    # Determine sudo prefix if not root
    SUDO=""
    if [[ $EUID -ne 0 ]]; then
        if command -v sudo >/dev/null 2>&1; then
            echo "--> Verifying sudo credentials for system-wide installation..."
            if [ -t 0 ]; then
                sudo -v
            elif [ -r /dev/tty ]; then
                sudo -v </dev/tty
            else
                sudo -v
            fi
            SUDO="sudo"
        else
            echo "Error: Root privileges or sudo required to install Bongo." >&2
            exit 1
        fi
    fi

    # On Debian/Ubuntu/Mint/Pop!_OS: install official prebuilt .deb package
    if command -v apt-get >/dev/null 2>&1 || command -v apt >/dev/null 2>&1 || command -v dpkg >/dev/null 2>&1; then
        echo "--> Detected Debian / Ubuntu based system (${DEB_ARCH})"
        TMP_DEB="/tmp/bongo_${DEB_ARCH}.deb"
        DEB_URL="https://github.com/mehedishakeel/Bongo/releases/latest/download/bongo_1.0.1_${DEB_ARCH}.deb"
        FALLBACK_URL="https://github.com/mehedishakeel/Bongo/releases/download/v1.0.1/bongo_1.0.1_${DEB_ARCH}.deb"

        DOWNLOADED=false
        echo "--> Downloading ${DEB_URL}..."
        if curl -sSL -f -o "${TMP_DEB}" "${DEB_URL}"; then
            DOWNLOADED=true
        elif curl -sSL -f -o "${TMP_DEB}" "${FALLBACK_URL}"; then
            DOWNLOADED=true
        fi

        if [[ "${DOWNLOADED}" == "true" && -s "${TMP_DEB}" ]]; then
            echo "--> Installing Bongo and resolving dependencies..."
            INSTALLED=false
            if command -v apt >/dev/null 2>&1; then
                ${SUDO} apt update -qq || true
                if ${SUDO} apt install -y "${TMP_DEB}"; then
                    INSTALLED=true
                fi
            fi

            if [[ "${INSTALLED}" != "true" ]]; then
                echo "--> Installing via dpkg and fixing dependencies..."
                ${SUDO} dpkg -i "${TMP_DEB}" || true
                if command -v apt-get >/dev/null 2>&1; then
                    ${SUDO} apt-get install -f -y || true
                fi
            fi
            rm -f "${TMP_DEB}"

            if command -v ibus >/dev/null 2>&1; then
                echo "--> Refreshing IBus component registry..."
                bongo_as_user ibus write-cache 2>/dev/null || true
                bongo_as_user ibus restart 2>/dev/null || true
            fi
            if [[ "${DESKTOP_KIND}" == "gnome" ]]; then
                bongo_enable_gnome_source || true
            fi

            echo "=================================================="
            echo "   Bongo has been successfully installed!        "
            echo "=================================================="
            echo ""
            echo "Next Steps:"
            if [[ "${IBUS_SOURCE_ENABLED}" == "true" ]]; then
                echo "1. Bongo has been added to your input sources."
                echo "2. Switch input methods with Super + Space."
                echo "3. If it is missing, open GNOME Settings -> Keyboard -> Input Sources."
            else
                echo "1. Open GNOME / KDE Settings -> Keyboard -> Input Sources."
                echo "2. Add 'Bengali (Bongo)' to your active keyboards."
                echo "3. Switch keyboards anytime with Super + Space or Control + Space."
            fi
            echo "4. Launch 'bongo-settings' to customize typing modes and fonts."
            echo ""
            exit 0
        else
            echo "--> Prebuilt .deb package unavailable. Proceeding to source build..."
        fi
    fi

    # Prepare package managers on other distributions
    if command -v dnf >/dev/null 2>&1; then
        echo "--> Detected Fedora / RHEL system (${ARCH})"
        echo "--> Ensuring build dependencies are installed via dnf..."
        ${SUDO} dnf install -y cargo rust ibus ibus-devel python3 python3-gobject gtk4 tar git || true
    elif command -v pacman >/dev/null 2>&1; then
        echo "--> Detected Arch Linux system (${ARCH})"
        echo "--> Ensuring build dependencies are installed via pacman..."
        ${SUDO} pacman -S --needed --noconfirm rust cargo ibus python-gobject gtk4 tar git || true
    fi

    # On non-Debian distributions or fallback: clone/extract source and run installer
    echo "--> Installing Bongo from source (${ARCH})..."
    TMP_SRC="$(mktemp -d /tmp/bongo-src-XXXXXX)"
    if command -v git >/dev/null 2>&1; then
        git clone --depth=1 https://github.com/mehedishakeel/Bongo.git "${TMP_SRC}"
    else
        echo "--> Downloading source archive..."
        curl -sSL https://github.com/mehedishakeel/Bongo/archive/refs/heads/main.tar.gz | tar -xz -C "${TMP_SRC}" --strip-components=1
    fi
    bash "${TMP_SRC}/platforms/linux/scripts/install.sh"
    rm -rf "${TMP_SRC}"
    exit 0
fi

# ========================================================
# Local In-Tree Build & Install Mode
# ========================================================
LINUX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${LINUX_ROOT}/../.." && pwd)"

BONGO_FCITX5="${BONGO_FCITX5:-auto}"
CONFIGURE_FCITX5=true
for arg in "$@"; do
    case "${arg}" in
        --no-configure-fcitx5)
            CONFIGURE_FCITX5=false
            ;;
        --configure-fcitx5)
            CONFIGURE_FCITX5=true
            ;;
        -h|--help)
            echo "Usage: install.sh [--no-configure-fcitx5]"
            echo "Environment: BONGO_FCITX5=auto|1|0 PREFIX=... DESTDIR=..."
            exit 0
            ;;
        *)
            echo "Unknown option: ${arg}" >&2
            exit 1
            ;;
    esac
done

case "${BONGO_FCITX5}" in
    1|true|yes) BONGO_FCITX5=1 ;;
    0|false|no) BONGO_FCITX5=0 ;;
    auto) ;;
    *)
        echo "Error: BONGO_FCITX5 must be auto, 1, or 0." >&2
        exit 1
        ;;
esac

PREFIX="${PREFIX:-/usr}"
DESTDIR="${DESTDIR:-}"

# If running as non-root and PREFIX was not explicitly changed, install to ~/.local
if [[ $EUID -ne 0 && "${PREFIX}" == "/usr" && -z "${DESTDIR}" ]]; then
    PREFIX="${HOME}/.local"
fi

echo "=================================================="
echo "           Bongo Linux Installation               "
echo "=================================================="

# Locate Cargo / Rust. When the installer runs through sudo, prefer building as
# the invoking user so a rustup installation in their home directory works and
# build artifacts stay user-owned. SUDO_HOME was resolved above.

CARGO_CMD=(cargo)
if [[ $EUID -eq 0 && -n "${SUDO_HOME}" && -x "${SUDO_HOME}/.cargo/bin/cargo" ]] && \
   command -v runuser >/dev/null 2>&1; then
    CARGO_CMD=(
        runuser -u "${SUDO_USER}" -- env
        "HOME=${SUDO_HOME}"
        "PATH=${SUDO_HOME}/.cargo/bin:${PATH}"
        cargo
    )
elif ! command -v cargo >/dev/null 2>&1; then
    if [[ -n "${SUDO_HOME}" && -x "${SUDO_HOME}/.cargo/bin/cargo" ]]; then
        export PATH="${SUDO_HOME}/.cargo/bin:${PATH}"
        export RUSTUP_HOME="${RUSTUP_HOME:-${SUDO_HOME}/.rustup}"
        export CARGO_HOME="${CARGO_HOME:-${SUDO_HOME}/.cargo}"
    elif [[ -x "${HOME}/.cargo/bin/cargo" ]]; then
        export PATH="${HOME}/.cargo/bin:${PATH}"
    fi
fi

if [[ "${CARGO_CMD[0]}" == "cargo" ]] && ! command -v cargo >/dev/null 2>&1; then
    echo "Error: cargo (Rust package manager) is required to build Bongo." >&2
    echo "Install Rust via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh" >&2
    echo "Or on Ubuntu/Debian: sudo apt install -y cargo rustc" >&2
    exit 1
fi

HAS_IBUS=false
if command -v ibus >/dev/null 2>&1; then
    HAS_IBUS=true
fi

HAS_FCITX5_RUNTIME=false
if command -v fcitx5 >/dev/null 2>&1; then
    HAS_FCITX5_RUNTIME=true
fi

HAS_FCITX5_HEADERS=false
if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists Fcitx5Core 2>/dev/null; then
    HAS_FCITX5_HEADERS=true
fi

if [[ "${HAS_IBUS}" != "true" && "${HAS_FCITX5_RUNTIME}" != "true" ]]; then
    echo "Error: neither IBus nor fcitx5 was detected." >&2
    echo "Install one of them, for example:" >&2
    echo "  Ubuntu/Debian: sudo apt install -y ibus fcitx5 fcitx5-configtool" >&2
    echo "  Arch:          sudo pacman -S ibus fcitx5 fcitx5-configtool" >&2
    echo "  Fedora:        sudo dnf install -y ibus fcitx5 fcitx5-configtool" >&2
    exit 1
fi

# Two enablement groups:
#   ibus   - GNOME (Bongo is added as an IBus input source)
#   fcitx5 - KDE, tiling Wayland compositors and everything else
# The group follows the running desktop first and falls back to whichever
# framework is installed when no desktop session is visible (e.g. SSH).
IM_FRAMEWORK=""
if [[ "${DESKTOP_KIND}" == "gnome" ]]; then
    IM_FRAMEWORK="ibus"
elif [[ "${DESKTOP_KIND}" == "kde" || "${DESKTOP_KIND}" == "wlwm" ]]; then
    IM_FRAMEWORK="fcitx5"
elif [[ "${HAS_FCITX5_RUNTIME}" == "true" ]]; then
    IM_FRAMEWORK="fcitx5"
elif [[ "${HAS_IBUS}" == "true" ]]; then
    IM_FRAMEWORK="ibus"
fi

if [[ "${HAS_IBUS}" != "true" ]]; then
    echo "Warning: IBus was not detected; GNOME users need IBus." >&2
    echo "The fcitx5 frontend will still be installed when its headers are available." >&2
fi

BUILD_FCITX5=false
case "${BONGO_FCITX5}" in
    1)
        if [[ "${HAS_FCITX5_HEADERS}" != "true" ]]; then
            echo "Error: BONGO_FCITX5=1 but fcitx5 development headers were not found." >&2
            echo "Install the fcitx5 development package (for example libfcitx5core-dev, fcitx5-devel, or fcitx5)." >&2
            exit 1
        fi
        BUILD_FCITX5=true
        ;;
    auto)
        if [[ "${HAS_FCITX5_HEADERS}" == "true" ]] && \
           { [[ "${HAS_FCITX5_RUNTIME}" == "true" ]] || [[ -n "${DESTDIR}" ]]; }; then
            BUILD_FCITX5=true
        fi
        ;;
esac

FCITX5_SYSTEM_INSTALL=false
if [[ "${BUILD_FCITX5}" == "true" ]]; then
    if [[ -n "${DESTDIR}" || ( $EUID -eq 0 && "${PREFIX}" == "/usr" ) ]]; then
        FCITX5_SYSTEM_INSTALL=true
    fi
fi

LIB_TARGET="${BONGO_LIB_TARGET:-${LINUX_ROOT}/engine/target/release/libbongo_engine.so}"
if [[ ! -f "${LIB_TARGET}" ]]; then
    echo "--> Building native engine (libbongo_engine.so)..."
    cd "${LINUX_ROOT}/engine"
    "${CARGO_CMD[@]}" build --release
fi

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
if [[ -z "${DESTDIR}" && "${PREFIX}" != "/usr" ]]; then
    sed -e "s|/usr/libexec/bongo-ibus-engine|${PREFIX}/libexec/bongo-ibus-engine|g" \
        -e "s|/usr/bin/bongo-settings|${PREFIX}/bin/bongo-settings|g" \
        -e "s|/usr/share/|${PREFIX}/share/|g" \
        "${LINUX_ROOT}/ibus/bongo.xml" > "${DESTDIR}${PREFIX}/share/ibus/component/bongo.xml"
    chmod 644 "${DESTDIR}${PREFIX}/share/ibus/component/bongo.xml"
else
    install -m 644 "${LINUX_ROOT}/ibus/bongo.xml" "${DESTDIR}${PREFIX}/share/ibus/component/bongo.xml"
fi

# 4. Install GTK Settings & Welcome app
chmod +x "${LINUX_ROOT}/ui/bongo_settings.py"
install -d "${DESTDIR}${PREFIX}/bin"
install -m 755 "${LINUX_ROOT}/ui/bongo_settings.py" "${DESTDIR}${PREFIX}/bin/bongo-settings"

# 5. Install fcitx5 profile helper
install -m 755 "${SCRIPT_DIR}/configure-fcitx5.py" "${DESTDIR}${PREFIX}/bin/bongo-fcitx5-setup"

# 6. Install Desktop entry
install -d "${DESTDIR}${PREFIX}/share/applications"
if [[ -z "${DESTDIR}" && "${PREFIX}" != "/usr" ]]; then
    sed "s|^Exec=bongo-settings|Exec=${PREFIX}/bin/bongo-settings|" "${LINUX_ROOT}/data/app.getbongo.Bongo.desktop" > "${DESTDIR}${PREFIX}/share/applications/app.getbongo.Bongo.desktop"
    chmod 644 "${DESTDIR}${PREFIX}/share/applications/app.getbongo.Bongo.desktop"
else
    install -m 644 "${LINUX_ROOT}/data/app.getbongo.Bongo.desktop" "${DESTDIR}${PREFIX}/share/applications/app.getbongo.Bongo.desktop"
fi

# Remove legacy duplicate launcher (installed by older versions) that caused
# Bongo to appear twice in application menus
if [[ -z "${DESTDIR}" ]]; then
    rm -f "${PREFIX}/share/applications/bongo.desktop" 2>/dev/null || true
fi

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

# Install pixmaps fallback
install -d "${DESTDIR}${PREFIX}/share/pixmaps"
install -m 644 "${LINUX_ROOT}/data/icons/bongo.png" "${DESTDIR}${PREFIX}/share/pixmaps/bongo.png"

# 9. Build and install the fcitx5 addon.
# fcitx5 only discovers addons from its system addon directory, so a local
# ~/.local install is intentionally skipped and the sudo command is printed.
if [[ "${BUILD_FCITX5}" == "true" ]]; then
    if [[ "${FCITX5_SYSTEM_INSTALL}" == "true" ]]; then
        if ! command -v cmake >/dev/null 2>&1; then
            echo "Error: cmake is required to build the fcitx5 addon." >&2
            exit 1
        fi

        echo "--> Building fcitx5 addon..."
        FCITX5_BUILD_DIR="${LINUX_ROOT}/build/fcitx5"
        CMAKE_ARGS=(
            -S "${LINUX_ROOT}/fcitx5"
            -B "${FCITX5_BUILD_DIR}"
            -DCMAKE_BUILD_TYPE=Release
            -DCMAKE_INSTALL_PREFIX="${PREFIX}"
            -DBUILD_TESTING=OFF
            -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON
        )
        fcitx5_libdir=""
        if command -v pkg-config >/dev/null 2>&1; then
            fcitx5_libdir="$(pkg-config --variable=libdir Fcitx5Core 2>/dev/null || true)"
        fi
        # fcitx5 discovers addons from its compiled-in addon directory, which
        # differs per distribution: /usr/lib/fcitx5 on Arch, lib64 on Fedora,
        # and the multiarch lib dir on Debian/Ubuntu. Derive it from the
        # installed Fcitx5Core package instead of trusting macro defaults.
        if [[ -n "${fcitx5_libdir}" && "${fcitx5_libdir}" == /* ]]; then
            fcitx5_libdir_rel="${fcitx5_libdir#"/usr/"}"
            FCITX5_ADDONDIR="${fcitx5_libdir}/fcitx5"
            CMAKE_ARGS+=(
                -DFCITX_INSTALL_USE_FCITX_SYS_PATHS=OFF
                -DCMAKE_INSTALL_LIBDIR="${fcitx5_libdir_rel}"
            )
        else
            FCITX5_ADDONDIR="${PREFIX}/lib/fcitx5"
        fi
        echo "    fcitx5 addon directory: ${FCITX5_ADDONDIR}"
        if command -v ninja >/dev/null 2>&1; then
            CMAKE_ARGS+=(-G Ninja)
        fi
        cmake "${CMAKE_ARGS[@]}"
        cmake --build "${FCITX5_BUILD_DIR}" --parallel
        DESTDIR="${DESTDIR}" cmake --install "${FCITX5_BUILD_DIR}"
    else
        echo "--> Skipping the fcitx5 addon: it must be installed system-wide."
        echo "    Run this command from the Bongo checkout:"
        echo "    sudo BONGO_FCITX5=1 bash ${SCRIPT_DIR}/install.sh"
    fi
elif [[ "${BONGO_FCITX5}" == "1" ]]; then
    echo "Error: fcitx5 was requested but cannot be built." >&2
    exit 1
fi

# Update system caches if running on live system
if [[ -z "${DESTDIR}" ]]; then
    echo "--> Updating desktop and icon caches..."
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "${PREFIX}/share/applications" || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "${PREFIX}/share/icons/hicolor" || true
    fi

    # Ensure ~/.local/bin is in PATH for shell sessions
    if [[ "${PREFIX}" == "${HOME}/.local" ]]; then
        if [[ -f "${HOME}/.bashrc" ]] && ! grep -q '\.local/bin' "${HOME}/.bashrc" 2>/dev/null; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
        fi
        if [[ -f "${HOME}/.profile" ]] && ! grep -q '\.local/bin' "${HOME}/.profile" 2>/dev/null; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.profile"
        fi
    fi

    # Refresh the IBus registry inside the desktop user's session.
    if command -v ibus >/dev/null 2>&1; then
        echo "--> Refreshing IBus component registry..."
        bongo_as_user ibus write-cache || true
        bongo_as_user ibus restart || true
    fi

    # Group 1: GNOME uses IBus. Add Bongo to the input sources so it is
    # available in the Super+Space switcher without manual setup.
    if [[ "${IM_FRAMEWORK}" == "ibus" ]]; then
        bongo_enable_gnome_source || true
    fi

    # Add Bongo to the invoking user's fcitx5 profile. fcitx5 rewrites this
    # profile when it exits, so edit it while fcitx5 is stopped and put the
    # user's input method framework back afterwards.
    if [[ "${IM_FRAMEWORK}" == "fcitx5" && "${FCITX5_SYSTEM_INSTALL}" == "true" && "${CONFIGURE_FCITX5}" == "true" && "${HAS_FCITX5_RUNTIME}" == "true" ]]; then
        FCITX5_SETUP="${PREFIX}/bin/bongo-fcitx5-setup"
        echo "--> Adding Bongo to the fcitx5 input method profile..."
        CONFIGURED=false
        FCITX5_STOPPED=false
        FCITX5_RESTARTED=false
        FCITX5_SETUP_SKIPPED=false
        FCITX5_PID="$(pgrep -u "${TARGET_USER_ID}" -x fcitx5 | head -1 || true)"
        FCITX5_ENV=()

        if [[ -n "${FCITX5_PID}" && -r "/proc/${FCITX5_PID}/environ" ]]; then
            mapfile -t FCITX5_ENV < <(
                tr '\0' '\n' < "/proc/${FCITX5_PID}/environ" |
                    grep -E '^(WAYLAND_DISPLAY|DISPLAY|XDG_RUNTIME_DIR|DBUS_SESSION_BUS_ADDRESS|XDG_SESSION_TYPE|XDG_CURRENT_DESKTOP|HYPRLAND_INSTANCE_SIGNATURE)=' \
                    || true
            )
        fi
        if [[ ! " ${FCITX5_ENV[*]} " == *"XDG_RUNTIME_DIR="* ]]; then
            FCITX5_ENV+=("XDG_RUNTIME_DIR=/run/user/${TARGET_USER_ID}")
        fi
        if [[ ! " ${FCITX5_ENV[*]} " == *"DBUS_SESSION_BUS_ADDRESS="* ]]; then
            FCITX5_ENV+=("DBUS_SESSION_BUS_ADDRESS=/run/user/${TARGET_USER_ID}/bus")
        fi

        FCITX5_RUNNER=()
        if [[ $EUID -eq 0 && -n "${SUDO_USER:-}" ]] && command -v runuser >/dev/null 2>&1; then
            FCITX5_RUNNER=(
                runuser -u "${SUDO_USER}" -- env
                "HOME=${TARGET_HOME}"
                "${FCITX5_ENV[@]}"
            )
        fi

        # Some desktops manage fcitx5 through a systemd user unit (Omarchy
        # ships omarchy-fcitx5.service). Killing the process and spawning a
        # bare fcitx5 there makes the unit start a competing instance on
        # every restart, so stop/start the owning unit instead.
        FCITX5_SYSTEMD=false
        FCITX5_UNIT=""
        SYSTEMD_RUNNER=()
        SYSTEMD_QUERY=false
        if command -v systemctl >/dev/null 2>&1; then
            if [[ $EUID -ne 0 ]]; then
                SYSTEMD_QUERY=true
            elif [[ -n "${SUDO_USER:-}" ]] && command -v runuser >/dev/null 2>&1; then
                SYSTEMD_QUERY=true
                SYSTEMD_RUNNER=(
                    runuser -u "${SUDO_USER}" -- env
                    "HOME=${TARGET_HOME}"
                    "XDG_RUNTIME_DIR=/run/user/${TARGET_USER_ID}"
                    "DBUS_SESSION_BUS_ADDRESS=/run/user/${TARGET_USER_ID}/bus"
                )
            fi
            if [[ "${SYSTEMD_QUERY}" == "true" && -n "${FCITX5_PID}" ]]; then
                while read -r systemd_unit; do
                    [[ -z "${systemd_unit}" ]] && continue
                    unit_pid="$("${SYSTEMD_RUNNER[@]}" systemctl --user \
                        show -p MainPID --value "${systemd_unit}" 2>/dev/null || true)"
                    if [[ -n "${unit_pid}" && "${unit_pid}" == "${FCITX5_PID}" ]]; then
                        FCITX5_UNIT="${systemd_unit}"
                        FCITX5_SYSTEMD=true
                        break
                    fi
                done < <("${SYSTEMD_RUNNER[@]}" systemctl --user list-units \
                    --type=service --state=running --no-legend --plain \
                    '*.service' 2>/dev/null | awk '{print $1}' || true)
            fi
        fi

        if [[ -n "${FCITX5_PID}" ]]; then
            if [[ "${FCITX5_SYSTEMD}" == "true" ]]; then
                echo "--> Stopping fcitx5 via ${FCITX5_UNIT} so the profile is not overwritten..."
                "${SYSTEMD_RUNNER[@]}" systemctl --user stop "${FCITX5_UNIT}" \
                    >/dev/null 2>&1 || true
            else
                echo "--> Stopping the running fcitx5 session so the profile is not overwritten..."
                if command -v fcitx5-remote >/dev/null 2>&1; then
                    (
                        cd /
                        "${FCITX5_RUNNER[@]}" fcitx5-remote -e
                    ) >/dev/null 2>&1 || true
                fi
            fi
            for _ in $(seq 1 25); do
                if ! pgrep -u "${TARGET_USER_ID}" -x fcitx5 >/dev/null 2>&1; then
                    FCITX5_STOPPED=true
                    break
                fi
                sleep 0.2
            done
            if [[ "${FCITX5_STOPPED}" != "true" ]]; then
                echo "Warning: could not stop fcitx5 automatically." >&2
                echo "Stop fcitx5, run ${FCITX5_SETUP}, then start it again to" >&2
                echo "avoid the live instance overwriting the profile." >&2
                FCITX5_SETUP_SKIPPED=true
            fi
        else
            FCITX5_STOPPED=true
        fi

        if [[ "${FCITX5_SETUP_SKIPPED}" != "true" ]]; then
            if [[ -n "${SUDO_USER:-}" ]]; then
                if command -v runuser >/dev/null 2>&1; then
                    if runuser -u "${SUDO_USER}" -- env \
                        "HOME=${TARGET_HOME}" \
                        python3 "${FCITX5_SETUP}"; then
                        CONFIGURED=true
                    fi
                fi
            elif [[ $EUID -eq 0 ]]; then
                echo "Warning: run the installer with sudo from your desktop user, or configure fcitx5 manually." >&2
            else
                if python3 "${FCITX5_SETUP}"; then
                    CONFIGURED=true
                fi
            fi

            if [[ "${CONFIGURED}" != "true" ]]; then
                echo "Warning: Bongo was not added to the fcitx5 profile automatically." >&2
                python3 "${FCITX5_SETUP}" --print-manual-steps 2>/dev/null || true
            fi

            if [[ "${FCITX5_STOPPED}" == "true" && -n "${FCITX5_PID}" ]]; then
                echo "--> Restarting fcitx5..."
                if [[ "${FCITX5_SYSTEMD}" == "true" ]]; then
                    "${SYSTEMD_RUNNER[@]}" systemctl --user start \
                        "${FCITX5_UNIT}" >/dev/null 2>&1 || true
                else
                    (
                        cd "${TARGET_HOME}" 2>/dev/null || cd /
                        "${FCITX5_RUNNER[@]}" fcitx5 -d
                    ) >/dev/null 2>&1
                fi
                for _ in $(seq 1 40); do
                    if "${FCITX5_RUNNER[@]}" fcitx5-remote >/dev/null 2>&1; then
                        FCITX5_RESTARTED=true
                        break
                    fi
                    sleep 0.25
                done
                if [[ "${FCITX5_RESTARTED}" != "true" ]]; then
                    echo "Warning: fcitx5 could not be restarted automatically." >&2
                    if [[ "${FCITX5_SYSTEMD}" == "true" ]]; then
                        echo "Start it with: systemctl --user start ${FCITX5_UNIT}" >&2
                    else
                        echo "Start it with: fcitx5 -d" >&2
                    fi
                fi
            fi

            # Group 2: KDE and tiling compositors. Make fcitx5 start with
            # the session unless systemd already supervises it (Omarchy) or
            # the distro/user already ships an autostart entry.
            if [[ "${DESKTOP_KIND}" == "kde" || "${DESKTOP_KIND}" == "wlwm" ]] && \
               [[ -n "${SUDO_USER:-}" || $EUID -ne 0 ]]; then
                AUTOSTART_FILE="${TARGET_HOME}/.config/autostart/org.fcitx.Fcitx5.desktop"
                SYSTEMD_FCITX5_UNIT=""
                if [[ "${SYSTEMD_QUERY}" == "true" ]]; then
                    SYSTEMD_FCITX5_UNIT="$("${SYSTEMD_RUNNER[@]}" systemctl --user \
                        list-unit-files --no-legend --plain '*.service' 2>/dev/null |
                        awk '$2 ~ /^enabled/ {print $1}' |
                        grep -i 'fcitx' | head -1 || true)"
                fi
                if [[ -n "${SYSTEMD_FCITX5_UNIT}" ]]; then
                    FCITX5_STARTUP_MANAGED=true
                    echo "--> fcitx5 starts at login via ${SYSTEMD_FCITX5_UNIT}."
                elif [[ -f "${AUTOSTART_FILE}" ]]; then
                    FCITX5_STARTUP_MANAGED=true
                    echo "--> fcitx5 autostart entry already present."
                else
                    if [[ $EUID -eq 0 ]]; then
                        install -d -o "${TARGET_USER_NAME}" -g "${TARGET_USER_GID}" \
                            "${TARGET_HOME}/.config/autostart" 2>/dev/null || \
                            mkdir -p "${TARGET_HOME}/.config/autostart"
                    else
                        mkdir -p "${TARGET_HOME}/.config/autostart"
                    fi
                    cat > "${AUTOSTART_FILE}" <<'EOF'
[Desktop Entry]
Type=Application
Name=Fcitx 5
Comment=Start Input Method
Exec=fcitx5 -d
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
                    if [[ $EUID -eq 0 ]]; then
                        chown "${TARGET_USER_NAME}:${TARGET_USER_GID}" \
                            "${AUTOSTART_FILE}" 2>/dev/null || true
                    fi
                    FCITX5_AUTOSTART_ADDED=true
                    echo "--> Added fcitx5 to startup applications."
                fi
            fi
        fi
    fi
fi

echo "=================================================="
echo "   Bongo has been successfully installed!        "
echo "=================================================="
echo ""
CONFIGURED="${CONFIGURED:-false}"
FCITX5_RESTARTED="${FCITX5_RESTARTED:-false}"
FCITX5_AUTOSTART_ADDED="${FCITX5_AUTOSTART_ADDED:-false}"
FCITX5_STARTUP_MANAGED="${FCITX5_STARTUP_MANAGED:-false}"
echo "Next Steps:"
if [[ "${IM_FRAMEWORK}" == "fcitx5" ]]; then
    if [[ "${CONFIGURED}" == "true" ]]; then
        echo "1. Bongo has been added to your fcitx5 input method list."
        if [[ "${FCITX5_RESTARTED}" == "true" ]]; then
            echo "2. fcitx5 was restarted with the new profile."
        else
            echo "2. Start fcitx5 with: fcitx5 -d"
        fi
        echo "3. Switch with Ctrl+Space, then type in any app."
        echo "4. Launch 'bongo-settings' to customize typing modes and fonts."
        if [[ "${FCITX5_AUTOSTART_ADDED}" == "true" ]]; then
            echo "5. fcitx5 will start automatically with your next login."
        fi
        if [[ "${DESKTOP_KIND}" == "wlwm" && "${FCITX5_STARTUP_MANAGED}" != "true" && "${FCITX5_AUTOSTART_ADDED}" != "true" ]]; then
            echo "   If fcitx5 does not start at login, add to your compositor config:"
            echo "     Hyprland: exec-once = fcitx5 -d"
            echo "     sway:     exec fcitx5 -d"
        fi
    else
        echo "1. Run: fcitx5-configtool"
        echo "2. Open Input Method -> add 'Bongo'."
        echo "3. Apply and restart fcitx5, then switch with Ctrl+Space."
        echo "4. Launch 'bongo-settings' to customize typing modes and fonts."
    fi
else
    if [[ "${IBUS_SOURCE_ENABLED}" == "true" ]]; then
        echo "1. Bongo has been added to your input sources."
        echo "2. Switch input methods with Super + Space."
        echo "3. If it is missing, open your desktop's keyboard settings."
    else
        echo "1. Open GNOME / IBus Settings -> Keyboard -> Input Sources."
        echo "2. Add 'Bengali (Bongo)' to your active keyboards."
        echo "3. Switch keyboards anytime with Super + Space or Control + Space."
    fi
    echo "4. Launch 'bongo-settings' to customize typing modes and fonts."
    if [[ "${BUILD_FCITX5}" == "true" && "${FCITX5_SYSTEM_INSTALL}" != "true" ]]; then
        echo ""
        echo "For fcitx5, run this installer system-wide from the checkout:"
        echo "  sudo BONGO_FCITX5=1 bash ${SCRIPT_DIR}/install.sh"
    fi
fi
echo ""
