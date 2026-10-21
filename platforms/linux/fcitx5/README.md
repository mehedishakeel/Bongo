# Bongo for fcitx5

Native fcitx5 frontend for Bongo's Rust Avro phonetic engine.

The addon is a C++20 `fcitx::InputMethodEngine` that:

- Loads `libbongo_engine.so` at runtime; no link-time dependency on Bongo's
  engine ABI.
- Keeps one engine instance per fcitx5 input context.
- Maps Bongo candidates to fcitx5's native preedit and candidate panel.
- Reads Bongo's `~/.config/bongo/settings.json` for typing mode and emoji
  suggestions.
- Exposes both options to fcitx5-configtool's native "Addons > Bongo"
  configuration page. Changes there are written back to
  `~/.config/bongo/settings.json` (all other keys, such as
  `candidate_font`, are preserved), so the GUI, IBus and fcitx5 stay in
  sync through one settings file.
- Matches the IBus frontend's key behavior: Space/Enter commit, Escape resets,
  Backspace edits, Tab/Up/Down/PageUp/PageDown navigate, `1`-`9` select, and
  Ctrl/Alt/Super commit the composition and pass the shortcut through.

## Build

```bash
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build/fcitx5
```

Requirements: fcitx5 5.1+ development headers, CMake 3.16+, and a C++20
compiler.

## Test

```bash
export BONGO_ENGINE_LIB="$PWD/platforms/linux/engine/target/release/libbongo_engine.so"
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build/fcitx5
ctest --test-dir build/fcitx5 --output-on-failure
```

The CTest integration test needs fcitx5's `testfrontend` addon. If it is not
installed, the unit tests still run and the integration target is skipped.

See `tests/smoke.md` for the manual GTK/Qt/Electron/terminal checklist.

## Install

The addon must be installed system-wide:

```bash
sudo cmake --install build/fcitx5
```

The default install paths come from fcitx5's CMake package:

- Addon library: `${FCITX_INSTALL_ADDONDIR}/libbongo.so`
- Addon metadata: `${FCITX_INSTALL_PKGDATADIR}/addon/bongo.conf`
- Input method metadata: `${FCITX_INSTALL_PKGDATADIR}/inputmethod/bongo.conf`

The addon searches for the engine next to itself and in the standard
`/usr/lib*/bongo` locations. The main installer places it at
`/usr/lib/bongo/libbongo_engine.so`.

## Enable

The installer adds **Bongo** to your fcitx5 input-method profile, restarts
fcitx5 (using its systemd user unit when one owns the process), and adds a
session autostart entry unless systemd or your distribution already starts
fcitx5. Switch with <kbd>Ctrl + Space</kbd>.

To configure it by hand instead:

```bash
fcitx5-configtool
```

Add **Bongo** under **Input Method**, apply, and restart fcitx5:

```bash
fcitx5-remote -r
```

The candidate font follows the fcitx5 theme; Bongo's `candidate_font` setting
is used by the IBus frontend only.

## Profile helper

The repository ships `platforms/linux/scripts/configure-fcitx5.py`, installed as
`bongo-fcitx5-setup`. It appends Bongo to the first fcitx5 input-method group,
preserves existing order, and makes a backup before editing. It never restarts
fcitx5 or overwrites unrelated settings.

Because fcitx5 rewrites its profile when it exits, run the helper only while
fcitx5 is stopped:

```bash
fcitx5-remote -e          # stop fcitx5
bongo-fcitx5-setup        # edit the profile
fcitx5 -d                 # start fcitx5 again
```

The Bongo installer performs this stop-configure-restart sequence for you.
