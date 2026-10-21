# Bongo for Linux

Native Avro phonetic Bengali input method for modern Linux desktop environments.

Powered by a pure-Rust transliteration engine shared by two native frontends:

- **IBus** for GNOME and other IBus-based desktops.
- **fcitx5** for KDE Plasma, Hyprland, Omarchy, and other fcitx5-based desktops.

Both frontends use the same `libbongo_engine.so` and the same GTK settings
application.

---

## Architecture Overview

```
platforms/linux/
├── data/
│   ├── app.getbongo.Bongo.desktop       # Desktop launcher specification
│   ├── app.getbongo.Bongo.metainfo.xml  # AppStream metadata
│   ├── bongo.xml                        # IBus component definition
│   └── icons/                           # App icons (16x16 to 512x512)
├── engine/                              # Rust transliteration engine (C ABI)
│   ├── Cargo.toml
│   └── src/lib.rs                       # Shared library (libbongo_engine.so)
├── fcitx5/                              # Native fcitx5 addon
│   ├── src/                             # Linux engine adapter and key handling
│   └── tests/                           # CTest unit and integration tests
├── ibus/                                # IBus input method engine daemon
│   └── bongo-ibus-engine.py             # Python IBus engine implementation
├── scripts/
│   ├── install.sh                       # Local build and install script
│   ├── configure-fcitx5.py              # Safe, idempotent profile helper
│   ├── build-deb.sh                     # Debian / Ubuntu package builder
│   ├── build-tarball.sh                 # Universal prebuilt tarball builder
│   └── build-rpm.sh                     # Legacy Fedora / RHEL package builder
└── ui/
    └── bongo_settings.py                # GTK settings and welcome application
```

The fcitx5 addon is a C++20 `fcitx::InputMethodEngine`. It loads the Rust engine
through `dlopen`, keeps one engine instance per fcitx5 input context, and maps
Bongo candidates to fcitx5's native preedit and candidate panel. It does not
replace or modify Bongo's transliteration rules.

---

## Prerequisites

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y cargo rustc cmake ninja-build \
  libfcitx5core-dev fcitx5 fcitx5-configtool \
  python3 python3-gi gir1.2-gtk-4.0
# For the IBus frontend on GNOME:
sudo apt install -y ibus libibus-1.0-dev gir1.2-ibus-1.0
```

### Fedora

```bash
sudo dnf install -y cargo rust cmake ninja-build \
  fcitx5-devel fcitx5 fcitx5-configtool \
  python3 python3-gobject gobject-introspection gtk4
# For the IBus frontend on GNOME:
sudo dnf install -y ibus ibus-devel
```

### Arch Linux / Omarchy

```bash
sudo pacman -S rust cargo cmake ninja fcitx5 fcitx5-configtool \
  python-gobject gtk4
# For the IBus frontend on GNOME:
sudo pacman -S ibus
```

The installer only needs the development package for the frontend it can build.
The fcitx5 addon requires `fcitx5` 5.1 or newer headers. IBus remains optional;
the package recommends it rather than forcing it.

---

## Installation

### Option 1: Universal Tarball (any distribution)

Download `Bongo-1.0.1-linux-x86_64.tar.gz` (64-bit PC) or
`Bongo-1.0.1-linux-aarch64.tar.gz` (ARM64) from the
[Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page, then
install the prebuilt payload:

```bash
tar -xzf Bongo-1.0.1-linux-x86_64.tar.gz
cd Bongo-1.0.1-linux-x86_64
sudo bash install.sh --prebuilt
```

The archive needs glibc 2.39+ (Ubuntu 24.04+, Debian 13+, Fedora 40+, Arch) and
Python 3 with GTK 4 for the settings app. It carries an `ARCH` marker and the
installer refuses a mismatched or unverified archive.

To uninstall a tarball install:

```bash
sudo bash install.sh --uninstall
```

### Option 2: Debian / Ubuntu Package

Download `bongo_1.0.1_amd64.deb` (or `bongo_1.0.1_arm64.deb`) from the [Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page:

```bash
sudo apt install ./bongo_1.0.1_amd64.deb
```

The package ships both frontends and uses the same glibc 2.39+ floor as the
tarball (Ubuntu 24.04+, Debian 13+). On GNOME, add **Bengali (Bongo)** under
IBus. On KDE, Hyprland, or Omarchy, add **Bongo** in `fcitx5-configtool`.

### Option 3: Build & Install from Source

For a normal system-wide install, run the installer with `sudo`. The fcitx5
addon must live in fcitx5's system addon directory; user-local addon installs
are not supported.

```bash
# From the repository root
sudo ./platforms/linux/scripts/install.sh
```

The installer detects fcitx5 and its headers automatically. Use
`BONGO_FCITX5=0` to skip the addon.

A non-root install can still install the engine, settings app, and IBus
frontend into `~/.local`. It deliberately skips the fcitx5 addon and prints the
exact `sudo` command needed to finish:

```bash
./platforms/linux/scripts/install.sh
```

To stage a package build without touching the live system:

```bash
DESTDIR=/tmp/bongo-stage PREFIX=/usr BONGO_FCITX5=1 \
  bash platforms/linux/scripts/install.sh
