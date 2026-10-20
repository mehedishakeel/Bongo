# Bongo fcitx5 Linux Frontend Design

## Intent

Bongo is a cross-platform Bangla phonetic input method. Linux currently has one frontend, an IBus engine. That works on GNOME, but it is not the native path on KDE Plasma, Omarchy, or Hyprland. The product goal is a polished Bongo everywhere, with native integration on each platform and one shared phonetic engine.

This design adds a first-class fcitx5 frontend for Linux. It is a thin adapter over Bongo's existing Rust engine, not a second engine. IBus remains in place for GNOME. fcitx5 becomes the preferred frontend on desktops where it is the native input framework.

## Goals

- Ship an installable fcitx5 addon named `bongo`.
- Reuse the existing `libbongo_engine.so` C ABI and the existing `~/.config/bongo/settings.json`.
- Match the IBus engine's typing behavior: preedit, candidates, commit, backspace, escape, candidate navigation, and number selection.
- Work on Arch/Omarchy first, then Debian/Fedora packaging.
- Keep IBus working and unchanged.
- Make installation and first-run setup understandable and repeatable.
- Add automated checks for the addon metadata, build, settings parser, and repository integration.

## Non-Goals

- No transliteration, dictionary, ranking, or candidate-quality changes in this project. Minimal Linux engine fixes needed to make the existing settings effective and to prevent crashes are in scope; they must not change Avro output for existing modes.
- No custom fcitx5 candidate window or theme in v1. Use fcitx5's native candidate panel.
- No changes to macOS, Windows, or Android frontends.
- No replacement of IBus on GNOME.
- No fork of OpenBangla or reuse of its GPL frontend code.
- No user-local fcitx5 addon installation as the supported path. fcitx5 addon discovery is system-wide.

## Anti-Goals

- A second Avro implementation that drifts from the Rust engine.
- A frontend that only works in one application or one compositor.
- An installer that silently edits a user's fcitx5 profile or breaks an existing input method.
- A build that requires fcitx5 to be the only input framework on the machine.

## Constraints

- fcitx5 5.1.0 or newer; C++17; CMake.
- Bongo remains MPL-2.0. New files use MPL-2.0 SPDX headers.
- The addon loads the engine dynamically. The engine may be installed in `lib`, `lib64`, or a multiarch directory.
- Addon data lives under `${PREFIX}/share/fcitx5`; addon library under `${PREFIX}/lib*/fcitx5`.
- Input method metadata: name `Bongo`, language `bn`, icon `bongo`, label `ব`, addon `bongo`.
- Candidate page size is 9, with labels `1` through `9`.
- Settings are read from `~/.config/bongo/settings.json`; the only v1 fields are `typing_mode` (0/1/2) and `suggest_emoji` (boolean).
- The fcitx5 candidate font is controlled by fcitx5's theme, not by Bongo's `candidate_font` setting. This is documented, not worked around.

## Architecture

```
platforms/linux/fcitx5/
├── CMakeLists.txt
├── README.md
├── data/
│   ├── bongo-addon.conf.in      # fcitx5 addon metadata
│   └── bongo.im.conf            # fcitx5 input method entry
├── src/
│   ├── bongo.cpp                # addon, engine class, key handling, UI
│   ├── bongo_api.h/.cpp         # dlopen wrapper around libbongo_engine
│   ├── bongo_settings.h/.cpp    # settings.json reader
│   └── bongo_state.h/.cpp       # per-input-context state
└── tests/
    └── test_settings.cpp
```

The addon is a `fcitx::InputMethodEngine`. It registers one input context property factory. Each fcitx5 input context gets its own `BongoState`, which owns one engine instance and one candidate list. There is no shared composition buffer.

`BongoApi` resolves and loads `libbongo_engine.so` from, in order:

