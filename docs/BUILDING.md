# Build Bongo from source

Build each package on its matching operating system. The scripts create release
artifacts; they do not install Bongo. Run the scripts as a normal user, without
`sudo` or an Administrator PowerShell session.

Clone the repository before following a platform section:

```sh
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo
```

The first Rust build needs internet access to download locked dependencies.

## macOS DMG

### Requirements

- Apple Silicon Mac running macOS 13 or later
- Xcode Command Line Tools, which provide Swift, Clang, codesign, lipo, ditto
  and the macOS disk-image tools
- Rust stable with Cargo and the `aarch64-apple-darwin` target
- Homebrew only when using the package command below to install rustup

Install the tools:

```sh
xcode-select --install
brew install rustup
export PATH="$(brew --prefix rustup)/bin:$PATH"
rustup default stable
rustup target add aarch64-apple-darwin
```

Create the DMG from the repository root:

```sh
./platforms/macos/scripts/create-dmg.sh
```

The output is `platforms/macos/release/Bongo-1.0-macos-arm64.dmg`. The DMG shows
only `Bongo.app` and the Applications shortcut. The signed input method is embedded
inside Bongo and is copied to the user's Input Methods folder on first launch.
Public distribution should replace the script's ad-hoc signature with an Apple
Developer ID signature and notarization.

The optional universal build also needs:

```sh
rustup target add x86_64-apple-darwin
./platforms/macos/scripts/create-dmg.sh release true
```

## Debian/Ubuntu DEB

### Requirements

- A Debian or Ubuntu system using IBus
- GNU C and C++ toolchain and Make
- CMake and CPack
- Rust compiler, Cargo and rustdoc
- pkg-config and Debian packaging tools
- Qt 5 Widgets/Network, IBus and zstd development files

Install every required package:

```sh
sudo apt update
sudo apt install build-essential cmake cargo rustc pkg-config dpkg-dev qtbase5-dev libibus-1.0-dev libzstd-dev
```

Create the DEB from the repository root:

```sh
./platforms/linux/scripts/create-deb.sh
```

The package is written under `platforms/linux/release/` as
`Bongo_1.0-ARCHITECTURE.deb`. The script uses one build job by default so compiler
errors remain readable. Set `BONGO_BUILD_JOBS` to use more jobs. Install the
package separately as described in [LINUX-INSTALL.md](LINUX-INSTALL.md).


## Validation

Repository checks can be run on macOS or Linux with Python 3:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Native typing and packaging must still be tested on each target operating
system. See [VALIDATION.md](VALIDATION.md).
