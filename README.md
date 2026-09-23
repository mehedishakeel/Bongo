# Bongo · বঙ্গ

<p align="center">
  <img src="assets/Bongo-logo-v2.png" width="144" alt="Bongo logo">
</p>

**Bongo** is a native Bangla keyboard for macOS, Linux and Windows, developed by
**Mehedi Shakeel**. It types directly inside other applications and keeps typing
data on the device.

> The macOS Apple Silicon build is working and tested. The Linux source and
> packaging are ready for native CI testing. The Windows port still needs its
> legacy Delphi dependencies and runtime data before it can ship as an installer.

| Platform | Technology | Status |
|---|---|---|
| macOS 13+, Apple Silicon | Swift, InputMethodKit, riti | Working native input source |
| Linux, IBus desktop | Qt 5, IBus, riti | Source and DEB packaging |
| Windows | Delphi 2010, Win32 keyboard hook | Source port; prerequisites outstanding |

## Install on macOS

Download the latest macOS DMG from GitHub Releases. Open it and drag **Bongo.app**
to **Input Methods**. Log out and back in, then open System Settings → Keyboard →
Input Sources → Edit → **+** and add Bongo. Switch keyboards with Globe or
Control-Space.

See [the full macOS guide](docs/MACOS-INSTALL.md).

## Install on Linux

On Debian or Ubuntu, download the latest `.deb` from GitHub Releases and run:

```sh
sudo apt install ./Bongo_*.deb
ibus restart
```

Log out and back in if Bongo does not appear immediately. Add **Bongo** in your
desktop's Keyboard/Input Sources settings, then select it from the IBus menu.

See [the full Linux guide](docs/LINUX-INSTALL.md).

## Install on Windows

No supported Windows executable exists yet. The port uses the original Delphi
2010 Avro desktop architecture and cannot be published until DISQLite3, ICS, JCL,
JVCL, and the required runtime database/layout/skin files are assembled and
tested with suitable redistribution rights.

When a signed executable is released, download it from GitHub Releases, run it,
start Bongo, and choose its Bangla typing mode from the tray icon. See the
[Windows release checklist](docs/WINDOWS-RELEASE.md).

## Updates

Release builds check **GitHub Releases** and open the release page when a newer
version exists. Bongo never silently replaces a running input method.

[Open Bongo Releases](https://github.com/mehedishakeel/Bongo/releases)

- macOS: Bongo → Preferences → **Check for Updates**.
- Linux: Bongo menu → **Check for updates**. The optional startup check follows
  the existing preference.
- Windows development build:
  `./platforms/windows/scripts/check-update.ps1 -Open`.

Repository owners should read [the release guide](docs/RELEASING.md). Set
`BONGO_GITHUB_REPOSITORY=mehedishakeel/Bongo` to override the repository used by
release packaging. The packaged defaults already point to the official Bongo
repository.

## Source layout

- `platforms/macos` — native InputMethodKit app, engine and DMG creator
- `platforms/linux` — native IBus/Qt application and DEB creator
- `platforms/windows` — Delphi Win32 port and EXE creator
- `assets` — Bongo branding and cross-platform source icons
- `vendor/rust` — pinned Rust crates for reproducible macOS builds
- `scripts` — shared testing, update-manifest and source-archive helpers

Unmodified upstream checkouts are not needed in the repository. Exact source
revisions remain recorded in [upstream.lock.json](upstream.lock.json).

## Upstream projects and credit

Bongo is an independent derivative project. It is not an official release or
endorsement from these projects:

- [OmicronLab Avro Keyboard](https://github.com/omicronlab/Avro-Keyboard) —
  Windows keyboard foundation, MPL-1.1.
- [Lekho](https://github.com/ARahim3/Lekho) — macOS InputMethodKit foundation,
  MPL-2.0.
- [OpenBangla Keyboard](https://github.com/OpenBangla/OpenBangla-Keyboard) —
  Linux IBus/Qt foundation, GPL-3.0-or-later.
- [riti](https://github.com/OpenBangla/riti) — Bangla phonetic engine used on
  macOS and Linux, MPL-2.0.

Copyright and license headers from the original sources remain intact. Read
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the files under
[licenses](licenses) before redistributing Bongo.

The Bongo name, new interface, integration, packaging, and logo are the work of
Mehedi Shakeel. The logo is original and does not reuse upstream artwork.
