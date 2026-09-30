# Bongo for Apple Silicon

Requires macOS 13 or later and an Apple Silicon Mac (M1/M2/M3/M4 or later). Download the current DMG from the project's [GitHub Releases](https://github.com/mehedishakeel/Bongo/releases) page.

## Install from DMG (all users)

1. Open the DMG and drag **Bongo.app** onto **Applications**.
2. Open **Bongo** from Applications and choose **Install** when it asks to install the keyboard. Bongo copies its embedded input method to your `~/Library/Input Methods` folder without requiring an administrator password.
3. Log out and back in once after first installation.

## Activate

1. Open **System Settings** → **Keyboard** → **Input Sources** → **Edit...** → **+**.
2. Find and add **Bongo** (listed under Bengali).
3. Use Globe (🌐) or Control-Space to switch to Bongo, then type `ami` in TextEdit: `আমি`.
4. Open **Bongo** from Applications to view the layout guide or change typing and font settings. You can also open settings directly from the Bongo menu bar item.

The keyboard uses native InputMethodKit, so it does not require Accessibility / keystroke logging permissions.

## Remove

1. Remove Bongo from macOS System Settings → Keyboard → Input Sources.
2. Delete `Bongo.app` from `/Applications`.
3. Delete `~/Library/Input Methods/Bongo.app`.
4. Log out and back in.
Learned words and preferences remain in `~/Library/Application Support/Bongo` unless removed manually.

## Update

Open Bongo from Applications, choose **Settings**, and click **Check for Updates**. Release builds query the official GitHub Releases API and open the latest release page when a newer version exists.
