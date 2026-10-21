# Bongo for Windows

Native Avro phonetic Bengali input method for modern Windows desktops (Windows 10 and 11, x64 and ARM64).

Powered by a pure-Rust transliteration engine connected through a low-level keyboard hook background service, a modern dark-themed Settings application, and professional setup packages (.exe and .msi).

---

## Architecture Overview

```
platforms/windows/
├── data/
│   ├── bongo.ico                        # Multi-size Windows application icon
│   └── bongo.png                        # High-resolution raster logo
├── engine/                              # Rust transliteration engine (C ABI)
│   ├── Cargo.toml
│   └── src/lib.rs                       # Shared library entry point (bongo_engine.dll)
├── installer/                           # Packaging definitions
│   ├── bongo.iss                        # Inno Setup 6 installer script (.exe)
│   └── bongo.wxs                        # WiX Toolset installer script (.msi)
├── scripts/
│   ├── build-windows.bat                # Automated batch build script
│   ├── package_windows.py               # Cross-platform packaging verification
│   └── install-windows.ps1              # PowerShell developer setup script
├── service/                             # Background input method service
│   └── bongo_service.py                 # Low-level keyboard hook and SendInput daemon
└── ui/
    └── bongo_settings.py                # Native Settings and Welcome application
```

---

## Features

* **Universal Compatibility**: Works across all Windows applications including browsers (Chrome, Edge, Firefox), Microsoft Office (Word, PowerPoint), editors (VS Code, Notepad), and messaging apps.
* **Instant Toggle**: Switch between English and Bangla at any moment using `F12` or `Ctrl + Space` (customizable in Settings).
* **Native Look and Feel**: Dark mode Settings application with 4 sections (Getting Started, Bongo Layout, Settings, Fonts).
* **Live Candidate HUD**: Floating candidate bar preview with configurable Bengali fonts and sizes.
* **Diagnostics & Logging**: Service activity and keystroke events are logged to `%APPDATA%\Bongo\bongo_service.log` for easy troubleshooting.
* **Clean Distribution**: Available as a standard Inno Setup executable (`Bongo-Setup-1.1.0.exe`), an enterprise MSI package (`Bongo-1.1.0-x64.msi`), and a portable ZIP (`Bongo-1.1.0-windows-portable.zip`).

---

## Prerequisites for Building

* **Windows 10 / 11** (x64 or ARM64)
* **Python 3.10+** (with Tkinter included by default)
* **Rust toolchain** (`rustup default stable`)
* **Inno Setup 6** (for building `.exe` setup package)
* **WiX Toolset v3 / v4** (for building `.msi` package)

---

## Building from Source

From the project root on a Windows terminal:

```cmd
platforms\windows\scripts\build-windows.bat
```

This will:
1. Compile `bongo_engine.dll` using Cargo.
2. Compile standalone executables `bongo.exe` and `bongo-settings.exe` using PyInstaller.
3. Build the Inno Setup installer `platforms\windows\release\Bongo-Setup-1.1.0.exe`.
4. Build the WiX MSI installer `platforms\windows\release\Bongo-1.1.0-x64.msi`.
5. Build the Portable ZIP package `platforms\windows\release\Bongo-1.1.0-windows-portable.zip`.
5. Generate SHA256 checksums for each release package.

---

## Developer Quick Start

To run Bongo directly without building installers:

```powershell
# Start the background typing service
python platforms\windows\service\bongo_service.py

# Or launch the Settings UI
python platforms\windows\ui\bongo_settings.py
```

Press `F12` to toggle Bangla typing on or off in any text field.
