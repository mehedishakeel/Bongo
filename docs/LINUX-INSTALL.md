# Installing Bongo on Linux

Bongo provides native Avro phonetic Bengali typing on modern Linux desktop environments (GNOME, KDE Plasma, XFCE) using the universal IBus input method framework.

---

## Supported Linux Distributions

- **Ubuntu**: 22.04 LTS, 24.04 LTS, and newer
- **Debian**: Debian 12 (Bookworm) and newer
- **Fedora**: Fedora 38, 39, 40, and newer
- **Arch Linux / Manjaro**
- **Pop!_OS / Linux Mint**

---

## Option 1: Install from Debian / Ubuntu Package (.deb)

Download `bongo_1.0.0_amd64.deb` from the [Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page, then install via terminal:

```bash
sudo apt install ./bongo_1.0.0_amd64.deb
```

Or on Fedora:

```bash
sudo dnf install ./bongo-1.0.0-1.x86_64.rpm
```

---

## Option 2: Install from Source

### Prerequisites

Ensure you have Rust, IBus, and Python 3 installed:

**On Ubuntu / Debian:**
```bash
sudo apt update
sudo apt install -y cargo rustc ibus libibus-1.0-dev python3 python3-gi gir1.2-ibus-1.0 gir1.2-gtk-4.0
```

**On Fedora:**
```bash
sudo dnf install -y cargo rust ibus ibus-devel python3 python3-gobject gtk4
```

### Build & Install

```bash
# Clone the repository
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo

# Run the installer
sudo ./platforms/linux/scripts/install.sh
```

---

## Activation in System Settings

After installing Bongo, activate it as an input source:

### On GNOME (Ubuntu, Fedora, Debian)

1. Open **Settings** -> **Keyboard**.
2. Under **Input Sources**, click **Add** (`+`).
3. Click the three vertical dots (`⋮`) to expand all languages.
4. Search for **Bengali** or **Bongo**, and select **Bengali (Bongo)**.
5. You can now toggle between English and Bongo using <kbd>Super + Space</kbd> or <kbd>Control + Space</kbd>.

### On KDE Plasma

1. Open **System Settings** -> **Input Devices** -> **Keyboard** -> **Layouts**.
2. Under IBus Input Method configuration, add **Bongo**.
3. Toggle with your configured input method shortcut.

---

## Bongo Settings & Layout Cheatsheet

Launch the Settings and Welcome application anytime:

- Open your app launcher and search for **Bongo**, or
- Run in terminal:
  ```bash
  bongo-settings
  ```

In the settings window, you can:
- Explore the complete phonetic keymap cheatsheet with live search.
- Switch typing modes: **Phonetic first** (recommended), **Smart suggestions**, or **Phonetic only**.
- Toggle emoji completion.
- Select your preferred Bengali font (e.g. Noto Sans Bengali, Kalpurush, SolaimanLipi) and candidate HUD font size.
