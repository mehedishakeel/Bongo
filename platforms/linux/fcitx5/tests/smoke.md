# fcitx5 manual smoke test

Run after installing the addon system-wide and restarting fcitx5.

Once on Hyprland/Wayland (Omarchy), all boxes below were verified on
2026-10-20 with fcitx5 5.1.23 using a GTK4 test app, a Qt6 test app, foot,
and VS Code under `wtype` key injection. The remaining unchecked items need
a GNOME session or manual interaction.

## Addon and input method

```bash
fcitx5-remote -n
fcitx5-configtool
```

- [x] `Bongo` appears in the input method list (`fcitx5-remote -m bongo`).
- [x] Selecting it does not require a logout or `fcitx5-remote -r`.
- [x] `Ctrl+Space` switches to Bongo; `fcitx5-remote -o` + `-s bongo` also work.

## GTK4 application

- [x] Type `ami`; the preedit is `আমি` and the candidate panel shows candidates.
- [x] `Space` commits `আমি` and still inserts a space.
- [x] Type `ami`, press `2`; `আমই` is committed.
- [x] `Backspace` edits the preedit.
- [x] `Escape` clears the preedit without committing.
- [x] `Down`/`Up` move between candidates and the preedit follows.
- [x] `Ctrl+C` while composing commits the current candidate and the shortcut
      reaches the application.
- [x] Focus another window while composing: exactly one commit, never duplicated
      (fcitx5 commits the client preedit itself; Bongo no longer commits again).
- [x] Digits are typed as text while only one candidate exists; `Shift+digits`
      types the shifted character.
- [x] `PageUp`/`PageDown` select the previous/next candidate (matching the IBus
      engine, not IBus's page semantics).

## Settings

Edit `~/.config/bongo/settings.json` and wait for the next key event; no
restart is required.

```json
{"typing_mode": 2, "suggest_emoji": false}
```

- [x] `ami` still commits `আমি`, but the candidate panel contains one direct
      transliteration (`typing_mode: 2`).
- [x] Type `:)`; the emoji candidate disappears with `suggest_emoji: false`
      and returns with `true`.

## Smart mode crash safety

```json
{"typing_mode": 1}
```

- [ ] Remove `~/.local/share/openbangla-keyboard` before selecting a candidate
      in Smart mode. Selecting a candidate must not crash fcitx5; the directory
      is recreated on the next selection.

## Other applications

- [x] Qt6 application: preedit, commit, and Backspace work; focus-out commits
      exactly once.
- [x] Electron application (VS Code, Wayland + `--enable-wayland-ime`):
      preedit and commit work; focus-out commits exactly once.
- [x] Terminal (foot): preedit and commit work; the exact bytes of
      `ami ` + commit are `আমি `.

## Native addon configuration (fcitx5-configtool)

- [x] `fcitx://config/addon/bongo` GetConfig returns values and the
      description (Enum `typing_mode` with Phonetic First/Smart/Phonetic
      Only, Boolean `suggest_emoji`) over DBus.
- [x] `SetConfig` from the config tool writes `~/.config/bongo/settings.json`
      (verified: `typing_mode` 0→2, `suggest_emoji` true→false) while
      preserving unrelated keys (`candidate_font`, `candidate_font_size`).
- [x] The addon reloads `settings.json` changes without a restart; GetConfig
      reflects restored values immediately.
- [x] Typing still works after reinstalling the reconfigured addon
      (`ami ` + Space commits `আমি ` in foot).

## Regression

- [ ] GNOME/IBus still works after installation (the fcitx5 changes must not
      remove or alter the IBus engine). Not verifiable on the test machine
      (no IBus installed); the fcitx5 work is additive but a GNOME check is
      still recommended.
