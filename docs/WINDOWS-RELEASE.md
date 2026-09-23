# Windows release status

Bongo uses OmicronLab's actual Avro Win32 keyboard implementation, preserving
its phonetic engine, system-wide hook, candidates, layouts and Unicode output.
This is a legacy Delphi source target, not a tested Windows release.

The upstream Readme.txt specifies **Delphi 2010**, plus **DISQLite3**, **ICS**,
**JCL** and **JVCL**. They are not all included or installed here. DISQLite3 is
listed by upstream as freeware rather than open source. Obtain appropriate
versions/licenses independently; this repository does not fabricate those dependencies.

Maintainers with the required Delphi environment create the release executable with:

```powershell
./platforms/windows/scripts/create-exe.ps1
```

The script compiles Bongo.rc with brcc32 and Bongo.dpr with dcc32, writing
`dist/windows/Bongo.exe`. The original Avro project remains for reference;
always build **Bongo.dpr** for the Bongo product.

Runtime data also needs to be provisioned and tested: the source expects
`Database.db3`, keyboard layouts, skins and support files. These runtime assets
are not all present in OmicronLab's source repository. A successful executable
compile alone would not make a complete distribution. Do not publish an executable
until the runtime payload is assembled with appropriate redistribution rights.

Bongo changes the registry to `Software\Bongo\Keyboard`, application data to
Bongo, startup entry, mutex, main window class/IPC identity, resource metadata,
and visible text. The legacy upstream updater remains disabled. Until the native
release is complete, check the project's GitHub Releases feed with:

```powershell
./platforms/windows/scripts/check-update.ps1 -Repository owner/Bongo -Open
```

The phonetic method still
uses the accurate name **Avro Phonetic** and the original author credits remain.
Some embedded legacy artwork may still need replacement after a Windows visual review.

Required release checks: Unicode typing and undo in Notepad/Word/browsers,
backspace and caret movement, shortcuts and mode switching, elevated applications,
32/64-bit hosts, keyboard coexistence, antivirus/signing and clean removal.
No Windows executable has been built on this Mac.
