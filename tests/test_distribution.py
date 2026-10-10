"""Validate Apple Silicon native identity isolation and resource integrity without activating an IME."""
import plistlib
from pathlib import Path
import unittest
import json

ROOT = Path(__file__).resolve().parents[1]

class DistributionTests(unittest.TestCase):
    def test_macos_registration(self):
        p = plistlib.loads((ROOT / 'platforms/macos/Bongo/Resources/Info.plist').read_bytes())
        self.assertEqual(p['CFBundleIdentifier'], 'org.bongo.inputmethod.Bongo')
        self.assertEqual(p['InputMethodServerControllerClass'], 'BongoInputController')
        self.assertEqual(p['TISIntendedLanguage'], 'bn')
        self.assertEqual(p['TISInputSourceID'], p['CFBundleIdentifier'])
        self.assertEqual(p['LSArchitecturePriority'], ['arm64'])
        controller = (ROOT / 'platforms/macos/Bongo/Sources/InputController.swift').read_text()
        self.assertIn('@objc(' + p['InputMethodServerControllerClass'] + ')', controller)
        main = (ROOT / 'platforms/macos/Bongo/Sources/main.swift').read_text()
        self.assertIn(p['InputMethodConnectionName'], main)
        welcome = (ROOT / 'platforms/macos/Bongo/Sources/WelcomeWindow.swift').read_text()
        self.assertIn('final class SidebarNavigationButton: NSButton', welcome)
        self.assertIn('acceptsFirstMouse(for event:', welcome)
        for title in ['Getting Started', 'Bongo Layout', 'Settings', 'Fonts']:
            self.assertIn('"' + title + '"', welcome)
        self.assertNotIn('"Avro Layout"', welcome)
        self.assertNotIn('On-device typing', welcome)
        self.assertIn('final class FontsView: NSView', welcome)
        self.assertIn('BongoFontSettings.font()', (ROOT / 'platforms/macos/Bongo/Sources/CandidatePanel.swift').read_text())
        self.assertTrue(p['TISIconIsTemplate'])
        icon = ROOT / 'platforms/macos/Bongo/Resources' / (p['tsInputMethodIconFileKey'] + '.pdf')
        self.assertTrue(icon.is_file())

        launcher_plist = plistlib.loads((ROOT / 'platforms/macos/Launcher/Resources/Info.plist').read_bytes())
        self.assertEqual(launcher_plist['CFBundleIdentifier'], 'org.bongo.Bongo')
        self.assertEqual(launcher_plist['LSArchitecturePriority'], ['arm64'])
        self.assertNotIn('LSUIElement', launcher_plist)
        launcher = (ROOT / 'platforms/macos/Launcher/Sources/main.swift').read_text()
        self.assertIn('org.bongo.inputmethod.Bongo', launcher)
        self.assertIn('Contents/Library/Input Methods/Bongo Input Method.app', launcher)
        self.assertIn('installInputMethod(from:', launcher)
        self.assertIn('CFBundleVersion', launcher)
        self.assertIn('configuration.arguments = ["--show-settings"]', launcher)
        self.assertIn('CommandLine.arguments.contains("--show-settings")', (ROOT / 'platforms/macos/Bongo/Sources/AppDelegate.swift').read_text())

    def test_apple_silicon_only_architecture(self):
        # Ensure no legacy platforms remain
        self.assertFalse((ROOT / 'platforms/linux').exists(), 'Linux platform directory should not exist')
        self.assertFalse((ROOT / 'platforms/windows').exists(), 'Windows platform directory should not exist')
        self.assertFalse((ROOT / 'licenses/GPL-3.0.txt').exists(), 'Linux GPL license should not exist')
        self.assertFalse((ROOT / 'licenses/MPL-1.1.txt').exists(), 'Windows MPL-1.1 license should not exist')
        self.assertFalse((ROOT / 'docs/LINUX-INSTALL.md').exists(), 'Linux install doc should not exist')

        # Check create-dmg.sh restricts to Apple Silicon
        script = (ROOT / 'platforms/macos/scripts/create-dmg.sh').read_text()
        self.assertIn('Apple Silicon (arm64) required', script)
        self.assertIn('aarch64-apple-darwin', script)
        self.assertIn('arm64-apple-macos13.0', script)
        self.assertNotIn('BUILD_UNIVERSAL', script)
        self.assertNotIn('x86_64-apple-darwin', script)

        # Ensure upstream.lock.json only has macOS Apple Silicon components
        upstream = json.loads((ROOT / 'upstream.lock.json').read_text())
        self.assertIn('Lekho', upstream)
        self.assertIn('riti-macos', upstream)
        self.assertNotIn('OpenBangla-Keyboard', upstream)
        self.assertNotIn('riti-linux', upstream)
        self.assertNotIn('Avro-Keyboard', upstream)

    def test_release_artifact_layout(self):
        for name in ['install.sh', 'uninstall.sh', 'create_dmg.sh']:
            self.assertFalse((ROOT / 'platforms/macos/scripts' / name).exists())
        self.assertFalse((ROOT / 'scripts/Register Bongo.command').exists())
        release = (ROOT / 'platforms/macos/scripts/create-dmg.sh').read_text()
        self.assertNotIn('BongoRegister', release)
        self.assertNotIn('Register Bongo.command', release)
        self.assertIn('$STAGE/Bongo.app', release)
        self.assertNotIn('$STAGE/Bongo Input Method.app', release)
        self.assertIn('Contents/Library/Input Methods/Bongo Input Method.app', release)
        self.assertIn("ln -s '/Applications'", release)
        self.assertNotIn("ln -s '/Library/Input Methods'", release)
        self.assertIn('RELEASE_DIR="$PROJECT_ROOT/release"', release)
        self.assertNotIn('dist/', release)

        self.assertTrue((ROOT / 'platforms/macos/release/.gitkeep').is_file())
        scripts = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / 'platforms').glob('*/scripts/*')
            if path.is_file()
        }
        self.assertEqual(scripts, {
            'platforms/macos/scripts/create-dmg.sh',
        })
        self.assertFalse((ROOT / 'scripts').exists())

    def test_updates_use_bongo_release_configuration(self):
        mac = (ROOT / 'platforms/macos/Bongo/Sources/WelcomeWindow.swift').read_text()
        self.assertIn('BongoGitHubRepository', mac)
        self.assertIn('api.github.com/repos/', mac)
        self.assertIn('releases?per_page=1', mac)
        self.assertIn('No newer release is published yet', mac)
        self.assertIn('statusCode == 404', mac)
        self.assertNotIn('openbangla.github.io', mac)
        self.assertNotIn('omicronlab.com/download/liveupdate', mac)

if __name__ == '__main__':
    unittest.main()
