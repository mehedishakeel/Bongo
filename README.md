# Bongo · বঙ্গ

<p align="center">
  <img src="assets/Bongo-logo-v2.png" width="144" alt="Bongo logo">
</p>

**Bongo** is a native Bangla keyboard for macOS, Linux and Windows. It types
directly in your applications and keeps typing data on your device.

[Download the latest release](https://github.com/mehedishakeel/Bongo/releases)

## Install Bongo

### macOS

1. Download the macOS `.dmg` from Releases.
2. Open it and drag **Bongo.app** to **Input Methods**.
3. Log out and back in.
4. Open System Settings → Keyboard → Input Sources → Edit → **+**, then add
   Bongo.
5. Switch keyboards with Globe or Control-Space.

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

## Credits and licenses

Bongo was developed by **Mehedi Shakeel**. It is an independent derivative
project built with work from:

- [OmicronLab Avro Keyboard](https://github.com/omicronlab/Avro-Keyboard)
- [Lekho](https://github.com/ARahim3/Lekho)
- [OpenBangla Keyboard](https://github.com/OpenBangla/OpenBangla-Keyboard)
- [riti](https://github.com/OpenBangla/riti)

Bongo is not an official release or endorsement from these projects. Their
copyright notices and licenses remain intact. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [licenses](licenses).