```

### Configuring fcitx5

The installer stops fcitx5, adds Bongo to the invoking user's profile, and
restarts fcitx5 (fcitx5 rewrites its profile on exit, so editing it while
running would be lost). If automatic configuration is skipped, run:

```bash
fcitx5-remote -e          # stop fcitx5
bongo-fcitx5-setup        # add Bongo to the profile
fcitx5 -d                 # start fcitx5 again
```

or add Bongo manually in `fcitx5-configtool`.

Switch input methods with <kbd>Ctrl + Space</kbd>. On Wayland, make sure your
desktop session exports the usual fcitx5 variables (`GTK_IM_MODULE`,
`QT_IM_MODULE`, and `XMODIFIERS`); Omarchy, KDE, and most fcitx5 setups already
do this.

---

## Enabling Bongo

### GNOME / IBus

1. Open **Settings** -> **Keyboard**.
2. Under **Input Sources**, click **Add** (`+`).
3. Click the three dots (`⋮`) to expand all languages.
4. Search for **Bengali (Bongo)** and add it.
5. Switch keyboards with <kbd>Super + Space</kbd> or
   <kbd>Control + Space</kbd>.

### KDE Plasma / Hyprland / Omarchy / fcitx5

1. Run `fcitx5-configtool`.
2. Open **Input Method** and click **+**.
3. Add **Bongo** and apply.
4. Restart fcitx5 with `fcitx5-remote -r`, then switch with
   <kbd>Ctrl + Space</kbd>.

> **Tip for Virtual Machine users (e.g. running Linux on a macOS host):**
> macOS intercepts <kbd>Cmd + Space</kbd> for Spotlight. To set the input
> switch shortcut to <kbd>Control + Space</kbd> on GNOME:
>
> ```bash
> gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Control>space']"
> ```
>
> Or to use <kbd>Alt + Shift</kbd>:
>
> ```bash
> gsettings set org.gnome.desktop.input-sources xkb-options "['grp:alt_shift_toggle']"
> ```

---

## Bongo Settings Application

Run the settings app from your application launcher or terminal:

```bash
bongo-settings
```

You can also open directly to specific tabs:

```bash
bongo-settings --tab 0  # Getting Started
bongo-settings --tab 1  # Phonetic Layout Cheatsheet
bongo-settings --tab 2  # Typing Settings (3 modes, emoji toggle)
bongo-settings --tab 3  # Fonts & Typography
```

Typing mode and emoji changes apply to the fcitx5 frontend on the next key
event. No fcitx5 restart is required.

The fcitx5 candidate font follows the active fcitx5 theme. Bongo's
`candidate_font` setting is used by the IBus frontend only.

---

## Building Packages

```bash
# Debian / Ubuntu
./platforms/linux/scripts/build-deb.sh

# Universal prebuilt tarball (any distribution)
./platforms/linux/scripts/build-tarball.sh
```

The package builders include the fcitx5 addon when the development headers are
available. Packages include both frontends rather than requiring either one,
so GNOME and KDE users can install only the frontend they need.

---

## Testing the fcitx5 Addon

```bash
export BONGO_ENGINE_LIB="$PWD/platforms/linux/engine/target/release/libbongo_engine.so"
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build/fcitx5
ctest --test-dir build/fcitx5 --output-on-failure
```

The integration test loads the addon into an in-process fcitx5 instance, types
`ami`, selects candidates, exercises Backspace/Escape/Enter/focus-out, and
verifies typing-mode and emoji changes. See
`platforms/linux/fcitx5/tests/smoke.md` for the manual checklist covering GTK,
Qt, Electron, and terminal applications.
