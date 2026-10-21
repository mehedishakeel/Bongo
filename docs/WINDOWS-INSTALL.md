# Installing Bongo on Windows

Bongo provides native Avro phonetic Bengali typing on modern Windows (Windows 10 and Windows 11, x64 and ARM64).

---

## Supported Windows Versions

* **Windows 11**: All editions (Home, Pro, Enterprise)
* **Windows 10**: Version 1903 and newer (64-bit and ARM64)
* **Windows Server**: 2019, 2022, and newer

---

## Option 1: Install via Setup Executable (.exe)

This is the recommended installation method for all individual users:

1. Download **`Bongo-Setup-1.1.0.exe`** from the [GitHub Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page.
2. Run the installer:
   * Select your preferred options (desktop shortcut, start on Windows startup).
   * Click **Install**.
3. Once completed, Bongo starts automatically in your taskbar notification area.
4. Press **`F12`** anywhere (browser, Word, Notepad, IDE) to toggle between Bangla and English mode.

---

## Option 2: Enterprise Deployment (.msi)

For network administrators and silent deployments:

1. Download **`Bongo-1.1.0-x64.msi`** from the [GitHub Releases](https://github.com/mehedishakeel/Bongo/releases/latest) page.
2. Install silently via command line or group policy:

```cmd
msiexec /i Bongo-1.1.0-x64.msi /qn /norestart
```

---

## Option 3: Portable Package (No Administrator Rights Needed)

For users on restricted or managed enterprise PCs:

1. Download **`Bongo-1.1.0-windows-portable.zip`** from [Releases](https://github.com/mehedishakeel/Bongo/releases/latest).
2. Extract the archive into any folder (e.g. `C:\Users\<YourUser>\Bongo`).
3. Launch `bongo.exe`. Bongo is immediately active in your system tray without requiring installation or UAC elevation.

---

## Option 3: Developer Setup from Source

If you want to contribute or build Bongo locally:

### Prerequisites
* Install Python 3.10 or newer (ensure Python and pip are added to your PATH).
* Install Rust toolchain: `winget install Rustlang.Rustup` or from [rustup.rs](https://rustup.rs).

### Build & Run
```cmd
git clone https://github.com/mehedishakeel/Bongo.git
cd Bongo

:: Run the background typing service directly
python platforms\windows\service\bongo_service.py

:: Or launch the Settings UI
python platforms\windows\ui\bongo_settings.py
```

---

## Quick Reference & Shortcuts

| Action | Keystroke | Description |
| :--- | :--- | :--- |
| **Toggle Bangla/English** | `F12` | Switches typing language instantly across all apps |
| **Commit Word** | `Space` / `Enter` | Commits current phonetic candidate |
| **Candidate Select** | `1` - `9` | Selects numbered suggestion from candidate bar |
| **Cancel Composition** | `Esc` | Discards active phonetic preedit |
| **Backspace** | `Backspace` | Deletes previous character or stroke |

---

## Recommended Bengali Fonts for Windows

For the best visual rendering of complex conjuncts and typography on Windows:

* **Noto Sans Bengali** (Downloadable free from Google Fonts)
* **Kalpurush** (Classic, highly legible Bengali typeface)
* **SolaimanLipi** (Popular newspaper and web font)
* **Vrinda** (Included with standard Windows Bengali language pack)
* **Nirmala UI** (Built into Windows 10/11)
