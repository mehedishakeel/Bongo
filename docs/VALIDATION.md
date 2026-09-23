# Validation status

## macOS ARM64

The native Swift/InputMethodKit app and Rust engine compiled on Apple Silicon.
The inherited controller integration suite passed all assertions against a mock
IMKTextInput client: phonetic output, candidate ordering and selection, remembered
choices, punctuation, emoji settings, smart/phonetic modes, backspace, digits, tab,
composition commit, changing clients, switching modes and corrupt-data recovery.

These tests exercise the real input controller and engine. They do not establish
compatibility with every real app. Bongo has also been installed as a macOS input
source and verified after logging back in. Broader third-party application coverage,
secure fields, restart behavior, and signed/notarized distribution remain manual
acceptance steps for each release.

The setup window and typing-settings tab were also opened and visually checked.
The app executable is Mach-O arm64 and its ad-hoc signature verifies.

## Linux / Windows

Source identity/resource checks only. Native OS compilation and end-to-end typing
are unverified. Windows additionally requires the documented proprietary toolchain,
third-party dependencies and missing runtime assets. No binaries are claimed.

## Before release

Create artifacts on each OS, complete real-app typing and installation tests, audit inherited
legacy behavior, resolve runtime payloads, replace remaining legacy artwork, sign the
binaries where applicable, and publish corresponding source and license notices.
