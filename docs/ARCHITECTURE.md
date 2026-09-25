# Bongo architecture

Bongo is one product with separate native front ends. No shared cross-platform
UI framework or web runtime is used.

## macOS

The application is an InputMethodKit input method written in Swift. The process
starts in `Bongo/Sources/main.swift`; `BongoInputController` receives key events,
and `BongoEngine` owns one process-wide riti context. A small AppKit settings and
welcome window shares the same bundle. The Rust engine is linked as a static
library and its dependencies are locked and vendored for reproducible builds.

## Linux

The input engine is a native IBus component in `src/engine/ibus/main.cpp`. The
settings/top-bar application starts in `src/frontend/main.cpp` and uses Qt 5.
Both use the local Rust riti engine through its C interface. CMake builds the
components and CPack creates the Debian package.

The settings application asks the GitHub Releases API for the latest published
release. It never downloads or installs an update itself.

## Windows

The Windows port is the legacy Delphi 2010 Win32 codebase. Its entry point is
`Keyboard and Spell checker/Bongo.dpr`. It needs commercial/third-party Delphi
packages and runtime data that are not stored in this repository, so the current
script can compile only after a maintainer supplies those dependencies. The
additional layout editor, skin designer, converter, and spell-checker projects
remain because the main application still exposes those optional companion
features; they are not part of the current single-EXE build.

## Releases and updates

Platform scripts only create artifacts and live under each matching platform.
Installation is manual from GitHub Releases. macOS and Linux check GitHub for a
newer release and open its page after the user agrees. CI validates repository
invariants, the Linux build/package, and macOS integration behavior.