1. `BONGO_ENGINE_LIB`, if set.
2. The addon-relative path `$ORIGIN/../bongo/libbongo_engine.so`.
3. Standard system paths: `/usr/lib/bongo`, `/usr/lib64/bongo`, `/usr/lib/x86_64-linux-gnu/bongo`, `/usr/lib/aarch64-linux-gnu/bongo`, `/usr/local/lib/bongo`.
4. `$HOME/.local/lib/bongo`.
5. The dynamic loader's default search path.

If the library cannot be loaded, the addon logs a clear error and lets key events pass through. It must not crash fcitx5.

### Engine settings and crash safety

The current Linux wrapper exposes `bongo_engine_set_mode` and `bongo_engine_set_emoji`, but the native path does not apply them fully. This project corrects that because the fcitx5 settings path must have visible behavior.

- `Phonetic first`: dictionary and phonetic candidates, no learning from candidate commits.
- `Smart suggestions`: dictionary and phonetic candidates, with candidate selections recorded for future ranking.
- `Phonetic only`: direct phonetic transliteration only, with no dictionary candidate list.
- Emoji suggestions are gated by the `suggest_emoji` setting. The `riti` config gains an `include_emoji` flag, defaulting to `true` so macOS, Windows, Android, and existing IBus behavior are unchanged.
- The Linux wrapper recreates its contexts when the typing mode changes. It updates the config when only emoji changes.
- The user data directory is created before writing learned selections, and a failed write must not panic the input method.

These changes stay inside the Linux engine wrapper and the shared `riti` config. They do not alter Avro transliteration rules or dictionary ranking.

## Behavior

The frontend mirrors `platforms/linux/ibus/bongo_ibus_engine.py`.

| Input | Behavior |
|---|---|
| Printable character | Feed the Unicode codepoint to the engine; consume if the engine handles it. |
| Space | Commit the selected candidate, then let the space reach the application. |
| Enter / keypad Enter | Commit the selected candidate and consume the key. |
| Backspace | Call the engine's backspace; consume. |
| Escape | Reset the composition and clear the panel; consume. |
| Up / Page Up | Move to the previous candidate; consume. |
| Down / Page Down | Move to the next candidate; consume. |
| Tab / Shift+Tab | Move to the next / previous candidate; consume. |
| `1`–`9` | Commit that candidate index when a composition has more than one candidate; consume. |
| Ctrl / Alt / Super combination | If composing, commit the current candidate, then pass the key through. |
| Key release | Ignore. |

The engine receives the current candidate cursor index as its `selection` argument, matching the IBus engine. Shift state is passed as the engine's modifier argument.

If a printable key is not handled by the native engine while a composition is active, the addon commits the current candidate and passes the key through. It must never leave a dangling preedit. The same rule applies when the engine library is missing.

On input-method switch or focus loss, the addon commits the active composition to match IBus's `do_focus_out` behavior. An explicit reset event or Escape discards it instead. The exact fcitx5 lifecycle hook is verified during integration testing and adjusted if fcitx5 delivers focus-out as a reset rather than a deactivate.

Preedit is shown inline when the client supports preedit, otherwise in fcitx5's panel. The candidate list is rebuilt after each engine update. Mouse selection uses the same commit path as keyboard selection.

Settings are reloaded when the file's modification time changes. Invalid or missing settings fall back to Bongo's defaults: phonetic-first mode, emoji suggestions on.

## Installation

`platforms/linux/scripts/install.sh` continues to install the IBus frontend when IBus is available. It also detects fcitx5 and its development headers. When both are present, it builds and installs the fcitx5 addon system-wide.

The installer must remain usable on a machine that has only one of the two frameworks. A machine with neither is an error.

When `DESTDIR` is set, the installer must not use runtime `command -v` detection to decide package contents. It builds every frontend whose build dependencies are present. `BONGO_FCITX5=1` forces the addon, `BONGO_FCITX5=0` disables it, and `auto` is the interactive default. Packaging scripts set `BONGO_FCITX5=1` and install the fcitx5 headers in the build environment.

