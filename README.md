<p align="center">
  <img src="assets/Bongo-logo-v2.png" width="128" alt="Bongo Logo">
</p>

<h1 align="center">Bongo · বঙ্গ</h1>

<p align="center">
  <strong>Native Bangla Phonetic Keyboard for macOS & Linux</strong>
</p>

<p align="center">
  <a href="https://github.com/mehedishakeel/Bongo/releases/latest"><img src="https://img.shields.io/badge/Platforms-macOS%20(Apple%20Silicon)%20|%20Linux%20(IBus)-4f46e5?style=flat-square" alt="Platforms"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MPL--2.0-indigo?style=flat-square" alt="License"></a>
  <a href="https://getbongo.app"><img src="https://img.shields.io/badge/Website-getbongo.app-6366f1?style=flat-square" alt="Website"></a>
</p>

<p align="center">
  <a href="https://github.com/mehedishakeel/Bongo/releases/latest/download/Bongo-1.0-macos-arm64.dmg">
    <img src="https://img.shields.io/badge/macOS-Download_DMG-4f46e5?style=for-the-badge&logo=apple&logoColor=white" alt="Download macOS DMG">
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/mehedishakeel/Bongo/releases/latest/download/bongo_1.0.0_amd64.deb">
    <img src="https://img.shields.io/badge/Linux-Download_DEB-e11d48?style=for-the-badge&logo=linux&logoColor=white" alt="Download Linux DEB">
  </a>
</p>

---

**Bongo** is a fast, lightweight, and modern Bengali input method built for macOS Apple Silicon and modern Linux desktop environments (GNOME, KDE Plasma, XFCE). It brings familiar phonetic typing directly into all your applications with instant suggestions, a sleek HUD candidate bar, and complete on-device privacy.

**Visit the official website & interactive demo**: [https://getbongo.app](https://getbongo.app)

---

## Quick Installation

### macOS (Apple Silicon)

1. **Download**: Get `Bongo-1.0-macos-arm64.dmg` from [Releases](https://github.com/mehedishakeel/Bongo/releases/latest).
2. **Install**: Open the DMG and drag **Bongo.app** into your **Applications** folder.
3. **Activate**:
   - Open **Bongo** from Applications once (it registers the keyboard service with macOS).
   - Go to **System Settings → Keyboard → Input Sources → Edit → +**, and select **Bongo** (under Bengali).
   - Switch keyboards anytime with the **Globe (<kbd>fn</kbd> / Globe)** key or <kbd>Control + Space</kbd>!

### Linux (Ubuntu, Debian, Fedora, Arch)

1. **Download**: Get `bongo_1.0.0_amd64.deb` (or build from source with `./platforms/linux/scripts/install.sh`).
2. **Install**: `sudo apt install ./bongo_1.0.0_amd64.deb`
3. **Activate**: Go to **Settings → Keyboard → Input Sources → Add**, and add **Bengali (Bongo)**.
   - Switch keyboards with <kbd>Super + Space</kbd> or <kbd>Control + Space</kbd>.
   - Open **Bongo Settings** (`bongo-settings`) from the app launcher anytime.

See [docs/LINUX-INSTALL.md](docs/LINUX-INSTALL.md) for full Linux instructions.

---

## How to Type

Bongo uses the standard, intuitive **Avro Phonetic** rules you already know. Type Bengali words according to how they sound in English letters:

| English Keystrokes | Bangla Output | Meaning |
|:---|:---|:---|
| `ami` | **আমি** | I / Me |
| `bangla` | **বাংলা** | Bengali |
| `dhonnobad` | **ধন্যবাদ** | Thank you |
| `shonar bangla` | **সোনার বাংলা** | Golden Bengal |
| `kemon achen` | **কেমন আছেন** | How are you? |
| `kkhoma` | **ক্ষমা** | Forgive |
| `gyan` / `jnj` | **জ্ঞান** | Knowledge |

Press <kbd>Space</kbd> to commit the highlighted word, or press number keys <kbd>1</kbd> to <kbd>9</kbd> to pick from the candidate list immediately.

---

## Key Features

- **Pure Rust Engine**: High-performance, zero-latency phonetic transliteration powered by offline dictionary Trie structures.
- **Privacy-First (On-Device)**: Your typing, vocabulary, and preferences never leave your device. No network calls, no analytics, and no telemetry.
- **Modern Candidate HUD**: Floating suggestion bar with tactile shortcut keys (`[1]`, `[2]`), arrow navigation, and high-contrast pill styling.
- **3 Typing Modes**: Choose between *Phonetic first* (exact phonetic spelling by default), *Smart suggestions* (dictionary auto-selection), or *Phonetic only* (direct inline output).
- **Custom Fonts**: Choose any Bengali font installed on your system (Noto Sans Bengali, Kalpurush, Kohinoor Bangla, SolaimanLipi, etc.) with real-time size adjustments.
- **Desktop Settings & Cheatsheet**: Native welcome and settings application on both macOS and Linux with searchable layout guide and interactive typing playground.

---

## Screenshots

<p align="center">
  <img src="docs/assets/bongo-hud-candidate.png" width="340" alt="Bongo Modern macOS HUD Candidate Panel">
  <br>
  <em>Tactile Candidate HUD with fast numbered shortcuts</em>
</p>

<p align="center">
  <img src="docs/assets/bongo-settings.png" width="700" alt="Bongo Settings Window">
  <br>
  <em>Modern Settings Window with 3 typing modes & emoji customization</em>
</p>

---

## For Developers

### Build on macOS:
```sh
./platforms/macos/scripts/create-dmg.sh
```

### Build on Linux:
```sh
./platforms/linux/scripts/install.sh
# Or create DEB / RPM packages:
./platforms/linux/scripts/build-deb.sh
./platforms/linux/scripts/build-rpm.sh
```

### Run Tests:
```sh
python3 -m unittest discover -s tests -v
```

See [docs/BUILDING.md](docs/BUILDING.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full developer documentation.

---

## Credits & License

Bongo is developed and maintained by **[Mehedi Shakeel](https://github.com/mehedishakeel)**.

- **Foundational Architecture**: Derived from [Lekho](https://github.com/ARahim3/Lekho) by Abdur Rahim.
- **Phonetic Engine**: Powered by [riti](https://github.com/OpenBangla/riti) (OpenBangla contributors).
- **Phonetic Layout Scheme**: Avro Phonetic scheme by OmicronLab (Dr. Mehdi Hasan Khan).

Licensed under the **[Mozilla Public License 2.0 (MPL-2.0)](LICENSE)**.
