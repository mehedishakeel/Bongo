# Bongo for Apple Silicon

Requires macOS 13 or later and an Apple Silicon Mac. Download the current DMG
from the project's GitHub Releases page.

## Install from DMG (all users)

Open the DMG and drag **Bongo.app** onto **Applications**. Open Bongo and choose
**Install** when it asks to install the keyboard. Bongo copies its signed embedded
input method to your `~/Library/Input Methods` folder without an administrator
password. Log out and back in once after the first installation.

## Activate

1. Close and reopen Keyboard settings after logging back in.
2. Open System Settings → Keyboard → Input Sources → Edit → +.
3. Find and add Bongo (under Bengali if grouped by language).
4. Use Globe or Control-Space to switch to it, then type `ami` in TextEdit: `আমি`.
5. Open Bongo from Applications to view the Avro layout or change typing and font
   settings. You can also open it from Bongo's input menu.

The keyboard uses InputMethodKit, so it does not require an Accessibility keylogger
permission. Password fields and some applications intentionally restrict input methods.

## Remove

Remove Bongo from Input Sources, delete `Bongo.app` from Applications and delete
`~/Library/Input Methods/Bongo.app`, then log out and back in. Learned words remain in
`~/Library/Application Support/Bongo` unless you remove that folder manually.

## Update

Open Bongo from Applications, choose **Settings**, and click **Check for
Updates**. Release builds check the project's latest GitHub Release and open its
download page when a newer version exists. Installing the replacement preserves
learned words and settings in your user Library.
