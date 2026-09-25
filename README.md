# Bongo · বঙ্গ

<p align="center">
  <img src="assets/Bongo-logo-v2.png" width="144" alt="Bongo logo">
</p>

**Bongo** is a native Bangla keyboard for macOS, Linux and Windows. It types
directly in your applications and keeps typing data on your device.

[Website](https://mehedishakeel.github.io/Bongo/) · [Download the latest release](https://github.com/mehedishakeel/Bongo/releases)

## Install Bongo

### macOS

1. Download the macOS `.dmg` from Releases.
2. Open it and drag **Bongo.app** to **Applications**.
3. Open Bongo from Applications and choose **Install** when prompted.
4. Log out and back in once.
5. Open System Settings → Keyboard → Input Sources → Edit → **+**, then add
   Bongo.
6. Switch keyboards with Globe or Control-Space. Open **Bongo** from Applications
   whenever you want the guide or settings.

[Full macOS instructions](docs/MACOS-INSTALL.md)

### Linux

Download the Debian package from Releases, then run:

```sh
sudo apt install ./Bongo_*.deb
ibus restart
```

Log out and back in if Bongo does not appear. Add it from your desktop's
Keyboard/Input Sources settings.

[Full Linux instructions](docs/LINUX-INSTALL.md)

### Windows

The Windows port is still under development. It should not be distributed as a
supported release until its Delphi dependencies, runtime files and native tests
are complete.

## Updates and privacy

Bongo checks its GitHub Releases page when you request an update. It opens the
download page and never silently replaces the installed keyboard. Typing and
learned-word data stay on your device.

## For developers

- [Build DMG, DEB and EXE files from source](docs/BUILDING.md)
- [Understand the native architecture](docs/ARCHITECTURE.md)
- [Prepare a GitHub release](docs/RELEASING.md)
- [Run validation checks](docs/VALIDATION.md)
- [Review the latest project audit](docs/AUDIT.md)
- [Review the Windows release checklist](docs/WINDOWS-RELEASE.md)

Each release script must run on its matching operating system. The build guide
lists every required compiler, tool and development package before the commands.
Generated release assets are kept under `platforms/macos/release`,
`platforms/linux/release` and `platforms/windows/release`.

## Credits and licenses

Bongo was developed by **Mehedi Shakeel** and is an independent derivative
project. It is not an official release or endorsement from any upstream
project. Copyright in upstream work remains with its respective authors.

| Upstream project | Authors / maintainers credited | License | Used in Bongo |
|---|---|---|---|
| [Avro Keyboard](https://github.com/omicronlab/Avro-Keyboard) | OmicronLab; original developer **Mehdi Hasan Khan** | MPL-1.1 | Windows foundation and Avro Phonetic compatibility |
| [Lekho](https://github.com/ARahim3/Lekho) | **Abdur Rahim** | MPL-2.0 | Native Apple Silicon input-method implementation foundation |
| [OpenBangla Keyboard](https://github.com/OpenBangla/OpenBangla-Keyboard) | **Muhammad Mominul Huque** and contributors | GPL-3.0-or-later | Linux IBus and Qt application foundation |
| [riti](https://github.com/OpenBangla/riti) | OpenBangla contributors | MPL-2.0 | Native phonetic conversion engine |

“Bongo Phonetic” is Bongo's product label for its compatible presentation of
the Avro Phonetic method; it does not claim authorship of that method. The new
Bongo layout-guide artwork does not reuse the upstream Avro artwork, logo,
website URL, or branding.

The original code and text of the GitHub Pages website are dedicated under
[CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/). That dedication
does not cover the Bongo software, upstream code, third-party names, trademarks,
or material owned by others. See [the website notice](docs/NOTICE.md),
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and [all license texts](licenses).
