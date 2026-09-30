# Build Bongo from source

Bongo is built for macOS on Apple Silicon. The script creates release artifacts; it does not install Bongo. Run the script as a normal user without `sudo`.

Clone the repository:

```sh
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo
```

## macOS DMG (Apple Silicon)

### Requirements

- Apple Silicon Mac running macOS 13 or later
- Xcode Command Line Tools, which provide Swift, Clang, codesign, ditto, and macOS disk-image tools
- Rust stable with Cargo and the `aarch64-apple-darwin` target
- Homebrew (recommended for managing toolchains)

Install the tools:

```sh
xcode-select --install
brew install rustup
export PATH="$(brew --prefix rustup)/bin:$PATH"
rustup default stable
rustup target add aarch64-apple-darwin
```

Create the Apple Silicon DMG from the repository root:

```sh
./platforms/macos/scripts/create-dmg.sh
```

The output is `platforms/macos/release/Bongo-1.0-macos-arm64.dmg`. The DMG provides `Bongo.app` and an Applications shortcut. The signed input method is embedded inside `Bongo.app` and is copied to the user's `~/Library/Input Methods` folder on launch.

Public distribution should replace the script's ad-hoc signature with an Apple Developer ID signature and notarization.

## Validation

Repository checks can be run on macOS with Python 3:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

See [VALIDATION.md](VALIDATION.md) for details.