If the installer is run without root and fcitx5 is present, it installs the IBus frontend as before, skips the system-wide fcitx5 addon, and prints the exact `sudo` command needed to finish. It must not create a user-local fcitx5 addon that fcitx5 will not discover.

A separate helper, `platforms/linux/scripts/configure-fcitx5.py`, adds `bongo` to the active fcitx5 profile. It must:

- Edit the invoking user's profile, not root's, when run through `sudo` (`SUDO_USER`).
- Respect `XDG_CONFIG_HOME`, falling back to `~/.config/fcitx5/profile`.
- Back up the profile before changing it.
- Be idempotent: never add a duplicate `bongo` entry.
- Add `bongo` to the first group in `[GroupOrder]`, not every group.
- Leave `DefaultIM`, existing item order, and existing layouts unchanged.
- Leave the profile untouched if its structure is not understood.
- Print the manual steps if it cannot make the change.
- Never remove or reorder existing input methods.

The helper is installed as `bongo-fcitx5-setup` so it can be re-run. It does not stop or restart fcitx5; it prints that fcitx5 must be restarted or the user must log out and back in.

The installer does not overwrite `GTK_IM_MODULE`, `QT_IM_MODULE`, or `XMODIFIERS`. On Omarchy these are already set for fcitx5. On other distributions the installer prints the relevant values when fcitx5 is present.

## Packaging

- Arch: the source installer is the first supported path. An AUR-style `PKGBUILD` may be added after the addon is proven.
- Debian: the existing `.deb` builder includes the fcitx5 addon when built with fcitx5 headers. `ibus`, `fcitx5`, and their bridge libraries become recommends, not hard dependencies. Python/GTK settings dependencies remain required.
- Fedora: the existing `.rpm` builder follows the same rule.
- Both frontends ship in the same `bongo` package. The package must not force a GNOME/IBus user to install fcitx5, or a KDE/fcitx5 user to install IBus.
- If the fcitx5 headers are older than 5.1, the addon build is skipped with a warning. Forced builds (`BONGO_FCITX5=1`) fail clearly instead of producing a broken addon.

## Testing

1. C++ unit test for the settings parser: defaults, valid values, malformed JSON, missing file.
2. Rust engine tests for typing modes, emoji gating, learned-selection write safety, and a missing user data directory.
3. Static repository test for fcitx5 metadata, install paths, and the absence of GPL code.
4. Build test: configure and build the addon against fcitx5 5.1.x.
5. Integration test on Omarchy:
   - Load the addon and confirm `bongo` appears in fcitx5's input method list.
   - Type `ami`, confirm the preedit/candidates, select with space and with `1`.
   - Test backspace, escape, arrows, Tab, and a Ctrl shortcut.
   - Test in a GTK4 entry and a terminal.
   - Confirm settings changes take effect after the file changes, including mode and emoji.
   - Confirm focus-out commits and Escape discards.
6. Regression test: run the existing Python test suite. The IBus files and behavior remain unchanged.

## Review Focus

- Key event parity: space must commit and still insert a space; Enter must commit without a newline; Escape must cancel.
- Engine discovery across Arch (`lib`), Fedora (`lib64`), and Debian multiarch layouts.
- Per-input-context isolation and engine cleanup; no shared composition buffer.
- Settings reload with malformed or missing JSON, and visible mode/emoji changes.
- Installer profile editing idempotency and safe failure, including the `sudo`/`SUDO_USER` path.
- Non-ASCII and shifted characters reaching the engine as the correct Unicode codepoint.
- Candidate selection by mouse and keyboard committing exactly once.
- Missing engine library: addon still loads, logs, and passes keys through.
- IBus installation and behavior unchanged.

## Decisions Left to the Builder

- Exact split of C++ files and helper functions.
- Whether to use `std::filesystem` or POSIX `stat` for settings mtime.
- Exact CMake install variable handling across distributions.
- Whether the profile helper is invoked by default or only with an explicit flag.
- The precise manual test application used on Omarchy.
