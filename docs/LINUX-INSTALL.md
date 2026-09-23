# Install Bongo on Linux

Download the current `.deb` from the project's GitHub Releases page.

## Install the DEB

Install the resulting package, then restart IBus:

```sh
sudo apt install ./Bongo_*.deb
ibus restart
```

Select Bongo in your desktop's Keyboard/Input Sources settings and restart your
session if necessary. The filename suffix can depend on `DIST`.

The desktop entry opens Bongo settings. IBus must be configured by the desktop:
this is not a standalone key-injection daemon. Wayland compatibility depends on
that desktop/application's IBus integration. Fcitx is not implemented.

Release builds check the `linux.json` attached to the latest GitHub Release when
requested, and optionally at startup when that preference is enabled. The updater
opens a release page and does not replace packages. Native typing and package
removal should be validated on supported Linux desktops before each release.
