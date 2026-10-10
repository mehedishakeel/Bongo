# Project audit

Last reviewed: 2026-09-29

## Scope reviewed

The audit covered macOS native entry points, Apple Silicon architecture targets, packaging scripts, update mechanisms, bundled assets, tests, licenses, Rust dependency locks, and repository hygiene.

## Architecture focus: Apple Silicon macOS

- **Removed Linux and Windows support**: Eliminated legacy Linux IBus/Qt and Windows Delphi platforms, release scripts, packaging configurations, and platform documentation.
- **Dedicated Apple Silicon build**: Configured macOS build strictly for `arm64` (`aarch64-apple-darwin`), removing universal binary compilation and Intel `x86_64` targets. Added `LSArchitecturePriority = ["arm64"]` to application property lists.
- **Streamlined upstream dependencies**: Pinned only required macOS upstream components (`Lekho` and `riti-macos`). Removed unneeded Linux (`OpenBangla-Keyboard`) and Windows (`Avro-Keyboard`) entries from lockfiles.
- **License cleanup**: Retained MPL-2.0 for macOS and vendored Rust engine dependencies; removed unused GPL-3.0 and MPL-1.1 text files.
- **Continuous Integration**: Streamlined GitHub Actions to validate repository invariants and run native Apple Silicon integration tests on macOS runners.

## Retained intentionally

- `vendor/rust` contains the dependency tree for the macOS phonetic engine static library (`libavrobangla_engine.a`).
- Upstream attribution headers and licenses are preserved in `THIRD_PARTY_NOTICES.md` and `licenses/`.
