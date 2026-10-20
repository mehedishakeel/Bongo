# fcitx5 manual smoke test

Run after installing the addon system-wide and restarting fcitx5.

## Addon and input method

```bash
fcitx5-remote -n
fcitx5-configtool
```

- [ ] `Bongo` appears in the input method list.
- [ ] Selecting it does not require a logout.
- [ ] `Ctrl+Space` switches to Bongo.

## GTK4 application

- [ ] Type `ami`; the preedit is `আমি` and the candidate panel shows four
      candidates.
- [ ] `Space` commits `আমি` and still inserts a space.
- [ ] Type `ami`, press `1`; the first candidate commits.
- [ ] Type `ami`, press `2`; `আমই` is committed.
- [ ] `Backspace` edits the preedit.
- [ ] `Escape` clears the preedit without committing.
- [ ] `Down`, `Tab`, `PageDown`, `Up`, and `PageUp` move the candidate page
      and the preedit follows the selected candidate.
- [ ] `Ctrl+C` while composing commits the current candidate and the shortcut
      reaches the application.
- [ ] Focus another window while composing; the composition must not be left
      dangling in the old window.

## Settings

Edit `~/.config/bongo/settings.json` and wait for the next key event; no
restart is required.

```json
{"typing_mode": 2, "suggest_emoji": false}
```

- [ ] `ami` still commits `আমি`, but the candidate panel contains one direct
      transliteration.
- [ ] Type `:)`; the emoji candidate is no longer present.
- [ ] Set `suggest_emoji` back to `true`; `:)` shows the emoji again.

## Smart mode crash safety

```json
{"typing_mode": 1}
```

- [ ] Remove `~/.local/share/openbangla-keyboard` before selecting a candidate
      in Smart mode. Selecting a candidate must not crash fcitx5; the directory
      is recreated on the next selection.

## Other applications

- [ ] Qt application (for example `systemsettings`): preedit, candidates,
      commit, and Backspace work.
- [ ] Electron application (for example VS Code): preedit and commit work.
- [ ] Terminal (foot, Alacritty, or Kitty): preedit and commit work; the
      candidate panel is visible.

## Regression

- [ ] GNOME/IBus still works after installation (the fcitx5 changes must not
      remove or alter the IBus engine).
