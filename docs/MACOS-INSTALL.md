# Bongo for Apple Silicon

Requires macOS 13 or later and an Apple Silicon Mac. Download the current DMG
from the project's GitHub Releases page.

## Install from DMG (all users)

Open the DMG and drag Bongo.app onto the Input Methods shortcut. This is the system
`/Library/Input Methods` folder, so Finder may request administrator authentication.
Alternatively, copy Bongo.app into your own `~/Library/Input Methods` folder.
Do not install both copies. Log out and back in after copying the app.

## Activate

1. Close and reopen Keyboard settings after logging back in.
2. Open System Settings → Keyboard → Input Sources → Edit → +.
3. Find and add Bongo (under Bengali if grouped by language).
4. Use Globe or Control-Space to switch to it, then type `ami` in TextEdit: `আমি`.
5. Open Bongo's settings from its input menu to choose your typing mode.

The keyboard uses InputMethodKit, so it does not require an Accessibility keylogger
permission. Password fields and some applications intentionally restrict input methods.

## Remove

Remove Bongo from Input Sources, delete the installed `Bongo.app` from the Input
Methods folder, then log out and back in. Learned words remain in
`~/Library/Application Support/Bongo` unless you remove that folder manually.

## Update

Open Bongo's settings window, choose **Preferences**, and click **Check for
Updates**. Release builds check the project's latest GitHub Release and open its
download page when a newer version exists. Installing the replacement preserves
learned words and settings in your user Library.
