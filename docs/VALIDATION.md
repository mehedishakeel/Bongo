# Validate Bongo

Run repository checks from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

GitHub Actions repeats these checks and runs the macOS InputMethodKit integration suite on Apple Silicon on each push and pull request.

## Release checks

Automated integration tests cover macOS phonetic output, candidates, learned choices, punctuation, emoji settings, typing modes, editing, composition handoff, and corrupt-data recovery.

Before a release:
1. Build the Apple Silicon DMG: `./platforms/macos/scripts/create-dmg.sh`.
2. Test installation via `Bongo.app` drag-and-drop.
3. Test activation under macOS System Settings → Keyboard → Input Sources.
4. Verify typing in real applications (Safari, TextEdit, Notes, Terminal).
5. Verify candidate selection, layout viewer, settings panel, and update check dialog.
