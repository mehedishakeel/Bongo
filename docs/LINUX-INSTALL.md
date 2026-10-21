# Installing Bongo on Linux

Bongo provides native Avro phonetic Bengali typing on modern Linux desktops. It
ships two frontends over the same Rust engine:

- **IBus** for GNOME and other IBus-based desktops.
- **fcitx5** for KDE Plasma, Hyprland, Omarchy, and other fcitx5-based desktops.

You only need the input framework your desktop already uses. The prebuilt
packages include both frontends rather than forcing either one.

---

## Supported Linux Distributions

- **Ubuntu**: 24.04 LTS and newer (22.04 via source)
- **Debian**: 13 (Trixie) and newer (12 via source)
- **Fedora**: 40 and newer
- **Arch Linux / Manjaro / Omarchy**
- **Pop!_OS / Linux Mint** (versions based on Ubuntu 24.04 or newer)

---

## Option 1: Universal tarball (any distribution)

Download `Bongo-1.0.1-linux-x86_64.tar.gz` from the [Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page, then extract and install:

```bash
tar -xzf Bongo-1.0.1-linux-x86_64.tar.gz
cd Bongo-1.0.1-linux-x86_64
sudo bash install.sh --prebuilt
```

The tarball contains prebuilt binaries, so no compiler or network access is
needed. It requires glibc 2.39+ (Ubuntu 24.04+, Debian 13+, Fedora 40+, Arch)
and Python 3 with GTK 4 for the settings app.

---

## Option 2: Debian / Ubuntu package

Download `bongo_1.0.1_amd64.deb` (or `bongo_1.0.1_arm64.deb`) from the [Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page, then install via terminal:

```bash
sudo apt install ./bongo_1.0.1_amd64.deb
```

The package installs the engine and settings app, and includes the fcitx5 addon
when it was built with fcitx5 development headers.

---

## Option 3: Install from Source

### Prerequisites

Install Rust, Python 3, GTK 4, and the framework you use.

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install -y cargo rustc cmake ninja-build \
  python3 python3-gi gir1.2-gtk-4.0

# For GNOME / IBus:
sudo apt install -y ibus libibus-1.0-dev gir1.2-ibus-1.0

# For KDE / Hyprland / Omarchy / fcitx5:
sudo apt install -y libfcitx5core-dev fcitx5 fcitx5-configtool
```

**Fedora:**

```bash
sudo dnf install -y cargo rust cmake ninja-build \
  python3 python3-gobject gtk4

# For GNOME / IBus:
sudo dnf install -y ibus ibus-devel

# For KDE / Hyprland / Omarchy / fcitx5:
sudo dnf install -y fcitx5-devel fcitx5 fcitx5-configtool
```

**Arch Linux / Omarchy:**

```bash
sudo pacman -S rust cargo cmake ninja python-gobject gtk4 \
  fcitx5 fcitx5-configtool
# For GNOME / IBus:
sudo pacman -S ibus
```

### Build & Install

```bash
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo

# Builds both frontends when their dependencies are present:
sudo ./platforms/linux/scripts/install.sh
```

The installer builds the fcitx5 addon automatically when fcitx5 and its
development headers are present. Use `BONGO_FCITX5=0` to skip it.

The fcitx5 addon is installed system-wide because fcitx5 does not reliably
discover user-local addons. A non-root install into `~/.local` installs the
engine, settings app, and IBus frontend, skips the fcitx5 addon, and prints the
`sudo` command needed to finish.

---

## Activation

The installer detects your desktop and enables one of two groups automatically:

| Desktop | Framework | What the installer does |
|---------|-----------|-------------------------|
| GNOME | IBus | Adds Bongo to the GNOME input sources (existing sources are preserved), then refreshes the IBus cache. |
| KDE Plasma, Hyprland, Omarchy, other Wayland compositors | native fcitx5 | Adds Bongo to the fcitx5 profile, restarts fcitx5 (through its systemd user unit when one owns the process), and adds a session autostart entry when nothing else starts fcitx5. |

Detection looks at the running desktop processes, so it also works when the
installer runs through `sudo` or `pkexec` and `XDG_CURRENT_DESKTOP` is missing.
The manual steps below are only needed when automatic setup was skipped
(`--no-configure-fcitx5`) or your session is custom.

### GNOME / IBus

Bongo is added to your input sources automatically. To add or remove it by hand:

1. Open **Settings** -> **Keyboard**.
2. Under **Input Sources**, click **Add** (`+`).
3. Click the three vertical dots (`⋮`) to expand all languages.
4. Search for **Bengali** or **Bongo**, and select **Bengali (Bongo)**.
5. Toggle between English and Bongo with <kbd>Super + Space</kbd> or
   <kbd>Control + Space</kbd>.

### KDE Plasma / Hyprland / Omarchy / fcitx5

1. Run `fcitx5-configtool`.
2. Open **Input Method** and click **+**.
3. Add **Bongo** and click **Apply**.
4. Restart fcitx5 with `fcitx5-remote -r`.
5. Switch input methods with <kbd>Ctrl + Space</kbd>.

The installer normally adds Bongo to your fcitx5 profile automatically, stopping
and restarting fcitx5 around the edit. You can re-run the helper manually, but
fcitx5 must be stopped first (it rewrites the profile on exit):

```bash
fcitx5-remote -e          # stop fcitx5
bongo-fcitx5-setup        # add Bongo to the profile
fcitx5 -d                 # start fcitx5 again
```

It preserves the existing input-method order and is idempotent.

---

## Troubleshooting

### Bongo does not appear in fcitx5

- Confirm the package is installed system-wide:
  `fcitx5-configtool` reads addons from the system paths, not `~/.local`.
- Restart fcitx5 completely (`fcitx5-remote -e`, then `fcitx5 -d`); a plain
  `fcitx5-remote -r` does not load newly installed addons.
- Re-run `bongo-fcitx5-setup` while fcitx5 is stopped (see above), then start
  fcitx5 and press <kbd>Ctrl + Space</kbd>.
- Check that fcitx5 is the active input framework for your session:
  `GTK_IM_MODULE`, `QT_IM_MODULE`, and `XMODIFIERS` should point to fcitx5
  (Omarchy and KDE set these for you).

### Typing works in some apps but not others

Wayland compositors and toolkits need their input-method module. On Hyprland,
make sure the fcitx5 environment variables are exported in your session config.
On GNOME, use the IBus frontend instead: GNOME's input-source integration is
IBus-native.

### Candidate font

The fcitx5 candidate window follows the fcitx5 theme. Bongo's
**Fonts & Typography** settings apply to the IBus candidate window and previews;
they do not override fcitx5's candidate font.

---

## Bongo Settings & Layout Cheatsheet

Launch the settings and welcome application anytime:

- Open your app launcher and search for **Bongo**, or
- Run:

  ```bash
  bongo-settings
  ```

In the settings window you can:

- Explore the complete phonetic keymap cheatsheet with live search.
- Switch typing modes: **Phonetic first** (recommended), **Smart suggestions**,
  or **Phonetic only**.
- Toggle emoji completion.
- Select a Bengali font and candidate HUD size for the IBus frontend.

Typing mode and emoji changes apply to the fcitx5 frontend on the next key
event; no restart is required.
