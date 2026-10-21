# Building Bongo from Source

This guide covers building release packages for macOS, Linux, and Windows.

Clone the repository:
```sh
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo
```

---

## 1. macOS (Apple Silicon & Intel)

### Requirements
- macOS 13 (Ventura) or newer
- Xcode Command Line Tools: `xcode-select --install`
- Rust stable: `rustup default stable`
- Rust targets:
  ```sh
  rustup target add aarch64-apple-darwin
  rustup target add x86_64-apple-darwin
  ```

### Build Commands
```sh
# Build Universal 2 DMG (Apple Silicon + Intel):
./platforms/macos/scripts/create-dmg.sh universal

# Or build Apple Silicon only:
./platforms/macos/scripts/create-dmg.sh arm64

# Or build Intel Mac only:
./platforms/macos/scripts/create-dmg.sh x86_64
```
Artifacts are saved into `platforms/macos/release/`.

---

## 2. Linux (Ubuntu, Debian, Fedora, Arch)

### Requirements
- Linux development headers:
  ```bash
  sudo apt install -y build-essential curl python3 cmake ninja-build \
    libibus-1.0-dev libfcitx5core-dev libgtk-4-dev libadwaita-1-dev dpkg-dev
  ```
- Rust stable: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

### Build Commands
```bash
# Compile core Rust engine:
(cd platforms/linux/engine && cargo build --release)

# Build and test the fcitx5 addon:
export BONGO_ENGINE_LIB="$PWD/platforms/linux/engine/target/release/libbongo_engine.so"
cmake -S platforms/linux/fcitx5 -B build/fcitx5 -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build/fcitx5
ctest --test-dir build/fcitx5 --output-on-failure

# Build Debian / Ubuntu .deb package:
BONGO_FCITX5=1 ./platforms/linux/scripts/build-deb.sh

# Build Fedora / RHEL .rpm package:
BONGO_FCITX5=1 ./platforms/linux/scripts/build-rpm.sh
```
Artifacts are saved into `platforms/linux/release/`.

The package builders include both frontends and recommend IBus and fcitx5
instead of requiring either one. Set `BONGO_FCITX5=0` only when building a
package without the fcitx5 addon.

---

## 3. Windows (Windows 10 & 11)

### Requirements
- Windows 10 (1903+) or Windows 11 (64-bit)
- Python 3.10+ with `pyinstaller` and `requests`: `pip install pyinstaller requests`
- Inno Setup 6 (installed to `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`)
- WiX Toolset v4/v5/v7 (available in PATH via `wix`)
- Rust toolchain (optional, for compiling `bongo_engine.dll` from source)

### Build Commands
```cmd
:: Build both Setup (.exe) and MSI packages:
platforms\windows\scripts\build-windows.bat

:: Or build via PowerShell:
powershell -ExecutionPolicy Bypass -File platforms\windows\scripts\build-windows.ps1
```
Artifacts are saved into `platforms/windows/release/`:
- `Bongo-Setup-1.0.1.exe`
- `Bongo-1.0.1-x64.msi`
- `Bongo-1.0.1-windows-portable.zip`
- Accompanying `.sha256` checksums

---

## 4. Automated Verification Suite

Run the distribution integrity test suite from the repository root:
```sh
python3 -m unittest discover -s tests -v
```
All 6 platform verification tests must pass.
