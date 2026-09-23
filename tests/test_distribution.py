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

    def test_release_artifacts_require_manual_installation(self):
        for name in ['install.sh', 'uninstall.sh', 'create_dmg.sh']:
            self.assertFalse((ROOT / 'platforms/macos/scripts' / name).exists())
        self.assertFalse((ROOT / 'scripts/Register Bongo.command').exists())
        release = (ROOT / 'platforms/macos/scripts/create-dmg.sh').read_text()
        self.assertNotIn('BongoRegister', release)
        self.assertNotIn('Register Bongo.command', release)

    def test_updates_use_bongo_release_configuration(self):
        mac = (ROOT / 'platforms/macos/Bongo/Sources/WelcomeWindow.swift').read_text()
        self.assertIn('BongoGitHubRepository', mac)
        self.assertIn('api.github.com/repos/', mac)
        linux = (ROOT / 'platforms/linux/src/frontend/TopBar.cpp').read_text()
        self.assertIn('BONGO_UPDATE_URL', linux)
        self.assertIn('gSettings->getUpdateCheck()', linux)
        self.assertNotIn('gSettings->getCheckUpdate()', linux)
        self.assertIn('updater->checkForUpdates(DEFS_URL)', linux)
        win = (ROOT / 'platforms/windows/Keyboard and Spell checker/Classes/clsUpdateInfoDownloader.pas').read_text()
        self.assertEqual(win.count('Exit; { Bongo: upstream updates disabled. }'), 2)
        combined = mac + linux
        self.assertNotIn('openbangla.github.io', combined)
        self.assertNotIn('omicronlab.com/download/liveupdate', combined)

if __name__ == '__main__':
    unittest.main()
