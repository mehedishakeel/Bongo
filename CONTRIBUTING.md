# Contributing to Bongo · বঙ্গ

Thank you for your interest in improving Bongo! This guide explains how to get started, what to work on, and how to get your changes merged.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Ways to Contribute](#ways-to-contribute)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Branch & Commit Conventions](#branch--commit-conventions)
6. [Running Tests](#running-tests)
7. [Submitting a Pull Request](#submitting-a-pull-request)
8. [Reporting Issues](#reporting-issues)
9. [Phonetic Engine & Rust](#phonetic-engine--rust)
10. [Release Process](#release-process)

---

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) as our baseline standard. Harassment of any kind is not tolerated.

---

## Ways to Contribute

| Type | Examples |
|------|---------|
| 🐛 **Bug fixes** | IME crash, wrong transliteration, missing candidate |
| ✨ **Features** | New theme, layout option, keyboard shortcut |
| 📖 **Documentation** | Installation guides, wiki pages, code comments |
| 🌐 **Translations** | Bengali (`bn`) strings in `docs/translations.js` |
| 🧪 **Tests** | New unit tests in `tests/`, platform integration tests |
| 🎨 **UI / Design** | Website improvements, Android settings polish |

---

## Development Setup

### Prerequisites

| Platform | Requirements |
|----------|-------------|
| **All** | Git, Python 3.10+, Rust + Cargo (stable) |
| **Android** | JDK 17, Android SDK, Gradle |
| **macOS** | Xcode 15+, Swift 5.9+ |
| **Linux** | GCC / Clang, CMake ≥ 3.16, IBus dev headers, fcitx5 dev headers |
| **Windows** | Python 3.10+, MSVC or MinGW |

### Clone & initial test

```bash
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo
python3 -m unittest discover -s tests -v
```

All 46 tests should pass before you make any changes.

### Platform-specific builds

```bash
# Android (debug APK)
cd platforms/android && ./gradlew assembleDebug

# macOS DMG
./platforms/macos/scripts/create-dmg.sh release

# Linux (system install from source)
sudo ./platforms/linux/scripts/install.sh

# Windows
platforms\windows\scripts\build-windows.bat
```

---

## Project Structure

```
Bongo/
├── platforms/
│   ├── android/        # Kotlin IME (BongoInputMethodService, BongoKeyboardView, SettingsActivity)
│   ├── macos/          # Swift + InputMethodKit (InputController, CandidatePanel, Engine)
│   ├── linux/          # Python IBus engine + C++ fcitx5 addon
│   ├── windows/        # Python tray app + settings
│   └── common/         # Pure-Python phonetic converter (fallback; also used by tests)
├── docs/               # Static website (getbongo.app) + markdown docs
│   ├── index.html      # Main site
│   ├── app.js          # Website JS
│   ├── translations.js # EN / BN i18n strings
│   └── releases/       # Release notes per version
├── tests/              # Cross-platform unit tests (Python unittest)
├── wiki/               # GitHub Wiki source files
├── .github/workflows/  # CI/CD (ci.yml, release.yml, build-windows-release.yml)
└── vendor/rust/        # Vendored Rust crates (do not edit manually)
```

> **Important**: `docs/install.sh` and `platforms/linux/scripts/install.sh` must remain byte-for-byte identical. Any change to either file must be mirrored to the other.

---

## Branch & Commit Conventions

### Branches

| Branch | Purpose |
|--------|---------|
| `main` | Stable, always releasable |
| `dev` | Integration branch — open PRs against this |
| `feat/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation only |

**Always branch from `dev`, not `main`.**

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(android): add swipe-to-type gesture input
fix(macos): candidate panel flicker on retina display
docs: add CONTRIBUTING.md
chore(ci): add test coverage reporting
```

Allowed types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `perf`, `style`.

---

## Running Tests

```bash
# Full test suite (all platforms cross-validated)
python3 -m unittest discover -s tests -v

# Single test file
python3 -m unittest tests.test_converter -v

# With coverage (requires pytest-cov)
pip install pytest pytest-cov
pytest tests/ --cov=platforms/common --cov-report=term-missing
```

The CI pipeline runs on every push to `main` and `dev`. **PRs must pass all tests**.

### Version consistency check

```bash
python3 tests/verify_release.py
```

This checks that the version string is consistent across all 12 version-bearing files. Update all of them together when bumping the version.

---

## Submitting a Pull Request

1. **Fork** the repo and create a branch from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feat/my-feature
   ```

2. **Make your changes** and add/update tests as appropriate.

3. **Run the test suite** and make sure everything passes:
   ```bash
   python3 -m unittest discover -s tests -v
   ```

4. **Commit** using the convention above.

5. **Open a PR** against the `dev` branch (not `main`).

6. Fill in the PR template:
   - What does this change?
   - Why is it needed?
   - How was it tested?
   - Screenshots if UI-related.

7. A maintainer will review and merge. CI must be green before merge.

---

## Reporting Issues

Use [GitHub Issues](https://github.com/mehedishakeel/Bongo/issues).

Include:
- **Platform & version** (e.g., Android 14, macOS 15.1, Ubuntu 24.04)
- **Bongo version** (e.g., 1.2.1)
- **Steps to reproduce**
- **Expected vs actual behaviour**
- **Logs or screenshots** if applicable

For Android: attach logcat output with tag `BongoIME`.
For macOS: check Console.app filtered by `BongoIME`.

---

## Phonetic Engine & Rust

The Rust phonetic engine lives in `platforms/<os>/engine/` for each platform (they share the same source via symlinks or cargo workspace). Key crates:

- **`riti`** – Core phonetic automaton (vendored from OpenBangla)
- **`fst`** – Finite-state transducer for dictionary lookups
- **`emojicon`** – Emoji search

If you change engine logic, run Rust tests too:

```bash
cd platforms/linux/engine
cargo test
```

The engine exposes a C FFI header (`engine.h`) used by Swift (macOS) and C++ (fcitx5). Keep the ABI stable — adding new exported functions is fine, changing or removing existing ones is a breaking change.

---

## Release Process

Releases are managed by the maintainer. The full process is documented in [docs/RELEASING.md](docs/RELEASING.md).

In brief:
1. All version strings in 12 files are bumped together.
2. `tests/verify_release.py` must pass.
3. A tag `vX.Y.Z` is pushed; CI builds all platform artifacts automatically.
4. GitHub Release is created with all artifacts attached.
5. `docs/install.sh` and the website are updated to match the new version.

---

*Happy contributing! 🥁*
