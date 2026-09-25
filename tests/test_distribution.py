"""Validate native identity isolation and resource integrity without activating an IME."""
import plistlib
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class DistributionTests(unittest.TestCase):
    def test_macos_registration(self):
        p = plistlib.loads((ROOT / 'platforms/macos/Bongo/Resources/Info.plist').read_bytes())
        self.assertEqual(p['CFBundleIdentifier'], 'org.bongo.inputmethod.Bongo')
        self.assertEqual(p['InputMethodServerControllerClass'], 'BongoInputController')
        self.assertEqual(p['TISIntendedLanguage'], 'bn')
        self.assertEqual(p['TISInputSourceID'], p['CFBundleIdentifier'])
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
        self.assertNotIn('LSUIElement', launcher_plist)
        launcher = (ROOT / 'platforms/macos/Launcher/Sources/main.swift').read_text()
        self.assertIn('org.bongo.inputmethod.Bongo', launcher)
        self.assertIn('Contents/Library/Input Methods/Bongo Input Method.app', launcher)
        self.assertIn('installInputMethod(from:', launcher)
        self.assertIn('CFBundleVersion', launcher)
        self.assertIn('configuration.arguments = ["--show-settings"]', launcher)
        self.assertIn('CommandLine.arguments.contains("--show-settings")', (ROOT / 'platforms/macos/Bongo/Sources/AppDelegate.swift').read_text())

    def test_linux_registration(self):
        p = ET.parse(ROOT / 'platforms/linux/data/bongo.xml.in').getroot()
        self.assertEqual(p.findtext('name'), 'org.freedesktop.IBus.Bongo')
        self.assertEqual(p.findtext('engines/engine/name'), 'Bongo')
        source = (ROOT / 'platforms/linux/src/engine/ibus/main.cpp').read_text()
        self.assertIn('"org.freedesktop.IBus.Bongo"', source)
        self.assertIn('"Bongo"', source)
        ipc = (ROOT / 'platforms/linux/src/frontend/main.cpp').read_text()
        self.assertIn('"org.bongo.keyboard"', ipc)
        self.assertNotIn('"com.openbangla.keyboard"', ipc)
        self.assertTrue((ROOT / 'platforms/linux/src/engine/riti/Cargo.lock').is_file())
        cargo_cmake = (ROOT / 'platforms/linux/cmake/CMakeCargo.cmake').read_text()
        self.assertIn('list(APPEND CARGO_ARGS "--locked")', cargo_cmake)
        topbar = (ROOT / 'platforms/linux/src/frontend/TopBar.cpp').read_text()
        self.assertIn('available.right() - width() - margin + 1', topbar)
        self.assertNotIn('available.center()', topbar)
        metadata = (ROOT / 'platforms/linux/data/avrophonetic.json').read_text()
        self.assertIn('"name": "Bongo Phonetic"', metadata)
        self.assertNotIn('Mehdi Hasan', metadata)
        self.assertNotIn('OmicronLab', metadata)
        viewer = (ROOT / 'platforms/linux/src/frontend/LayoutViewer.ui').read_text()
        for removed_control in ['viewNormal', 'viewAltGr', 'buttonAboutLayout']:
            self.assertNotIn(removed_control, viewer)
        self.assertTrue((ROOT / 'platforms/linux/src/frontend/images/bongo_phonetic_layout.png').is_file())
        self.assertFalse((ROOT / 'platforms/linux/src/frontend/AboutFile.cpp').exists())

    def test_qt_resources_resolve(self):
        for qrc in (ROOT / 'platforms/linux').rglob('*.qrc'):
            for f in ET.parse(qrc).iter('file'):
                self.assertTrue((qrc.parent / f.text).is_file(), str(qrc.parent / f.text))

    def test_windows_identity(self):
        base = ROOT / 'platforms/windows/Keyboard and Spell checker'
        self.assertIn("'Bongo_Keyboard'", (base / 'Bongo.dpr').read_text())
        self.assertIn("'TBongoMainForm1'", (base / 'Units/uCommandLineFunctions.pas').read_text())
        settings = (base / 'Units/uRegistrySettings.pas').read_text()
        self.assertIn('Software\\Bongo\\Keyboard', settings)
        self.assertNotIn('Software\\OmicronLab\\Avro Keyboard', settings)
        self.assertTrue((base / 'Bongo.ico').is_file())

    def test_windows_ui_and_optional_tools(self):
        base = ROOT / 'platforms/windows/Keyboard and Spell checker'
        main = (base / 'Forms/uForm1.pas').read_text(errors='replace')
        main_form = (base / 'Forms/uForm1.dfm').read_text(errors='replace')
        self.assertNotIn('InternetCheck', main + main_form)
        self.assertNotIn('TUpdateCheck', main)
        self.assertFalse((base / 'Classes/clsUpdateInfoDownloader.pas').exists())
        self.assertFalse((base / 'Forms/ufrmUpdateNotify.pas').exists())
        self.assertIn("Spellcheck1.Visible := FileExists", main)
        self.assertIn("Layout Editor.exe", main)
        for form in (ROOT / 'platforms/windows').rglob('*.dfm'):
            captions = '\n'.join(
                line for line in form.read_text(errors='replace').splitlines()
                if 'Caption =' in line or 'Hint =' in line
            )
            self.assertNotIn('OmicronLab', captions, str(form))
            self.assertNotIn('Avro Keyboard', captions, str(form))

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

        linux_release = (ROOT / 'platforms/linux/scripts/create-deb.sh').read_text()
        linux_cmake = (ROOT / 'platforms/linux/CMakeLists.txt').read_text()
        windows_release = (ROOT / 'platforms/windows/scripts/create-exe.ps1').read_text()
        self.assertIn('platforms/linux/release', linux_release)
        self.assertIn('THIRD_PARTY_NOTICES.md', linux_cmake)
        self.assertIn('RITI-MPL-2.0.txt', linux_cmake)
        self.assertIn('platforms/windows/release', windows_release)
        self.assertNotIn('dist/', release + linux_release + windows_release)
        for platform in ['macos', 'linux', 'windows']:
            self.assertTrue((ROOT / 'platforms' / platform / 'release' / '.gitkeep').is_file())
        scripts = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / 'platforms').glob('*/scripts/*')
            if path.is_file()
        }
        self.assertEqual(scripts, {
            'platforms/linux/scripts/create-deb.sh',
            'platforms/macos/scripts/create-dmg.sh',
            'platforms/windows/scripts/create-exe.ps1',
        })
        self.assertFalse((ROOT / 'scripts').exists())

    def test_updates_use_bongo_release_configuration(self):
        mac = (ROOT / 'platforms/macos/Bongo/Sources/WelcomeWindow.swift').read_text()
        self.assertIn('BongoGitHubRepository', mac)
        self.assertIn('api.github.com/repos/', mac)
        self.assertIn('releases?per_page=1', mac)
        self.assertIn('No newer release is published yet', mac)
        self.assertIn('statusCode == 404', mac)
        linux = (ROOT / 'platforms/linux/src/frontend/TopBar.cpp').read_text()
        self.assertIn('BONGO_GITHUB_REPOSITORY', linux)
        self.assertIn('gSettings->getUpdateCheck()', linux)
        self.assertNotIn('gSettings->getCheckUpdate()', linux)
        self.assertIn('api.github.com/repos/', linux)
        self.assertIn('releases?per_page=1', linux)
        self.assertIn('No newer release is published yet', linux)
        self.assertIn('statusCode == 404', linux)
        self.assertNotIn('QSimpleUpdater', linux)
        self.assertIn('timeout->start(15000)', linux)
        win = (ROOT / 'platforms/windows/Keyboard and Spell checker/Forms/uForm1.pas').read_text()
        self.assertIn('github.com/mehedishakeel/Bongo/releases/latest', win)
        self.assertNotIn('clsUpdateInfoDownloader', win)
        combined = mac + linux + win
        self.assertNotIn('openbangla.github.io', combined)
        self.assertNotIn('omicronlab.com/download/liveupdate', combined)

    def test_github_pages_site(self):
        site = ROOT / 'docs'
        for name in ['index.html', 'styles.css', 'script.js', 'NOTICE.md', '.nojekyll', 'assets/bongo-icon.png']:
            self.assertTrue((site / name).is_file(), name)
        html = (site / 'index.html').read_text()
        self.assertIn('Developed by Mehedi Shakeel', html)
        self.assertIn('github.com/mehedishakeel/Bongo/releases/latest', html)
        self.assertNotIn('Powered by Lekho', html)
        self.assertNotIn('arahim.dev', html)
        footer = html.split('<footer>', 1)[1]
        self.assertNotIn('>Credits<', footer)
        self.assertNotIn('>License<', footer)
        self.assertIn('https://github.com/mehedishakeel">Developed by Mehedi Shakeel', html)
        for upstream in ['Avro Keyboard', 'Lekho', 'OpenBangla Keyboard', 'riti']:
            self.assertIn(upstream, html)
        self.assertIn('CC0-1.0', html)
        css = (site / 'styles.css').read_text()
        self.assertIn('@media (prefers-color-scheme: dark)', css)

if __name__ == '__main__':
    unittest.main()
