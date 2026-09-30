# Bongo architecture

Bongo is a native Bangla input method built specifically for macOS on Apple Silicon.

## macOS (Apple Silicon)

The application is an InputMethodKit input method written in Swift, targeting Apple Silicon (`arm64`). The process starts in `Bongo/Sources/main.swift`; `BongoInputController` receives key events, and `BongoEngine` owns one process-wide riti context. A lightweight AppKit settings and layout guide window shares the same bundle. The Rust phonetic engine (`avrobangla_engine`) is linked as a static library targeting `aarch64-apple-darwin`, and its dependencies are locked and vendored for reproducible builds.

A companion launcher application (`Launcher/Sources/main.swift`) embeds the input method bundle (`Contents/Library/Input Methods/Bongo Input Method.app`) and installs it to `~/Library/Input Methods` upon user approval, presenting a clean drag-and-drop installer workflow.

## Releases and updates

The build script creates the release DMG under `platforms/macos/release`. Installation is handled natively. Bongo checks the GitHub Releases API for a newer release and opens its download page after the user agrees. CI validates repository invariants and runs Apple Silicon InputMethodKit integration tests.
